#!/usr/bin/env python3
"""Create and seed a simulated CRM alongside Phoenix, without changing store data."""
import datetime,hashlib,json,pathlib,random,secrets,subprocess,sys
from zoneinfo import ZoneInfo
ROOT=pathlib.Path('/opt/terra-nostra')
COMPOSE=['docker','compose','--env-file',str(ROOT/'azure/cloud.env'),'-f',str(ROOT/'azure/compose.yaml')]
DB='terra_nostra_crm';VERSION='terra-nostra-crm-v1'
def mysql(sql):
    command=COMPOSE+['exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --default-character-set=utf8mb4 --batch --raw --skip-column-names']
    p=subprocess.run(command,input=sql.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout.decode().strip()
def q(v):
    if v is None:return 'NULL'
    if isinstance(v,(int,float)):return str(v)
    return "'"+str(v).replace('\\','\\\\').replace("'","\\'")+"'"
def ins(table,data):return 'INSERT INTO '+DB+'.'+table+' (`'+'`,`'.join(data)+'`) VALUES ('+','.join(q(v) for v in data.values())+');'
def store_hash():
    cmd=COMPOSE+['exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --no-tablespaces --no-create-info --skip-extended-insert --skip-comments --compact -u"$MYSQL_USER" phoenix customers products orders orders_products orders_total']
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return hashlib.sha256(p.stdout).hexdigest()
before=store_hash()
mysql('''CREATE DATABASE IF NOT EXISTS terra_nostra_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS terra_nostra_crm.seed_runs (version varchar(64) PRIMARY KEY,seeded_at datetime NOT NULL,anchor_date date NOT NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS terra_nostra_crm.customers (
 crm_customer_id bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
 crm_code varchar(32) NOT NULL UNIQUE,
 ecommerce_customer_id int NULL UNIQUE,
 first_name varchar(100) NOT NULL,last_name varchar(150) NOT NULL,
 email varchar(255) NOT NULL UNIQUE,
 province varchar(100) NOT NULL,city varchar(100) NOT NULL,
 customer_type enum('Cliente','Prospecto') NOT NULL,
 segment varchar(50) NOT NULL,
 acquisition_channel varchar(50) NOT NULL,
 preferred_contact_channel varchar(50) NOT NULL,
 lifecycle_stage varchar(50) NOT NULL,
 marketing_consent boolean NOT NULL DEFAULT FALSE,
 registered_at datetime NOT NULL,last_contact_at datetime NULL,created_at datetime NOT NULL,
 INDEX idx_province(province),INDEX idx_segment(segment),INDEX idx_acquisition(acquisition_channel)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS terra_nostra_crm.interactions (
 interaction_id bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
 interaction_key varchar(64) NOT NULL UNIQUE,
 crm_customer_id bigint unsigned NOT NULL,
 contact_channel varchar(50) NOT NULL,
 interaction_type varchar(50) NOT NULL,
 occurred_at datetime NOT NULL,
 outcome varchar(80) NOT NULL,
 notes text NOT NULL,
 CONSTRAINT fk_crm_interaction_customer FOREIGN KEY(crm_customer_id) REFERENCES terra_nostra_crm.customers(crm_customer_id),
 INDEX idx_contact_date(occurred_at)
) ENGINE=InnoDB;''')
secret_file=ROOT/'azure/crm.env'
if not secret_file.exists():
    secret_file.write_text('CRM_DATABASE='+DB+'\nCRM_USER=terra_crm\nCRM_PASSWORD='+secrets.token_hex(24)+'\nETL_USER=terra_etl\nETL_PASSWORD='+secrets.token_hex(24)+'\n')
    secret_file.chmod(0o600)
env=dict(line.split('=',1) for line in secret_file.read_text().splitlines() if '=' in line)
mysql("CREATE USER IF NOT EXISTS 'terra_crm'@'%' IDENTIFIED BY "+q(env['CRM_PASSWORD'])+"; GRANT SELECT,INSERT,UPDATE,DELETE ON terra_nostra_crm.* TO 'terra_crm'@'%'; CREATE USER IF NOT EXISTS 'terra_etl'@'%' IDENTIFIED BY "+q(env['ETL_PASSWORD'])+"; GRANT SELECT ON terra_nostra_crm.* TO 'terra_etl'@'%'; GRANT SELECT ON phoenix.* TO 'terra_etl'@'%';")
if mysql('SELECT COUNT(*) FROM '+DB+'.seed_runs WHERE version='+q(VERSION))=='1':
    assert store_hash()==before,'Store changed while checking CRM seed'
    print('CRM already seeded; existing data and edits preserved.');sys.exit(0)
raw=mysql("SELECT JSON_ARRAYAGG(JSON_OBJECT('id',c.customers_id,'first',c.customers_firstname,'last',c.customers_lastname,'email',c.customers_email_address,'province',a.entry_state,'city',a.entry_city,'registered',ci.customers_info_date_account_created)) FROM phoenix.customers c JOIN phoenix.address_book a ON a.address_book_id=c.customers_default_address_id AND a.customers_id=c.customers_id JOIN phoenix.customers_info ci ON ci.customers_info_id=c.customers_id;")
store_customers=sorted(json.loads(raw),key=lambda c:c['id'])
now=datetime.datetime.now(ZoneInfo('America/Costa_Rica')).replace(tzinfo=None,microsecond=0)
anchor=now.replace(hour=0,minute=0,second=0)
channels=['Instagram','Facebook','Google','Recomendación','Feria local','Visita directa']
contact=['WhatsApp','Correo electrónico','Teléfono']
provinces=[('San José','San José'),('Alajuela','Alajuela'),('Cartago','Paraíso'),('Heredia','Heredia'),('Guanacaste','Liberia'),('Puntarenas','Puntarenas'),('Limón','Limón')]
first=['Valentina','Emilio','Daniela','Julián','Renata','Tomás','Gabriela','Adrián','Victoria','Samuel','Carolina','Javier','Andrea','Mauricio','Fernanda','Esteban','Jimena','Pablo','Verónica','Roberto']
last=['Salas','Montero','Alfaro','Ramírez','Aguilar','Villalobos','Quesada','Campos','Soto','Méndez']
data=[]
for i,c in enumerate(store_customers):
    data.append({'crm_code':f'TN-C-{c["id"]:05d}','ecommerce_customer_id':c['id'],'first_name':c['first'],'last_name':c['last'],'email':c['email'],'province':c['province'] or 'Cartago','city':c['city'] or 'Paraíso','customer_type':'Cliente','segment':['Frecuente','Ocasional','Premium','Reactivación'][i%4],'acquisition_channel':channels[i%6],'preferred_contact_channel':contact[i%3],'lifecycle_stage':'Cliente activo','marketing_consent':0,'registered_at':c['registered'],'created_at':now})
for i in range(20):
    province,city=provinces[i%7]
    data.append({'crm_code':f'TN-P-{i+1:05d}','ecommerce_customer_id':None,'first_name':first[i],'last_name':last[i%10],'email':f'prospecto{i+1:02d}@example.test','province':province,'city':city,'customer_type':'Prospecto','segment':'Potencial','acquisition_channel':channels[(i+2)%6],'preferred_contact_channel':contact[(i+1)%3],'lifecycle_stage':['Interesado','En seguimiento'][i%2],'marketing_consent':0,'registered_at':anchor-datetime.timedelta(days=60+i),'created_at':now})
statements=['START TRANSACTION;']
for i,c in enumerate(data):
    dates=[anchor-datetime.timedelta(days=35+(i%14)),anchor-datetime.timedelta(days=12+(i%10)),anchor-datetime.timedelta(days=1+(i%7))]
    c['last_contact_at']=dates[-1].replace(hour=10+i%7,minute=(i*7)%60)
    statements.extend([ins('customers',c),'SET @crm_id=LAST_INSERT_ID();'])
    for j,date in enumerate(dates):
        at=date.replace(hour=10+i%7,minute=(i*7)%60)
        # Dates are after registration, and all interactions are historical.
        kind=(['Consulta de productos','Seguimiento de compra','Preferencias del cliente'] if c['customer_type']=='Cliente' else ['Consulta de catálogo','Seguimiento comercial','Interés en productos'])[j]
        notes=['Consulta sobre disponibilidad y presentaciones.','Se compartió información de productos y formas de entrega.','Se registraron preferencias para futuras compras.'][j]
        values={'interaction_key':f'{c["crm_code"]}-I{j+1}','contact_channel':contact[(i+j)%3],'interaction_type':kind,'occurred_at':at,'outcome':['Consulta atendida','Información compartida','Seguimiento pendiente'][j],'notes':notes}
        statements.append('INSERT INTO '+DB+'.interactions (crm_customer_id,`'+'`,`'.join(values)+'`) VALUES (@crm_id,'+','.join(q(v) for v in values.values())+');')
statements.extend([ins('seed_runs',{'version':VERSION,'seeded_at':now,'anchor_date':anchor.date()}),'COMMIT;'])
mysql('\n'.join(statements))
assert before==store_hash(),'Store data changed during CRM setup'
print(f'CRM created: {len(store_customers)} linked customers, 20 prospects, {len(data)*3} interactions.')
print('PASS original store customers, products and orders unchanged')

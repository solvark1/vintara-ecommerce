#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path('/opt/terra-nostra');CRM='terra_nostra_crm'
BASE=['docker','compose','--env-file',str(ROOT/'azure/cloud.env'),'-f',str(ROOT/'azure/compose.yaml'),'exec','-T','db']
def rootquery(sql):
 p=subprocess.run(BASE+['sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --default-character-set=utf8mb4 -N -B'],input=sql.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 return p.stdout.decode().strip()
checks={
 '60 CRM records':"SELECT COUNT(*)=60 FROM terra_nostra_crm.customers;",
 '40 clients linked to the store':"SELECT COUNT(*)=40 FROM terra_nostra_crm.customers WHERE customer_type='Cliente' AND ecommerce_customer_id IS NOT NULL;",
 '20 prospects without store references':"SELECT COUNT(*)=20 FROM terra_nostra_crm.customers WHERE customer_type='Prospecto' AND ecommerce_customer_id IS NULL;",
 'No missing or mismatched store customers':"SELECT COUNT(*)=0 FROM terra_nostra_crm.customers c LEFT JOIN phoenix.customers p ON p.customers_id=c.ecommerce_customer_id WHERE c.ecommerce_customer_id IS NOT NULL AND (p.customers_id IS NULL OR p.customers_email_address<>c.email);",
 'Every store client is represented once':"SELECT COUNT(*)=0 FROM phoenix.customers p LEFT JOIN terra_nostra_crm.customers c ON c.ecommerce_customer_id=p.customers_id WHERE c.crm_customer_id IS NULL;",
 'Every purchase connects to a CRM client':"SELECT COUNT(*)=0 FROM phoenix.orders o LEFT JOIN terra_nostra_crm.customers c ON c.ecommerce_customer_id=o.customers_id WHERE c.crm_customer_id IS NULL;",
 '180 interactions with valid customer references':"SELECT COUNT(*)=180 AND COUNT(c.crm_customer_id)=180 FROM terra_nostra_crm.interactions i LEFT JOIN terra_nostra_crm.customers c ON c.crm_customer_id=i.crm_customer_id;",
 'Contacts after registration and before now':"SELECT COUNT(*)=0 FROM terra_nostra_crm.interactions i JOIN terra_nostra_crm.customers c ON c.crm_customer_id=i.crm_customer_id WHERE i.occurred_at<c.registered_at OR i.occurred_at>NOW();",
 'Last contact dates match interactions':"SELECT COUNT(*)=0 FROM terra_nostra_crm.customers c WHERE c.last_contact_at<>(SELECT MAX(i.occurred_at) FROM terra_nostra_crm.interactions i WHERE i.crm_customer_id=c.crm_customer_id);",
 'Prospects include all seven provinces':"SELECT COUNT(DISTINCT province)=7 FROM terra_nostra_crm.customers WHERE customer_type='Prospecto';",
 'No visible DEMO labels':"SELECT COUNT(*)=0 FROM terra_nostra_crm.customers WHERE first_name LIKE '%DEMO%' OR last_name LIKE '%DEMO%';",
}
failed=False
for name,sql in checks.items():
 ok=rootquery(sql)=='1';print(('PASS 'if ok else'FAIL ')+name);failed|=not ok
# Authenticate using the actual dedicated SQL users, not just grants inspected as root.
env=dict(line.split('=',1)for line in (ROOT/'azure/crm.env').read_text().splitlines()if'='in line)
def login(user,password,sql):
 return subprocess.run(BASE+['env','MYSQL_PWD='+password,'mysql','-h127.0.0.1','-u'+user,'-N','-B','-e',sql],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
for label,user,password,sql in[
 ('CRM user can read CRM',env['CRM_USER'],env['CRM_PASSWORD'],'SELECT COUNT(*) FROM terra_nostra_crm.customers'),
 ('ETL reader can join both sources',env['ETL_USER'],env['ETL_PASSWORD'],'SELECT COUNT(*) FROM phoenix.orders o JOIN terra_nostra_crm.customers c ON c.ecommerce_customer_id=o.customers_id'),
]:
 p=login(user,password,sql);ok=p.returncode==0;print(('PASS 'if ok else'FAIL ')+label+(' ('+p.stdout.decode().strip()+')'if ok else''));failed|=not ok
for label,user,password,sql in[
 ('CRM user cannot read store purchases',env['CRM_USER'],env['CRM_PASSWORD'],'SELECT COUNT(*) FROM phoenix.orders'),
 ('ETL reader cannot write CRM',env['ETL_USER'],env['ETL_PASSWORD'],'UPDATE terra_nostra_crm.customers SET first_name=first_name WHERE 1=0'),
 ('ETL reader cannot write store',env['ETL_USER'],env['ETL_PASSWORD'],'UPDATE phoenix.customers SET customers_firstname=customers_firstname WHERE 1=0'),
]:
 p=login(user,password,sql);ok=p.returncode!=0 and (b'denied'in p.stderr.lower());print(('PASS 'if ok else'FAIL ')+label);failed|=not ok
snapshot={}
for table in['customers','interactions','seed_runs']:
 p=subprocess.run(BASE+['sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump --no-tablespaces --no-create-info --skip-extended-insert --skip-comments --compact -uroot terra_nostra_crm '+table],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 snapshot[table]={'count':rootquery('SELECT COUNT(*) FROM terra_nostra_crm.'+table),'sha256':hashlib.sha256(p.stdout).hexdigest()}
print('SNAPSHOT '+json.dumps(snapshot))
sys.exit(1 if failed else 0)

"""One-time Vintara academic dataset migration. Run as root on the VM after store deployment."""
import subprocess,datetime,gzip,pathlib,json
ROOT=pathlib.Path('/opt/vintara')
DC=['docker','compose','--env-file',str(ROOT/'azure/cloud.env'),'-f',str(ROOT/'azure/compose.yaml')]
def sql(query):
 p=subprocess.run(DC+['exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --database=phoenix --default-character-set=utf8mb4 --batch --raw --skip-column-names'],input=query,text=True,capture_output=True)
 if p.returncode: raise RuntimeError(p.stderr)
 return p.stdout.strip()
def q(s): return "'"+str(s).replace('\\','\\\\').replace("'","''")+"'"
if sql("SELECT COUNT(*) FROM phoenix.configuration WHERE configuration_key='VINTARA_DATA_V2'")=='1':
 print('Vintara data migration already applied'); raise SystemExit
backup=ROOT/'backups'/('vintara-data-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.sql.gz')
subprocess.run(DC+['stop','proxy'],check=True)
try:
 p=subprocess.run(DC+['exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --no-tablespaces --databases phoenix vintara_crm'],capture_output=True,check=True)
 with gzip.open(backup,'wb') as f:f.write(p.stdout)
 backup.chmod(0o600)
 wines=[int(v) for v in sql('SELECT products_id FROM phoenix.vintara_wines ORDER BY products_id').splitlines()]
 assert len(wines)==18
 old=[int(v) for v in sql("SELECT products_id FROM phoenix.products WHERE products_id NOT IN (SELECT products_id FROM phoenix.vintara_wines) ORDER BY products_id").splitlines()]
 commands=['START TRANSACTION;']
 for i,oldid in enumerate(old):
  wine=wines[i%len(wines)]
  commands += [f"UPDATE phoenix.orders_products o JOIN phoenix.products p ON p.products_id={wine} JOIN phoenix.products_description d ON d.products_id=p.products_id AND d.language_id=1 SET o.products_id=p.products_id,o.products_name=d.products_name,o.products_model=p.products_model WHERE o.products_id={oldid};",
  f"UPDATE phoenix.reviews SET products_id={wine} WHERE products_id={oldid};",
  f"UPDATE phoenix.products o JOIN phoenix.products p ON p.products_id={wine} SET o.products_model=CONCAT('VIN-ARCH-',o.products_id),o.products_image=p.products_image,o.products_price=p.products_price,o.manufacturers_id=p.manufacturers_id,o.products_status=0 WHERE o.products_id={oldid};",
  f"UPDATE phoenix.products_description o JOIN phoenix.products_description n ON n.products_id={wine} AND n.language_id=o.language_id SET o.products_name=CONCAT(n.products_name,' (archivo)'),o.products_description=n.products_description,o.products_seo_title=n.products_seo_title,o.products_seo_description=n.products_seo_description WHERE o.products_id={oldid};"]
 commands += ["DELETE pc FROM phoenix.products_to_categories pc LEFT JOIN phoenix.vintara_wines v ON v.products_id=pc.products_id WHERE v.products_id IS NULL;",
 "DELETE cd FROM phoenix.categories_description cd WHERE cd.categories_id NOT IN (SELECT categories_id FROM phoenix.products_to_categories);",
 "DELETE c FROM phoenix.categories c WHERE c.categories_id NOT IN (SELECT categories_id FROM phoenix.products_to_categories);",
 "DELETE s FROM phoenix.specials s LEFT JOIN phoenix.vintara_wines v ON v.products_id=s.products_id WHERE v.products_id IS NULL;",
 "UPDATE phoenix.products p SET products_ordered=(SELECT COALESCE(SUM(products_quantity),0) FROM phoenix.orders_products o WHERE o.products_id=p.products_id);",
 "UPDATE vintara_crm.customers SET crm_code=REPLACE(crm_code,'TN-','VIN-'),acquisition_channel=REPLACE(acquisition_channel,'Feria local','Feria de vinos');",
 "UPDATE vintara_crm.interactions SET interaction_key=REPLACE(interaction_key,'TN-','VIN-'),notes=CASE MOD(interaction_id,3) WHEN 0 THEN 'Consulta sobre uvas, añadas y disponibilidad de vinos.' WHEN 1 THEN 'Se compartieron recomendaciones de maridaje y condiciones de entrega.' ELSE 'Seguimiento de preferencias de vino y presupuesto para próximas compras.' END;",
 "UPDATE phoenix.orders_status_history SET comments=REPLACE(comments,'Pedido TN-','Pedido VIN-');"]
 # Replace company name in all textual application/CRM fields, including CMS and configuration.
 columns=sql("SELECT TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA IN ('phoenix','vintara_crm') AND DATA_TYPE IN ('varchar','text','mediumtext','longtext','char')").splitlines()
 for row in columns:
  schema,table,col=row.split('\t'); name=f'`{schema}`.`{table}`'; field=f'`{col}`'
  expr=field
  for a,b in [('Vintara','Vintara'),('vintara','vintara'),('vintara','vintara'),('vintara','vintara'),('VINTARA','VINTARA')]: expr=f'REPLACE({expr},{q(a)},{q(b)})'
  # Keep seeder version metadata to prevent obsolete seeds running again.
  if table not in ('demo_seed_runs','demo_seed_entities','seed_runs'):
   commands.append(f'UPDATE {name} SET {field}={expr} WHERE LOWER({field}) REGEXP '+q('terra[ _-]?nostra')+';')
 commands += ["INSERT INTO phoenix.configuration(configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES ('Vintara data migration','VINTARA_DATA_V2','1','Academic wine dataset adapted from previous synthetic seed; historical transaction amounts retained',6,0,NOW());",'COMMIT;']
 sql('\n'.join(commands))
 assert sql('SELECT COUNT(*) FROM phoenix.orders_products o LEFT JOIN phoenix.vintara_wines v USING(products_id) WHERE v.products_id IS NULL')=='0'
 assert sql('SELECT COUNT(*) FROM vintara_crm.customers c LEFT JOIN phoenix.customers p ON p.customers_id=c.ecommerce_customer_id WHERE c.ecommerce_customer_id IS NOT NULL AND p.customers_id IS NULL')=='0'
 print('PASS: wine order links, CRM customer links, 18 active wines. Backup:',backup)
 print(sql("SELECT 'customers',COUNT(*) FROM phoenix.customers UNION ALL SELECT 'orders',COUNT(*) FROM phoenix.orders UNION ALL SELECT 'crm',COUNT(*) FROM vintara_crm.customers UNION ALL SELECT 'interactions',COUNT(*) FROM vintara_crm.interactions;"))
finally:
 subprocess.run(DC+['up','-d','--no-deps','proxy'],check=True)

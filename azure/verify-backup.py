#!/usr/bin/env python3
"""Verify a private multi-database backup in isolated schemas, never the live databases."""
import gzip,hashlib,json,pathlib,re,subprocess,urllib.request,uuid
root=pathlib.Path('/opt/vintara')
file=max((root/'backups').glob('vintara-*.sql.gz'),key=lambda p:p.stat().st_mtime)
account=(root/'azure/backup-storage.txt').read_text().strip()
req=urllib.request.Request('http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fstorage.azure.com%2F',headers={'Metadata':'true'})
with urllib.request.urlopen(req,timeout=30)as r: token=json.load(r)['access_token']
req=urllib.request.Request('https://'+account+'.blob.core.windows.net/backups/'+file.name,headers={'Authorization':'Bearer '+token,'x-ms-version':'2023-11-03'})
with urllib.request.urlopen(req,timeout=60)as r:data=r.read()
assert hashlib.sha256(data).digest()==hashlib.sha256(file.read_bytes()).digest(),'Backup content differs'
print('PASS private cloud backup downloaded and hash matches')
base=['docker','compose','--env-file',str(root/'azure/cloud.env'),'-f',str(root/'azure/compose.yaml'),'exec','-T','db']
def mysql(args,sql=None):
 cmd=base+['sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --default-character-set=utf8mb4 "$@"','mysql']+args
 return subprocess.run(cmd,input=sql,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
sql=gzip.decompress(data).decode('utf8')
suffix=uuid.uuid4().hex[:12]
uses=re.findall(r'^USE `([^`]+)`;',sql,re.M)
originals=list(dict.fromkeys(uses)) if uses else ['phoenix']
assert set(originals).issubset({'phoenix','vintara_crm'}),'Unexpected database in backup'
mapping={name:'restore_check_'+suffix+'_'+str(i) for i,name in enumerate(originals)}
# Rewrite only schema-changing statements at the beginning of lines.
for old,new in mapping.items():
 sql=re.sub(r'^(CREATE DATABASE[^\n]*?)`'+re.escape(old)+r'`',lambda m:m[1]+'`'+new+'`',sql,flags=re.M)
 sql=re.sub(r'^USE `'+re.escape(old)+r'`;',lambda m:'USE `'+new+'`;',sql,flags=re.M)
 assert not re.search(r'^USE `'+re.escape(old)+r'`;',sql,re.M)
 assert not re.search(r'^CREATE DATABASE[^\n]*`'+re.escape(old)+r'`',sql,re.M)
for name in mapping.values(): mysql(['-e','CREATE DATABASE `'+name+'`'])
try:
 mysql([mapping['phoenix']],sql.encode())
 checks={
 'phoenix':"SELECT (SELECT COUNT(*) FROM products WHERE products_status=1),(SELECT COUNT(*) FROM customers),(SELECT COUNT(*) FROM orders),(SELECT SUM(value) FROM orders_total WHERE class='ot_total');",
 'vintara_crm':"SELECT (SELECT COUNT(*) FROM customers),(SELECT COUNT(*) FROM interactions),(SELECT COUNT(*) FROM seed_runs);"
 }
 for original,name in mapping.items():
  restored=mysql(['-N',name,'-e',checks[original]]).decode().strip()
  live=mysql(['-N',original,'-e',checks[original]]).decode().strip()
  assert restored==live,(original,restored,live)
  print('PASS '+original+' restored into isolated schema; counts and sums match: '+restored)
finally:
 for name in mapping.values(): mysql(['-e','DROP DATABASE `'+name+'`'])

#!/usr/bin/env python3
"""Back up the Azure store and CRM using VM managed identity; no account keys."""
import datetime, gzip, json, os, pathlib, subprocess, urllib.request
root=pathlib.Path('/opt/terra-nostra')
storage=(root/'azure/backup-storage.txt').read_text().strip()
now=datetime.datetime.now(datetime.timezone.utc)
folder=root/'backups';folder.mkdir(exist_ok=True);os.chmod(folder,0o700)
file=folder/('terra-nostra-'+now.strftime('%Y%m%dT%H%M%SZ')+'.sql.gz')
command=['docker','compose','--env-file',str(root/'azure/cloud.env'),'-f',str(root/'azure/compose.yaml'),'exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump --no-tablespaces --single-transaction --databases -uroot phoenix terra_nostra_crm']
with gzip.open(file,'wb') as output:
    os.chmod(file,0o600)
    process=subprocess.Popen(command,stdout=subprocess.PIPE)
    for chunk in iter(lambda:process.stdout.read(1024*1024),b''): output.write(chunk)
    if process.wait()!=0: raise RuntimeError('Database backup failed')
request=urllib.request.Request('http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fstorage.azure.com%2F',headers={'Metadata':'true'})
with urllib.request.urlopen(request,timeout=30) as response: token=json.load(response)['access_token']
url='https://'+storage+'.blob.core.windows.net/backups/'+file.name
request=urllib.request.Request(url,data=file.read_bytes(),method='PUT',headers={'Authorization':'Bearer '+token,'x-ms-version':'2023-11-03','x-ms-blob-type':'BlockBlob','Content-Type':'application/gzip'})
with urllib.request.urlopen(request,timeout=120) as response:
    if response.status!=201: raise RuntimeError('Cloud upload failed')
print('Backup uploaded: '+file.name)
# Keep one week of local copies; Azure keeps the off-VM copies.
for old in folder.glob('terra-nostra-*.sql.gz'):
    if old.stat().st_mtime<now.timestamp()-7*86400:old.unlink()

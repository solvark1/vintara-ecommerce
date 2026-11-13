import pathlib,subprocess
r=pathlib.Path('/opt/vintara')
p=r/'azure/cloud.env'
s=p.read_text(); s=s.replace('vintara-if6201-508832.westus2.cloudapp.azure.com','vintara-if6201-508832.westus2.cloudapp.azure.com'); p.write_text(s)
c=['docker','compose','--env-file',str(p),'-f',str(r/'azure/compose.yaml')]
subprocess.run(c+['build','web'],check=True,stdout=open('/tmp/vintara-rebuild.log','w'),stderr=subprocess.STDOUT)
subprocess.run(c+['up','-d','--no-deps','--wait','web','proxy'],check=True)

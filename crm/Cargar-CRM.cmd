@echo off
cd /d "%~dp0.."
ssh -i azure/private/terra-nostra -o UserKnownHostsFile=azure/private/known_hosts -o BatchMode=yes azureuser@20.230.232.196 "sudo python3 /opt/terra-nostra/crm/seed_crm.py"
pause

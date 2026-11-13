@echo off
cd /d "%~dp0.."
ssh -i azure/private/vintara -o UserKnownHostsFile=azure/private/known_hosts -o BatchMode=yes azureuser@20.3.229.69 "sudo python3 /opt/vintara/crm/seed_crm.py"
pause

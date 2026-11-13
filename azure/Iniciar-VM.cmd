@echo off
call "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" vm start --subscription 5f66fa39-f868-42f5-b9ac-a7d110508832 --resource-group rg-vintara --name vm-vintara
if errorlevel 1 (pause & exit /b 1)
start "" https://vintara-if6201-508832.westus2.cloudapp.azure.com/

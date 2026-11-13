@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Actualizar-Vintara-Azure.ps1"
pause

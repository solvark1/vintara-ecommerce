@echo off
cd /d "%~dp0"
docker compose up -d --wait
if errorlevel 1 (pause & exit /b 1)
start "" http://localhost:8082

@echo off
cd /d "%~dp0"
docker compose exec -T web php /opt/phoenix/seed-demo.php
pause

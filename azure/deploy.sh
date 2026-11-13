#!/bin/bash
set -euo pipefail
cd /opt/vintara
chmod 600 azure/cloud.env
compose=(docker compose --env-file azure/cloud.env -f azure/compose.yaml)
"${compose[@]}" up -d db
# Wait until the database is ready, before importing or exposing the application.
for attempt in $(seq 1 90); do
  if "${compose[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysqladmin ping -h127.0.0.1 -u"$MYSQL_USER" --silent' >/dev/null 2>&1; then break; fi
  sleep 2
done
"${compose[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" "$MYSQL_DATABASE"' < azure/migration.sql
"${compose[@]}" build web
"${compose[@]}" up -d --wait web
# Synchronize actual shop images from the local installation's persistent volume.
"${compose[@]}" cp azure/images.tar.gz web:/tmp/images.tar.gz
"${compose[@]}" exec -T web tar -xzf /tmp/images.tar.gz -C /var/www/html
"${compose[@]}" exec -T web chown -R www-data:www-data /var/www/html/images
"${compose[@]}" up -d --wait
"${compose[@]}" exec -T web php /opt/phoenix/verify-demo.php
printf '0 8 * * * root /usr/bin/python3 /opt/vintara/azure/backup.py >> /var/log/vintara-backup.log 2>&1\n' > /etc/cron.d/vintara-backup
chmod 644 /etc/cron.d/vintara-backup
"${compose[@]}" ps

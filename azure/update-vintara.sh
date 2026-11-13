#!/usr/bin/env bash
# Run only after uploading the release to /tmp/vintara-release.tar.gz.
set -Eeuo pipefail
umask 077
expected_sha=${1:?Expected release SHA256 is required}
[[ "$expected_sha" =~ ^[a-fA-F0-9]{64}$ ]] || { echo 'Invalid release hash'; exit 1; }
printf '%s  %s\n' "$expected_sha" /tmp/vintara-release.tar.gz | sha256sum --check --status
cd /opt/vintara
exec 9>/opt/vintara/.vintara-deploy.lock
flock -n 9 || { echo 'Another Vintara deployment is running'; exit 1; }
dc() { docker compose --env-file azure/cloud.env -f azure/compose.yaml "$@"; }
stamp=$(date -u +%Y%m%dT%H%M%SZ)
release="/opt/vintara/backups/vintara-$stamp"
mkdir -p "$release"
# Take a complete private snapshot before any store change.
tar -czf "$release/code.tar.gz" Dockerfile docker branding azure/compose.yaml
dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --no-tablespaces --add-drop-database --databases phoenix vintara_crm' | gzip > "$release/database.sql.gz"
gzip -t "$release/database.sql.gz"
oldimage=$(docker inspect --format '{{.Image}}' "$(dc ps -q web)")
docker image tag "$oldimage" "vintara-rollback:$stamp"
preserved() {
 dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --no-tablespaces --compact --skip-comments --skip-extended-insert --order-by-primary --no-create-info phoenix customers customers_info address_book orders orders_products orders_products_attributes orders_status_history orders_total' | sha256sum | cut -d' ' -f1
 dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --no-tablespaces --compact --skip-comments --skip-extended-insert --order-by-primary --no-create-info vintara_crm' | sha256sum | cut -d' ' -f1
}
preserved > "$release/history-before.sha256"
maintenance=0
rollback() {
 status=$?
 trap - ERR
 echo "Update failed. Restoring previous code, image and database."
 dc stop web || true
 tar -xzf "$release/code.tar.gz" -C /opt/vintara
 if [ "$maintenance" = 1 ]; then
  gzip -dc "$release/database.sql.gz" | dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'
 fi
 imageName=$(dc config --format json | python3 -c 'import sys,json; c=json.load(sys.stdin); print(c["services"]["web"].get("image",c["name"]+"-web"))')
 docker image tag "vintara-rollback:$stamp" "$imageName"
 dc up -d --no-deps --no-build --wait web
 dc up -d --no-deps proxy
 echo "Rollback complete. Backup: $release"
 exit "$status"
}
trap rollback ERR
tar -xzf /tmp/vintara-release.tar.gz -C /opt/vintara
dc build web
dc run --rm --no-deps --entrypoint php web /opt/phoenix/lint-vintara.php
# Pause public checkout for the short migration and verification window.
dc stop proxy web
preserved > "$release/history-before.sha256"
# Refresh snapshot with checkout stopped, so rollback cannot lose an intervening order.
dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --no-tablespaces --add-drop-database --databases phoenix vintara_crm' | gzip > "$release/database.sql.gz"
gzip -t "$release/database.sql.gz"
maintenance=1
dc run --rm --no-deps --entrypoint php web /opt/phoenix/vintara.php
dc run --rm --no-deps --entrypoint php web /opt/phoenix/verify-vintara.php
preserved > "$release/history-after.sha256"
cmp "$release/history-before.sha256" "$release/history-after.sha256"
# Exercise the normal entrypoint after the additive migration.
dc up -d --no-deps --no-build --wait web
dc exec -T web curl -fsS http://localhost/index.php > "$release/home.html"
grep -q 'VINTARA' "$release/home.html"
grep -q 'images/vintara/hero.svg' "$release/home.html"
dc exec -T web curl -fsS http://localhost/products_new.php > "$release/catalog.html"
grep -q 'VIN\|vintara/vin-' "$release/catalog.html"
# Idempotency: a second application must leave the catalog byte-for-byte unchanged.
catalog_hash() {
 dc exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --no-tablespaces --compact --skip-comments --skip-extended-insert --order-by-primary --no-create-info phoenix products products_description products_to_categories categories categories_description vintara_wines configuration' | sha256sum | cut -d' ' -f1
}
catalog_hash > "$release/catalog-before.sha256"
dc exec -T web php /opt/phoenix/vintara.php
catalog_hash > "$release/catalog-after.sha256"
cmp "$release/catalog-before.sha256" "$release/catalog-after.sha256"
dc exec -T web php /opt/phoenix/verify-vintara.php
trap - ERR
dc up -d --no-deps proxy
echo "VINTARA DEPLOYED AND VERIFIED. Historical orders and CRM preserved. Backup: $release"

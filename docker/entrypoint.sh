#!/bin/sh
set -eu
php /opt/phoenix/bootstrap.php
if [ "${DEMO_SEED_ENABLED:-false}" = "true" ]; then php /opt/phoenix/seed-demo.php; fi
php /opt/phoenix/customize.php
php /opt/phoenix/refine.php
php /opt/phoenix/azure-runtime.php
php /opt/phoenix/vintara.php
exec docker-php-entrypoint "$@"

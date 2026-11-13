FROM php:8.3-apache
RUN apt-get update && apt-get install -y --no-install-recommends libicu-dev libpng-dev libjpeg62-turbo-dev libfreetype6-dev libzip-dev && docker-php-ext-configure gd --with-freetype --with-jpeg && docker-php-ext-install -j$(nproc) mysqli intl gd zip && rm -rf /var/lib/apt/lists/*
COPY source/CE-PhoenixCart-PhoenixCart-1c2161d/ /var/www/html/
COPY docker/bootstrap.php /opt/phoenix/bootstrap.php
COPY docker/entrypoint.sh /usr/local/bin/phoenix-entrypoint
RUN chmod +x /usr/local/bin/phoenix-entrypoint && mkdir -p /var/www/html/includes/work /var/www/html/admin/backups && chown -R www-data:www-data /var/www/html
ENTRYPOINT ["phoenix-entrypoint"]
CMD ["apache2-foreground"]
RUN mv /var/www/html/install /opt/phoenix/install
COPY docker/seed-demo.php /opt/phoenix/seed-demo.php
COPY branding/overlay/ /var/www/html/
COPY branding/assets/ /opt/phoenix/brand-assets/
COPY docker/customize.php /opt/phoenix/customize.php
COPY docker/verify-demo.php /opt/phoenix/verify-demo.php
COPY docker/refine.php /opt/phoenix/refine.php
COPY azure/runtime.php /opt/phoenix/azure-runtime.php
COPY docker/vintara.php docker/vintara-catalog.json /opt/phoenix/
COPY docker/verify-vintara.php /opt/phoenix/
COPY docker/lint-vintara.php /opt/phoenix/

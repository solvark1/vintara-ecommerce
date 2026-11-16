"""An allowlist-only, read-only, consistent snapshot of both MySQL sources."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/opt/vintara')

DATASETS = {
    'products': ('phoenix.products p JOIN phoenix.vintara_wines v ON v.products_id=p.products_id JOIN phoenix.products_description d ON d.products_id=p.products_id AND d.language_id=1', {
        'product_id': 'p.products_id', 'sku': 'p.products_model', 'name': 'd.products_name',
        'category': 'v.category', 'grape': 'v.grape', 'vintage': 'v.vintage', 'region': 'v.region',
        'country': 'v.country', 'winery': 'v.winery', 'catalog_price_crc': 'CAST(p.products_price AS CHAR)',
        'stock': 'p.products_quantity', 'active': 'p.products_status', 'is_synthetic': 'v.is_synthetic'}),
    'customers': ('phoenix.customers c JOIN phoenix.customers_info i ON i.customers_info_id=c.customers_id', {
        'customer_id': 'c.customers_id', 'registered_at': 'i.customers_info_date_account_created'}),
    'orders': ('phoenix.orders', {'order_id': 'orders_id', 'customer_id': 'customers_id',
        'purchased_at': 'date_purchased', 'status_id': 'orders_status', 'currency': 'currency',
        'currency_value': 'CAST(currency_value AS CHAR)'}),
    'order_lines': ('phoenix.orders_products', {'order_line_id': 'orders_products_id', 'order_id': 'orders_id',
        'product_id': 'products_id', 'quantity': 'products_quantity', 'unit_price_crc': 'CAST(final_price AS CHAR)',
        'tax_pct': 'CAST(products_tax AS CHAR)'}),
    'order_totals': ('phoenix.orders_total', {'order_total_id': 'orders_total_id', 'order_id': 'orders_id',
        'class': 'class', 'value_crc': 'CAST(value AS CHAR)'}),
    'order_statuses': ('phoenix.orders_status WHERE language_id=1', {'status_id': 'orders_status_id', 'name': 'orders_status_name'}),
    'crm_customers': ('vintara_crm.customers', {'crm_customer_id': 'crm_customer_id', 'customer_id': 'ecommerce_customer_id',
        'customer_type': 'customer_type', 'segment': 'segment', 'acquisition_channel': 'acquisition_channel',
        'province': 'province', 'registered_at': 'registered_at', 'last_contact_at': 'last_contact_at'}),
    'crm_interactions': ('vintara_crm.interactions', {'interaction_id': 'interaction_id', 'crm_customer_id': 'crm_customer_id',
        'channel': 'contact_channel', 'type': 'interaction_type', 'occurred_at': 'occurred_at', 'outcome': 'outcome'}),
}


def extract():
    env = dict(line.split('=', 1) for line in (ROOT / 'azure/crm.env').read_text().splitlines() if '=' in line)
    statements = ['SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;',
                  'START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;']
    for name, (table, columns) in DATASETS.items():
        fields = ','.join("'" + key + "'," + value for key, value in columns.items())
        statements.append(f"SELECT JSON_OBJECT('dataset','{name}','rows',(SELECT JSON_ARRAYAGG(JSON_OBJECT({fields})) FROM {table}));")
    statements.append('COMMIT;')
    # Password travels through stdin, never a process argument, log or artifact.
    command = ['docker', 'compose', '--env-file', str(ROOT / 'azure/cloud.env'), '-f', str(ROOT / 'azure/compose.yaml'),
               'exec', '-T', 'db', 'sh', '-c',
               'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mysql --default-character-set=utf8mb4 --batch --raw --skip-column-names --user="$1"',
               'mysql-readonly', env['ETL_USER']]
    payload = env['ETL_PASSWORD'] + '\n' + '\n'.join(statements)
    result = subprocess.run(command, input=payload.encode(), capture_output=True)
    if result.returncode:
        # SQL errors contain no row data; avoid publishing stdout on failure.
        raise RuntimeError('Read-only MySQL extraction failed: ' + result.stderr.decode(errors='replace'))
    datasets = {}
    for line in result.stdout.decode('utf-8').splitlines():
        record = json.loads(line)
        rows = record['rows'] or []
        datasets[record['dataset']] = sorted(rows, key=lambda r: json.dumps(r, sort_keys=True, ensure_ascii=False))
    if set(datasets) != set(DATASETS):
        raise RuntimeError('Incomplete MySQL snapshot')
    return datasets

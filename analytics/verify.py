#!/usr/bin/env python3
"""Independently verify the published manifest, cloud objects and sales reconciliation."""
import csv
import hashlib
import io
import json
from decimal import Decimal
from storage import BlobStore


def verify():
    cloud = BlobStore('stvintara508832')
    pointer_data, _ = cloud.get('datalake', 'latest.json')
    pointer = json.loads(pointer_data)
    manifest_data, _ = cloud.get('datalake', pointer['manifest'])
    assert hashlib.sha256(manifest_data).hexdigest() == pointer['manifest_sha256'], 'Manifest hash differs'
    manifest = json.loads(manifest_data)
    assert manifest['status'] == 'succeeded' and manifest['run_id'] == pointer['run_id']
    tables = {}
    for file in manifest['files']:
        data, _ = cloud.get('datalake', file['path'])
        assert len(data) == file['bytes'] and hashlib.sha256(data).hexdigest() == file['sha256'], file['path']
        if file['path'].endswith('.csv'):
            rows = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
            if file['rows'] is not None:
                assert len(rows) == file['rows'], 'CSV row count differs'
            tables[file['path'].rsplit('/', 1)[-1]] = rows
    def total(name):
        return sum((Decimal(row['revenue_crc']) for row in tables[name]), Decimal(0))
    expected = Decimal(manifest['quality']['net_product_revenue_crc'])
    for name in ['q01_monthly_category.csv', 'q02_category_sales.csv', 'q03_price_volume.csv',
                 'q04_revenue_volume.csv', 'q05_category_pareto.csv', 'customer_segment_sales.csv']:
        assert total(name) == expected, 'Business aggregate mismatch: ' + name
    assert sum(int(row['review_count']) for row in tables['review_summary.csv']) == len(tables['fact_reviews.csv'])
    assert all(row['status_id'] in ('2', '3') for row in tables['fact_order_lines.csv'] if row['included_sale'] == '1')
    print(json.dumps({'verified': True, 'run_id': pointer['run_id'], 'trigger': manifest['trigger'],
        'cloud_files_hash_verified': len(manifest['files']), 'quality': manifest['quality']}, ensure_ascii=False))
    return manifest


if __name__ == '__main__':
    verify()

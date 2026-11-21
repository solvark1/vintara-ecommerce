import contextlib
import copy
import datetime as dt
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from model import transform
from extract import DATASETS


def fixture():
    source = {
        'products': [dict(product_id=i, name=f'Wine {i}', category=c, catalog_price_crc='1000', active=1)
                     for i, c in [(1, 'Tintos'), (2, 'Blancos')]],
        'customers': [dict(customer_id=1, registered_at='2025-01-01')],
        'crm_customers': [dict(crm_customer_id=10, customer_id=1, segment='Premium', acquisition_channel='Google', province='Cartago')],
        'crm_interactions': [dict(interaction_id=1, crm_customer_id=10)],
        'orders': [], 'order_lines': [], 'order_totals': [], 'order_statuses': []}
    data = [(1, '2026-01-01', 3, 1, 2, '100'), (2, '2026-02-01', 2, 1, 1, '150'),
            (3, '2026-01-01', 3, 2, 3, '50'), (4, '2026-01-01', 4, 1, 99, '100'),
            (5, '2026-02-01', 1, 1, 99, '100')]
    for oid, date, status, pid, qty, price in data:
        source['orders'].append(dict(order_id=oid, customer_id=1, purchased_at=date, status_id=status, currency='CRC', currency_value='1'))
        source['order_lines'].append(dict(order_line_id=oid, order_id=oid, product_id=pid, quantity=qty, unit_price_crc=price, tax_pct='0'))
        source['order_totals'].append(dict(order_id=oid, **{'class': 'ot_subtotal'}, value_crc=str(qty * int(price))))
    review = dict(review_id='MOCK-1', order_id='1', order_line_id='1', product_id='1', customer_id='1',
                  review_date='2026-01-04', platform='Instagram', rating='5', comment='Buen vino.', is_synthetic='1')
    return source, review


class BusinessTests(unittest.TestCase):
    def run_model(self, reviews=None):
        source, review = fixture()
        return transform(source, [review] if reviews is None else reviews, dt.date(2026, 3, 15))

    def test_revenue_excludes_cancelled_and_pending_without_duplicate_join(self):
        silver, gold, _, quality = self.run_model()
        self.assertEqual(quality['net_product_revenue_crc'], '500.0000')
        self.assertEqual(quality['excluded_lines'], 2)
        self.assertEqual(gold['customer_segment_sales'][0]['orders'], 3)
        self.assertEqual(len(silver['fact_order_lines']), 5)

    def test_previous_month_disappearance_is_minus_one_hundred_percent(self):
        _, gold, _, _ = self.run_model()
        row = next(r for r in gold['q06_monthly_change'] if r['product_id'] == 2 and r['month'] == '2026-02')
        self.assertEqual(row['change_pct'], '-100.0000')
        self.assertEqual(row['units'], 0)
        self.assertEqual(row['is_complete_month'], 1)

    def test_zero_baseline_is_blank_and_current_month_is_partial(self):
        _, gold, _, _ = self.run_model()
        row = next(r for r in gold['q06_monthly_change'] if r['product_id'] == 2 and r['month'] == '2026-03')
        self.assertIsNone(row['change_pct'])
        self.assertEqual(row['comparison'], 'sin_base')
        self.assertEqual(row['is_complete_month'], 0)

    def test_review_duplicates_do_not_multiply_rows_and_bad_join_is_quarantined(self):
        _, review = fixture()
        bad = {**review, 'review_id': 'BAD', 'product_id': '2'}
        silver, _, quarantine, quality = self.run_model([review, copy.deepcopy(review), bad])
        self.assertEqual(len(silver['fact_reviews']), 1)
        self.assertEqual(quality['duplicate_reviews'], 1)
        self.assertEqual(len(quarantine), 1)

    def test_invalid_money_and_orphan_lines_fail(self):
        source, review = fixture()
        source['order_lines'][0]['unit_price_crc'] = 'NaN'
        with self.assertRaises(ValueError):
            transform(source, [review], dt.date(2026, 3, 15))
        source, review = fixture()
        source['order_lines'][0]['product_id'] = 999
        with self.assertRaises(ValueError):
            transform(source, [review], dt.date(2026, 3, 15))

    def test_customer_and_order_extracts_do_not_include_personal_or_payment_fields(self):
        prohibited = ('password', 'email', 'firstname', 'lastname', 'telephone', 'street', 'cc_')
        for dataset in ('customers', 'orders', 'crm_customers', 'crm_interactions'):
            expression = str(DATASETS[dataset]).lower()
            self.assertFalse(any(term in expression for term in prohibited))

    @unittest.skipUnless(os.name == 'posix', 'Cloud runner uses Linux flock')
    def test_failed_gold_upload_cannot_replace_published_snapshot(self):
        import etl
        source, review = fixture()
        old = b'{"run_id":"previous-good-run"}'
        class FailingStore:
            def __init__(self):
                self.latest = old
            def optional(self, container, name):
                return (self.latest, 'prior-etag') if name == 'latest.json' else (None, None)
            def list(self, *args):
                return ['reviews/test.csv']
            def get(self, *args):
                return etl.csv_bytes([review]), 'csv-etag'
            def put(self, container, name, data, *args, **kwargs):
                if name.startswith('gold/'):
                    raise RuntimeError('Simulated storage failure')
                if name == 'latest.json':
                    self.latest = data
        store = FailingStore()
        with tempfile.TemporaryDirectory() as temp, patch.object(etl, 'PRIVATE', pathlib.Path(temp)), patch.object(etl, 'extract', return_value=source), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'Simulated storage failure'):
                etl.run('manual', store)
        self.assertEqual(store.latest, old)


if __name__ == '__main__':
    unittest.main()

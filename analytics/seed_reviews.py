#!/usr/bin/env python3
"""Create one explicitly synthetic CSV from actual academic purchase identifiers."""
import datetime as dt
from zoneinfo import ZoneInfo
from extract import extract
from etl import csv_bytes
from model import REVIEW_FIELDS, SALE_STATUSES
from storage import BlobStore

BLOB = 'reviews/reviews_academic_v1.csv'


def main():
    cloud = BlobStore('stvintara508832')
    existing, _ = cloud.optional('fuentes', BLOB)
    if existing is not None:
        print('Source CSV already exists; edits preserved.')
        return
    source = extract()
    orders = {int(row['order_id']): row for row in source['orders']}
    today = dt.datetime.now(ZoneInfo('America/Costa_Rica')).date()
    eligible = [line for line in sorted(source['order_lines'], key=lambda r: int(r['order_line_id']))
                if int(orders[int(line['order_id'])]['status_id']) in SALE_STATUSES
                and dt.datetime.fromisoformat(orders[int(line['order_id'])]['purchased_at']).date() <= today]
    if not eligible:
        raise ValueError('No eligible academic purchases')
    comments = [
        (5, 'Buen aroma y sabor equilibrado. La presentación llegó en excelente estado.'),
        (4, 'El vino acompañó muy bien la cena; el precio me pareció razonable.'),
        (3, 'La botella estaba bien presentada, pero esperaba un sabor más intenso.'),
        (2, 'La entrega tardó y la relación entre precio y calidad no me convenció.'),
        (5, 'Muy buen maridaje con quesos y una compra sencilla.'),
        (4, 'Buena calidad y embalaje; me gustaría más información del origen.'),
        (1, 'La presentación llegó dañada y la atención posterior fue lenta.'),
        (3, 'Me gustó el aroma, aunque el precio es alto para mi presupuesto.'),
        (5, 'Sabor agradable, empaque cuidado y entrega puntual.'),
        (4, 'Una buena opción para compartir; volvería a comprar este vino.'),
    ]
    count = min(180, len(eligible))
    rows = []
    for index in range(count):
        line = eligible[index * len(eligible) // count]
        order = orders[int(line['order_id'])]
        date = min(today, dt.datetime.fromisoformat(order['purchased_at']).date() + dt.timedelta(days=3))
        rating, comment = comments[(int(line['product_id']) + index) % len(comments)]
        rows.append({'review_id': f'MOCK-TN-{index + 1:04}', 'order_id': line['order_id'],
            'order_line_id': line['order_line_id'], 'product_id': line['product_id'], 'customer_id': order['customer_id'],
            'review_date': date.isoformat(), 'platform': ['Instagram', 'Facebook', 'Google Reviews'][index % 3],
            'rating': rating, 'comment': comment, 'is_synthetic': 1})
    cloud.put('fuentes', BLOB, csv_bytes(rows, REVIEW_FIELDS), 'text/csv; charset=utf-8', condition=('If-None-Match', '*'))
    print(f'PASS: {count} explicitly synthetic reviews published privately; no original purchase was changed.')


if __name__ == '__main__':
    main()

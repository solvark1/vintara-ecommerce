"""Business transformations for CONTI / Terra Nostra. No cloud or database writes."""
import calendar
import datetime as dt
from collections import defaultdict
from decimal import Decimal
import statistics

SALE_STATUSES = (2, 3)
REVIEW_FIELDS = ('review_id', 'order_id', 'order_line_id', 'product_id', 'customer_id',
                 'review_date', 'platform', 'rating', 'comment', 'is_synthetic')


def money(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Non-finite monetary value')
    return result


def amount(value):
    return format(money(value).quantize(Decimal('.0001')), 'f')


def unique(rows, key):
    mapped = {int(row[key]): row for row in rows}
    if len(mapped) != len(rows):
        raise ValueError('Duplicate primary key: ' + key)
    return mapped


def months_between(first, last):
    result = []
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        result.append(f'{year:04}-{month:02}')
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def month_previous(month):
    year, number = map(int, month.split('-'))
    return f'{year - 1:04}-12' if number == 1 else f'{year:04}-{number - 1:02}'


def transform(source, review_rows, as_of):
    products = unique(source['products'], 'product_id')
    customers = unique(source['customers'], 'customer_id')
    orders = unique(source['orders'], 'order_id')
    lines = unique(source['order_lines'], 'order_line_id')
    crm = unique(source['crm_customers'], 'crm_customer_id')
    interactions = unique(source['crm_interactions'], 'interaction_id')
    linked = {}
    for person in crm.values():
        if person['customer_id'] is not None:
            key = int(person['customer_id'])
            if key not in customers or key in linked:
                raise ValueError('Invalid or duplicated CRM/store customer relationship')
            linked[key] = person
    for item in interactions.values():
        if int(item['crm_customer_id']) not in crm:
            raise ValueError('Orphan CRM interaction')
    for order in orders.values():
        if int(order['customer_id']) not in customers:
            raise ValueError('Orphan store order')
        if order['currency'] != 'CRC' or money(order['currency_value']) != 1:
            raise ValueError('Unsupported order currency; explicit conversion required')
        if dt.datetime.fromisoformat(order['purchased_at']).date() > as_of:
            raise ValueError('Future purchase date')

    dim_customers = []
    for key, customer in sorted(customers.items()):
        extra = linked.get(key, {})
        dim_customers.append({'customer_id': key, 'registered_at': customer['registered_at'],
            'crm_customer_id': extra.get('crm_customer_id'), 'segment': extra.get('segment', 'Sin clasificar'),
            'acquisition_channel': extra.get('acquisition_channel', 'Sin clasificar'),
            'province': extra.get('province', 'Sin clasificar')})

    facts = []
    subtotal = defaultdict(Decimal)
    for key, line in sorted(lines.items()):
        oid, pid = int(line['order_id']), int(line['product_id'])
        if oid not in orders or pid not in products:
            raise ValueError('Order line missing its order or wine profile')
        qty = int(line['quantity'])
        price = money(line['unit_price_crc'])
        if qty <= 0 or price < 0 or money(line['tax_pct']) < 0:
            raise ValueError('Invalid order quantity or price')
        order = orders[oid]
        product = products[pid]
        date = dt.datetime.fromisoformat(order['purchased_at']).date()
        total = qty * price
        subtotal[oid] += total
        facts.append({'order_line_id': key, 'order_id': oid, 'customer_id': int(order['customer_id']),
            'product_id': pid, 'date': date.isoformat(), 'month': date.strftime('%Y-%m'),
            'status_id': int(order['status_id']), 'included_sale': int(int(order['status_id']) in SALE_STATUSES),
            'quantity': qty, 'unit_price_crc': amount(price), 'revenue_crc': amount(total),
            'category': product['category'], 'segment': linked.get(int(order['customer_id']), {}).get('segment', 'Sin clasificar')})
    # Net product amount, excluding shipping/tax; discrepancies are surfaced, never silently overwritten.
    reconciliation = []
    for total in source['order_totals']:
        if total['class'] == 'ot_subtotal':
            oid = int(total['order_id'])
            if abs(subtotal.get(oid, Decimal(0)) - money(total['value_crc'])) > Decimal('.01'):
                reconciliation.append({'order_id': oid, 'lines_crc': amount(subtotal.get(oid, Decimal(0))),
                                       'source_subtotal_crc': amount(total['value_crc'])})
    if reconciliation:
        raise ValueError(f'{len(reconciliation)} order subtotals disagree with source lines')

    reviews, quarantine, seen = [], [], {}
    duplicates = 0
    for original in review_rows:
        row = {key: str(original.get(key, '')).strip() for key in REVIEW_FIELDS}
        origin = original.get('_source_blob', '')
        try:
            if not row['review_id'] or not row['comment'] or len(row['comment']) > 4000:
                raise ValueError('Missing review identifier/comment or comment too long')
            line = lines[int(row['order_line_id'])]
            order = orders[int(row['order_id'])]
            if int(line['order_id']) != int(row['order_id']) or int(line['product_id']) != int(row['product_id']) or int(order['customer_id']) != int(row['customer_id']):
                raise ValueError('Review identifiers disagree with purchase')
            date = dt.date.fromisoformat(row['review_date'])
            if date < dt.datetime.fromisoformat(order['purchased_at']).date() or date > as_of:
                raise ValueError('Review date outside purchase/as-of interval')
            if row['platform'] not in ('Instagram', 'Facebook', 'Google Reviews'):
                raise ValueError('Unsupported source platform')
            if not 1 <= int(row['rating']) <= 5 or row['is_synthetic'] not in ('0', '1'):
                raise ValueError('Invalid rating or synthetic indicator')
            signature = tuple(row.items())
            if row['review_id'] in seen:
                if seen[row['review_id']] != signature:
                    raise ValueError('Conflicting duplicate review identifier')
                duplicates += 1
                continue
            seen[row['review_id']] = signature
            reviews.append({**row, 'rating': int(row['rating']), 'is_synthetic': int(row['is_synthetic']), 'source_blob': origin})
        except (ValueError, KeyError) as exc:
            quarantine.append({'review_id': row['review_id'], 'source_blob': origin, 'reason': str(exc)})

    sales = [row for row in facts if row['included_sale']]
    if not sales:
        raise ValueError('No eligible sales available')
    first = min(dt.date.fromisoformat(r['date']) for r in facts)
    months = months_between(first, as_of)
    categories = sorted({p['category'] for p in products.values()})
    grouped = defaultdict(lambda: {'units': 0, 'revenue': Decimal(0), 'orders': set()})
    for row in sales:
        g = grouped[(row['month'], row['product_id'])]
        g['units'] += row['quantity']
        g['revenue'] += money(row['revenue_crc'])
        g['orders'].add(row['order_id'])
    product_metrics = []
    category_metrics = []
    monthly = []
    for month in months:
        for category in categories:
            cells = [g for (m, pid), g in grouped.items() if m == month and products[pid]['category'] == category]
            monthly.append({'month': month, 'category': category, 'units': sum(g['units'] for g in cells),
                'revenue_crc': amount(sum((g['revenue'] for g in cells), Decimal(0))),
                'is_complete_month': int(month < as_of.strftime('%Y-%m'))})
    monthly_units = {(row['month'], row['category']): row['units'] for row in monthly}
    for row in monthly:
        previous = monthly_units.get((month_previous(row['month']), row['category']))
        row['previous_units'] = previous
        row['change_units'] = row['units'] - previous if previous is not None else None
        row['change_pct'] = amount(Decimal(row['units'] - previous) / previous * 100) if previous else None
    for pid, product in sorted(products.items()):
        cells = [g for (m, key), g in grouped.items() if key == pid]
        units = sum(g['units'] for g in cells)
        revenue = sum((g['revenue'] for g in cells), Decimal(0))
        product_metrics.append({'product_id': pid, 'product': product['name'], 'category': product['category'],
            'units': units, 'revenue_crc': amount(revenue), 'average_realized_price_crc': amount(revenue / units) if units else None,
            'current_catalog_price_crc': amount(product['catalog_price_crc'])})
    for category in categories:
        cells = [p for p in product_metrics if p['category'] == category]
        category_metrics.append({'category': category, 'units': sum(c['units'] for c in cells),
            'revenue_crc': amount(sum((money(c['revenue_crc']) for c in cells), Decimal(0)))})
    total_revenue = sum((money(c['revenue_crc']) for c in category_metrics), Decimal(0))
    pareto, cumulative = [], Decimal(0)
    for rank, category in enumerate(sorted(category_metrics, key=lambda r: (-money(r['revenue_crc']), r['category'])), 1):
        cumulative += money(category['revenue_crc'])
        pareto.append({**category, 'rank': rank, 'share_pct': amount(money(category['revenue_crc']) / total_revenue * 100) if total_revenue else '0.0000',
            'cumulative_pct': amount(cumulative / total_revenue * 100) if total_revenue else '0.0000'})
    active_sales = [p for p in product_metrics if p['units']]
    median_units = statistics.median(p['units'] for p in active_sales)
    median_revenue = statistics.median(money(p['revenue_crc']) for p in active_sales)
    scatter = [{**p, 'high_revenue_low_volume': int(p['units'] > 0 and p['units'] <= median_units and money(p['revenue_crc']) >= median_revenue)} for p in product_metrics]
    mom = []
    for month in months[1:]:
        previous = month_previous(month)
        for pid, product in sorted(products.items()):
            current = grouped[(month, pid)]['units']
            before = grouped[(previous, pid)]['units']
            mom.append({'month': month, 'previous_month': previous, 'product_id': pid, 'product': product['name'],
                'category': product['category'], 'units': current, 'previous_units': before,
                'change_units': current - before, 'change_pct': amount(Decimal(current - before) / before * 100) if before else None,
                'comparison': 'sin_base' if not before else ('baja' if current < before else 'sube' if current > before else 'igual'),
                'is_complete_month': int(month < as_of.strftime('%Y-%m'))})
    segment_metrics = []
    for segment in sorted({r['segment'] for r in sales}):
        rows = [r for r in sales if r['segment'] == segment]
        segment_metrics.append({'segment': segment, 'customers': len({r['customer_id'] for r in rows}),
            'orders': len({r['order_id'] for r in rows}), 'units': sum(r['quantity'] for r in rows),
            'revenue_crc': amount(sum((money(r['revenue_crc']) for r in rows), Decimal(0)))})
    review_summary = []
    for pid, product in sorted(products.items()):
        rows = [r for r in reviews if int(r['product_id']) == pid]
        review_summary.append({'product_id': pid, 'product': product['name'], 'review_count': len(rows),
            'average_rating': amount(Decimal(sum(r['rating'] for r in rows)) / len(rows)) if rows else None})
    dates = []
    date = first
    while date <= as_of:
        dates.append({'date': date.isoformat(), 'year': date.year, 'month_number': date.month,
            'month': date.strftime('%Y-%m'), 'quarter': (date.month - 1) // 3 + 1,
            'day': date.day, 'is_complete_month': int(date.strftime('%Y-%m') < as_of.strftime('%Y-%m'))})
        date += dt.timedelta(days=1)
    silver = {'dim_product': list(products.values()), 'dim_customer': dim_customers, 'dim_date': dates,
        'crm_customers': list(crm.values()), 'crm_interactions': list(interactions.values()),
        'fact_order_lines': facts, 'fact_reviews': reviews}
    gold = {'q01_monthly_category': monthly, 'q02_category_sales': category_metrics,
        'q03_price_volume': product_metrics, 'q04_revenue_volume': scatter,
        'q05_category_pareto': pareto, 'q06_monthly_change': mom,
        'customer_segment_sales': segment_metrics, 'review_summary': review_summary}
    quality = {'store_customers': len(customers), 'orders': len(orders), 'order_lines': len(lines),
        'included_lines': len(sales), 'excluded_lines': len(facts) - len(sales),
        'crm_customers': len(crm), 'crm_interactions': len(interactions),
        'unmatched_store_customers': len(customers) - len(linked), 'valid_reviews': len(reviews),
        'quarantined_reviews': len(quarantine), 'duplicate_reviews': duplicates,
        'first_purchase': first.isoformat(), 'as_of': as_of.isoformat(), 'months_including_partial': len(months),
        'included_statuses': list(SALE_STATUSES), 'net_product_revenue_crc': amount(total_revenue),
        'subtotal_mismatches': 0, 'personal_fields_extracted': False}
    return silver, gold, quarantine, quality

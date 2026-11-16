#!/usr/bin/env python3
"""Terra Nostra ETL: immutable snapshots, validation, then one atomic latest pointer."""
import argparse
import csv
import datetime as dt
import fcntl
import hashlib
import io
import json
import os
import pathlib
import sys
import traceback
import uuid
from zoneinfo import ZoneInfo

from extract import extract
from model import REVIEW_FIELDS, SALE_STATUSES, transform
from storage import BlobStore

ROOT = pathlib.Path(__file__).resolve().parent
PRIVATE = ROOT / 'private'
ACCOUNT = 'stvintara508832'
VERSION = '1.0.0'


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def csv_bytes(rows, fields=None):
    output = io.StringIO(newline='')
    keys = fields or (list(rows[0]) if rows else [])
    writer = csv.DictWriter(output, fieldnames=keys, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8-sig')


def parse_reviews(data, blob):
    text = data.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text, newline=''))
    if not reader.fieldnames or set(reader.fieldnames) != set(REVIEW_FIELDS):
        raise ValueError('CSV schema mismatch in ' + blob)
    result = []
    for line in reader:
        if None in line or any(v is None for v in line.values()):
            raise ValueError('Malformed CSV row in ' + blob)
        result.append({**line, '_source_blob': blob})
    return result


def run(trigger, store=None):
    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    as_of = now.astimezone(ZoneInfo('America/Costa_Rica')).date()
    run_id = now.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    local = PRIVATE / 'runs' / run_id
    local.mkdir(parents=True, mode=0o700)
    cloud = store or BlobStore(ACCOUNT)
    report = {'run_id': run_id, 'trigger': trigger, 'started_at_utc': now.isoformat(),
        'as_of_costa_rica': as_of.isoformat(), 'pipeline_version': VERSION,
        'business': 'Terra Nostra', 'provider': 'CONTI', 'status': 'running',
        'source_environment': 'academic_store_no_real_payments', 'files': []}

    def upload(path, data, mime, rows=None):
        destination = local / path
        if not destination.resolve().is_relative_to(local.resolve()):
            raise ValueError('Unsafe source blob path')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        cloud.put('datalake', path, data, mime)
        report['files'].append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(),
                               'bytes': len(data), 'rows': rows})

    try:
        _, previous_etag = cloud.optional('datalake', 'latest.json')
        snapshot = extract()
        for name, rows in snapshot.items():
            upload(f'bronze/runs/{run_id}/{name}.json', json_bytes(rows), 'application/json', len(rows))
        source_files, reviews = [], []
        for name in cloud.list('fuentes', 'reviews/'):
            if not name.lower().endswith('.csv'):
                continue
            data, etag = cloud.get('fuentes', name)
            if len(data) > 10 * 1024 * 1024:
                raise ValueError('Review CSV exceeds 10 MiB limit')
            # Preserve source path, so equal basenames in separate folders cannot collide.
            path = f'bronze/runs/{run_id}/csv/{name}'
            upload(path, data, 'text/csv; charset=utf-8')
            source_files.append({'blob': name, 'etag': etag, 'sha256': hashlib.sha256(data).hexdigest()})
            reviews.extend(parse_reviews(data, name))
        if not source_files:
            raise ValueError('No CSV reviews found in fuentes/reviews/')
        silver, gold, quarantine, quality = transform(snapshot, reviews, as_of)
        report['source_files'] = source_files
        report['quality'] = quality
        code_hash = hashlib.sha256(b''.join((ROOT / file).read_bytes() for file in ['etl.py', 'extract.py', 'model.py', 'storage.py'])).hexdigest()
        fingerprint = {'source': snapshot, 'reviews': reviews, 'as_of': as_of.isoformat(),
                       'statuses': SALE_STATUSES, 'version': VERSION, 'code_hash': code_hash}
        report['code_sha256'] = code_hash
        report['input_sha256'] = hashlib.sha256(json_bytes(fingerprint)).hexdigest()
        upload(f'silver/runs/{run_id}/quarantine.csv', csv_bytes(quarantine, ['review_id', 'source_blob', 'reason']),
               'text/csv; charset=utf-8', len(quarantine))
        if quarantine:
            raise ValueError(f'{len(quarantine)} invalid reviews quarantined; latest snapshot was not replaced')
        if not quality['valid_reviews']:
            raise ValueError('No valid reviews available')
        for layer, tables in [('silver', silver), ('gold', gold)]:
            for name, rows in tables.items():
                upload(f'{layer}/runs/{run_id}/{name}.csv', csv_bytes(rows), 'text/csv; charset=utf-8', len(rows))
        report['status'] = 'succeeded'
        report['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        manifest_path = f'runs/{run_id}/manifest.json'
        manifest_data = json_bytes(report)
        (local / 'manifest.json').write_bytes(manifest_data)
        cloud.put('datalake', manifest_path, manifest_data)
        pointer = {'run_id': run_id, 'manifest': manifest_path, 'manifest_sha256': hashlib.sha256(manifest_data).hexdigest(),
                   'published_at_utc': report['finished_at_utc'], 'silver_prefix': f'silver/runs/{run_id}/',
                   'gold_prefix': f'gold/runs/{run_id}/', 'input_sha256': report['input_sha256']}
        condition = ('If-Match', previous_etag) if previous_etag else ('If-None-Match', '*')
        # No consumer is pointed at a partially uploaded or failed run.
        cloud.put('datalake', 'latest.json', json_bytes(pointer), condition=condition)
        temporary = PRIVATE / 'latest.json.tmp'
        temporary.write_bytes(json_bytes(pointer))
        temporary.replace(PRIVATE / 'latest.json')
        print(json.dumps({'status': 'succeeded', 'run_id': run_id, 'trigger': trigger,
                          'quality': quality}, ensure_ascii=False), flush=True)
        return report
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)
        report['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        failure = json_bytes(report)
        (local / 'failure.json').write_bytes(failure)
        try:
            cloud.put('datalake', f'audit/{run_id}.json', failure)
        except Exception:
            pass  # Local evidence survives a cloud outage; latest remains unchanged.
        print(json.dumps({'status': 'failed', 'run_id': run_id, 'error': str(exc)}), file=sys.stderr, flush=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger', choices=['manual', 'systemd', 'timer-proof'], default='manual')
    args = parser.parse_args()
    PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (PRIVATE / 'etl.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args.trigger)


if __name__ == '__main__':
    main()

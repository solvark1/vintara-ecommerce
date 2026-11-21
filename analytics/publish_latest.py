"""Publish verified Silver/Gold CSVs at stable paths for Power BI.

Directory renames avoid showing a half-uploaded set. The two directory moves
leave a short unavailable interval, not a multi-file read transaction: schedule
Power BI after the ETL. A durable journal restores an interrupted publication.
"""
import hashlib
import json
import pathlib
import re

CONTAINER = 'datalake'
JOURNAL = '_latest_publication.json'


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def read_json(cloud, name):
    data, _ = cloud.optional(CONTAINER, name)
    return json.loads(data) if data is not None else None


def move(cloud, source, destination, run_id):
    try:
        cloud.rename_directory(CONTAINER, source, destination)
    except Exception:
        # A response can be lost after Azure has completed the rename.
        actual = read_json(cloud, destination + '/manifest.json')
        source_manifest = read_json(cloud, source + '/manifest.json')
        if source_manifest is not None or not actual or actual['run_id'] != run_id:
            raise


def recover_latest(cloud):
    journal = read_json(cloud, JOURNAL)
    if not journal or journal['status'] != 'pending':
        return False
    run_id = journal['run_id']
    pointer = read_json(cloud, 'latest.json')
    current = read_json(cloud, 'latest/manifest.json')
    committed = bool(pointer and pointer['run_id'] == run_id
                     and pointer.get('latest_publication_id') == journal['publication_id'])
    if committed:
        if current is None:
            move(cloud, journal['staging'], 'latest', run_id)
        elif current['run_id'] != run_id:
            raise RuntimeError('Concurrent latest publication; refusing to replace it')
    else:
        if current and current.get('publication_id') == journal['publication_id']:
            move(cloud, 'latest', journal['staging'], run_id)
            current = None
        previous = journal['previous_run_id']
        if previous and current is None:
            move(cloud, journal['previous'], 'latest', previous)
        elif previous and current['run_id'] != previous:
            raise RuntimeError('Concurrent latest publication; recovery needs review')
    cloud.put(CONTAINER, JOURNAL, encode({**journal, 'status': 'committed' if committed else 'rolled_back'}))
    return committed


def publish_latest(cloud, report, pointer, previous_etag):
    """Stage and verify every table, swap folders, then commit latest.json."""
    import uuid
    recover_latest(cloud)
    if report['status'] != 'succeeded':
        raise ValueError('Only successful snapshots can be published')
    run_id = report['run_id']
    if not re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{8}', run_id):
        raise ValueError('Invalid run identifier')
    publication_id = uuid.uuid4().hex
    staging = '_latest_staging/' + publication_id
    previous = '_latest_previous/' + publication_id
    old = read_json(cloud, 'latest/manifest.json')
    if old is None and cloud.list(CONTAINER, 'latest/'):
        raise RuntimeError('Existing latest folder has no managed manifest; refusing to replace it')
    files = []
    for source in report['files']:
        path = pathlib.PurePosixPath(source['path'])
        if (len(path.parts) != 4 or path.parts[0] not in ('silver', 'gold')
                or path.parts[1:3] != ('runs', run_id)
                or path.name == 'quarantine.csv' or path.suffix != '.csv'):
            continue
        data, _ = cloud.get(CONTAINER, source['path'])
        if len(data) != source['bytes'] or hashlib.sha256(data).hexdigest() != source['sha256']:
            raise RuntimeError('Source snapshot integrity failure: ' + source['path'])
        relative = path.parts[0] + '/' + path.name
        cloud.put(CONTAINER, staging + '/' + relative, data, 'text/csv; charset=utf-8')
        files.append({**source, 'source_path': source['path'], 'path': relative})
    if not files or len({f['path'] for f in files}) != len(files):
        raise ValueError('Missing or duplicate publication tables')
    manifest = {'run_id': run_id, 'publication_id': publication_id, 'status': 'succeeded',
                'snapshot_manifest': pointer['manifest'], 'snapshot_manifest_sha256': pointer['manifest_sha256'],
                'source_trigger': report['trigger'], 'as_of_costa_rica': report['as_of_costa_rica'],
                'pipeline_version': report['pipeline_version'], 'quality': report['quality'], 'files': files}
    cloud.put(CONTAINER, staging + '/manifest.json', encode(manifest))
    journal = {'status': 'pending', 'run_id': run_id, 'publication_id': publication_id,
               'staging': staging, 'previous': previous, 'previous_run_id': old['run_id'] if old else None}
    # Persist before moving the visible folder so process termination is recoverable.
    cloud.put(CONTAINER, JOURNAL, encode(journal))
    published_pointer = {**pointer, 'latest_prefix': 'latest/', 'latest_publication_id': publication_id}
    try:
        if old:
            move(cloud, 'latest', previous, old['run_id'])
        move(cloud, staging, 'latest', run_id)
        condition = ('If-Match', previous_etag) if previous_etag else ('If-None-Match', '*')
        cloud.put(CONTAINER, 'latest.json', encode(published_pointer), condition=condition)
        cloud.put(CONTAINER, JOURNAL, encode({**journal, 'status': 'committed'}))
    except Exception:
        if not recover_latest(cloud):
            raise
    return published_pointer

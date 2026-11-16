#!/usr/bin/env python3
"""Export a verified, private BI snapshot; does not publish data to GitHub or the web."""
import hashlib
import json
import os
import pathlib
import zipfile
from storage import BlobStore
from verify import verify

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    os.umask(0o077)
    manifest = verify()
    cloud = BlobStore('stvintara508832')
    target = ROOT / 'private' / 'bi' / manifest['run_id']
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    selected = [f for f in manifest['files'] if f['path'].startswith(('silver/', 'gold/')) and not f['path'].endswith('quarantine.csv')]
    for record in selected:
        data, _ = cloud.get('datalake', record['path'])
        assert hashlib.sha256(data).hexdigest() == record['sha256']
        layer = record['path'].split('/')[0]
        destination = target / layer / record['path'].rsplit('/', 1)[-1]
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(data)
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = ROOT / 'private' / 'bi' / 'terranostra-bi-latest.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for file in sorted(target.rglob('*')):
            if file.is_file():
                output.write(file, str(file.relative_to(target)))
    print(json.dumps({'exported': True, 'run_id': manifest['run_id'], 'csv_tables': len(selected),
                      'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'archive': str(archive)}))


if __name__ == '__main__':
    main()

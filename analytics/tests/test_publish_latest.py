import hashlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from publish_latest import JOURNAL, encode, publish_latest, recover_latest


class MemoryStore:
    def __init__(self):
        self.data = {}
        self.fail_put = lambda name: False
        self.fail_move = lambda source, destination: False
        self.lost_move_response = False

    def get(self, container, name):
        return self.data[name], 'etag'

    def optional(self, container, name):
        return (self.data[name], 'etag') if name in self.data else (None, None)

    def list(self, container, prefix):
        return sorted(k for k in self.data if k.startswith(prefix))

    def put(self, container, name, data, *args, **kwargs):
        if self.fail_put(name):
            raise RuntimeError('upload failed')
        self.data[name] = data

    def rename_directory(self, container, source, destination):
        if self.fail_move(source, destination):
            raise RuntimeError('move failed')
        entries = self.list(container, source + '/')
        if not entries or self.list(container, destination + '/'):
            raise RuntimeError('missing source or existing target')
        for key in entries:
            self.data[destination + key[len(source):]] = self.data.pop(key)
        if self.lost_move_response:
            raise RuntimeError('response lost after successful move')


def snapshot(store, run_id, tables=('q01', 'q02')):
    files = []
    for name in tables:
        data = ('value\n' + run_id + '\n').encode()
        path = 'gold/runs/' + run_id + '/' + name + '.csv'
        store.data[path] = data
        files.append({'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'rows': 1})
    report = {'status': 'succeeded', 'run_id': run_id, 'files': files, 'trigger': 'systemd',
              'as_of_costa_rica': '2026-11-20', 'pipeline_version': '1.1.0', 'quality': {}}
    pointer = {'run_id': run_id, 'manifest': 'runs/' + run_id + '/manifest.json', 'manifest_sha256': 'example'}
    return report, pointer


class LatestTests(unittest.TestCase):
    old_id = '20261119T090000Z-11111111'
    new_id = '20261120T090000Z-22222222'

    def setUp(self):
        self.cloud = MemoryStore()
        report, pointer = snapshot(self.cloud, self.old_id, ('q01', 'removed'))
        publish_latest(self.cloud, report, pointer, None)
        self.old = {k: v for k, v in self.cloud.data.items() if k.startswith('latest/') or k == 'latest.json'}
        self.report, self.pointer = snapshot(self.cloud, self.new_id)

    def assert_previous_is_preserved(self):
        visible = {k: v for k, v in self.cloud.data.items() if k.startswith('latest/') or k == 'latest.json'}
        self.assertEqual(visible, self.old)

    def test_next_run_replaces_set_without_stale_tables_or_accumulation(self):
        publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assertEqual(self.cloud.list('datalake', 'latest/gold/'), ['latest/gold/q01.csv', 'latest/gold/q02.csv'])
        self.assertEqual(json.loads(self.cloud.data['latest/manifest.json'])['run_id'], self.new_id)
        self.assertIn('gold/runs/' + self.old_id + '/removed.csv', self.cloud.data)

    def test_staging_failure_preserves_previous(self):
        self.cloud.fail_put = lambda name: name.startswith('_latest_staging/') and name.endswith('/q02.csv')
        with self.assertRaises(RuntimeError):
            publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assert_previous_is_preserved()

    def test_source_corruption_preserves_previous(self):
        self.cloud.data[self.report['files'][0]['path']] = b'corrupt'
        with self.assertRaisesRegex(RuntimeError, 'integrity'):
            publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assert_previous_is_preserved()

    def test_failed_folder_promotion_restores_previous(self):
        self.cloud.fail_move = lambda source, destination: source.startswith('_latest_staging/')
        with self.assertRaises(RuntimeError):
            publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assert_previous_is_preserved()

    def test_pointer_commit_failure_rolls_back_folder(self):
        self.cloud.fail_put = lambda name: name == 'latest.json'
        with self.assertRaises(RuntimeError):
            publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assert_previous_is_preserved()

    def test_lost_rename_response_is_reconciled(self):
        self.cloud.lost_move_response = True
        publish_latest(self.cloud, self.report, self.pointer, 'etag')
        self.assertEqual(json.loads(self.cloud.data['latest.json'])['run_id'], self.new_id)

    def test_process_death_after_moving_old_folder_recovers_on_next_run(self):
        previous = '_latest_previous/interrupted'
        self.cloud.rename_directory('datalake', 'latest', previous)
        self.cloud.data[JOURNAL] = encode({'status': 'pending', 'run_id': self.new_id,
            'publication_id': 'interrupted', 'staging': '_latest_staging/interrupted',
            'previous': previous, 'previous_run_id': self.old_id})
        self.assertFalse(recover_latest(self.cloud))
        self.assert_previous_is_preserved()

    def test_unmanaged_latest_folder_is_not_overwritten(self):
        del self.cloud.data['latest/manifest.json']
        with self.assertRaisesRegex(RuntimeError, 'no managed manifest'):
            publish_latest(self.cloud, self.report, self.pointer, 'etag')


if __name__ == '__main__':
    unittest.main()

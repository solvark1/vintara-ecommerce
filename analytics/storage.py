"""Private Azure Blob operations using only the VM's managed identity."""
import base64
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class BlobStore:
    def __init__(self, account):
        self.base = f'https://{account}.blob.core.windows.net'
        self.token = None
        self.expires = 0

    def request(self, container, name='', method='GET', data=None, extra=None, query='', endpoint='blob'):
        if time.time() + 120 >= self.expires:
            req = urllib.request.Request(
                'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fstorage.azure.com%2F',
                headers={'Metadata': 'true'})
            with urllib.request.urlopen(req, timeout=20) as response:
                identity = json.load(response)
            self.token = identity['access_token']
            self.expires = int(identity['expires_on'])
        base = self.base if endpoint == 'blob' else self.base.replace('.blob.', '.dfs.')
        url = base + '/' + container + '/' + urllib.parse.quote(name, safe='/') + query
        headers = {'Authorization': 'Bearer ' + self.token, 'x-ms-version': '2023-11-03', **(extra or {})}
        if method == 'PUT' and endpoint == 'blob':
            headers.update({'x-ms-blob-type': 'BlockBlob', 'Content-MD5': base64.b64encode(hashlib.md5(data).digest()).decode()})
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, method=method, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=90) as response:
                    return response.read(), response.headers.get('ETag')
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
            except urllib.error.URLError:
                if attempt == 3:
                    raise
            time.sleep(2 ** attempt)

    def get(self, container, name):
        return self.request(container, name)

    def optional(self, container, name):
        try:
            return self.get(container, name)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, None
            raise

    def put(self, container, name, data, mime='application/json', condition=None):
        headers = {'Content-Type': mime}
        if condition:
            headers[condition[0]] = condition[1]
        self.request(container, name, 'PUT', data, headers)
        # Readback detects corrupt/truncated content before a snapshot can be published.
        actual, _ = self.get(container, name)
        if hashlib.sha256(actual).digest() != hashlib.sha256(data).digest():
            raise RuntimeError('Blob integrity check failed: ' + name)

    def list(self, container, prefix=''):
        marker = ''
        result = []
        while True:
            query = '?' + urllib.parse.urlencode({'restype': 'container', 'comp': 'list', 'prefix': prefix, 'marker': marker})
            data, _ = self.request(container, query=query)
            tree = ET.fromstring(data)
            result.extend(node.findtext('Name') for node in tree.findall('./Blobs/Blob'))
            marker = tree.findtext('NextMarker')
            if not marker:
                return sorted(result)

    def rename_directory(self, container, source, destination):
        """Move a small prepared publication; never overwrite a destination."""
        for path in (source, destination):
            if not path or path.startswith('/') or any(p in ('', '.', '..') for p in path.split('/')):
                raise ValueError('Unsafe directory path')
        parent = destination.rpartition('/')[0]
        if parent:
            try:
                self.request(container, parent, 'PUT', b'',
                             {'If-None-Match': '*'}, '?resource=directory', endpoint='dfs')
            except urllib.error.HTTPError as exc:
                if exc.code not in (409, 412):
                    raise
        self.request(container, destination, 'PUT', b'',
                     {'x-ms-rename-source': '/' + container + '/' + urllib.parse.quote(source, safe='/'),
                      'If-None-Match': '*'}, '?mode=posix', endpoint='dfs')

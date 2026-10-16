#!/usr/bin/env python3
"""Fail closed when a full-ISO bundle is missing or modified."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('bundle', type=Path)
args = parser.parse_args()
bundle = args.bundle.resolve()
manifest = json.loads((bundle / 'manifest.json').read_text())
required = set()
for name in ['compose.yml', 'erpnext.compose.yml']:
    config = yaml.safe_load((root / 'services' / name).read_text())
    required.update(service['image'] for service in config['services'].values())
    overrides = json.loads((bundle / (name + '.override.json')).read_text())['services']
    for service, spec in config['services'].items():
        assert overrides[service]['image'] == manifest[spec['image']]['local_tag'], 'Incomplete offline overrides'
for image in sorted(required):
    item = manifest[image]
    archive = (bundle / item['file']).resolve()
    assert archive.parent == bundle, 'Archive path escapes bundle'
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256'], 'Checksum mismatch: ' + image
    assert item['image_id'].startswith('sha256:') and item['local_tag'].startswith('9b7-offline/')
with (bundle / 'models.tar').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == (bundle / 'models.sha256').read_text().split()[0]
print(f'Full bundle verified: {len(required)} images and local model archive')

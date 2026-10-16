#!/usr/bin/env python3
"""Validate real Docker archive loading without permitting a registry pull at runtime."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from nineb7.services import ensure_images

tag = '9b7-offline/roundtrip:test'
subprocess.run(['docker', 'image', 'inspect', 'alpine:3.22'], stdout=subprocess.DEVNULL, check=True)
with tempfile.TemporaryDirectory(prefix='9b7-roundtrip-') as directory:
    base = Path(directory)
    (base / 'services').mkdir()
    (base / 'offline').mkdir()
    (base / 'services/compose.yml').write_text(json.dumps({'services': {'n8n': {'image': tag, 'profiles': ['n8n']}}}))
    subprocess.run(['docker', 'tag', 'alpine:3.22', tag], check=True)
    image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag], text=True).strip()
    archive = base / 'offline/image.tar.gz'
    with gzip.open(archive, 'wb') as stream:
        stream.write(subprocess.check_output(['docker', 'save', tag]))
    with archive.open('rb') as stream:
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    (base / 'offline/manifest.json').write_text(json.dumps({'upstream': {'local_tag': tag, 'image_id': image_id, 'file': 'image.tar.gz', 'sha256': sha}}))
    subprocess.run(['docker', 'image', 'rm', tag], check=True, stdout=subprocess.DEVNULL)
    os.environ['NINEB7_ROOT'] = str(base)
    os.environ['XDG_STATE_HOME'] = str(base / 'state')
    try:
        ensure_images('n8n')
        result = subprocess.check_output(['docker', 'run', '--rm', '--pull', 'never', tag, 'echo', '9b7-offline-ok'], text=True)
        assert result.strip() == '9b7-offline-ok'
        print('Offline archive roundtrip passed: verified archive loaded and ran with --pull never')
    finally:
        subprocess.run(['docker', 'image', 'rm', tag], check=True, stdout=subprocess.DEVNULL)

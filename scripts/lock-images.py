#!/usr/bin/env python3
"""Resolve current declared service image versions to immutable amd64 digests."""
import concurrent.futures
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
files = [root / 'services/compose.yml', root / 'services/erpnext.compose.yml']
texts = {path: path.read_text() for path in files}
pattern = re.compile(r'(?m)^(\s*(?:image:|x-image: &image)\s+)([^\s#]+)')
images = {m[2].split('@')[0] for text in texts.values() for m in pattern.finditer(text) if not m[2].startswith('*')}


def resolve(image):
    result = json.loads(subprocess.check_output(['docker', 'manifest', 'inspect', '--verbose', image], text=True))
    entries = result if isinstance(result, list) else [result]
    candidates = [entry['Descriptor'] for entry in entries if entry['Descriptor'].get('platform', {}).get('architecture') == 'amd64'
                  and entry['Descriptor'].get('platform', {}).get('os') == 'linux']
    if len(candidates) != 1:
        raise RuntimeError('Expected exactly one linux/amd64 image: ' + image)
    return image, candidates[0]['digest']


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    locked = dict(executor.map(resolve, sorted(images)))
for path, text in texts.items():
    def replace(match):
        image = match[2].split('@')[0]
        return match[0] if image.startswith('*') else match[1] + image + '@' + locked[image]
    path.write_text(pattern.sub(replace, text))
(root / 'services/images.lock.json').write_text(json.dumps(locked, indent=2) + '\n')
print(f'Locked {len(locked)} images to linux/amd64 manifests')

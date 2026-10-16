#!/usr/bin/env python3
"""Fetch the pinned official Ollama model, verifying every blob before packaging."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'packaging/model-lock.json').read_text())
    raw = (ROOT / 'packaging/qwen2.5-1.5b.manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != lock['manifest_sha256']:
        raise ValueError('Pinned model manifest checksum mismatch')
    manifest = json.loads(raw)
    cache = ROOT / 'cache/model'
    blobs = cache / 'models/blobs'
    blobs.mkdir(parents=True, exist_ok=True)
    for layer in [manifest['config'], *manifest['layers']]:
        digest = layer['digest']
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError('Invalid model digest')
        target = blobs / digest.replace(':', '-')
        if target.exists():
            with target.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() == digest[7:]:
                    continue
        print('Downloading verified model blob:', digest, flush=True)
        partial = target.with_suffix('.partial')
        checksum = hashlib.sha256()
        size = 0
        with urllib.request.urlopen('https://registry.ollama.ai/v2/library/qwen2.5/blobs/' + digest, timeout=120) as response, partial.open('wb') as stream:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                checksum.update(chunk)
                stream.write(chunk)
        if size != layer['size'] or checksum.hexdigest() != digest[7:]:
            partial.unlink()
            raise ValueError('Model blob size or checksum mismatch: ' + digest)
        partial.replace(target)
    destination = cache / 'models/manifests/registry.ollama.ai/library/qwen2.5/1.5b'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    archive = output / 'models.tar'
    with tarfile.open(output / 'models.tar.partial', 'w') as stream:
        stream.add(cache / 'models', arcname='models')
    (output / 'models.tar.partial').replace(archive)
    with archive.open('rb') as stream:
        checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
    (output / 'models.sha256').write_text(checksum + '  models.tar\n')
    print('Pinned Qwen model verified and packaged', flush=True)


if __name__ == '__main__':
    main()

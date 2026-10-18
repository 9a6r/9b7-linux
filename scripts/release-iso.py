#!/usr/bin/env python3
"""Prepare, resume-upload, and independently verify split GitHub ISO releases."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request
import urllib.parse

CHUNK = 1900 * 1024**2  # GitHub limits each release asset to 2 GiB.
BUFFER = 8 * 1024**2


def gh(*args):
    env = dict(os.environ)
    if env.get('GH_UPLOAD_TOKEN'): env['GH_TOKEN'] = env['GH_UPLOAD_TOKEN']
    return subprocess.check_output(['gh', *map(str, args)], text=True, env=env)


def get_release(repo, tag):
    # GitHub's /releases/tags endpoint returns 404 for unpublished draft tags.
    url = json.loads(gh('release', 'view', tag, '--repo', repo, '--json', 'apiUrl'))['apiUrl']
    return json.loads(gh('api', url))


def prepare(iso, output, chunk_size=CHUNK):
    if not re.fullmatch(r'[A-Za-z0-9._-]+', iso.name):
        raise ValueError('ISO filename must contain only letters, digits, dots, underscores and hyphens')
    expected = iso.with_name(iso.name + '.sha256').read_text().split()[0]
    total = hashlib.sha256()
    parts = []
    with iso.open('rb') as source:
        while True:
            digest = hashlib.sha256()
            size = 0
            while size < chunk_size:
                data = source.read(min(BUFFER, chunk_size - size))
                if not data:
                    break
                size += len(data)
                digest.update(data)
                total.update(data)
            if not size:
                break
            parts.append({'file': f'{iso.name}.part{len(parts)+1:02}',
                          'size': size, 'sha256': digest.hexdigest()})
    if total.hexdigest() != expected or not parts:
        raise ValueError('Original ISO checksum mismatch or empty ISO')
    manifest = {'iso': iso.name, 'size': sum(p['size'] for p in parts),
                'sha256': expected, 'parts': parts}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'iso-parts.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'SHA256SUMS.parts').write_text(''.join(
        f"{p['sha256']}  {p['file']}\n" for p in parts))
    script = '#!/usr/bin/env bash\nset -euo pipefail\ncd "$(dirname "${BASH_SOURCE[0]}")"\n'
    script += f'iso="{iso.name}"\n[[ ! -e "$iso" && ! -e "$iso.partial" ]] || {{ echo "Output already exists; rename it first." >&2; exit 1; }}\n'
    script += 'sha256sum --check SHA256SUMS.parts\n'
    script += 'cat -- ' + ' '.join('"'+p['file']+'"' for p in parts) + ' > "$iso.partial"\n'
    script += f'printf "%s\\n" "{expected}  $iso.partial" | sha256sum --check -\nmv -- "$iso.partial" "$iso"\necho "ISO verified. Open it in VirtualBox."\n'
    (output / 'JOIN-LINUX.sh').write_text(script)
    windows = r'''$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$m = Get-Content -Raw -LiteralPath 'iso-parts.json' | ConvertFrom-Json
if ($m.iso -notmatch '^[A-Za-z0-9._-]+$') { throw 'Invalid ISO name' }
$partial = $m.iso + '.partial'
if ((Test-Path -LiteralPath $m.iso) -or (Test-Path -LiteralPath $partial)) { throw 'Output already exists; rename it first.' }
foreach ($part in $m.parts) {
    if ($part.file -notmatch '^[A-Za-z0-9._-]+$') { throw 'Invalid part name' }
    if ((Get-Item -LiteralPath $part.file).Length -ne $part.size) { throw "Wrong size: $($part.file)" }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $part.file).Hash -ne $part.sha256) { throw "Checksum mismatch: $($part.file)" }
}
$target = [IO.File]::Open((Join-Path $PSScriptRoot $partial), [IO.FileMode]::CreateNew)
try {
    foreach ($part in $m.parts) {
        $source = [IO.File]::OpenRead((Join-Path $PSScriptRoot $part.file))
        try { $source.CopyTo($target) } finally { $source.Dispose() }
    }
} finally { $target.Dispose() }
if ((Get-Item -LiteralPath $partial).Length -ne $m.size) { throw 'ISO size mismatch' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $partial).Hash -ne $m.sha256) { throw 'ISO checksum mismatch' }
Move-Item -LiteralPath $partial -Destination $m.iso
Write-Host 'ISO verified. Open it in VirtualBox.'
'''
    (output / 'JOIN-WINDOWS.ps1').write_text(windows)
    (output / 'JOIN-WINDOWS.cmd').write_bytes(b'@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0JOIN-WINDOWS.ps1"\r\nif errorlevel 1 (echo Assembly failed. & pause & exit /b 1)\r\npause\r\n')
    subprocess.run(['bash', '-n', str(output / 'JOIN-LINUX.sh')], check=True)
    return manifest


def upload(iso, output, tag, repo):
    manifest = json.loads((output / 'iso-parts.json').read_text())
    expected = iso.with_name(iso.name + '.sha256').read_text().split()[0]
    if manifest['sha256'] != expected or manifest['size'] != iso.stat().st_size:
        raise ValueError('Run prepare for this ISO first')
    release = get_release(repo, tag)
    if not release['draft']:
        raise ValueError('Only draft releases can be uploaded; publish after validation')
    # Probe asset authorization before allocating a large temporary part.
    metadata = [output / name for name in ('iso-parts.json', 'SHA256SUMS.parts',
                'JOIN-LINUX.sh', 'JOIN-WINDOWS.cmd', 'JOIN-WINDOWS.ps1')]
    metadata += [iso.with_name(iso.name + '.sha256'), iso.with_name(iso.name + '.packages.txt'), (iso.with_name(iso.name + '.source-commit') if iso.with_name(iso.name + '.source-commit').exists() else iso.parent / 'SOURCE-COMMIT')]
    gh('release', 'upload', tag, '--repo', repo, '--clobber', *metadata)
    assets = {a['name']: a for a in release['assets']}
    token = os.environ.get('GH_UPLOAD_TOKEN') or os.environ.get('GH_TOKEN') or gh('auth', 'token').strip()
    upload_url = release['upload_url'].split('{')[0]
    if urllib.parse.urlparse(upload_url).hostname != 'uploads.github.com':
        raise ValueError('Unexpected GitHub upload host')

    def upload_part(task):
        part, offset = task
        asset = assets.get(part['file'], {})
        if asset.get('size') == part['size'] and asset.get('digest') == 'sha256:' + part['sha256']:
            print('Verified existing asset:', part['file'], flush=True)
            return
        if asset.get('id'):
            gh('api', '--method', 'DELETE', f"repos/{repo}/releases/assets/{asset['id']}")
        digest = hashlib.sha256()

        def body():
            # A bounded stream avoids a second 1.9 GiB file on constrained builders.
            with iso.open('rb') as source:
                source.seek(offset)
                remaining = part['size']
                while remaining:
                    data = source.read(min(BUFFER, remaining))
                    if not data:
                        raise ValueError('Unexpected ISO EOF')
                    digest.update(data)
                    remaining -= len(data)
                    yield data

        request = urllib.request.Request(
            upload_url + '?' + urllib.parse.urlencode({'name': part['file']}),
            data=body(), method='POST', headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(part['size']),
                'Accept': 'application/vnd.github+json',
                'User-Agent': '9b7-verified-release-publisher',
            })
        with urllib.request.urlopen(request, timeout=900) as response:
            uploaded = json.load(response)
        if (digest.hexdigest() != part['sha256'] or uploaded['size'] != part['size']
                or uploaded.get('digest') != 'sha256:' + part['sha256']):
            raise ValueError('Uploaded part digest does not match prepared ISO: ' + part['file'])
        print('Uploaded and server digest verified:', part['file'], flush=True)

    tasks = []
    offset = 0
    for part in manifest['parts']:
        tasks.append((part, offset))
        offset += part['size']
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(upload_part, tasks))


def verify(output, tag, repo):
    manifest = json.loads((output / 'iso-parts.json').read_text())
    release = get_release(repo, tag)
    if release['draft']:
        raise ValueError('Publish as a prerelease before checking anonymous downloads')
    assets = {a['name']: a for a in release['assets']}
    total = hashlib.sha256()
    size = 0
    for part in manifest['parts']:
        asset = assets[part['file']]
        if asset['size'] != part['size']:
            raise ValueError('Published asset size mismatch')
        digest = hashlib.sha256()
        part_size = 0
        # Deliberately no authorization: validates the public download path.
        with urllib.request.urlopen(asset['browser_download_url'], timeout=120) as response:
            while data := response.read(BUFFER):
                total.update(data)
                digest.update(data)
                part_size += len(data)
        if part_size != part['size'] or digest.hexdigest() != part['sha256']:
            raise ValueError('Downloaded part checksum mismatch: ' + part['file'])
        size += part_size
        print('Downloaded and verified:', part['file'], flush=True)
    if size != manifest['size'] or total.hexdigest() != manifest['sha256']:
        raise ValueError('Reassembled download does not match original ISO')
    for name in ('iso-parts.json', 'SHA256SUMS.parts', 'JOIN-LINUX.sh', 'JOIN-WINDOWS.cmd', 'JOIN-WINDOWS.ps1'):
        with urllib.request.urlopen(assets[name]['browser_download_url'], timeout=60) as response:
            if response.read() != (output / name).read_bytes():
                raise ValueError('Published helper mismatch: ' + name)
    evidence = {'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'release': release['html_url'], 'size': size, 'sha256': total.hexdigest(),
                'parts': len(manifest['parts']), 'anonymous_download': True}
    (output / 'PUBLIC-DOWNLOAD-VERIFIED.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'upload', 'verify'])
    parser.add_argument('--iso', type=Path)
    parser.add_argument('--output', type=Path, default=Path('work/release-delivery'))
    parser.add_argument('--tag', default='v0.1.0-rc1')
    parser.add_argument('--repo', default='9a6r/9b7-linux')
    args = parser.parse_args()
    if args.action != 'verify' and args.iso is None:
        parser.error('--iso is required for prepare/upload')
    if args.action == 'prepare':
        result = prepare(args.iso.resolve(), args.output)
        print(f"Prepared {len(result['parts'])} parts; original SHA256 {result['sha256']}")
    elif args.action == 'upload':
        upload(args.iso.resolve(), args.output, args.tag, args.repo)
    else:
        verify(args.output, args.tag, args.repo)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare verified Docker archives and one local model for the full ISO."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nineb7 import services


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove-exported', action='store_true', help='Remove each exported image from this dedicated Docker daemon to bound storage use')
    args = parser.parse_args()
    output = ROOT / "cache/offline"
    output.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output).free < 12 * 1024**3:
        raise SystemExit("Offline bundling needs 12 GiB free plus space in the Docker data store; use a dedicated builder.")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    with tempfile.TemporaryDirectory() as state:
        os.environ["XDG_STATE_HOME"] = state
        images = set()
        for stack in services.CATALOG:
            result = subprocess.check_output(services.compose_command(stack, "config", "--images"), text=True)
            images.update(result.splitlines())
        for image in sorted(images):
            archive = output / (image.replace("/", "_").replace(":", "_") + ".tar.gz")
            existing = manifest.get(image)
            if existing and archive.exists():
                with archive.open("rb") as stream:
                    if hashlib.file_digest(stream, "sha256").hexdigest() == existing["sha256"]:
                        print("Reusing verified archive:", image, flush=True)
                        continue
            run("docker", "pull", "--platform", "linux/amd64", image)
            local_tag = "9b7-offline/" + image.split(":")[0].replace("/", "-") + ":" + image.rsplit(":", 1)[1]
            run("docker", "tag", image, local_tag)
            temp = archive.with_suffix(".partial")
            # Docker load accepts gzip directly; stream compression avoids a second
            # full-size uncompressed copy of every multi-gigabyte image.
            with temp.open('wb') as stream:
                save = subprocess.Popen(['docker', 'save', local_tag], stdout=subprocess.PIPE)
                try:
                    compressed = subprocess.run(['gzip', '-3', '-n'], stdin=save.stdout, stdout=stream)
                    save.stdout.close()
                    status = save.wait()
                    if status or compressed.returncode:
                        raise RuntimeError('Docker image export/compression failed: ' + image)
                finally:
                    if save.poll() is None:
                        save.kill()
                        save.wait()
            temp.replace(archive)
            digest = subprocess.check_output(["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", image], text=True).strip()
            with archive.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            image_id = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()
            manifest[image] = {"file": archive.name, "sha256": checksum, "digest": digest,
                               "local_tag": local_tag, "image_id": image_id}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            print('Verified compressed archive:', archive.name, flush=True)
            if args.remove_exported:
                run('docker', 'image', 'rm', local_tag, image)
        # Docker save/load does not preserve registry RepoDigests. Verified local tags
        # and image IDs are used in these overrides, so full ISOs never need a registry.
        for stack, filename in [("databases", "compose.yml"), ("erpnext", "erpnext.compose.yml")]:
            cmd = services.compose_command(stack, "config", "--format", "json")
            # Activate every profile while generating the complete main override.
            cmd[cmd.index("--profile") + 1] = "*"
            config = json.loads(subprocess.check_output(cmd, text=True))
            override = {"services": {name: {"image": manifest[svc["image"]]["local_tag"]}
                                      for name, svc in config["services"].items()}}
            (output / (filename + ".override.json")).write_text(json.dumps(override, indent=2) + "\n")
        run(sys.executable, str(ROOT / 'scripts/fetch-model.py'), str(output))
        run(sys.executable, str(ROOT / 'scripts/verify-offline.py'), str(output))
    print("Offline bundle complete. Verify the full ISO in a VM with networking disconnected.")


if __name__ == "__main__":
    main()

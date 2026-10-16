#!/usr/bin/env python3
"""Prepare verified Docker archives and one local model for the full ISO."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nineb7 import services


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    output = ROOT / "cache/offline"
    output.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output).free < 35 * 1024**3:
        raise SystemExit("Offline bundling needs at least 35 GiB free; full ISO builds need a 100 GiB workspace.")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    with tempfile.TemporaryDirectory() as state:
        os.environ["XDG_STATE_HOME"] = state
        images = set()
        for stack in services.CATALOG:
            result = subprocess.check_output(services.compose_command(stack, "config", "--images"), text=True)
            images.update(result.splitlines())
        for image in sorted(images):
            archive = output / (image.replace("/", "_").replace(":", "_") + ".tar")
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
            run("docker", "save", "-o", str(temp), local_tag)
            temp.replace(archive)
            digest = subprocess.check_output(["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", image], text=True).strip()
            with archive.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            image_id = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()
            manifest[image] = {"file": archive.name, "sha256": checksum, "digest": digest,
                               "local_tag": local_tag, "image_id": image_id}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
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
        # The temporary model container has no host ports and is always removed.
        ai_image = next(name for name in images if name.startswith("ollama/ollama:"))
        container = "9b7-model-export-" + str(os.getpid())
        run("docker", "run", "-d", "--name", container, ai_image)
        try:
            for attempt in range(30):
                probe = subprocess.run(["docker", "exec", container, "ollama", "list"], capture_output=True)
                if probe.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Ollama did not start")
            run("docker", "exec", container, "ollama", "pull", "qwen2.5:1.5b")
            with (output / "models.tar.partial").open("wb") as stream:
                run("docker", "exec", container, "tar", "-C", "/root/.ollama", "-cf", "-", "models", stdout=stream)
            (output / "models.tar.partial").replace(output / "models.tar")
            with (output / "models.tar").open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            (output / "models.sha256").write_text(checksum + "  models.tar\n")
        finally:
            run("docker", "rm", "-f", container)
    print("Offline bundle complete. Verify the full ISO in a VM with networking disconnected.")


if __name__ == "__main__":
    main()

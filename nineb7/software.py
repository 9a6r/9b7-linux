"""Verified per-user agent installation; no credentials or root privileges."""
from __future__ import annotations
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from .services import project_root


def catalog():
    return json.loads((project_root() / "packaging/agents-lock.json").read_text())


def data_root():
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "9b7/agents"


def entry(key):
    entries = catalog()
    if key not in entries:
        raise ValueError("Unknown agent")
    return entries[key]


def installed(key):
    entry(key)
    receipt = data_root() / key / "current/receipt.json"
    if not receipt.is_file():
        return None
    data = json.loads(receipt.read_text())
    binary = data_root() / key / "current" / data["binary"]
    if not binary.is_file() or not os.access(binary, os.X_OK):
        return None
    return {**data, "path": str(binary)}


def download(item, destination, progress=lambda *_: None):
    request = urllib.request.Request(item["url"], headers={"User-Agent": "9b7-AI-Hub/0.1"})
    if not item["url"].startswith("https://"):
        raise ValueError("HTTPS is required")
    digest = hashlib.sha256(); size = 0
    with urllib.request.urlopen(request, timeout=60) as response, open(destination, "xb") as stream:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > item["size"]:
                raise ValueError("Download exceeds the reviewed size")
            digest.update(chunk); stream.write(chunk); progress(size, item["size"])
    if size != item["size"] or digest.hexdigest() != item["sha256"]:
        raise ValueError("Download checksum or size mismatch; nothing installed")


def extract(archive, target):
    """Reject traversal, links, devices and oversized archives before extracting."""
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if len(members) > 50000 or sum(m.size for m in members) > 2 * 1024**3:
            raise ValueError("Archive exceeds extraction limits")
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not (member.isfile() or member.isdir()):
                raise ValueError("Unsafe archive entry")
        for member in members:
            name = target.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                name.mkdir(parents=True, exist_ok=True)
                continue
            name.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as src, name.open("xb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            name.chmod(0o755 if member.mode & 0o111 else 0o644)


def install(key, progress=lambda *_: None, fetch=download):
    item = entry(key)
    if item.get("requires", "").startswith("node"):
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Node.js 20 or newer is required; install it from Software Center")
        major = int(subprocess.check_output([node, "--version"], text=True).strip().lstrip("v").split(".")[0])
        if major < 20:
            raise RuntimeError("Node.js 20 or newer is required")
    if platform.machine() not in ("x86_64", "AMD64"):
        raise RuntimeError("This catalog currently supports Linux x86_64 only")
    parent = data_root() / key
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (parent / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        existing = installed(key)
        if existing and existing["sha256"] == item["sha256"]:
            return existing
        if shutil.disk_usage(parent).free < item["size"] * 5 + 500 * 1024**2:
            raise RuntimeError("Insufficient free disk space for download and extraction")
        with tempfile.TemporaryDirectory(prefix=".install-", dir=parent) as temp:
            temp = Path(temp); archive = temp / "download"; stage = temp / "package"; stage.mkdir()
            fetch(item, archive, progress)
            # Verify independently even when an alternate downloader is injected.
            h = hashlib.sha256()
            with archive.open("rb") as stream:
                while chunk := stream.read(1024 * 1024): h.update(chunk)
            if h.hexdigest() != item["sha256"] or archive.stat().st_size != item["size"]:
                raise ValueError("Artifact checksum mismatch")
            if item["format"] == "binary":
                binary = stage / item["executable"]; shutil.copyfile(archive, binary); binary.chmod(0o755)
            else:
                extract(archive, stage)
                matches = [p for p in stage.rglob(item["executable"]) if p.is_file() and os.access(p, os.X_OK)]
                if len(matches) != 1:
                    raise ValueError("Expected exactly one agent executable")
                binary = matches[0]
            receipt = {"version": item["version"], "sha256": item["sha256"],
                       "binary": str(binary.relative_to(stage)), "license": item["license"]}
            (stage / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
            destination = parent / (item["version"] + "-" + item["sha256"][:12])
            if destination.exists():
                raise ValueError("An incomplete or unselected version already exists; inspect it before retrying")
            stage.rename(destination)
            link = parent / ".current-new"
            if link.is_symlink(): link.unlink()
            link.symlink_to(destination.name, target_is_directory=True)
            link.replace(parent / "current")
        return installed(key)


def remove(key):
    entry(key)
    parent = data_root() / key
    if not parent.exists(): return
    with (parent / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Remove only version directories created by this manager; never CLI login
        # files, workspace files, or system-installed copies.
        for path in parent.iterdir():
            if path.name in ("current", ".current-new") and path.is_symlink(): path.unlink()
            elif path.is_dir() and not path.is_symlink() and (path / "receipt.json").is_file(): shutil.rmtree(path)


def version(key):
    state = installed(key)
    if not state: return None
    result = subprocess.run([state["path"], "--version"], capture_output=True, text=True, timeout=30, check=True)
    return result.stdout.strip()[:300]


def launch(key, directory=None):
    state = installed(key)
    if not state: raise RuntimeError("Install this agent first")
    terminal = shutil.which("xfce4-terminal")
    if not terminal: raise RuntimeError("No supported terminal available")
    args = [terminal]
    if directory: args += ["--working-directory", str(Path(directory).resolve())]
    # Every CLI retains its normal interactive authorization and sign-in flow.
    return subprocess.Popen(args + ["--execute", state["path"]], start_new_session=True)

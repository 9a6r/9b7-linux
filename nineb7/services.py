"""Allowlisted, on-demand lab stacks with isolated persistent state."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

CATALOG = {
    "n8n": {"title": "n8n", "port": 5678, "check": "/healthz", "ram_mb": 700},
    "superset": {"title": "Apache Superset", "port": 8088, "check": "/health", "ram_mb": 2200},
    "metabase": {"title": "Metabase", "port": 3000, "check": "/api/health", "ram_mb": 1800},
    "odoo": {"title": "Odoo", "port": 8069, "check": "/web/login", "ram_mb": 1600},
    "erpnext": {"title": "ERPNext", "port": 8080, "check": "/api/method/ping", "ram_mb": 3500},
    "ai": {"title": "Local AI · Ollama", "port": 11434, "check": "/api/tags", "ram_mb": 2000},
    "databases": {"title": "Database lab", "port": None, "check": None, "ram_mb": 3000},
}


def project_root() -> Path:
    if os.environ.get("NINEB7_ROOT"):
        return Path(os.environ["NINEB7_ROOT"])
    return Path(__file__).resolve().parent.parent


def runtime_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "9b7/services"


def prepare() -> Path:
    target = runtime_dir()
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    env_file = target / ".env"
    # O_EXCL avoids clobbering credentials on repeat startup or concurrent calls.
    try:
        fd = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return env_file
    with os.fdopen(fd, "w") as stream:
        for name in ("POSTGRES_PASSWORD", "N8N_ENCRYPTION_KEY", "SUPERSET_SECRET_KEY", "DB_ROOT_PASSWORD"):
            stream.write(f"{name}={secrets.token_hex(32)}\n")
        stream.write("LAB_ADMIN_USER=9b7\nLAB_ADMIN_PASSWORD=9b7\n")
    return env_file


def compose_command(stack: str, *arguments: str) -> list[str]:
    if stack not in CATALOG:
        raise ValueError("unknown stack: " + stack)
    env_file = prepare()
    config = project_root() / "services" / ("erpnext.compose.yml" if stack == "erpnext" else "compose.yml")
    return ["docker", "compose", "--env-file", str(env_file), "--project-name", "9b7-" + stack,
            "-f", str(config), "--profile", stack, *arguments]


def healthy(stack: str) -> bool:
    item = CATALOG[stack]
    if not item["port"]:
        return False  # Database health is checked with compose --wait, not an HTTP guess.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{item["port"]}{item["check"]}', timeout=3) as response:
            return 200 <= response.status < 400
    except (OSError, urllib.error.URLError):
        return False


def ensure_images(stack: str) -> None:
    """Load only the selected stack's verified offline archives, or pull online."""
    proc = subprocess.run(compose_command(stack, "config", "--images"), capture_output=True, text=True, check=True)
    manifest_file = project_root() / "offline/manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
    for name in dict.fromkeys(proc.stdout.splitlines()):
        if subprocess.run(["docker", "image", "inspect", name], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            continue
        entry = manifest.get(name)
        if entry:
            archive = manifest_file.parent / entry["file"]
            with archive.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != entry["sha256"]:
                raise ValueError("offline image checksum mismatch: " + name)
            subprocess.run(["docker", "load", "-i", str(archive)], check=True)
        else:
            subprocess.run(["docker", "pull", name], check=True)


def action(stack: str, operation: str, wait: bool = True) -> None:
    if operation not in {"start", "stop", "status", "logs"}:
        raise ValueError("unsupported service action")
    if operation == "start":
        ensure_images(stack)
        subprocess.run(compose_command(stack, "up", "-d", "--wait", "--wait-timeout", "600"), check=True)
        if wait and CATALOG[stack]["port"]:
            deadline = time.monotonic() + 180
            while not healthy(stack):
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"{stack} did not pass its functional HTTP readiness check; inspect logs")
                time.sleep(3)
    elif operation == "stop":
        subprocess.run(compose_command(stack, "down"), check=True)  # Named data volumes survive.
    elif operation == "status":
        subprocess.run(compose_command(stack, "ps", "-a"), check=True)
    else:
        subprocess.run(compose_command(stack, "logs", "--tail", "100"), check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "start", "stop", "status", "logs"])
    parser.add_argument("stack", nargs="?", choices=list(CATALOG))
    args = parser.parse_args(argv)
    if args.action == "list":
        print(json.dumps(CATALOG, indent=2))
        return 0
    if not args.stack:
        parser.error("a stack name is required")
    if not shutil.which("docker"):
        parser.exit(1, "Docker is not installed\n")
    try:
        action(args.stack, args.action)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"9b7 Services: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

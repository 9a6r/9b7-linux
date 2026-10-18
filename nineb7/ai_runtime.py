"""Local hardware, Ollama operations and explicitly selected usage snapshots."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import urllib.request

MODELS = {
    "qwen2.5:0.5b": {"download_mb": 400, "working_mb": 1500},
    "qwen2.5:1.5b": {"download_mb": 1000, "working_mb": 3000},
}


def hardware():
    mem = {line.split(":")[0]: int(line.split()[1]) // 1024 for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith(("MemTotal:", "MemAvailable:"))}
    vram = []
    for path in Path("/sys/class/drm").glob("card*/device/mem_info_vram_total"):
        try: vram.append(int(path.read_text()) // 1024**2)
        except (OSError, ValueError): pass
    return {"ram_mb": mem["MemTotal"], "available_mb": mem["MemAvailable"],
            "cpu_threads": os.cpu_count(), "vram_mb": max(vram) if vram else None,
            "free_disk_mb": shutil.disk_usage(Path.home()).free // 1024**2,
            "recommended": "qwen2.5:1.5b" if mem["MemTotal"] >= 7000 and mem["MemAvailable"] >= 3500 else "qwen2.5:0.5b"}


def ollama_request(path, data=None, method=None):
    # Local business/model requests never traverse the environment HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    payload = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request("http://127.0.0.1:11434/api/" + path, data=payload,
                                     method=method, headers={"Content-Type": "application/json"})
    return opener.open(request, timeout=600 if path == "pull" else 15)


def model_action(name, operation, progress=lambda *_: None):
    if name not in MODELS:
        raise ValueError("Choose a model from the reviewed small-model catalog")
    if operation == "pull":
        info = hardware(); spec = MODELS[name]
        if info["free_disk_mb"] < spec["download_mb"] * 2 + 500:
            raise RuntimeError("Insufficient disk space")
        with ollama_request("pull", {"model": name, "stream": True}) as response:
            complete = False
            for line in response:
                item = json.loads(line)
                if "error" in item: raise RuntimeError(item["error"])
                progress(item.get("completed", 0), item.get("total", 0))
                complete = item.get("status") == "success"
            if not complete:
                raise RuntimeError("Model download ended without success confirmation")
    elif operation == "delete":
        with ollama_request("delete", {"model": name}, "DELETE") as response: response.read()
    elif operation == "unload":
        with ollama_request("generate", {"model": name, "keep_alive": 0, "stream": False}) as response: response.read()
    else:
        raise ValueError("Unknown model operation")


def read_codex_usage(directory):
    """Opt-in, bounded local snapshots. Never opens auth files or returns prompts."""
    directory = Path(directory)
    if not directory.is_dir(): return []
    candidates = []
    visited = 0
    for root, dirs, names in os.walk(directory, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        if len(Path(root).relative_to(directory).parts) >= 6:
            dirs.clear()
        visited += len(names) + len(dirs)
        for name in names:
            path = Path(root) / name
            if name.endswith(".jsonl") and not path.is_symlink():
                try: candidates.append((path.stat().st_mtime, path))
                except OSError: continue
        if visited >= 20000:
            break
    files = [p for _, p in sorted(candidates, reverse=True)[:5]]
    snapshots = {}
    for path in files:
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 256 * 1024))
            for line in stream:
                try:
                    event = json.loads(line)
                    payload = event.get("payload", {})
                    limits = payload.get("rate_limits")
                    if event.get("type") != "event_msg" or payload.get("type") != "token_count" or not isinstance(limits, dict): continue
                    timestamp = event.get("timestamp", "")
                    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if parsed.tzinfo is None: continue
                    timestamp = parsed.astimezone(timezone.utc).isoformat()
                    key = limits.get("limit_id", "codex")
                    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", key): continue
                    filtered = {"limit_id": key, "timestamp": timestamp}
                    for window in ("primary", "secondary"):
                        value = limits.get(window)
                        if isinstance(value, dict) and isinstance(value.get("used_percent"), (int, float)) and 0 <= value["used_percent"] <= 100:
                            filtered[window] = {"used_percent": value["used_percent"]}
                            for field in ("window_minutes", "resets_at"):
                                number = value.get(field)
                                if type(number) is int and 0 <= number <= 10**12:
                                    filtered[window][field] = number
                    if len(filtered) > 2 and timestamp > snapshots.get(str(key), {}).get("timestamp", ""):
                        snapshots[str(key)] = filtered
                except (ValueError, TypeError, AttributeError): continue
    return list(snapshots.values())


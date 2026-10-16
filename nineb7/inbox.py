"""Idempotent watched-folder automation built on 9b7 Flow."""
from pathlib import Path
import json
import shutil
import uuid
from . import flow


def main():
    inbox = Path.home() / "9b7-Inbox"
    inbox.mkdir(exist_ok=True)
    for source in sorted(inbox.glob("*.csv")):
        job = uuid.uuid4().hex
        output = flow.state_dir() / "inbox-runs" / job
        try:
            result = flow.run(source, flow.state_dir() / "business.sqlite3", output)
            status = "review" if result["rejected"] else "processed"
        except (ValueError, OSError) as exc:
            status = "failed"
            flow.atomic_write(output / "error.json", json.dumps({"error": str(exc)}))
        destination = inbox / status
        destination.mkdir(exist_ok=True)
        shutil.move(str(source), str(destination / (job + "-" + source.name)))


if __name__ == "__main__":
    main()

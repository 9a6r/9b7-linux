from pathlib import Path
import os
import stat
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from nineb7 import services


class ServiceTests(unittest.TestCase):
    def test_credentials_persist_and_are_private(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_STATE_HOME": directory}):
            path = services.prepare()
            first = path.read_bytes()
            self.assertEqual(services.prepare().read_bytes(), first)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertIn(b"LAB_ADMIN_USER=9b7", first)

    def test_arbitrary_stack_names_cannot_execute_commands(self):
        with self.assertRaises(ValueError):
            services.compose_command("n8n;touch /tmp/injected", "up")

    def test_stop_preserves_volumes(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_STATE_HOME": directory}):
            with patch("subprocess.run") as run:
                services.action("erpnext", "stop")
                args = run.call_args.args[0]
                self.assertEqual(args[-1], "down")
                self.assertNotIn("--volumes", args)
                self.assertNotIn("-v", args)

    def test_tampered_offline_archive_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            offline = root / "offline"
            offline.mkdir()
            (offline / "image.tar").write_bytes(b"tampered archive")
            (offline / "manifest.json").write_text(json.dumps({"upstream@sha256:123": {
                "file": "image.tar", "local_tag": "9b7-offline/example:123", "sha256": "0" * 64,
                "image_id": "sha256:expected"}}))
            outputs = [subprocess.CompletedProcess([], 0, stdout="9b7-offline/example:123\n"),
                       subprocess.CompletedProcess([], 1, stdout="")]
            with patch.object(services, "project_root", return_value=root), patch.object(services, "compose_command", return_value=["docker", "compose"]):
                with patch("subprocess.run", side_effect=outputs) as run:
                    with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                        services.ensure_images("n8n")
                    self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import os
import stat
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


if __name__ == "__main__":
    unittest.main()

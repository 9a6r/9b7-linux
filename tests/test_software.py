import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from nineb7 import software, ai_runtime


class SoftwareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root)}); self.env.start()
        self.binary = b'#!/bin/sh\necho test-1\n'
        self.item = {"version": "1", "sha256": hashlib.sha256(self.binary).hexdigest(),
                     "size": len(self.binary), "format": "binary", "executable": "test-agent", "license": "MIT"}
        self.catalog = patch.object(software, 'catalog', return_value={"test": self.item}); self.catalog.start()

    def tearDown(self):
        self.catalog.stop(); self.env.stop(); self.temp.cleanup()

    def fetch(self, item, destination, progress): destination.write_bytes(self.binary)

    def test_install_version_remove_preserves_unmanaged_data(self):
        software.install("test", fetch=self.fetch)
        self.assertEqual(software.version("test"), "test-1")
        unrelated = software.data_root() / 'test/projects'; unrelated.mkdir()
        (unrelated / 'keep.txt').write_text('user work')
        software.install("test", fetch=lambda *_: self.fail('Redownloaded installed artifact'))
        software.remove("test")
        self.assertIsNone(software.installed("test"))
        self.assertEqual((unrelated / 'keep.txt').read_text(), 'user work')

    def test_failed_update_keeps_working_version(self):
        original = software.install("test", fetch=self.fetch)
        self.item.update(version='2', sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            software.install("test", fetch=self.fetch)
        self.assertEqual(software.installed("test")['path'], original['path'])
        self.assertEqual(software.version("test"), "test-1")

    def test_reject_corrupt_download_without_current_link(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            software.install("test", fetch=lambda item, dst, progress: dst.write_bytes(b'bad'))
        self.assertIsNone(software.installed("test"))
        with self.assertRaises(ValueError): software.install('../escape')

    def test_reject_archive_escape_and_link_before_any_extraction(self):
        for kind, name in ((tarfile.REGTYPE, '../escape'), (tarfile.SYMTYPE, 'link'), (tarfile.LNKTYPE, 'hardlink')):
            archive = self.root / 'test.tar.gz'; target = self.root / 'extract'; target.mkdir(exist_ok=True)
            with tarfile.open(archive, 'w:gz') as tar:
                good = tarfile.TarInfo('good'); good.size = 2; tar.addfile(good, io.BytesIO(b'ok'))
                bad = tarfile.TarInfo(name); bad.type = kind; bad.linkname = '/tmp/escape'; tar.addfile(bad)
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                software.extract(archive, target)
            self.assertEqual(list(target.iterdir()), [])
        self.assertFalse((self.root / 'escape').exists())


class LocalAITests(unittest.TestCase):
    def test_usage_only_explicit_quota_fields_and_latest_utc(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = [
                {"type":"event_msg", "timestamp":"2026-10-18T10:00:00+03:00", "payload": {"type":"token_count", "rate_limits": {"primary":{"used_percent":5, "resets_at":"secret", "window_minutes":300}}, "prompt":"SECRET_PROMPT"}},
                {"type":"event_msg", "timestamp":"2026-10-18T08:00:00Z", "payload": {"type":"token_count", "rate_limits": {"primary":{"used_percent":25, "resets_at":123456, "window_minutes":300, "credential":"SECRET_TOKEN"}}}},
                {"type":"response_item", "timestamp":"2027-10-18T08:00:00Z", "payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":99}}}},
            ]
            (root / 'session.jsonl').write_text('\n'.join(json.dumps(x) for x in events))
            (root / 'auth.json').write_text('SECRET_AUTH')
            (root / 'linked.jsonl').symlink_to(root / 'auth.json')
            rows = ai_runtime.read_codex_usage(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['primary']['used_percent'], 25)
            self.assertEqual(rows[0]['timestamp'], '2026-10-18T08:00:00+00:00')
            self.assertNotIn('SECRET', json.dumps(rows))
            (root / 'session.jsonl').write_text('{broken')
            self.assertEqual(ai_runtime.read_codex_usage(root), [])

    def test_model_pull_requires_explicit_success_and_known_model(self):
        with patch.object(ai_runtime, 'hardware', return_value={'free_disk_mb':10000}):
            with patch.object(ai_runtime, 'ollama_request', return_value=io.BytesIO(b'{"status":"downloading"}\n')):
                with self.assertRaisesRegex(RuntimeError, 'without success'): ai_runtime.model_action('qwen2.5:0.5b', 'pull')
            with patch.object(ai_runtime, 'ollama_request', return_value=io.BytesIO(b'{"status":"success"}\n')):
                ai_runtime.model_action('qwen2.5:0.5b', 'pull')
            with patch.object(ai_runtime, 'ollama_request') as request:
                with self.assertRaises(ValueError): ai_runtime.model_action('unreviewed:70b', 'pull')
                request.assert_not_called()


if __name__ == '__main__': unittest.main()

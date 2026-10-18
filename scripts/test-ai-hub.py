#!/usr/bin/env python3
"""Real Qt worker delivery, verified test install/removal and local usage display."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from nineb7.ai_hub import AIHub
from nineb7.software_center import SoftwareCenter
from nineb7 import software

with tempfile.TemporaryDirectory() as temp:
    os.environ['XDG_DATA_HOME'] = temp
    os.environ['XDG_CACHE_HOME'] = temp
    app = QApplication([])
    hub = AIHub(); hub.show(); app.processEvents()
    assert hub.default.currentText() == 'claude'
    assert all('Not installed' in label.text() for label in hub.agent_labels.values())
    hub.default.setCurrentText('codex'); hub.save_default()
    assert json.loads((software.data_root() / 'preferences.json').read_text())['default'] == 'codex'
    def wait():
        deadline = time.monotonic() + 15
        while hub.jobs and time.monotonic() < deadline:
            app.processEvents(); time.sleep(.01)
        assert not hub.jobs, 'Task did not finish'
        app.processEvents()
    binary = b'#!/bin/sh\necho verified-test-agent\n'
    item = {'version':'test-1', 'sha256':hashlib.sha256(binary).hexdigest(), 'size':len(binary),
            'format':'binary', 'executable':'agent', 'license':'MIT'}
    original = software.catalog()
    with patch.object(software, 'catalog', return_value={**original, 'claude':item}):
        hub.run_task(lambda: software.install('claude', hub.progress_signal.changed.emit,
            fetch=lambda entry, dest, progress: (dest.write_bytes(binary), progress(len(binary), len(binary)))), 'Testing install')
        wait()
        assert 'Installed' in hub.agent_labels['claude'].text()
        assert software.version('claude') == 'verified-test-agent'
        hub.run_task(lambda: software.remove('claude'), 'Testing removal'); wait()
        assert 'Not installed' in hub.agent_labels['claude'].text()
    logs = Path(temp) / 'sessions'; logs.mkdir()
    (logs / 'example.jsonl').write_text(json.dumps({'type':'event_msg','timestamp':'2026-10-18T12:00:00Z',
        'payload':{'type':'token_count','rate_limits':{'primary':{'used_percent':17.5,'window_minutes':300}}}}))
    with patch.object(QFileDialog, 'getExistingDirectory', return_value=str(logs)):
        hub.choose_usage(); wait()
    assert '17.5' in hub.usage.toPlainText()
    assert '2026-10-18' in hub.usage.toPlainText()
    assert hub.grab().save(str(Path(os.environ.get('NINEB7_AI_SCREENSHOT', '/tmp/9b7-ai-hub.png'))))
    center = SoftwareCenter(); center.show(); app.processEvents()
    assert 'ollama' in center.states
    center.close(); hub.close()
    print('PASS: blank catalog/default persistence, real verified installation/removal through Qt worker, local usage display, Software Center startup')

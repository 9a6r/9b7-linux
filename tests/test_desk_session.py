"""Exercise the real session wrapper with controlled compositor outcomes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WRAPPER = Path(__file__).resolve().parents[1] / 'iso/virtualbox/airootfs/usr/local/bin/9b7-desk-session'


class SessionFallbackTests(unittest.TestCase):
    def run_session(self, mode):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'desk-session'
            child.write_text('''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
root = Path(os.environ['TEST_ROOT'])
with (root / 'calls').open('a') as stream:
    stream.write(json.dumps({k:os.environ.get(k) for k in ('WLR_RENDERER', 'DESK_NO_GPU', 'DESK_LIBRARY_WORKSPACE')}) + '\\n')
software = os.environ.get('WLR_RENDERER') == 'pixman'
mode = os.environ['TEST_MODE']
if software:
    print('the first frame (0.01 s)', flush=True)
    sys.exit(0)
if mode == 'early-failure': sys.exit(1)
if mode == 'hang': time.sleep(60)
if mode != 'cancel':
    print('the first frame (0.01 s)', flush=True)
    time.sleep(.25)
sys.exit(7 if mode == 'late-failure' else 0)
''')
            child.chmod(0o755)
            # Speed up the wrapper's polling only; child process timing stays real.
            sleep = root / 'sleep'
            sleep.write_text('#!/bin/sh\nexec /bin/sleep .02\n')
            sleep.chmod(0o755)
            env = dict(os.environ, PATH=f'{root}:/usr/bin:/bin',
                       XDG_STATE_HOME=str(root / 'state'), TEST_ROOT=directory, TEST_MODE=mode)
            for key in ('WLR_RENDERER', 'DESK_NO_GPU', 'DESK_ON_CPU'):
                env.pop(key, None)
            result = subprocess.run(['bash', str(WRAPPER)], env=env, capture_output=True, text=True, timeout=5)
            calls = [json.loads(line) for line in (root / 'calls').read_text().splitlines()]
            archived = (root / 'state/desk/renderer-startup-failed.log').exists()
            return result.returncode, calls, archived

    def test_accelerated_session_not_forced_to_software(self):
        status, calls, archived = self.run_session('normal')
        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 1)
        self.assertIsNone(calls[0]['WLR_RENDERER'])
        self.assertEqual(calls[0]['DESK_LIBRARY_WORKSPACE'], '1')
        self.assertFalse(archived)

    def test_failed_renderer_retries_same_session_once(self):
        for mode in ('early-failure', 'hang'):
            with self.subTest(mode=mode):
                status, calls, archived = self.run_session(mode)
                self.assertEqual(status, 0)
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[1]['WLR_RENDERER'], 'pixman')
                self.assertEqual(calls[1]['DESK_NO_GPU'], '1')
                self.assertTrue(archived)

    def test_failure_after_first_frame_does_not_restart_user_session(self):
        status, calls, archived = self.run_session('late-failure')
        self.assertEqual(status, 7)
        self.assertEqual(len(calls), 1)
        self.assertFalse(archived)

    def test_clean_exit_without_a_frame_does_not_force_login_again(self):
        status, calls, archived = self.run_session('cancel')
        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 1)
        self.assertFalse(archived)

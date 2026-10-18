#!/usr/bin/env python3
"""Boot the actual ISO, log in through SDDM, and exercise its desktop apps.

This is a live-session smoke test, not installed-system or VirtualBox certification.
Requires QEMU, sshpass and (for UEFI) OVMF. Never attaches a host block device.
"""
import argparse
import glob
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


class Monitor:
    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.settimeout(30)
        self.socket.connect(str(path))
        self.stream = self.socket.makefile('rwb', buffering=0)
        self.stream.readline()
        self.call('qmp_capabilities')

    def call(self, name, arguments=None):
        request = {'execute': name}
        if arguments is not None: request['arguments'] = arguments
        self.stream.write((json.dumps(request) + '\n').encode())
        while True:
            reply = json.loads(self.stream.readline())
            if 'return' in reply: return reply['return']
            if 'error' in reply: raise RuntimeError(reply['error'])

    def key(self, name):
        self.call('human-monitor-command', {'command-line': 'sendkey ' + name + ' 80'})

    def text(self, value):
        keys = {' ': 'spc', '\n': 'ret', '-': 'minus', '/': 'slash', '.': 'dot', '|': 'shift-backslash'}
        for char in value:
            self.key(keys.get(char, 'shift-' + char.lower() if char.isupper() else char))
            time.sleep(.12)

    def screen(self, path):
        self.call('screendump', {'filename': str(path), 'format': 'png'})

    def close(self):
        self.stream.close(); self.socket.close()


def exercise_session(monitor, guest, output, kvm, mode, acceleration):
    monitor.screen(output / 'sddm.png')
    print('Trying the Live TTY to enable test-only SSH', flush=True)
    # Enable SSH on this disposable Live guest via its real login TTY.
    # SDDM can use VT1 or VT2. Use the reserved getty VT6, then
    # discover the greeter's actual VT instead of guessing it.
    monitor.key('ctrl-alt-f6'); time.sleep(10)
    monitor.text('9b7\n'); time.sleep(8)
    monitor.text('9b7\n'); time.sleep(10)
    monitor.text('echo 9b7 | sudo -S systemctl start sshd\n')
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            result = guest('systemctl is-active sddm\n')
            if result.returncode == 0 and 'active' in result.stdout: break
        except subprocess.TimeoutExpired: pass
        time.sleep(5)
    else: raise RuntimeError('Could not reach the Live guest and active SDDM')
    result = guest('cat /etc/sddm.conf.d/9b7.conf 2>/dev/null; grep -R "^Current=" /etc/sddm.conf.d; uname -r\n')
    (output / 'system.txt').write_text(result.stdout + result.stderr)
    if 'Slot-SDDM-6' not in result.stdout: raise RuntimeError('Original SDDM theme is not selected')
    print('SDDM active; trying password login into DEsk', flush=True)
    result = guest('''for session in $(loginctl list-sessions --no-legend | awk '{print $1}'); do
    if [ "$(loginctl show-session "$session" -p Class --value)" = greeter ]; then
        loginctl show-session "$session" -p VTNr --value
    fi
done
''')
    terminals = result.stdout.split()
    if result.returncode or len(terminals) != 1 or terminals[0] not in ('1','2','3','4','5'):
        raise RuntimeError('Cannot identify the SDDM greeter VT: ' + result.stdout + result.stderr)
    monitor.key('ctrl-alt-f' + terminals[0]); time.sleep(5)
    monitor.screen(output / 'sddm.png')
    monitor.key('ctrl-a')  # The supplied theme focuses its password field.
    monitor.text('9b7\n')
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        result = guest('pgrep -u 1000 -x desk\n')
        if result.returncode == 0: break
        time.sleep(5)
    else: raise RuntimeError('Password login did not start DEsk')
    print('DEsk started; launching desktop applications', flush=True)
    result = guest('''set -e
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_CURRENT_DESKTOP=DEsk
# DEsk publishes its display to the user service manager after startup.
# Its PID alone does not mean that a display socket is ready yet.
for attempt in $(seq 1 60); do
    session_env=$(systemctl --user show-environment)
    for key in WAYLAND_DISPLAY DISPLAY XAUTHORITY; do
        value=$(printf '%s\\n' "$session_env" | sed -n "s/^$key=//p")
        if [ -n "$value" ]; then export "$key=$value"; fi
    done
    if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then break; fi
    sleep 2
done
test -n "${WAYLAND_DISPLAY:-}" && test -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
export XDG_STATE_HOME=/tmp/9b7-smoke-state
nohup 9b7-studio >/tmp/9b7-studio-smoke.log 2>&1 </dev/null &
nohup thunar >/tmp/9b7-thunar-smoke.log 2>&1 </dev/null &
printf '<!doctype html><meta charset="UTF-8"><h1>9b7 / العربية</h1>' > /tmp/9b7-browser-test.html
nohup firefox --new-window file:///tmp/9b7-browser-test.html >/tmp/9b7-firefox-smoke.log 2>&1 </dev/null &
''', timeout=150)
    if result.returncode: raise RuntimeError(result.stderr)
    time.sleep(45 if kvm else 90)
    result = guest('''set -e
pgrep -u 1000 -f 'python -m nineb7.studio'
pgrep -u 1000 -x Thunar || pgrep -u 1000 -x thunar
pgrep -u 1000 -x firefox
cat /tmp/9b7-studio-smoke.log
tail -60 ~/.local/state/desk/session.log
grep -F 'a window comes onto the desk:' ~/.local/state/desk/session.log | tail -20
''')
    (output / 'desktop.txt').write_text(result.stdout + result.stderr)
    if result.returncode or 'Traceback (most recent call last)' in result.stdout:
        raise RuntimeError('Desktop application startup failed; inspect evidence')
    windows = [line for line in result.stdout.splitlines() if 'a window comes onto the desk:' in line]
    for app_id in ('9b7-studio', 'thunar', 'firefox'):
        if not any(f'({app_id})' in line for line in windows):
            raise RuntimeError('DEsk did not report a window for ' + app_id)
    monitor.screen(output / 'desktop.png')
    evidence = {'mode':mode, 'acceleration':acceleration, 'memory_mib':4096,
                'sddm_password_login':True, 'desk_session':True,
                'application_processes':['Firefox','Thunar','9b7 Studio'],
                'application_windows_reported_by_compositor':True,
                'screenshots':'captured; review visually',
                'not_tested':['VirtualBox','hardware','installation','audio output','cloud AI authentication']}
    (output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', required=True, type=Path)
    parser.add_argument('--mode', choices=['bios', 'uefi'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=2235)
    args = parser.parse_args()
    iso = args.iso.resolve(); output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    if not iso.is_file(): raise RuntimeError('ISO does not exist: ' + str(iso))
    # Reusing a result directory could misrepresent evidence from an older ISO.
    if any(output.iterdir()): raise RuntimeError('Use a new, empty output directory')
    for program in ('qemu-system-x86_64', 'sshpass', 'ssh'):
        if not shutil.which(program): raise RuntimeError('Missing prerequisite: ' + program)
    kvm = os.access('/dev/kvm', os.R_OK | os.W_OK)
    acceleration = 'kvm' if kvm else 'tcg,thread=multi'
    with tempfile.TemporaryDirectory(prefix='9b7-qemu-') as temp:
        temp = Path(temp); qmp = temp / 'qmp.sock'
        command = ['qemu-system-x86_64', '-machine', 'q35', '-accel', acceleration,
                   '-cpu', 'host' if kvm else 'max', '-smp', '2', '-m', '4096', '-vga', 'std',
                   '-display', 'none', '-device', 'qemu-xhci', '-device', 'usb-tablet',
                   '-netdev', f'user,id=n,hostfwd=tcp:127.0.0.1:{args.port}-:22',
                   '-device', 'virtio-net-pci,netdev=n', '-cdrom', str(iso), '-boot', 'd',
                   '-qmp', f'unix:{qmp},server=on,wait=off', '-serial', f'file:{output / "serial.log"}']
        if args.mode == 'uefi':
            codes = glob.glob('/usr/share/OVMF/OVMF_CODE_4M.fd') + glob.glob('/usr/share/edk2/x64/OVMF_CODE.4m.fd')
            variables = glob.glob('/usr/share/OVMF/OVMF_VARS_4M.fd') + glob.glob('/usr/share/edk2/x64/OVMF_VARS.4m.fd')
            if not codes or not variables: raise RuntimeError('OVMF firmware unavailable')
            shutil.copyfile(variables[0], temp / 'vars.fd')
            command += ['-drive', f'if=pflash,format=raw,readonly=on,file={codes[0]}',
                        '-drive', f'if=pflash,format=raw,file={temp / "vars.fd"}']
        env = dict(os.environ, SSHPASS='9b7')  # Public Live test credentials only.
        ssh = ['sshpass', '-e', 'ssh', '-p', str(args.port), '-o', 'StrictHostKeyChecking=no',
               '-o', f'UserKnownHostsFile={temp / "known-hosts"}', '-o', 'ConnectTimeout=5', '9b7@127.0.0.1']
        def guest(script, timeout=30):
            return subprocess.run(ssh + ['bash', '-s'], input=script, text=True,
                                  capture_output=True, timeout=timeout, env=env)
        monitor = None
        with (output / 'qemu.log').open('w') as log:
            vm = subprocess.Popen(command, stdout=log, stderr=log)
            try:
                print(f'Booting {args.mode}, {acceleration}, 4096 MiB: {iso.name}', flush=True)
                deadline = time.monotonic() + 30
                while not qmp.exists() and time.monotonic() < deadline:
                    if vm.poll() is not None: raise RuntimeError('QEMU exited before boot')
                    time.sleep(.5)
                monitor = Monitor(qmp)
                # Keep real boot frames, including Plymouth; no replacement artwork.
                boot_seconds = 90 if kvm else 300
                for frame in range(boot_seconds // 5):
                    monitor.screen(output / f'boot-{frame:03}.png')
                    time.sleep(5)
                exercise_session(monitor, guest, output, kvm, args.mode, acceleration)
            except Exception as error:
                (output / 'failure.json').write_text(json.dumps({'mode':args.mode, 'error':str(error)}, indent=2) + '\n')
                if monitor:
                    try: monitor.screen(output / 'failure.png')
                    except (OSError, ValueError, RuntimeError): pass
                try:
                    result = guest('journalctl -b -u sddm --no-pager -n 100; tail -80 ~/.local/state/desk/session.log\n')
                    (output / 'failure-journal.txt').write_text(result.stdout + result.stderr)
                except subprocess.TimeoutExpired: pass
                raise
            finally:
                if monitor: monitor.close()
                vm.terminate()
                try: vm.wait(timeout=15)
                except subprocess.TimeoutExpired: vm.kill(); vm.wait()


if __name__ == '__main__': main()

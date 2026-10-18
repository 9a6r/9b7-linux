"""Explicit whole-disk installation backend. Never selects a target automatically."""
from __future__ import annotations
from dataclasses import dataclass, field
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

SESSIONS = {
    'desk': '/usr/share/wayland-sessions/9b7-desk.desktop',
    'desk-2d': '/usr/share/wayland-sessions/9b7-desk-2d.desktop',
    'hyprland': '/usr/share/wayland-sessions/9b7-hyprland.desktop',
    'xfce': '/usr/share/xsessions/xfce.desktop',
}
LANGUAGES = {'en_US.UTF-8', 'ar_EG.UTF-8'}
KEYBOARDS = {'us', 'ara', 'us,ara'}


@dataclass
class InstallConfig:
    disk: str
    username: str
    password: str = field(repr=False)
    hostname: str = '9b7-pc'
    timezone: str = 'Africa/Cairo'
    language: str = 'en_US.UTF-8'
    keyboard: str = 'us,ara'
    session: str = 'desk'
    confirmation: str = ''

    def validate(self, require_confirmation=True):
        if not re.fullmatch(r'/dev/[A-Za-z0-9_-]+', self.disk): raise ValueError('Select a whole disk under /dev')
        if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', self.username) or self.username in {'root', 'nobody', 'sddm', 'lightdm'}:
            raise ValueError('Use a new Linux username starting with a lowercase letter')
        if len(self.password) < 8 or len(self.password) > 512 or self.password == '9b7' or any(ord(c) < 32 for c in self.password):
            raise ValueError('Choose a new password of at least 8 characters without control characters')
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', self.hostname): raise ValueError('Invalid computer name')
        if not re.fullmatch(r'[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+){0,3}', self.timezone) or not (Path('/usr/share/zoneinfo') / self.timezone).is_file():
            raise ValueError('Choose an installed timezone')
        if self.language not in LANGUAGES or self.keyboard not in KEYBOARDS or self.session not in SESSIONS:
            raise ValueError('Unsupported language, keyboard or session')
        if require_confirmation and self.confirmation != 'ERASE ' + self.disk:
            raise ValueError('The exact disk erase confirmation is required')
        return self


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def disks():
    info = json.loads(subprocess.check_output(['lsblk', '--json', '--bytes', '--paths', '-o', 'NAME,TYPE,SIZE,MODEL,TRAN,RO,MOUNTPOINTS'], text=True))
    def mounted(node):
        return any(node.get('mountpoints') or []) or any(mounted(c) for c in node.get('children', []))
    return [{**node, 'mounted': mounted(node)} for node in info['blockdevices'] if node['type'] == 'disk']


def validate_target(disk, source=Path('/run/archiso/airootfs')):
    if os.geteuid() != 0: raise ValueError('Administrator authentication is required')
    if not source.is_dir() or not Path('/run/archiso/bootmnt').is_dir(): raise ValueError('Run only inside the 9b7 Live ISO')
    path = Path(disk)
    if path.resolve() != path or not stat.S_ISBLK(path.stat().st_mode): raise ValueError('Choose a real whole block disk')
    candidates = {d['name']: d for d in disks()}
    item = candidates.get(disk)
    if not item or item['ro'] or item['mounted']: raise ValueError('Disk is missing, read-only, or contains a mounted filesystem')
    live_source = subprocess.check_output(['findmnt', '-nro', 'SOURCE', '/run/archiso/bootmnt'], text=True).strip()
    if live_source.startswith('/dev/'):
        ancestors = subprocess.check_output(['lsblk', '-snrpo', 'NAME', live_source], text=True).splitlines()
        if disk in ancestors: raise ValueError('The live USB/ISO disk cannot be the installation target')
    used = int(subprocess.check_output(['du', '-sx', '--apparent-size', '--block-size=1', str(source)], text=True).split()[0])
    if int(item['size']) < used + 20 * 1024**3: raise ValueError('Disk needs installed image size plus at least 20 GiB')
    return item


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)


def install(config):
    config.validate(); validate_target(config.disk)
    disk = config.disk; source = Path('/run/archiso/airootfs')
    if any(line.split(':')[0] == config.username for line in (source / 'etc/passwd').read_text().splitlines()):
        raise ValueError('Username already exists in the source system')
    target = Path(tempfile.mkdtemp(prefix='9b7-install.', dir='/mnt'))
    def chroot(*args, **kwargs): return run(['arch-chroot', str(target), *args], **kwargs)
    def phase(text): print(text, flush=True)
    try:
        # Repeat protection immediately before the first destructive operation.
        validate_target(disk)
        phase('1/7 Creating the explicitly confirmed partitions')
        run(['wipefs', '--all', disk])
        run(['parted', '--script', disk, 'mklabel', 'gpt', 'mkpart', 'BIOS', '1MiB', '3MiB', 'set', '1', 'bios_grub', 'on',
             'mkpart', 'EFI', 'fat32', '3MiB', '1027MiB', 'set', '2', 'esp', 'on', 'mkpart', 'ROOT', 'ext4', '1027MiB', '100%'])
        run(['partprobe', disk]); run(['udevadm', 'settle'])
        prefix = disk + ('p' if disk[-1].isdigit() else '')
        efi, root = prefix + '2', prefix + '3'
        run(['mkfs.fat', '-F32', '-n', '9B7_EFI', efi]); run(['mkfs.ext4', '-F', '-L', '9B7_ROOT', root])
        run(['mount', root, str(target)]); (target / 'boot/efi').mkdir(parents=True)
        run(['mount', efi, str(target / 'boot/efi')])
        phase('2/7 Copying the live system — this can take several minutes')
        run(['rsync', '-aHAX', '--numeric-ids', '--info=progress2', str(source) + '/', str(target) + '/'])
        shutil.copy2('/run/archiso/bootmnt/arch/boot/x86_64/vmlinuz-linux', target / 'boot/vmlinuz-linux')
        for name in ('etc/mkinitcpio.conf.d/archiso.conf', 'etc/initcpio/hooks/archiso',
                     'usr/share/applications/9b7-install.desktop'):
            (target / name).unlink(missing_ok=True)
        for service in ('pacman-init', 'choose-mirror', 'reflector', '9b7-firstboot'):
            (target / f'etc/systemd/system/multi-user.target.wants/{service}.service').unlink(missing_ok=True)
        write(target / 'etc/mkinitcpio.conf.d/9b7.conf', 'HOOKS=(base udev plymouth autodetect microcode modconf kms keyboard keymap consolefont block filesystems fsck)\n')
        write(target / 'etc/mkinitcpio.d/linux.preset', '''ALL_kver="/boot/vmlinuz-linux"
PRESETS=('default' 'fallback')
default_image="/boot/initramfs-linux.img"
fallback_image="/boot/initramfs-linux-fallback.img"
fallback_options="-S autodetect"
''')
        write(target / 'etc/default/grub', '''GRUB_DEFAULT=0
GRUB_TIMEOUT=8
GRUB_TIMEOUT_STYLE=menu
GRUB_DISTRIBUTOR="9b7"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
GRUB_PRELOAD_MODULES="part_gpt part_msdos"
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUB_GFXMODE=auto
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_DISABLE_OS_PROBER=true
''')
        phase('3/7 Creating your permanent account and regional settings')
        # The pristine squashfs normally has no live account. Refuse collisions
        # rather than adopting an existing privileged/system account.
        accounts = (target / 'etc/passwd').read_text().splitlines()
        if any(line.split(':')[0] == config.username for line in accounts):
            raise ValueError('Username already exists in the source system')
        # If a future profile pre-creates the demo user, lock and remove it only
        # from this fresh target; never copy Live-session business data.
        if any(line.startswith('9b7:') for line in accounts): chroot('userdel', '-r', '9b7')
        chroot('useradd', '-m', '-U', '-s', '/bin/bash', config.username)
        chroot('chpasswd', input=f'{config.username}:{config.password}\n', text=True)
        groups = {line.split(':')[0] for line in (target / 'etc/group').read_text().splitlines()}
        selected = [g for g in ('wheel', 'audio', 'video', 'storage', 'input', 'docker', 'wireshark') if g in groups]
        chroot('usermod', '-aG', ','.join(selected), config.username); chroot('passwd', '-l', 'root')
        write(target / 'etc/hostname', config.hostname + '\n')
        write(target / 'etc/hosts', f'127.0.0.1 localhost\n::1 localhost\n127.0.1.1 {config.hostname}.localdomain {config.hostname}\n')
        write(target / 'etc/locale.conf', 'LANG=' + config.language + '\n')
        localtime = target / 'etc/localtime'; localtime.unlink(missing_ok=True)
        localtime.symlink_to('/usr/share/zoneinfo/' + config.timezone)
        write(target / 'etc/vconsole.conf', 'KEYMAP=us\n')
        options = 'grp:alt_shift_toggle' if ',' in config.keyboard else ''
        write(target / 'etc/X11/xorg.conf.d/00-keyboard.conf', f'Section "InputClass"\n Identifier "9b7 keyboard"\n MatchIsKeyboard "on"\n Option "XkbLayout" "{config.keyboard}"\n Option "XkbOptions" "{options}"\nEndSection\n')
        user_home = target / 'home' / config.username
        desk = user_home / '.config/desk/shell.conf'
        layouts = config.keyboard.split(',')
        write(desk, f'keyboard_layout = {layouts[0]}\nkeyboard_second = {layouts[1] if len(layouts)>1 else "none"}\nkeyboard_switch = alt_shift\n')
        hypr = user_home / '.config/hypr/hyprland.conf'
        if hypr.exists(): hypr.write_text(re.sub(r'kb_layout\s*=.*', 'kb_layout = ' + config.keyboard, hypr.read_text()))
        chroot('chown', '-R', f'{config.username}:{config.username}', f'/home/{config.username}')
        write(target / 'var/lib/sddm/state.conf', f'[Last]\nUser={config.username}\nSession={SESSIONS[config.session]}\n')
        chroot('chown', '-R', 'sddm:sddm', '/var/lib/sddm')
        lightdm_session = Path(SESSIONS[config.session]).stem
        write(target / 'etc/lightdm/lightdm.conf.d/90-9b7-compat.conf', f'[Seat:*]\nuser-session={lightdm_session}\n')
        write(target / 'var/lib/9b7/provisioned', '')
        write(target / 'etc/9b7-installed', 'Installed with a user-selected identity; no default live administrator.\n')
        write(target / 'etc/machine-id', '')
        phase('4/7 Generating locale, package trust and machine identity')
        chroot('locale-gen'); chroot('pacman-key', '--init'); chroot('pacman-key', '--populate', 'archlinux')
        chroot('systemd-machine-id-setup')
        phase('5/7 Generating normal installed-system initramfs and boot menu')
        with (target / 'etc/fstab').open('w') as fstab: run(['genfstab', '-U', str(target)], stdout=fstab)
        chroot('mkinitcpio', '-P')
        chroot('grub-install', '--target=x86_64-efi', '--efi-directory=/boot/efi', '--bootloader-id=9b7', '--removable', '--no-nvram')
        chroot('grub-install', '--target=i386-pc', disk)
        chroot('grub-mkconfig', '-o', '/boot/grub/grub.cfg')
        phase('6/7 Creating 8 GiB swap')
        chroot('fallocate', '-l', '8G', '/swapfile'); (target / 'swapfile').chmod(0o600); chroot('mkswap', '/swapfile')
        with (target / 'etc/fstab').open('a') as fstab: fstab.write('/swapfile none swap defaults 0 0\n')
        phase('7/7 Flushing disk writes'); run(['sync'])
    finally:
        if os.path.ismount(target): run(['umount', '-R', str(target)])
        target.rmdir()
    print('INSTALLATION_COMPLETE: Shut down, remove ISO/USB, then boot the installed disk.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config-stdin', action='store_true')
    parser.add_argument('--disk'); parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.dry_run:
            if not args.disk: raise ValueError('--disk is required for dry run')
            print(json.dumps(validate_target(args.disk), indent=2)); print('No writes performed. Whole-disk GPT + BIOS/EFI/ext4 + swap; no dual boot.'); return 0
        if args.config_stdin:
            if os.geteuid() != 0: raise ValueError('Administrator authentication is required')
            print('9B7_READY_FOR_CONFIGURATION', flush=True)
            line = sys.stdin.buffer.readline(65537)
            if len(line) > 65536: raise ValueError('Configuration is too large')
            config = InstallConfig(**json.loads(line))
        else:
            if not sys.stdin.isatty(): raise ValueError('Interactive confirmation is required')
            disk = args.disk or input('Whole disk to erase: ')
            config = InstallConfig(disk=disk, username=input('New permanent username: '), password=getpass.getpass('New password (at least 8 characters): '),
                hostname=input('Computer name [9b7-pc]: ') or '9b7-pc', timezone=input('Timezone [Africa/Cairo]: ') or 'Africa/Cairo',
                language=input('Locale [en_US.UTF-8]: ') or 'en_US.UTF-8', keyboard=input('Keyboard [us,ara]: ') or 'us,ara',
                session=input('Session desk/desk-2d/hyprland/xfce [desk]: ') or 'desk')
            config.validate(require_confirmation=False); validate_target(disk)
            config.confirmation = input(f'ALL data will be erased. Type ERASE {disk}: ')
        install(config); return 0
    except Exception as exc:
        print(f'Installation failed: {exc}', file=sys.stderr, flush=True); return 1


if __name__ == '__main__': raise SystemExit(main())

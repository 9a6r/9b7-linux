#!/usr/bin/env bash
# Creates a disposable profile; never edits the system releng profile.
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
profile=${1:?Usage: prepare-profile.sh NEW_PROFILE_DIRECTORY [desktop|full]}
edition=${2:-full}
[[ $edition == full || $edition == desktop ]] || { echo 'Unknown edition' >&2; exit 2; }
[[ ! -e $profile ]] || { echo "Profile already exists: $profile (use a new directory)" >&2; exit 2; }
releng=${ARCHISO_RELENG:-/usr/share/archiso/configs/releng}
[[ -d $releng ]] || { echo 'Install archiso on an Arch builder first' >&2; exit 1; }
mkdir -p "$profile"
cp -a "$releng/." "$profile/"
cp -a "$project/iso/airootfs/." "$profile/airootfs/"
root="$profile/airootfs"
# Replace only conflicting packages inherited from releng.
sed -i '/^virtualbox-guest-utils-nox$/d; /^iptables$/d; /^ntfsprogs$/d' "$profile/packages.x86_64"
cat "$project/iso/packages.x86_64" >> "$profile/packages.x86_64"
sort -u -o "$profile/packages.x86_64" "$profile/packages.x86_64"
sed -i '/^iso_name=/c\iso_name="9b7-linux"' "$profile/profiledef.sh"
sed -i '/^iso_publisher=/c\iso_publisher="9b7 BIS Project <https://github.com/9a6r/9b7-linux>"' "$profile/profiledef.sh"
sed -i '/^iso_application=/c\iso_application="9b7 BIS Live Desktop"' "$profile/profiledef.sh"
cat >> "$profile/profiledef.sh" <<'PROFILE'
iso_label="9B7_$(date -u +%Y%m%d)"
iso_version="$(date -u +%Y.%m.%d)"
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15' '-b' '1M' '-processors' '2' '-mem' '512M')
file_permissions["/etc/shadow"]="0:0:400"
file_permissions["/etc/sudoers.d/90-9b7"]="0:0:440"
unset 'file_permissions[/root/.automated_script.sh]'
PROFILE
# Desktop is the rapid test track; zstd 6 keeps rebuilds practical in CPU-only
# cloud builders. Full retains the smaller level-15 archive.
if [[ $edition == desktop ]]; then
    sed -i "s/'15'/'6'/" "$profile/profiledef.sh"
fi
for script in "$root"/usr/local/bin/9b7-*; do
    chmod 755 "$script"
    printf 'file_permissions["%s"]="0:0:755"\n' "${script#"$root"}" >> "$profile/profiledef.sh"
done
# Releng is a root installer environment: remove its automatic root login and network services.
find "$root/etc/systemd/system" -type l \( -name 'sshd.service' -o -name 'iwd.service' -o -name 'systemd-networkd.service' -o -name 'systemd-networkd.socket' -o -name 'systemd-resolved.service' -o -name 'systemd-networkd-wait-online.service' -o -name 'systemd-time-wait-sync.service' -o -name 'dbus-org.freedesktop.resolve1.service' -o -name 'dbus-org.freedesktop.network1.service' \) -delete
rm -rf "$root/etc/systemd/system/cloud-init.target.wants"
mkdir -p "$root/etc/cloud"
touch "$root/etc/cloud/cloud-init.disabled"
rm -rf "$root/etc/systemd/system/getty@tty1.service.d" "$root/etc/systemd/system/serial-getty@.service.d" "$root/etc/systemd/system/getty@.service.d"
rm -f "$root/root/.automated_script.sh" "$root/etc/systemd/system/multi-user.target.wants/reflector.service"
printf 'root:!:19000:0:99999:7:::\n' > "$root/etc/shadow"
chmod 400 "$root/etc/shadow"
printf 'root:x:0:0:root:/root:/bin/bash\n' > "$root/etc/passwd"
mkdir -p "$root/etc/systemd/system/multi-user.target.wants" "$root/etc/systemd/system/graphical.target.wants"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$root/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
ln -sf /usr/lib/systemd/system/docker.service "$root/etc/systemd/system/multi-user.target.wants/docker.service"
ln -sf /usr/lib/systemd/system/vboxservice.service "$root/etc/systemd/system/multi-user.target.wants/vboxservice.service"
ln -sf /etc/systemd/system/9b7-firstboot.service "$root/etc/systemd/system/multi-user.target.wants/9b7-firstboot.service"
ln -sf /usr/lib/systemd/system/sddm.service "$root/etc/systemd/system/display-manager.service"
ln -sf /usr/lib/systemd/system/graphical.target "$root/etc/systemd/system/default.target"
mkdir -p "$root/etc/NetworkManager/conf.d" "$root/etc/plymouth"
printf '[main]\ndns=default\n' > "$root/etc/NetworkManager/conf.d/9b7.conf"
rm -f "$root/etc/resolv.conf"
ln -s /run/NetworkManager/resolv.conf "$root/etc/resolv.conf"
printf '[Daemon]\nTheme=arch-slider-and-glow\nShowDelay=0\n' > "$root/etc/plymouth/plymouthd.conf"
printf 'en_US.UTF-8 UTF-8\nar_EG.UTF-8 UTF-8\n' > "$root/etc/locale.gen"
ln -sf /usr/share/zoneinfo/Africa/Cairo "$root/etc/localtime"
mkdir -p "$root/opt/9b7" "$root/usr/share/backgrounds/9b7" "$root/usr/share/icons/hicolor/scalable/apps"
for part in nineb7 data services docs automation; do
    cp -a "$project/$part" "$root/opt/9b7/"
done
find "$root/opt/9b7" -type d -name __pycache__ -prune -exec rm -rf {} +
cp "$project/README.md" "$project/LICENSE" "$root/opt/9b7/"
cp "$project/assets/wallpaper.svg" "$root/usr/share/backgrounds/9b7/"
rsvg-convert -o "$root/usr/share/backgrounds/9b7/wallpaper.png" "$project/assets/wallpaper.svg"
cp "$project/assets/9b7.svg" "$root/usr/share/icons/hicolor/scalable/apps/"
for module in studio flow services agents control_center; do
    command_name=${module//_/-}
    cat > "$root/usr/local/bin/9b7-$command_name" <<LAUNCHER
#!/usr/bin/env bash
export PYTHONPATH=/opt/9b7
exec /usr/bin/python -m nineb7.$module "\$@"
LAUNCHER
    chmod 755 "$root/usr/local/bin/9b7-$command_name"
    printf 'file_permissions["/usr/local/bin/9b7-%s"]="0:0:755"\n' "$command_name" >> "$profile/profiledef.sh"
done
for i in {1..9}; do
    printf 'bind = $mod, %s, workspace, %s\nbind = $mod SHIFT, %s, movetoworkspace, %s\n' "$i" "$i" "$i" "$i" >> "$root/etc/skel/.config/hypr/hyprland.conf"
done
mkdir -p "$root/etc/skel/.config/systemd/user/default.target.wants" "$root/etc/skel/9b7-Inbox"
ln -sf ../9b7-inbox.path "$root/etc/skel/.config/systemd/user/default.target.wants/9b7-inbox.path"
cat > "$profile/syslinux/archiso_sys-linux.cfg" <<'BOOT'
LABEL 9b7
MENU LABEL 9b7 Linux - Live desktop
LINUX /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
INITRD /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
APPEND archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% quiet splash cow_spacesize=4G %KERNEL_PARAMS%
LABEL 9b7-safe
MENU LABEL 9b7 Linux - Compatibility / VirtualBox (XFCE)
LINUX /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
INITRD /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
APPEND archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% 9b7.safe=1 cow_spacesize=4G %KERNEL_PARAMS%
BOOT
sed -i 's/^DEFAULT arch$/DEFAULT 9b7/; s/^TIMEOUT .*/TIMEOUT 80/' "$profile/syslinux/archiso_sys.cfg"
sed -i 's/^MENU TITLE .*/MENU TITLE 9b7 Linux - BIS Workspace/' "$profile/syslinux/archiso_head.cfg"
rsvg-convert -w 640 -h 480 -o "$profile/syslinux/splash.png" "$project/assets/wallpaper.svg"
mkdir -p "$profile/efiboot/loader/entries"
rm -f "$profile/efiboot/loader/entries/"*.conf
cat > "$profile/efiboot/loader/entries/01-9b7.conf" <<'BOOT'
title 9b7 Linux - Live desktop
linux /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
initrd /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
options archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% quiet splash cow_spacesize=4G %KERNEL_PARAMS%
BOOT
sed 's/Live desktop/Compatibility - XFCE/; s/quiet splash/9b7.safe=1/' "$profile/efiboot/loader/entries/01-9b7.conf" > "$profile/efiboot/loader/entries/02-9b7-safe.conf"
printf 'default 01-9b7.conf\ntimeout 8\nconsole-mode max\neditor no\n' > "$profile/efiboot/loader/loader.conf"
if [[ -f "$root/etc/mkinitcpio.conf.d/archiso.conf" ]]; then
    sed -i 's/udev /udev plymouth /' "$root/etc/mkinitcpio.conf.d/archiso.conf"
fi
if [[ $edition == full ]]; then
    [[ -s "$project/cache/offline/manifest.json" && -s "$project/cache/offline/models.tar" ]] || {
        echo 'Full edition requires scripts/bundle-offline.py first; refusing a partial full ISO' >&2; exit 1;
    }
    python "$project/scripts/verify-offline.py" "$project/cache/offline"
    if [[ ${NINEB7_BIND_OFFLINE:-0} == 1 ]]; then
        [[ $EUID == 0 ]] || { echo 'Offline bind mode requires the privileged builder' >&2; exit 1; }
        mkdir -p "$root/opt/9b7/offline"
        mount --bind "$project/cache/offline" "$root/opt/9b7/offline"
        mount -o remount,bind,ro "$root/opt/9b7/offline"
    else
        cp -a "$project/cache/offline" "$root/opt/9b7/"
    fi
fi
printf '%s\n' "$edition" > "$root/etc/9b7-edition"
git -c safe.directory="$project" -C "$project" rev-parse HEAD > "$root/opt/9b7/SOURCE-COMMIT"
echo "Prepared $edition profile: $profile"

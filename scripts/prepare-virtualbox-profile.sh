#!/usr/bin/env bash
# Independent Live-only profile. Legacy Desktop/Full sources stay in Git.
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
profile=${1:?Usage: prepare-virtualbox-profile.sh NEW_PROFILE_DIRECTORY}
releng=${ARCHISO_RELENG:-/usr/share/archiso/configs/releng}
[[ -d $releng && ! -e $profile ]] || { echo 'Use an installed releng and a new profile directory' >&2; exit 2; }
mkdir -p "$profile"
cp -a "$releng/." "$profile/"
root="$profile/airootfs"
# Use the lean package allowlist, not releng's recovery/installer/firmware set.
sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$project/iso/virtualbox/packages.x86_64" > "$profile/packages.x86_64"
cp -a "$project/iso/virtualbox/airootfs/." "$root/"
# Retain the external tools and their pinned service configurations, without
# copying nineb7/, custom GUI entry points, the installer or their autostarts.
mkdir -p "$root/usr/share/bis-services" "$root/usr/share/applications"
for config in compose.yml erpnext.compose.yml odoo.conf superset_config.py superset-init.py images.lock.json; do
    cp "$project/services/$config" "$root/usr/share/bis-services/"
done
sed -i 's/Run 9b7-services first/Use bis-service to start this stack/g' "$root/usr/share/bis-services/"*.yml
sed 's/9b7-storage/live-docker-storage/g' "$project/iso/airootfs/usr/local/bin/9b7-storage" > "$root/usr/local/bin/live-docker-storage"
cat >> "$root/usr/local/bin/live-docker-storage" <<'STORAGE'
# Keep service credentials on the same persistent volume as their databases.
if [[ -n ${SUDO_UID:-} && ${SUDO_UID} != 0 ]]; then
    install -d -m 700 -o "$SUDO_UID" -g "$SUDO_GID" "$mount_dir/.bis-services"
fi
STORAGE
while IFS='|' read -r stack title icon; do
    cat > "$root/usr/share/applications/bis-$stack.desktop" <<ENTRY
[Desktop Entry]
Type=Application
Name=$title
Comment=Start the upstream service on demand
Exec=foot --hold bis-service $stack start
Icon=$icon
Categories=Office;Development;
Terminal=false
ENTRY
done <<'SERVICES'
n8n|n8n|applications-development
superset|Apache Superset|office-chart-bar
metabase|Metabase|office-chart-bar
odoo|Odoo|x-office-document
erpnext|ERPNext|x-office-document
databases|PostgreSQL, Cassandra & Redis|server-database
ai|Ollama|applications-science
SERVICES
chmod 755 "$root/usr/local/bin/bis-service" "$root/usr/local/bin/live-docker-storage"
# Retain exactly the supplied login and splash designs, with reviewed fixes.
for asset in usr/share/sddm/themes/Slot-SDDM-6 usr/share/plymouth/themes/arch-slider-and-glow \
    usr/share/licenses/Slot-SDDM-6 etc/sudoers.d/90-9b7 etc/os-release; do
    mkdir -p "$(dirname "$root/$asset")"
    cp -a "$project/iso/airootfs/$asset" "$root/$asset"
done
# The live account is prepared during the build, not on the boot critical path.
mkdir -p "$root/var/lib/sddm" "$root/opt/9b7" "$root/usr/share/9b7/no-x11-sessions"
printf 'root:!:19000:0:99999:7:::\n' > "$root/etc/shadow"
printf 'root:x:0:0:root:/root:/bin/bash\n' > "$root/etc/passwd"
# mkarchiso custom hook runs after packages and sysusers, inside the image root.
mkdir -p "$root/etc/pacman.d/hooks"
cat > "$root/etc/pacman.d/hooks/zz-9b7-live-account.hook" <<'HOOK'
# remove from airootfs: build-only account preparation
[Trigger]
Operation = Install
Type = Package
Target = sddm
[Action]
Description = Prepare the VirtualBox Live account
When = PostTransaction
Exec = /usr/local/bin/9b7-prepare-live-account
HOOK
cat > "$root/usr/local/bin/9b7-prepare-live-account" <<'ACCOUNT'
#!/usr/bin/env bash
set -euo pipefail
systemd-sysusers
if ! id 9b7 >/dev/null 2>&1; then
    useradd --badname -m -u 1000 -U -s /bin/bash 9b7
fi
usermod -aG wheel,docker,wireshark 9b7
chown -R 1000:1000 /home/9b7
printf '9b7:9b7\n' | chpasswd
printf '[Last]\nUser=9b7\nSession=/usr/share/9b7/sessions/9b7-virtualbox.desktop\n' > /var/lib/sddm/state.conf
chown -R sddm:sddm /var/lib/sddm
# Exactly one login session. The compositor package's generic session is
# replaced by our wrapper; no alternate DE packages are in this profile.
find /usr/share/wayland-sessions /usr/share/xsessions -maxdepth 1 -name '*.desktop' -delete 2>/dev/null || true
ACCOUNT
chmod 755 "$root/usr/local/bin/9b7-prepare-live-account" "$root/usr/local/bin/9b7-desk-session"
# Remove the releng network waits, accessibility startup, mirror selection and
# installer autologin. Only explicit Live desktop services are enabled here.
rm -rf "$root/etc/systemd/system" "$root/root/.automated_script.sh"
mkdir -p "$root/etc/systemd/system/multi-user.target.wants"
for unit in NetworkManager vboxservice; do
    ln -s "/usr/lib/systemd/system/$unit.service" "$root/etc/systemd/system/multi-user.target.wants/$unit.service"
done
ln -s /usr/lib/systemd/system/sddm.service "$root/etc/systemd/system/display-manager.service"
ln -s /usr/lib/systemd/system/graphical.target "$root/etc/systemd/system/default.target"
ln -s /dev/null "$root/etc/systemd/system/NetworkManager-wait-online.service"
mkdir -p "$root/etc/NetworkManager/conf.d" "$root/etc/plymouth"
printf '[main]\ndns=default\n' > "$root/etc/NetworkManager/conf.d/9b7.conf"
rm -f "$root/etc/resolv.conf"
ln -s /run/NetworkManager/resolv.conf "$root/etc/resolv.conf"
printf '[Daemon]\nTheme=arch-slider-and-glow\nShowDelay=0\nDeviceTimeout=2\n' > "$root/etc/plymouth/plymouthd.conf"
printf 'en_US.UTF-8 UTF-8\nar_EG.UTF-8 UTF-8\n' > "$root/etc/locale.gen"
printf '9b7\n' > "$root/etc/hostname"
ln -sf /usr/share/zoneinfo/Africa/Cairo "$root/etc/localtime"
# No physical GPU firmware, microcode or PXE/NFS boot in this VM-only image.
cat > "$root/etc/mkinitcpio.conf.d/archiso.conf" <<'INITRAMFS'
MODULES=(vmwgfx bochs vboxguest)
HOOKS=(base udev plymouth modconf archiso archiso_loop_mnt block filesystems keyboard)
COMPRESSION="zstd"
COMPRESSION_OPTIONS=(-3)
INITRAMFS
cat >> "$profile/profiledef.sh" <<'PROFILE'
iso_name="9b7-linux"
iso_label="9B7_VBOX_$(date -u +%Y%m%d)"
iso_publisher="9b7 Linux <https://github.com/9a6r/9b7-linux>"
iso_application="9b7 VirtualBox Live preview"
iso_version="$(date -u +%Y.%m.%d)"
bootmodes=('bios.syslinux')
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '6' '-b' '1M' '-processors' '2' '-mem' '512M')
file_permissions["/etc/shadow"]="0:0:400"
file_permissions["/etc/sudoers.d/90-9b7"]="0:0:440"
file_permissions["/usr/local/bin/9b7-desk-session"]="0:0:755"
file_permissions["/usr/local/bin/9b7-prepare-live-account"]="0:0:755"
file_permissions["/usr/local/bin/bis-service"]="0:0:755"
file_permissions["/usr/local/bin/live-docker-storage"]="0:0:755"
unset 'file_permissions[/root/.automated_script.sh]'
PROFILE
cat > "$profile/syslinux/archiso_sys.cfg" <<'SYSLINUX'
UI vesamenu.c32
DEFAULT 9b7
PROMPT 0
TIMEOUT 10
MENU TITLE 9b7 - VirtualBox preview
INCLUDE archiso_sys-linux.cfg
SYSLINUX
cat > "$profile/syslinux/archiso_sys-linux.cfg" <<'BOOT'
LABEL 9b7
MENU LABEL 9b7 Linux - VirtualBox
LINUX /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
INITRD /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
APPEND archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% quiet splash cow_spacesize=2G %KERNEL_PARAMS%
BOOT
printf 'virtualbox\n' > "$root/etc/9b7-edition"
git -c safe.directory="$project" -C "$project" rev-parse HEAD > "$root/opt/9b7/SOURCE-COMMIT"
cp "$project/LICENSE" "$root/opt/9b7/"
echo "Prepared VirtualBox-only profile: $profile"

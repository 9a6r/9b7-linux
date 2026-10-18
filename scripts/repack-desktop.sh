#!/usr/bin/env bash
# Reuse a verified Desktop boot image after updating a disposable native root.
# Full source builds remain scripts/build-iso.sh; this does not modify the base ISO.
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
base=$(realpath "${1:?Usage: repack-desktop.sh BASE_DESKTOP_ISO PREPARED_ROOT NEW_ISO}")
root=$(realpath "${2:?Prepared native Desktop root required}")
output=$(realpath -m "${3:?New ISO path required}")
[[ $EUID == 0 && -f /etc/arch-release ]] || { echo 'Use the privileged Arch builder' >&2; exit 1; }
[[ $base == *-desktop.iso && $output == *.iso && ! -e $output ]] || { echo 'Refusing to overwrite an artifact or use a Full ISO' >&2; exit 1; }
[[ $(cat "$root/etc/9b7-edition") == desktop ]]
[[ -z $(git -c safe.directory="$project" -C "$project" status --porcelain) ]]
commit=$(git -c safe.directory="$project" -C "$project" rev-parse HEAD)
[[ $(cat "$root/opt/9b7/SOURCE-COMMIT") == "$commit" ]] || { echo 'Prepared root source does not match HEAD' >&2; exit 1; }
[[ -z $(find "$root/home" -mindepth 1 -maxdepth 1 -print -quit) ]] || { echo 'Refusing to package user homes' >&2; exit 1; }
[[ ! -d $root/etc/pacman.d/gnupg/private-keys-v1.d ]]
[[ ! -e $root/etc/ca-certificates/trust-source/anchors/9b7-build-environment.crt ]]
[[ $(findmnt -rn -o TARGET -R "$root" | wc -l) -le 1 ]] || { echo 'Unmount nested chroot filesystems first' >&2; exit 1; }
(cd "$(dirname "$base")" && sha256sum -c "$(basename "$base").sha256")
work=$(mktemp -d "${NINEB7_WORK_DIR:-$project/work}/repack.XXXXXX")
[[ -s $root/boot/vmlinuz-linux && -s $root/boot/initramfs-linux.img ]]
# Extract only original boot files, not another copy of the old squashfs.
xorriso -osirrox on -indev "$base" -extract /EFI "$work/EFI" \
    -extract /loader "$work/loader" -extract /shellx64.efi "$work/shellx64.efi"
# Keep the base volume UUID: both BIOS and UEFI archiso entries search for it.
uuid=$(xorriso -indev "$base" -pvd_info 2>/dev/null | awk '/^Creation Time:/ {print $3}')
[[ $uuid =~ ^[0-9]{16}$ ]]
# A fresh FAT image includes the UPDATED matching kernel/initramfs for UEFI.
kernel_bytes=$(stat -c %s "$root/boot/vmlinuz-linux")
initramfs_bytes=$(stat -c %s "$root/boot/initramfs-linux.img")
fat_mib=$(( (kernel_bytes + initramfs_bytes) / 1048576 + 48 ))
truncate -s "${fat_mib}M" "$work/efiboot.img"
mkfs.fat -F 32 -n 9B7_EFI "$work/efiboot.img"
mcopy -i "$work/efiboot.img" -s "$work/EFI" "$work/loader" "$work/shellx64.efi" ::/
mmd -i "$work/efiboot.img" ::/arch ::/arch/boot ::/arch/boot/x86_64
mcopy -i "$work/efiboot.img" "$root/boot/vmlinuz-linux" "$root/boot/initramfs-linux.img" ::/arch/boot/x86_64/
# Keep prepared root/boot intact; omit duplicate boot files from squashfs.
mksquashfs "$root" "$work/airootfs.sfs" -noappend -comp zstd -Xcompression-level 6 -b 1M -processors 2 -mem 512M -e boot/vmlinuz-linux boot/initramfs-linux.img
(cd "$work" && sha512sum airootfs.sfs > airootfs.sha512)
pacman --root "$root" -Q > "$work/packages.txt"
xorriso -indev "$base" -outdev "$output" -boot_image any replay \
    -append_partition 2 0xef "$work/efiboot.img" -volume_date uuid "$uuid" \
    -update "$work/airootfs.sfs" /arch/x86_64/airootfs.sfs \
    -update "$work/airootfs.sha512" /arch/x86_64/airootfs.sha512 \
    -update "$root/boot/vmlinuz-linux" /arch/boot/x86_64/vmlinuz-linux \
    -update "$root/boot/initramfs-linux.img" /arch/boot/x86_64/initramfs-linux.img \
    -map "$root/opt/9b7/SOURCE-COMMIT" /SOURCE-COMMIT \
    -map "$work/packages.txt" /packages.txt
(cd "$(dirname "$output")" && sha256sum "$(basename "$output")" > "$(basename "$output").sha256")
cp "$work/packages.txt" "$output.packages.txt"
cp "$root/opt/9b7/SOURCE-COMMIT" "$output.source-commit"
printf 'Built %s from %s; BIOS/UEFI boot and installation still require verification.\n' "$output" "$commit"

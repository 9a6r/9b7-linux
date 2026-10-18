#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
edition=${1:-full}
[[ $edition == desktop || $edition == full ]] || { echo 'Usage: build-iso.sh [full|desktop]' >&2; exit 2; }
[[ $EUID == 0 && -f /etc/arch-release ]] || { echo 'Use an Arch Linux root builder; see docs/BUILD.ar.md' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'Only x86_64 is supported' >&2; exit 1; }
for command in mkarchiso rsvg-convert mksquashfs git; do command -v "$command" >/dev/null; done
workspace=${NINEB7_WORK_DIR:-$project/work}
mkdir -p "$workspace" "$project/out"
available=$(df --output=avail -k "$workspace" | tail -1)
required=18000000
[[ $edition == desktop ]] || required=55000000
if [[ ${NINEB7_BIND_OFFLINE:-0} == 1 && $edition == full ]]; then
    # Separate RAM-backed workspace: one root plus its compressed SquashFS.
    # Archives stay on the output filesystem and are mounted into the profile.
    [[ $(stat -c %d "$workspace") != "$(stat -c %d "$project/out")" ]] || {
        echo 'Compact full build needs separate work and output filesystems' >&2; exit 1;
    }
    bundle_kib=$(du -sk "$project/cache/offline" | cut -f1)
    required=$((bundle_kib * 2 + 13000000))
    output_free=$(df --output=avail -k "$project/out" | tail -1)
    (( output_free >= bundle_kib + 5000000 )) || { echo 'Output filesystem needs bundle size plus 5GB free' >&2; exit 1; }
fi
(( available >= required )) || { echo "Insufficient build space: need at least $required KiB free for $edition" >&2; exit 1; }
source_status=$(git -c safe.directory="$project" -C "$project" status --porcelain --untracked-files=normal)
if [[ -n $source_status ]]; then
    echo 'Commit or preserve source changes first so SOURCE-COMMIT identifies the actual build.' >&2
    exit 1
fi
build=$(mktemp -d "$workspace/iso-$edition.XXXXXX")
iso_output=$(mktemp -d "$project/out/.build-$edition.XXXXXX")
cleanup() {
    if mountpoint -q "$build/profile/airootfs/opt/9b7/offline"; then
        umount "$build/profile/airootfs/opt/9b7/offline"
    fi
}
trap cleanup EXIT
bash "$project/scripts/prepare-profile.sh" "$build/profile" "$edition"
# Locally built AUR packages are signed and verified with a dedicated build key.
[[ -f "$project/cache/packages/9b7.db.tar.gz" && -f "$project/cache/packages/builder.asc" ]] || {
    echo 'Run scripts/build-extra-packages.sh first' >&2; exit 1;
}
pacman-key --init
pacman-key --populate archlinux
pacman-key --add "$project/cache/packages/builder.asc"
fingerprint=$(gpg --show-keys --with-colons "$project/cache/packages/builder.asc" | awk -F: '$1=="fpr" {print $10; exit}')
pacman-key --lsign-key "$fingerprint"
cat >> "$build/profile/pacman.conf" <<LOCALREPO

[9b7]
SigLevel = Required DatabaseRequired
Server = file://$project/cache/packages
LOCALREPO
printf 'vscodium-bin\nburpsuite\nobsidian-bin\npython-cassandra-driver\n9b7-desk\n' >> "$build/profile/packages.x86_64"
if ! mkarchiso -v -w "$build/work" -o "$iso_output" "$build/profile"; then
    root="$build/work/x86_64/airootfs"
    # Some container hosts expose a bare devtmpfs without /dev/stdin. Arch's
    # kernel hook then fails despite successful package installation. The
    # supported namespace mode creates private standard device links.
    if [[ -f "$build/work/base._make_packages" &&
          ! -s "$build/work/x86_64/boot/initramfs-linux.img" &&
          -f "$root/usr/share/libalpm/scripts/mkinitcpio" ]]; then
        echo 'Retrying missing initramfs with private chroot device links...'
        arch-chroot -N "$root" bash -c 'printf "%s\n" usr/lib/modules/*/vmlinuz | /usr/share/libalpm/scripts/mkinitcpio install'
        [[ -s "$root/boot/initramfs-linux.img" && -s "$root/boot/vmlinuz-linux" ]]
        rm -f "$build/work/base._copy_boot_out_of_pacstrap_dir" "$build/work/base._check_if_initramfs_has_ucode"
        mkarchiso -v -w "$build/work" -o "$iso_output" "$build/profile"
    else
        exit 1
    fi
fi
mapfile -t images < <(find "$iso_output" -maxdepth 1 -name '9b7-linux-*.iso' -type f)
(( ${#images[@]} == 1 )) && [[ -s ${images[0]} ]]
image="$project/out/$(basename "${images[0]}" .iso)-$edition.iso"
[[ ! -e $image ]] || { echo "Preserving existing ISO: $image. New output: ${images[0]}" >&2; exit 1; }
mv -n "${images[0]}" "$image"
rmdir "$iso_output"
(cd "$project/out" && sha256sum "$(basename "$image")" > "$(basename "$image").sha256")
cp "$build/work/x86_64/airootfs/opt/9b7/SOURCE-COMMIT" "$project/out/SOURCE-COMMIT"
cp "$build/work/x86_64/airootfs/opt/9b7/SOURCE-COMMIT" "$image.source-commit"
pacman --root "$build/work/x86_64/airootfs" -Q > "$image.packages.txt"
echo "Built $image — boot verification is still required before release."

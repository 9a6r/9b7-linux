#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
edition=${1:-full}
[[ $edition == desktop || $edition == full ]] || { echo 'Usage: build-iso.sh [full|desktop]' >&2; exit 2; }
[[ $EUID == 0 && -f /etc/arch-release ]] || { echo 'Use an Arch Linux root builder; see docs/BUILD.ar.md' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'Only x86_64 is supported' >&2; exit 1; }
for command in mkarchiso rsvg-convert mksquashfs git; do command -v "$command" >/dev/null; done
available=$(df --output=avail -k "$project" | tail -1)
required=18000000
[[ $edition == desktop ]] || required=55000000
(( available >= required )) || { echo "Insufficient build space: need at least $required KiB free for $edition" >&2; exit 1; }
mkdir -p "$project/work" "$project/out"
build=$(mktemp -d "$project/work/iso-$edition.XXXXXX")
bash "$project/scripts/prepare-profile.sh" "$build/profile" "$edition"
# Locally built AUR packages are signed and verified with a dedicated build key.
[[ -f "$project/cache/packages/9b7.db.tar.gz" && -f "$project/cache/packages/builder.asc" ]] || {
    echo 'Run scripts/build-extra-packages.sh first' >&2; exit 1;
}
pacman-key --add "$project/cache/packages/builder.asc"
fingerprint=$(gpg --show-keys --with-colons "$project/cache/packages/builder.asc" | awk -F: '$1=="fpr" {print $10; exit}')
pacman-key --lsign-key "$fingerprint"
cat >> "$build/profile/pacman.conf" <<LOCALREPO

[9b7]
SigLevel = Required DatabaseRequired
Server = file://$project/cache/packages
LOCALREPO
printf 'vscodium-bin\nburpsuite\nobsidian-bin\npython-cassandra-driver\n' >> "$build/profile/packages.x86_64"
mkarchiso -v -w "$build/work" -o "$project/out" "$build/profile"
image=$(find "$project/out" -maxdepth 1 -name '9b7-linux-*.iso' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
[[ -s $image ]]
mv "$image" "${image%.iso}-$edition.iso"
image="${image%.iso}-$edition.iso"
(cd "$project/out" && sha256sum "$(basename "$image")" > "$(basename "$image").sha256")
cp "$build/work/x86_64/airootfs/opt/9b7/SOURCE-COMMIT" "$project/out/SOURCE-COMMIT"
pacman --root "$build/work/x86_64/airootfs" -Q > "$image.packages.txt"
echo "Built $image — boot verification is still required before release."

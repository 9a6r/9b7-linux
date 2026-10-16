#!/usr/bin/env bash
# Execute only inside the dedicated Arch builder. Reviewed upstream refs are pinned.
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID == 0 && -f /etc/arch-release ]] || { echo 'Requires a dedicated Arch root builder' >&2; exit 1; }
pacman -Syu --needed --noconfirm base-devel sudo git gnupg python python-build python-installer python-wheel python-setuptools jq
id builder >/dev/null 2>&1 || useradd -m builder
printf 'builder ALL=(ALL) NOPASSWD: /usr/bin/pacman\n' > /etc/sudoers.d/9b7-builder
chmod 440 /etc/sudoers.d/9b7-builder
mkdir -p "$project/cache/packages" "$project/cache/signing" "$project/cache/aur-build"
chmod 700 "$project/cache/signing"
chown -R builder:builder "$project/cache/packages" "$project/cache/signing" "$project/cache/aur-build"
export GNUPGHOME="$project/cache/signing"
if ! runuser -u builder -- gpg --list-secret-keys --with-colons | grep -q '^sec:'; then
    runuser -u builder -- gpg --batch --passphrase '' --quick-generate-key '9b7 local build <build@9b7.invalid>' ed25519 sign 0
fi
key=$(runuser -u builder -- gpg --list-secret-keys --with-colons | awk -F: '$1=="fpr" {print $10; exit}')
runuser -u builder -- gpg --armor --export "$key" > "$project/cache/packages/builder.asc"
pacman-key --add "$project/cache/packages/builder.asc"
pacman-key --lsign-key "$key"
for package in python-geomet python-cassandra-driver vscodium-bin burpsuite obsidian; do
    directory="$project/cache/aur-build/$package"
    if [[ $package == python-* ]]; then
        mkdir -p "$directory"
        cp "$project/packaging/$package/PKGBUILD" "$directory/"
    else
        commit=$(jq -r --arg package "$package" '.[$package].commit' "$project/packaging/aur-lock.json")
        if [[ ! -d $directory/.git ]]; then
            runuser -u builder -- git init "$directory"
            runuser -u builder -- git -C "$directory" remote add origin https://github.com/archlinux/aur.git
        fi
        runuser -u builder -- git -C "$directory" fetch --depth 1 origin "$commit"
        runuser -u builder -- git -C "$directory" checkout --detach "$commit"
        [[ $(git -c safe.directory="$directory" -C "$directory" rev-parse HEAD) == "$commit" ]]
    fi
    chown -R builder:builder "$directory"
    (cd "$directory" && runuser -u builder -- env PKGDEST="$project/cache/packages" MAKEFLAGS=-j2 TERM=xterm \
        makepkg --syncdeps --noconfirm --cleanbuild --clean --sign --key "$key")
    if [[ $package == python-geomet ]]; then
        pacman -U --noconfirm "$project"/cache/packages/python-geomet-*.pkg.tar.zst
    fi
done
runuser -u builder -- repo-add --sign --key "$key" "$project/cache/packages/9b7.db.tar.gz" "$project"/cache/packages/*.pkg.tar.zst
echo 'Extra packages built and signed. Private signing key stays in ignored cache/signing.'

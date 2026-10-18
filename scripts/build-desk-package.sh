#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID == 0 && -f /etc/arch-release ]] || { echo 'Use the dedicated Arch builder' >&2; exit 1; }
[[ -s "$project/cache/packages/builder.asc" ]] || { echo 'Build the signed extra packages first' >&2; exit 1; }
pacman -Syu --needed --noconfirm base-devel meson ninja wayland wayland-protocols libxkbcommon \
    libinput cairo pixman fontconfig libdrm libglvnd mesa libpulse pam libxcb xcb-util-wm \
    seatd libdisplay-info hwdata libx11 xcb-util-renderutil xorg-xwayland \
    xdg-desktop-portal-gtk xdg-desktop-portal-wlr gsfonts noto-fonts libnotify xdg-user-dirs xdg-utils
directory="$project/cache/desk-build"
mkdir -p "$directory"
cp "$project/packaging/9b7-desk/PKGBUILD" "$directory/"
cp "$project/packaging/9b7-desk/"*.patch "$directory/"
chown -R builder:builder "$directory"
export GNUPGHOME="$project/cache/signing"
key=$(gpg --show-keys --with-colons "$project/cache/packages/builder.asc" | awk -F: '$1=="fpr" {print $10; exit}')
(cd "$directory" && runuser -u builder -- env PKGDEST="$project/cache/packages" MAKEFLAGS=-j2 \
    makepkg --noconfirm --cleanbuild --force --sign --key "$key")
runuser -u builder -- repo-add --sign --key "$key" "$project/cache/packages/9b7.db.tar.gz" "$project"/cache/packages/*.pkg.tar.zst

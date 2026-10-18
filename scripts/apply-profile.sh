#!/usr/bin/env bash
# Apply only a trusted generated project profile to a disposable native root.
set -euo pipefail
profile=$(realpath "${1:?Usage: apply-profile.sh GENERATED_PROFILE DISPOSABLE_NATIVE_ROOT}")
root=$(realpath "${2:?Native root required}")
[[ $EUID == 0 && -d $root/var/lib/pacman/local && -f $profile/profiledef.sh ]]
[[ $root != / && -f $profile/airootfs/opt/9b7/SOURCE-COMMIT ]]
# Cloud-created source directories can be 0700. Apply the same public defaults
# as mkarchiso, then its explicit exceptions; never preserve checkout ownership.
rsync -a --chown=0:0 --chmod=D755,F644 "$profile/airootfs/" "$root/"
declare -A file_permissions
# shellcheck source=/dev/null
source "$profile/profiledef.sh"
for path in "${!file_permissions[@]}"; do
    [[ -e $root$path ]] || continue
    IFS=: read -r owner group mode <<< "${file_permissions[$path]}"
    chown "$owner:$group" "$root$path"
    chmod "$mode" "$root$path"
done
# Keep vendor metadata intact and the distribution override as a regular file.
[[ ! -L $root/etc/os-release && $(stat -c %a "$root") == 755 ]]
find "$root/opt/9b7" -type d -name __pycache__ -prune -exec rm -rf {} +

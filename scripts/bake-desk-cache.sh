#!/usr/bin/env bash
# Build-only: render the original software scenes natively into the Live home.
# No replacement artwork, user settings, GPU policy, or applications are added.
set -euo pipefail
[[ $EUID == 0 && -x /usr/bin/desk ]] || { echo 'Run inside the prepared Arch image root' >&2; exit 1; }
scratch=$(mktemp -d /tmp/desk-precache.XXXXXX)
chown 1000:1000 "$scratch"
chmod 700 "$scratch"
pid=
cleanup() {
    if [[ -n $pid ]]; then kill -TERM "$pid" 2>/dev/null || true; wait "$pid" || true; fi
    rm -rf "$scratch"
}
trap cleanup EXIT
for size in 800x600 1024x768 1280x800 1366x768; do
    log="$scratch/$size.log"
    echo "Rendering DEsk's original cached scenes at $size"
    runuser -u 9b7 -- env -u DISPLAY -u WAYLAND_DISPLAY -u DESK_SESSION \
        XDG_RUNTIME_DIR="$scratch" XDG_CONFIG_HOME=/home/9b7/.config \
        XDG_CACHE_HOME=/home/9b7/.cache XDG_STATE_HOME="$scratch" \
        DESK_NO_GPU=1 DESK_ON_CPU=1 WLR_RENDERER=pixman \
        desk --headless --size "$size" > "$log" 2>&1 &
    pid=$!
    ready=false
    for ((attempt=0; attempt<300; attempt++)); do
        if grep -Fq 'the lamp is up' "$log"; then ready=true; break; fi
        kill -0 "$pid" 2>/dev/null || break
        sleep 2
    done
    if ! $ready; then cat "$log" >&2; echo "DEsk cache did not finish at $size" >&2; exit 1; fi
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" || true
    pid=
    grep -E 'the (desk|bookcase|Control Panel|post box|lamp) is up|read back|the views,' "$log"
done
test -n "$(find /home/9b7/.cache/desk -name 'room-*.meta' -print -quit)"
du -sh /home/9b7/.cache/desk

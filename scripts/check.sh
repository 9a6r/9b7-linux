#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m unittest discover -s tests -v
while IFS= read -r -d '' script; do
    bash -n "$script"
done < <(find scripts iso/airootfs/usr/local/bin iso/virtualbox/airootfs/usr/local/bin -type f \( -name '*.sh' -o -path '*/usr/local/bin/*' \) -print0)
if command -v shellcheck >/dev/null; then
    find scripts iso/airootfs/usr/local/bin iso/virtualbox/airootfs/usr/local/bin -type f \( -name '*.sh' -o -path '*/usr/local/bin/*' \) -print0 |
        xargs -0 shellcheck --severity=warning
fi
if docker compose version >/dev/null 2>&1; then
    check_state=$(mktemp -d)
    trap 'rm -rf "$check_state"' EXIT
    XDG_STATE_HOME="$check_state" python3 - <<'PY'
import subprocess
from nineb7.services import CATALOG, compose_command
for stack in CATALOG:
    subprocess.run(compose_command(stack, 'config', '--quiet'), check=True)
print('All seven Compose stack configurations validated')
PY
fi

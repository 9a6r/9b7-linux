# AI Hub and Software Center

AI Hub installs individually selected official tools into `$XDG_DATA_HOME/9b7/agents`
(default `~/.local/share/9b7/agents`). Claude Code is first and initially selected.
`packaging/agents-lock.json` pins version, HTTPS origin, exact size, SHA-256 and
license for each tool. Updates use this reviewed catalog, not an unverified
latest-install script. Downloads and extraction are checked before atomically
switching the active version. Previous versions are retained until removal.
Removal affects managed binaries only, preserving official login files and projects.

The launch button opens the chosen project in the official CLI, with its normal
interactive permissions and login. No credential reader, automatic login, paid
request, unrestricted-agent flag or automatic Studio-data transfer is added.
Claude/Codex/Copilot generally require an eligible account, plan or API billing;
Gemini eligibility follows Google's current rules. Read the linked upstream terms.

Actual host Linux x86_64 `--version` results on 18 October 2026:

| Tool | Verified version |
|---|---|
| Claude Code | 2.1.292 |
| Codex | 0.163.0 |
| OpenCode | 1.19.3 |
| Copilot CLI | 1.0.98 |
| Gemini CLI | 0.64.0 |

These checks verify downloaded executable startup, **not account authentication,
model responses or every CLI feature**. Gemini uses its official bundled JS and
Node.js >=20; optional native PTY/keychain integrations are not bundled. The ISO
includes Node.js, but cloud-agent binaries and models remain opt-in downloads.

Ollama can use the existing Docker Local AI service or the optional native Arch
package from Software Center. Start only one runtime on localhost:11434. Native
start/stop needs administrator authentication and is not enabled automatically.
The model panel offers Qwen2.5 0.5B/1.5B, shows estimated download/RAM and measured
resources, confirms downloads/deletion, and can unload model RAM. Sizes vary;
8GB machines should avoid multiple heavy services. There is no automatic model
download. Runtime/model licenses are separate (Ollama MIT, Qwen2.5 Apache-2.0).

Claude usage is explicitly unavailable in this app: use the official `/usage`
command/account page. Codex quota snapshots require selecting a local sessions
folder, read bounded tails of at most five recent JSONL files, and display the
recorded UTC timestamp. They are historical snapshots, not live usage. Only
allowlisted quota fields are displayed; auth files and prompt text are excluded.
No source from the supplied GPL Plasma widgets is copied, and Plasma is not added.

Software Center shares the reviewed installation boundary. System packages use
signed Arch repositories and `pacman -Syu --needed`, with an administrator password
and pacman's final package/size confirmation in the terminal. Only explicitly
listed optional packages can be removed; core desktop applications stay protected
in this catalog. User data is preserved. Live-session installs disappear on reboot.

Validation: six backend tests cover corrupt downloads, failed-update rollback,
archive traversal/link rejection, preservation of unmanaged data, quota filtering
and incomplete model pulls. A real offscreen Qt test performs a verified test
install/removal through worker threads and displays selected quota snapshots.
Native package install/remove and authenticated cloud operations still require
separate runtime testing. See VALIDATION.md for ISO/session status.

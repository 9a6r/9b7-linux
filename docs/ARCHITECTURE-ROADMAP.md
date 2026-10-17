# 9b7: architecture and staged delivery

The current user specification is preserved in USER-ROADMAP-2026-10-17.md.
It supersedes plans to remove Hyprland: DEsk, Hyprland and XFCE stay in one
distribution, officially named **9b7**. No new distribution logo is commissioned.
Desktop/Full describe build payloads, not separate product identities.

## Phase 1 findings (2026-10-17)

The existing Flow importer, SQLite analytics, service manager and local three-role
AI pipeline are real working components. Their tests and data are retained.
Studio's next implementation will use a separate business database, so existing
Flow history cannot be mistaken for institutional records. Initial business
modules will be complete vertical slices: organization setup/settings, customers,
products/stock, posted sales invoices and audit/reporting. Other modules remain
explicit roadmap items until implemented; no decorative empty pages.

Business rules live outside Qt. SQLite migrations are versioned and backed up
before upgrade; money uses integer minor units, references use foreign keys,
stock/invoice/audit updates share transactions. UI translations are shared
Arabic/English keys with persisted language and RTL/LTR layout. A repository
boundary allows a later PostgreSQL adapter without embedding SQL in widgets.
Demo data is opt-in and isolated from the real organization database.

Control Center groups services, system tools and Flow. AI Hub uses a shared
software catalog/installer rather than duplicating package operations. Installs
are per-user where possible, selected individually, checksum verified and atomic.
Credentials remain with each official CLI's login flow; the hub does not read
OAuth credential files or send Studio records to cloud agents. Package-manager
operations requiring root use an explicit authorization boundary.

### Agents reviewed at their official repositories

| Tool | Source/license | Installation and authentication |
|---|---|---|
| Claude Code | anthropics/claude-code; proprietary Anthropic terms | Native official Linux binary and manifest. npm is deprecated. Claude account/eligible plan or API billing; Claude's cloud models are not local downloads. |
| Codex | openai/codex; Apache-2.0 | Official binary or @openai/codex; official sign-in/API setup. |
| OpenCode | anomalyco/opencode; MIT | Official @opencode/cli or release binary; provider-specific accounts. |
| Gemini CLI | google-gemini/gemini-cli; Apache-2.0 | @google/gemini-cli; Google/API/Vertex authentication. Current README changes unpaid/Google One eligibility: do not promise universal free access. |
| Copilot CLI | github/copilot-cli; custom GitHub license | Official @github/copilot or release; active subscription/organization policy applies. |
| Ollama | ollama/ollama; MIT, models have separate licenses | Local runtime; models are individually selected and size-confirmed. Existing Docker-backed local AI remains available. |

The Claude install-script endpoint returned HTTP403 in this cloud; no script was
executed. Official downloads.claude.ai manifest was reachable, and its Linux
checksum matches the maintained Homebrew cask. Prefer verified native assets.
Research alone does not establish a successful install or authenticated request.

### Uploaded add-ons

`packaging/additional-attachments.json` records exact archive hashes.
Claude Usage2.4.2 and Codex Usage1.2.1 are Plasma6 applets by **izll**, respectively
https://github.com/izll/plasma-claude-usage and
https://github.com/izll/plasma-codex-usage, GPL-3.0-or-later per metadata.
Do not install Plasma to run them. Claude's script reads a credential file and
calls an OAuth usage endpoint; we will not transplant this flow without a
supported provider contract. Codex's script reads local JSONL rate-limit
snapshots; a separately implemented, opt-in, bounded local parser can display
available data, its timestamp and unavailable/stale states. No invented usage.
No GPL applet code has been copied into the MIT application.

Korkhon archive contains CUR/ANI and Windows INF files, with no included license
or identified author. The supplied follow-up URL points to DEsk, whose MIT
license does not automatically license separately supplied cursor artwork.
No Windows installer was run. Cursor conversion may be tested locally, but
redistribution remains blocked on provenance. Any eventual cursor choice is
opt-in and scoped to DEsk, leaving XFCE/Hyprland/SDDM defaults untouched.

### Measured footprint and compatibility

The first DEsk Desktop ISO is **4,038,098,944 bytes** (verify sidecar before use),
versus original Full **12,352,876,544 bytes**. Desktop keeps native applications
and all three sessions; service images/models are downloaded on demand.
Largest installed packages: Burp706MiB, VSCodium595MiB, Ansible511MiB,
Obsidian361MiB, Firefox302MiB, Nerd fonts232MiB. Native packages total7748MiB.
No required program was removed. Build cache is outside the ISO.

DEsk0.1.2 is beta and requires a private wlroots0.18.3. Arabic shell shaping/RTL
is incomplete upstream; application Arabic support is independent. QEMU is TCG
only; VirtualBox, physical USB/hardware and Secure Boot are untested. QEMU11.1.2
crashed with the virtio VGA test setup; standard VGA successfully reached the
original Plymouth screen under UEFI. This does not yet prove login or desktop.

## Gates for the next phases

1. Studio: blank first launch, persisted organization/language, CRUD/search,
   transactional invoices/stock, audit, backup/restore and real Arabic UI tests.
2. AI Hub: Claude first, verified install/version/uninstall, no automatic models;
   remaining agents and usage panels tested independently of paid authentication.
3. Desktop: original login/boot graphics, all sessions, applications, lock/logout,
   network/audio, then clean Desktop ISO boot and disposable-disk installation.
4. Installer: user-selected disk, identity/password/timezone/session, final erase
   confirmation, install and second boot. Existing experimental terminal installer
   is not yet the requested graphical installer and does not meet new identity rules.
5. Release: publish only actual tested experimental artifacts; all parts, SHA256,
   assembly helpers and anonymous download verification. Full stays preserved;
   separate optional offline bundles replace a mandatory giant download.

# Latest status — 18 October 2026

- Preserved Full and first Desktop ISO SHA-256 rechecks: PASS.
- Current source: 35 Python tests, ShellCheck, seven Compose configs: PASS.
- Desktop workflow YAML/expressions and embedded shell: actionlint 1.7.7 PASS.
  A complete GitHub-hosted build/publish run of the new workflow has NOT RUN.
- User's Fork run (screenshot): ISO build and SHA-256 PASS; BIOS test did not
  start because the runner could not create root-owned `work/qemu-bios`.
  Fixed all host-side evidence/release paths to use `RUNNER_TEMP`.
  Non-root permission reproduction: old path fails as reported; new BIOS/UEFI
  paths save failure evidence; release manifest/JOIN preparation succeeds.
  QEMU was deliberately stubbed to fail in this permission check, so this is
  not a new boot result. Artifact upload now precedes boot tests, preserving a
  clearly experimental download for manual VirtualBox testing; Release still
  requires successful BIOS and UEFI checks. Hosted rerun remains pending.
- Real offscreen Qt: legacy Studio, Control Center, new bilingual Business Studio,
  AI Hub verified test installation/removal and usage display: PASS.
- Five official agent binary `--version` checks on host Linux: PASS; details in AI-HUB.md.
  Account authentication and paid requests: NOT RUN.
- First Desktop UEFI under QEMU TCG 4GiB: original Plymouth visible with progress,
  original Slot-SDDM-6 visible, 9b7 login into DEsk pixman/2D: PASS.
  Firefox, Thunar and legacy Studio windows visible. Source QML corrections and
  new Business Studio/AI Hub are not yet incorporated in a tested final ISO.
- PipeWire services/sink: detected; audible output NOT TESTED (null backend).
  Local network/DHCP/SSH works; external guest Internet NOT VERIFIED.
- New Desktop `9b7-2026.10.18-x86_64-desktop.iso`, source `507d24f`,
  4,108,910,592 bytes: SHA-256 recheck PASS, original Plymouth and Slot-SDDM-6
  visually confirmed under both BIOS and UEFI in QEMU TCG, 4GiB, std VGA.
  UEFI password login, DEsk CPU renderer, and Firefox/Thunar/new Studio window
  creation: PASS. Screenshots in `images/desktop-20261018/`.
  DEsk's first-start preparation overlay was still visible in the app screenshot;
  this does not certify a fully prepared desktop or complete app functionality.
- The first automation attempt guessed the wrong greeter VT. It was interrupted
  while preserving the VMs, then the corrected session checks were resumed.
  UEFI session checks passed. BIOS initially reached DEsk, but a subsequent
  automation attempt after restarting SDDM failed authentication; it is NOT a
  passing complete BIOS automation run. The harness now discovers the greeter VT,
  uses TTY6 and clears the password field. A fresh complete run of the final
  harness is still required and is enforced by the publishing workflow.
- New XFCE/Hyprland session switching, lock/unlock, logout, installation/second
  boot: PENDING. VirtualBox/hardware: UNAVAILABLE.
- Cloud restart stopped VMs and cleared tmpfs roots; Desktop root restored from
  checksum-verified ISO. No earlier runtime process is assumed to have survived.
- No completed public release/download verification. Original Full draft remains
  incomplete. Do not describe either build as a stable final system.

The dated entries below are historical evidence, not the latest release state.

# Validation evidence and release gates

Updated 2026-10-17. QEMU live boot has now been tested. Hardware/VirtualBox and installed-system certification remain pending.

| Check | Result | Evidence / limits |
|---|---|---|
| Core Flow + database + service tests | PASS | 19 tests executed, including split-ISO roundtrip and corrupt/missing-part rejection; money precision, atomic rollback, duplicate/conflict behavior, HTML escaping, read-only SQLite, audit and private state |
| Native Qt GUI | PASS | Offscreen real demo import, expected 8 orders, real SQLite query returning 4 products, screenshot |
| Compose configuration | PASS | Seven selectable stacks parsed by Docker Compose v2.40.3 |
| Shell syntax / ShellCheck | PASS | Current original shell scripts checked, warning severity |
| n8n 2.43.6 | PASS | HTTP health plus imported `automation/n8n-demo.json`, CLI execution `status=success`, `finished=true`, expected output KPIs |
| Metabase 0.64.1 | PASS | PostgreSQL metadata initialized, health=ok, actual sample query `SELECT COUNT(*) FROM ORDERS` returned 18760 |
| Superset 6.1.0 | PASS | Initialization, authenticated login/API, stop/start with retained account |
| Odoo 18 | PASS | Created real database and authenticated user 9b7; fixed config readability |
| ERPNext | BLOCKED IN NESTED RUNTIME | Images pulled; cloud cgroup v2 prevents nested container start. Validate in the booted VM |
| Cassandra / PostgreSQL / Redis console | PASS | Actual driver queries; revenue 39100 checked through PostgreSQL and Redis; Cassandra cluster query succeeded |
| Local Ollama inference | PASS WITH QUALITY LIMITS | Real Ollama 0.40.5 + pinned Qwen 1.5B returned all three Arabic roles and correct demo KPIs. Small model invented a currency; prompt now explicitly forbids this, and human review remains required |
| Extra Arch packages | PASS | Signed VSCodium, Obsidian, Burp, geomet, Cassandra 3.30.1-2 built; real Cassandra import on Arch/Python 3.14 |
| Native archiso profile | PASS | Generated with installed releng and librsvg; actual full ISO built and booted |
| Offline archive mechanism | PASS | Compressed Docker save/load, SHA256 and image ID, then real run with --pull never |
| Model download integrity | PASS | Pinned official Qwen manifest; all blob sizes and SHA256 verified; real native inference passed |
| ISO generation and integrity | PASS | 12,352,876,544 bytes; SHA256 rechecked against sidecar; source 8e538d7 |
| BIOS + UEFI live boot | PASS IN QEMU | 4GiB/2CPU TCG, LightDM, 9b7 login; UEFI Hyprland + Studio and Flow demo verified |
| VirtualBox + laptop boot | NOT RUN | No VirtualBox or target hardware in this environment |
| Whole-disk installation + second boot | NOT RUN | Disposable 80GiB QCOW2 test being prepared; no completed install yet |
| Full offline bundle | PASS | Ten digest-pinned compressed image archives and Qwen model verified; booted offline runtime still pending |

## Artifact and delivery

ISO: `9b7-linux-2026.10.16-x86_64-full.iso` (source `8e538d7130751eeec62af0ca893ed3530bfbec89`).

SHA256: `b84e6627fea5ad1c063930321f7df8d9e7a6e9a75a30378a79113f02a5a43bc3`.

Draft `v0.1.0-rc1` contains metadata and original ISO parts01–04. User-supplied temporary upload credentials resolved the platform credential failure. Upload was paused after discovering the XFCE selection defect; the draft is incomplete and must not be advertised as downloadable. No complete public download verification has passed. Linux Bash and PowerShell7 assembly/rejection tests passed; Windows itself was not tested.

The booted image logs an upstream systemd-loop attempt to dissect its CD-ROM as a partitioned disk (`No suitable partitions found`). The ISO itself mounts and the desktop works. This warning is recorded rather than reported as a clean systemd check.

## Release checklist

- [ ] `scripts/check.sh` and GUI smoke succeed on final commit.
- [x] AUR package builds complete with checksums/signatures; installed package versions recorded.
- [x] `full` bundle contains all declared image digests and verified local model archive.
- [x] `mkarchiso` completes, outputs ISO and SHA256, with no omitted requested component.
- [ ] BIOS boot reaches greeter; login 9b7 succeeds; desktop, keyboard, networking, audio work.
- [x] UEFI boot reaches greeter with Secure Boot disabled.
- [ ] Hyprland on supported physical GPU; XFCE compatibility in VirtualBox VMSVGA.
- [ ] Firefox, VSCodium, Obsidian, Wireshark, Burp, Ansible and btop start.
- [ ] Run Studio demo twice: still 8 orders; imported=0, duplicates=8 on second run.
- [ ] Install to disposable VDI, eject ISO, reboot, then test persistent data and GRUB menu.
- [ ] Disconnect network; start each full-edition stack one at a time and run functional requests.
- [ ] Run three local AI agents and inspect generated figures against report.
- [ ] Record memory/disk usage on the user's 8GB laptop and restore after reboot.
- [ ] Confirm bundled software redistribution terms before a public binary release.

Store large ISO/VM artifacts outside Git. Preserve concise evidence here, not logs containing authentication tokens or credentials.


## Theme request and compatibility correction (17 October)

- The supplied-theme archives `SDDM.zip` and `plymouth theme.zip` are not available in the current workspace, container, Git history or release assets. Original `Slot-SDDM-6` and `arch-slider-and-glow` extraction, licenses, QML imports, visual checks and login tests are **NOT RUN**. No replacement artwork has been substituted for this request.
- User requires a tested **Desktop** ISO before another Full build. No new ISO for these themes has been built or published.
- Actual LightDM parser exposed a configuration precedence defect: the main config overrode the compatibility drop-in. Moving the default session to `50-9b7-default.conf` makes the actual parser select XFCE with the compatibility file and Hyprland without it. The preserved original ISO predates this fix.
- The live VM started whole-disk installation to a newly created, empty 80GiB QCOW2. Formatting and rsync started; copying is paused. Installation and second boot remain **UNVERIFIED**.

- Reused-guest login still selected its previous Hyprland session despite the corrected parser default. Fresh-boot XFCE login and cached-session selection remain to be checked; parser success is not counted as a graphical XFCE pass.

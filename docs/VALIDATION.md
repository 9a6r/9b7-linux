# Validation evidence and release gates

Updated 2026-10-16. These results concern this development environment, not an ISO boot certification.

| Check | Result | Evidence / limits |
|---|---|---|
| Core Flow + database + service tests | PASS | 15 tests executed; money precision, atomic rollback, duplicate/conflict behavior, HTML escaping, read-only SQLite, audit and private state |
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
| Native archiso profile | PASS | Generated with installed releng and librsvg; ISO build/boot still pending |
| Offline archive mechanism | PASS | Compressed Docker save/load, SHA256 and image ID, then real run with --pull never |
| Model download integrity | PASS | Pinned official Qwen manifest; all blob sizes and SHA256 verified; inference pending |
| ISO generation | PENDING | No ISO yet |
| BIOS + UEFI live boot | NOT RUN | Requires generated ISO |
| VirtualBox + laptop boot | NOT RUN | Requires generated ISO and target hardware |
| Whole-disk installation + second boot | NOT RUN | Installer is not certified; first test must use a disposable virtual disk |
| Full offline bundle | PASS | Ten digest-pinned compressed image archives and Qwen model verified; booted offline runtime still pending |

## Release checklist

- [ ] `scripts/check.sh` and GUI smoke succeed on final commit.
- [ ] AUR package builds complete with checksums/signatures; installed package versions recorded.
- [x] `full` bundle contains all declared image digests and verified local model archive.
- [ ] `mkarchiso` completes, outputs ISO and SHA256, with no omitted requested component.
- [ ] BIOS boot reaches greeter; login 9b7 succeeds; desktop, keyboard, networking, audio work.
- [ ] UEFI boot reaches greeter with Secure Boot disabled.
- [ ] Hyprland on supported physical GPU; XFCE compatibility in VirtualBox VMSVGA.
- [ ] Firefox, VSCodium, Obsidian, Wireshark, Burp, Ansible and btop start.
- [ ] Run Studio demo twice: still 8 orders; imported=0, duplicates=8 on second run.
- [ ] Install to disposable VDI, eject ISO, reboot, then test persistent data and GRUB menu.
- [ ] Disconnect network; start each full-edition stack one at a time and run functional requests.
- [ ] Run three local AI agents and inspect generated figures against report.
- [ ] Record memory/disk usage on the user's 8GB laptop and restore after reboot.
- [ ] Confirm bundled software redistribution terms before a public binary release.

Store large ISO/VM artifacts outside Git. Preserve concise evidence here, not logs containing authentication tokens or credentials.

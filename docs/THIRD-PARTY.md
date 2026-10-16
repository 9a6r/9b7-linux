# Provenance and licensing

Original 9b7 Python code, shell automation, artwork and documentation use the repository MIT license. Upstream software retains its own license; a package being downloadable does not make it MIT or grant unlimited redistribution rights.

| Component | Source | License / note |
|---|---|---|
| Arch / archiso releng | https://gitlab.archlinux.org/archlinux/archiso | GPL-3.0-or-later; profile copied from installed archiso at build time |
| Hyprland | https://github.com/hyprwm/Hyprland | BSD-3-Clause; Omarchy-inspired workflow, original 9b7 config |
| Omarchy inspiration | https://github.com/basecamp/omarchy | MIT; no claim of affiliation or copied installer |
| Qt / PySide6 | https://www.qt.io/qt-for-python | LGPL/GPL/commercial options; dynamically linked distribution |
| ERPNext Docker recipe | https://github.com/frappe/frappe_docker/blob/main/pwd.yml | MIT recipe adapted; ERPNext itself GPL-3.0 |
| n8n | https://github.com/n8n-io/n8n | Sustainable Use License and enterprise components; not conventional unrestricted open source |
| Apache Superset | https://github.com/apache/superset | Apache-2.0 |
| Metabase | https://github.com/metabase/metabase | AGPL community edition; other editions have separate terms |
| Odoo | https://github.com/odoo/odoo | LGPL community core; addon licenses vary |
| Ollama / Qwen2.5 1.5B | https://github.com/ollama/ollama / https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | MIT / Apache-2.0 for the selected 1.5B model; verify model manifest |
| VSCodium | https://github.com/VSCodium/vscodium | MIT; third-party notices preserved by package |
| Obsidian | https://obsidian.md/license | Proprietary; personal use availability does not itself authorize public ISO redistribution |
| Burp Suite Community | https://portswigger.net/burp/eula | Proprietary; preserve EULA and check redistribution terms before publishing binary ISO |
| AUR recipes | https://github.com/archlinux/aur | Reviewed refs in packaging/aur-lock.json; no unpinned AUR helper install |

The repository contains build instructions, not redistributed proprietary binaries. Before a public ISO release, confirm rights for Obsidian and Burp or distribute a community ISO with their official download/install instructions instead. Keep `/usr/share/licenses`, package manifest, corresponding GPL source links and build scripts with the release. Do not describe all bundled tools as open source.

The original Frappe Docker MIT notice is preserved verbatim in [docs/licenses/frappe-docker-MIT.txt](licenses/frappe-docker-MIT.txt).

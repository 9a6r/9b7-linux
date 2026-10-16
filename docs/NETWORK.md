# Setup network destinations

The existing package-manager preset is retained. Additional destinations saved in the cloud draft:

- `archlinux.org`, `aur.archlinux.org`, `geo.mirror.pkgbuild.com`, `fastly.mirror.pkgbuild.com`, `archive.archlinux.org`: signed Arch packages, packaging metadata and mirrors.
- `portswigger.net`, `portswigger-cdn.net`: Burp Community artifacts referenced by the pinned AUR recipe.
- `ollama.com`, `registry.ollama.ai`, `*.r2.cloudflarestorage.com`: local model distribution and signed model blob redirects.

Already covered by package-manager/GitHub presets: GitHub, raw GitHub, release-assets.githubusercontent.com, PyPI/files.pythonhosted.org, Docker registry/auth/CDN.

Do not disable TLS, GPG checks, or replace expected artifact hashes to work around network errors. Draft save is not runtime policy application. After environment settings are saved/published, retry the exact failed operation before claiming access works.

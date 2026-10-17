# DEsk integration — experimental Desktop track

The October 17 decision makes DEsk the primary desktop for the experimental
Desktop ISO. XFCE remains a recovery session. Hyprland stays installed until
real application and session tests justify its removal.

## Provenance and licenses

* DEsk: https://github.com/fyzugx/DEsk, v0.1.2, commit
  `195435a09b9343e49b12e8dd8838a6e579a9aaa4`, MIT, 2026 the DEsk authors.
  There is **no stable release**; upstream marks it BETA. Original compositor,
  room, application library, icons and GTK theme are retained.
* Arch has moved beyond the required wlroots ABI. `packaging/9b7-desk/PKGBUILD`
  builds verified wlroots **0.18.3** under `/opt/9b7/desk-wlroots`, without
  replacing Arch's libraries. Both source archives have fixed SHA-256 values;
  licenses are installed in the signed package. No upstream installer is run.
* User `SDDM.zip`: SHA-256
  `0e00acd03eb4206c10c8e1312c5329c582e0c8bd4ecefe00d7ea1aaba856c2e7`.
  Member `SDDM/SDDM` is a TAR. Original Slot-SDDM-6 QML/artwork are vendored
  under `iso/airootfs/usr/share/sddm/themes/Slot-SDDM-6`. Metadata declares
  **GPLv3**, author **l4k1**, version 1.0. The missing full license text is
  supplied in `usr/share/licenses/Slot-SDDM-6`. Only `theme.conf.user` adds
  the 9b7 greeting and allows the requested username. Original hashes: packaging.
* User `plymouth theme.zip`: SHA-256
  `570c4f08a483148cb5c36f8f0927f16cb08ba01feb510ffc7d8ffa1a350e21d5`.
  **arch-slider-and-glow**, MIT, 2026 Hasan Agit Ünal. Original two-step
  definition, animation frames and license are vendored. `install.sh` is
  excluded and was never executed. Previous 9b7 artwork remains in source.

## Sessions and recovery

SDDM uses Slot on X11, with software Qt Quick rendering for VMs. It offers
DEsk, DEsk 2D, XFCE and retained Hyprland. First login selects DEsk; compatibility
boot selects XFCE. SDDM remembers subsequent choices. DEsk automatically selects
CPU/pixman in VMs. From Ctrl+Alt+F3, log in and run
`sudo 9b7-display-manager lightdm` for recovery. The reverse command selects
SDDM. Switching ends graphical sessions.

Plymouth's original theme is selected before initramfs generation. Both live
and installed initramfs include plymouth; normal boot has quiet/splash.
Compatibility boot leaves text diagnostics available.

## Applications and language

9b7 Control Center is a separate Qt application for system tools/status,
services, databases, AI agents and Flow. It reuses Studio's existing actions;
Studio remains independently launchable. DEsk's drawer/shelves include Studio,
Flow, Control Center, Firefox, Thunar, VSCodium and on-demand service launchers.
No heavy service starts on login, for the target 8GB laptop.

US/Arabic keyboard layouts use Alt+Shift; Noto and URW fonts are installed.
**Upstream has no Arabic shell translation.** Its Cairo toy text API also lacks
full Arabic shaping/bidi. This release uses English shell text; Qt/GTK Arabic
and keyboard input must be tested independently. Full shell translation needs
a reviewed Pango/bidi change before translating labels.

Super+A apps, Super+D drawer, Super+C DEsk settings, Super+L lock,
Super+Enter terminal, Super+N notifications. Control Center is in the drawer.
DEsk supplies its own notification server; mako remains Hyprland-only.

## Validation gate

Package/ISO build success is not a session test. Record actual boot/login,
apps, lock/unlock, logout, notifications, network and audio in VALIDATION.md.
Desktop must pass boot tests before rebuilding Full. VirtualBox and physical
hardware are unverified until actually used.

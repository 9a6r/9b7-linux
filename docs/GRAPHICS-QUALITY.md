# Graphics correction — 19 October 2026 (Cairo)

Scope: the supplied Plymouth background and DEsk's rendering/display quality.
The original Arch logo, progress frames, SDDM theme, DEsk visual design, apps,
XFCE and Hyprland are retained. No Full image was rebuilt for this change.

## Plymouth: reproduce and fix the seam

The supplied background is 1366×768. Plymouth's two-step plugin tiles it by
default. At 1280×800 it repeats along the bottom; at 1920×1080 it repeats on
both axes. `ScaleBackgroundImage=true` makes the plugin resize that same
background to the display. All **152 original resource files** match the
SHA-256 provenance manifest; no replacement artwork was generated.

These are screenshots of Arch Plymouth **26.134.222-3**, using its real
two-step plugin and X11 renderer on Xvfb, captured with xwd and converted to PNG.
Both runs used the same supplied resources and theme; only the scale flag
differed. Logs confirm 94 animation frames and 51 progress frames loaded.

| Output | Before | After |
|---|---|---|
| 1280×800 | [Repeated bottom edge](images/graphics-20261019/plymouth-before-1280x800.png) | [Background fits](images/graphics-20261019/plymouth-after-1280x800.png) |
| 1920×1080 | [Repeated right/bottom edges](images/graphics-20261019/plymouth-before-1920x1080.png) | [Background fits](images/graphics-20261019/plymouth-after-1920x1080.png) |

The Arch logo and progress bar remain centered and visible. This tests rendering,
**not a new BIOS/UEFI boot or initramfs**. The existing ISO build selects this
theme before generating initramfs for both boot paths; the next Desktop build
still has to pass the workflow's actual BIOS/UEFI checks.

## DEsk: retain detail and permit acceleration

The 9b7 session wrapper previously forced pixman/CPU for every VM. Normal DEsk
now leaves renderer selection to wlroots; the explicit **DEsk 2D** recovery
session still forces software rendering. The machine default is High instead
of Medium. DEsk's upstream CPU detection selects 2D unless the user explicitly
chooses a graphics level in their own settings.

Upstream's 2D scene was rendered at a width cap of 640 and enlarged to fit the
screen. The checksummed downstream patch in `9b7-desk 0.1.2-2` raises that cap
to **1280**, retaining one sample per pixel and disabled heavy effects. The
scene cache names include dimensions, so a cached 640px room cannot masquerade
as the new 1280px room. CPU preparation costs more; the cap avoids forcing
full 1080p/4K ray tracing on the target 8GB machine. It is not equivalent to
accelerated High at all resolutions.

Actual headless DEsk sessions with pixman at 1280×800 were captured using grim:

| Before | After |
|---|---|
| [640px scene enlarged](images/graphics-20261019/desk-before.png) | [1280px scene](images/graphics-20261019/desk-after.png) |

The room logs report `640x402 at 2D, 1 sample a pixel` before and
`1280x804 at 2D, 1 sample a pixel` after. The initial room took 2.5s and 6.4s
respectively on this cloud CPU; these are **not VirtualBox performance figures**.
The screenshots were taken after the preparation overlay closed; clock and
notification contents differ because the sessions ran at different times.

## Resolution and checks

`wdisplays` (1.1.3-2) and `wlr-randr` (0.5.0-1) are in the ISO package list.
Display Settings is in the DEsk drawer; XFCE keeps its own display settings.
The launcher passed `desktop-file-validate`.

- Clean `makepkg --cleanbuild` through `scripts/build-desk-package.sh`: PASS.
  Both pinned source hashes and the patch hash passed; the new package and
  repository database were signed; the package signature verified successfully.
- Session wrapper tested with a temporary session stub in the dedicated builder:
  normal mode leaves CPU variables unset, explicit `--2d` sets them, and other
  arguments reach the upstream session script: PASS.
- New DEsk binary, machine High config, no user graphics override, headless
  pixman: automatically selects 2D: PASS.
- Live `wlr-randr` change from 1280×800 to 1366×768 at scale 1: PASS; DEsk
  applied the mode and saved `displays.conf`.
- `wdisplays` opened a Wayland window inside DEsk as the ordinary builder user:
  PASS ([actual screenshot](images/graphics-20261019/display-settings.png)).
  An initial root-run test failed in the GTK/glycin image loader's sandbox;
  rerunning as an ordinary user succeeded with the sandbox enabled. No sandbox
  override was added to the ISO or launcher.
- 35 Python tests, shell syntax/ShellCheck, seven Compose configurations: PASS.

Use VMSVGA, 128MB video memory, 4096MB RAM and two CPUs. Enable VirtualBox 3D
for the accelerated quality trial; if it fails, disable it and select DEsk 2D
or XFCE. Keep VirtualBox Scale Factor at 100% and turn Scaled Mode off. Select
the guest's actual resolution in Display Settings instead of enlarging a
low-resolution guest image. See [Arabic instructions](BUILD.ar.md#virtualbox).

**Not run for this revision:** a new ISO build/boot, VirtualBox 3D, physical GPU,
installation, or a fresh full login/apps/audio/lock acceptance suite. The
renderer checks above do not replace those tests. Build Desktop from the updated
main through Actions; on a fork, Sync fork then start a new workflow run.

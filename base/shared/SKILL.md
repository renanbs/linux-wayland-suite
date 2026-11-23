---
name: linux-wayland-suite
description: Comprehensive Linux Wayland configuration suite for KDE Plasma, GNOME, and multi-vendor hardware: keyboard shortcuts repair, Tongfang/Avell/Clevo matrix unlocking, smart dynamic keyboard power management, native cedilla on US-intl via the native pt_BR compose table (LC_CTYPE, no input method), Wayland clipboard repair, 3/4-finger touchpad gestures, Logitech MX Master 3S button/scroll configuration via logiops, battery/power diagnostics, and a read-only fan RPM/temperature sensor for Uniwill/Tongfang ECs over ACPI-WMI.
---

# Linux Wayland Suite (Input, Hardware & Desktop Automation)
This skill provides automations and diagnostics to resolve common problems in the input stack and clipboard of **KDE Plasma 6 (Wayland)**:

1. **Keyboard Shortcut Repair (`Ctrl+C` on ABNT2)**: Eliminates legacy `im-cedilla` module that grabs keystrokes and breaks `Ctrl+C` under Wayland.
2. **Native Cedilla on US-intl (`dead_acute + c` $\to$ `ç` in Chrome, Orca IDE, Electron, GTK, Qt)**:
   - **Desktop & Toolkit Level:** Achieved **without any input method** via `LC_CTYPE=pt_BR.UTF-8` in `~/.config/environment.d/cedilla.conf` (+ `systemd --user set-environment` and `~/.config/fish/conf.d/cedilla.fish`), leveraging the system compose table (`/usr/share/X11/locale/pt_BR.UTF-8/Compose`) for Qt, GTK, Konsole, and Kate.
   - **Chromium & Electron Native Wayland Patcher (`patch-cedilla`):** Resolves the upstream Chromium `ui::CharacterComposer` bug (Issue 40272818) where `<dead_acute> + c` is hardcoded to `ć`. Powered by the upstream byte-pattern engine by **Leandro Cassa** ([lcassa/chromium-wayland-cedilla-fix](https://github.com/lcassa/chromium-wayland-cedilla-fix)), `./bin/linux-wayland-config patch-cedilla --apply` directly patches Google Chrome, Orca IDE, VS Code, Discord, Brave, and Antigravity binaries, and registers `/etc/pacman.d/hooks/99-cedilla-wayland.hook` for automatic post-upgrade autorepair.
3. **Wayland Clipboard Deadlock Repair (`Ctrl+Shift+V` / Images)**: Cleans up zombie `xsel` processes and ensures native `wl-clipboard` (`wl-copy`/`wl-paste`) operation in Konsole and shells.
4. **Portable Touchpad Gestures**: Maps 3 and 4-finger gestures complementary to KWin via `libinput-gestures` and D-Bus (`qdbus6`), without concurrency conflicts with native Plasma gestures.
5. **General Diagnostics and Verification**: Real-time auditing of session state, active layouts, clipboard health, browser flags, composition validation, and daemon status.
6. **Logitech MX Master 3S (`logiops`/`logid`)**: Installs `logiops`, generates `~/.config/logid.cfg` (symlinked to `/etc/logid.cfg`, editable without sudo), maps the thumb gesture button to workspace switching / Overview / Show Desktop, and locks SmartShift into free-spin scrolling. Also enables `kwinrc [Windows] PerOutputVirtualDesktops=true` for multi-monitor setups.
7. **Battery and Power Diagnostics & Optimization**: `diagnose-battery.sh` audits compositor primary GPU on hybrid Intel/NVIDIA/AMD laptops, PCIe ASPM policies, PCI runtime power management, battery health, and idle radios (read-only). `configure-battery.sh` applies user-selected fixes (`BATTERY_FIX_GPU_PRIMARY`, `BATTERY_FIX_PCIE_ASPM`, `BATTERY_FIX_PCIE_ASPM_PERSIST`, `BATTERY_FIX_PCI_RUNTIME_PM`, `BATTERY_FIX_PCI_RUNTIME_PM_PERSIST`) with automatic backup snapshots; `revert-battery.sh` rolls back snapshots.
8. **KWin `kxkbrc` Collapse Bug Detection**: `check-status.sh` detects when Plasma overwrote `~/.config/kxkbrc` retaining only the layout active at logout time. `fix-keyboard.sh` repairs the file immediately and can optionally install an autostart hook (`KDE_SUITE_LAYOUT_AUTOHEAL=1`) to re-apply the dual layout on every login.
9. **System-wide Ctrl Key Lockup Prevention**: Prevents keymap compilation failures when `LayoutList` and `VariantList` element counts mismatch during live KWin reloads.
10. **fcitx5 Key Grabbing Deactivation**: Masks system-level autostarts (`/etc/xdg/autostart/org.fcitx.Fcitx5.desktop`) with `Hidden=true` in `~/.config/autostart/` to prevent fcitx5 from swallowing Ctrl combinations under Wayland.
11. **Tongfang / Avell / Clevo Hardware Matrix Fix**: Unlocks the physical Control/Fn matrix on Tongfang chassis via GRUB kernel parameters (`i8042.nopnp=1 i8042.nomux=1 i8042.reset=1 acpi_osi='Windows 2020'`).
12. **Smart Dynamic Keyboard Power Management (`smart-keyboard-power`)**: Dynamic udev rule (`/etc/udev/rules.d/90-kde-smart-keyboard-power.rules`) keeping `power/control = on` (zero latency) when standalone, and switching to `auto` (power saver) when external keyboards connect.
13. **Smart Dynamic Wi-Fi Power Management (`smart-wifi-power`)**: Dynamic udev rule (`/etc/udev/rules.d/90-linux-wayland-smart-wifi-power.rules`), NetworkManager dispatcher, and sleep hook keeping 802.11 power saving off and PCIe awake on AC power (eliminating radio sleep and packet timeouts for Orca/SSH), while enabling full power saving on battery.
14. **Machine Profiling & Modular Setup (`/init` & `/setup`)**: `/init` (or `/scan`) performs non-destructive hardware inspection saving `~/.config/linux-wayland-suite/machine-profile.json`. `/setup` uses this profile to offer a contextual configuration wizard tailored to detected hardware.
15. **Tongfang S3 Deep Sleep Resume Fix**: Hook in `/etc/systemd/system-sleep/90-kde-keyboard-resume.sh` issuing `rescan` to `/sys/devices/platform/i8042/serio0/drvctl` upon lid open.
16. **Structured Event Logs and Historical Reporting**: Every execution records a run in `~/.local/state/linux-wayland-suite/runs/<timestamp>-<cmd>/` with `events.tsv`, `output.log`, and `meta.env`. `report` parses structured events to produce reproducible reports and actionable remediation advice.
17. **Uniwill/Tongfang Fan RPM Sensor (`fan-sensor`)**: Read-only hwmon driver (`uniwill-ec-hwmon-dkms`, published on AUR) for ECs that are only reachable through the `AcpiTest_MULong` ACPI-WMI bridge (`ABBC0F6F-8EA1-11D1-00A0-C90629100000`, method 4) because the BIOS does not expose `INOU0000` — exactly the case where the in-tree `uniwill-laptop` driver cannot probe. Exposes `fan1_input`/`fan2_input` (RPM), `temp1_input`/`temp2_input` (CPU/GPU) and `pwm1`/`pwm2` to `sensors`, `coolercontrol` and any hwmon consumer; it never writes to the EC. `fan-sensor status|install|uninstall` manages the DKMS package, `/setup` offers it as option `F`, and `/init` records `uniwill_ec_wmi`, `uniwill_inou0000_present` and `uniwill_hwmon_present` in `machine-profile.json`.
> **Evidence-First Verdict Output Format**: Every command in this suite reports in the format defined in `OUTPUT-CONTRACT.md` (**Verdict** $\to$ **Execution Breakdown** $\to$ **Ground Truth Evidence** $\to$ **Daily Impact** $\to$ **Action Required**), identical across Claude Code, Cursor, OMP, OpenCode, and Antigravity.

> **Internationalization & Translation**: Internally, all commands, skills, contracts, and runlogs are maintained in English. The AI agent translates explanations and interaction dialogues into the user's selected language (`en` or `pt-BR`) as configured.

---

## Guided `init` Workflow (Mandatory for AI Agents)

`init` configures multiple subsystems at once (language, keyboard, gestures, mouse, power, harness). **Never run `init` blindly.** Before executing any command, use `AskUserQuestion` (or `ask`) to prompt the user with all questions in a single turn:

### Question 1 — Language Preference (`language`) (singleSelect):
- **"English (en) (Recommended)"** — Standard English. Internal operations remain canonical English.
- **"Português do Brasil (pt-BR)"** — Brazilian Portuguese. Internal operations remain in English; the AI will translate user-facing messages and reports to Portuguese.
### Question 2 — Components (`components`) (multiSelect):
- **"Keyboard, desktop shortcuts, and native compose (Ctrl+C ABNT2, US-intl native ç for Qt/GTK)"** — Recommended.
- **"Wayland Cedilla Patch for Chromium & Electron (Chrome, Orca, VS Code, Discord, Brave: '+c -> ç)"** — Recommended if Chromium/Electron apps are used (powered by Leandro Cassa's byte patcher + Pacman hook) [Requires sudo].
- **"Touchpad gestures (3/4 fingers via libinput-gestures)"** — Recommended if touchpad is present.
- **"Logitech MX Master 3S mouse (logiops / logid)"** — Only if the user has this mouse.
- **"Battery / power consumption diagnostic"** — Recommended (read-only diagnostic within init; no fixes applied yet).

### Question 3 — Layout Auto-Heal on Login (`autoheal`) (singleSelect):
- **"Yes, protect against KWin/Plasma layout collapse bug (Recommended)"** — Installs autostart hook that re-applies dual layout on every login.
- **"No, manual layout management"** — Skips autostart hook.

### Question 4 — AI Host Profile & Model Roles (`harness`):
- Automatically aligns with active host (OMP, Claude Code, Cursor, Antigravity) and configures model role mapping.

### Mapping Answers to Command Execution:

```bash
# Example: Language English, user does not have mouse, wants other components and auto-heal
KDE_SUITE_LANG=en SKIP_MOUSE=1 KDE_SUITE_LAYOUT_AUTOHEAL=1 ./bin/kde-config init

# Example: Language pt-BR, user only wants keyboard and battery diagnostic
KDE_SUITE_LANG=pt-BR SKIP_GESTURES=1 SKIP_MOUSE=1 ./bin/kde-config init
```

The environment variables `KDE_SUITE_LANG`, `SKIP_KEYBOARD`, `SKIP_GESTURES`, `SKIP_MOUSE`, and `SKIP_BATTERY` control each stage. The selected language is saved in `~/.config/linux-wayland-suite/harness-profile.json`.

### Battery: Diagnostic Inside `init`, Fixes Applied Separately

`init` only runs `battery-status` (read-only). **Never pass `BATTERY_FIX_*` during `init`**. Once diagnostics appear in the output, explain findings to the user and prompt with `AskUserQuestion` to decide which optimizations to apply, only then executing `./bin/kde-config battery-apply` with corresponding flags.

---

## Available Scripts & Commands

| Script / Command | Description |
| :--- | :--- |
| `shared/profile-machine.sh` | Non-destructive machine profiling and hardware inspection |
| `shared/setup-suite.sh` | Contextual modular configuration wizard based on machine profile |
| `shared/manage-wifi-power.sh` | Dynamic Wi-Fi power management (AC vs Battery) |
| `shared/check-status.sh` | Full audit of environment, keyboard, native cedilla, Wayland clipboard, IM variables, gestures, Wi-Fi |
| `shared/fix-keyboard.sh` | Repairs `Ctrl+C`, native US-intl cedilla, clipboard deadlocks, hot-reloads KWin |
| `shared/configure-gestures.sh` | Setup of `libinput-gestures.conf` and service restart |
| `shared/configure-mouse.sh` | Installs `logiops` and configures MX Master 3S (gesture button, SmartShift) |
| `shared/diagnose-battery.sh` | Read-only battery/power diagnostics: primary GPU, PCIe ASPM, battery health, idle radios |
| `shared/configure-battery.sh` | Applies user-chosen battery optimizations (`BATTERY_FIX_*`) with backup snapshot |
| `shared/revert-battery.sh` | Reverts the last application of `configure-battery.sh` (or specific snapshot) |
| `shared/fix-tongfang.sh` | Unlocks keyboard matrix on Tongfang/Avell/Clevo laptops via GRUB |
| `shared/test-keyboard.py` | Interactive real-time key event monitor (/dev/input/eventX) |
| `shared/monitor-irq.py` | Hardware electric pulse monitor on IRQ 1 (i8042 keyboard) |
| `shared/manage-keyboard-power.sh` | Dynamic keyboard power management (on standalone, auto with USB/BT keyboard) |
| `shared/manage-uniwill-hwmon.sh` | Read-only fan RPM/temps sensor for Uniwill/Tongfang ECs over ACPI-WMI (`status`/`install`/`uninstall`, DKMS) |
| `shared/preflight-base.sh` | Preflight checks for environment, DMI hardware, Plasma version, and D-Bus tools |
| `bin/linux-wayland-config switch [br\|us]` | Immediate keyboard layout switching via D-Bus |
| `bin/linux-wayland-config set-lang [en\|pt-BR]` | Saves user language preference |
| `bin/linux-wayland-config screen-hz [60\|120]` | Switches internal display refresh rate |
| `bin/linux-wayland-config fan-sensor [status\|install\|uninstall]` | Manages the Uniwill/Tongfang EC fan RPM/temp sensor (read-only hwmon, DKMS) |
---

## Quick CLI Usage

```bash
# Machine profiling & scan (safe, read-only)
./bin/linux-wayland-config init

# Contextual modular configuration wizard
./bin/linux-wayland-config setup

# Full health audit
./bin/linux-wayland-config status

# Enable dynamic smart Wi-Fi power management (AC vs Battery)
./bin/linux-wayland-config smart-wifi-power --apply

# Switch internal screen refresh rate (60 Hz vs 120 Hz)
./bin/linux-wayland-config screen-hz 60

# Apply keyboard, cedilla, and clipboard fix
./bin/linux-wayland-config fix-keyboard

# Unlock keyboard matrix on Tongfang/Avell laptops (GRUB)
./bin/linux-wayland-config fix-tongfang

# Enable dynamic smart keyboard power management
./bin/linux-wayland-config smart-keyboard-power --apply

# Apply touchpad gestures
./bin/linux-wayland-config gestures

# Configure Logitech MX Master 3S mouse
./bin/linux-wayland-config mouse

# Battery / power diagnostic (read-only)
./bin/linux-wayland-config battery-status

# Apply user-selected battery fix
BATTERY_FIX_GPU_PRIMARY=1 ./bin/linux-wayland-config battery-apply

# Revert last battery optimization
./bin/linux-wayland-config battery-revert

# Switch active layout
./bin/linux-wayland-config switch br
./bin/linux-wayland-config switch us
```

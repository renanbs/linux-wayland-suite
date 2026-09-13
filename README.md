# KDE Plasma 6 Wayland Suite: Input, Hardware & Keyboard Repair

[![Language: English](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Language: Português](https://img.shields.io/badge/Idioma-Portugu%C3%AAs%20do%20Brasil-green.svg)](README.pt-BR.md)
[![KDE Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6-blue.svg)](https://kde.org/plasma-desktop/)
[![Wayland Ready](https://img.shields.io/badge/Wayland-Native-success.svg)](https://wayland.freedesktop.org/)
[![Multi-Harness Plugin](https://img.shields.io/badge/AI%20Harnesses-OMP%20%7C%20Claude%20%7C%20Cursor%20%7C%20Antigravity%20%7C%20OpenCode-purple.svg)](#-installation--ai-tools-integration)
[![Version](https://img.shields.io/badge/Version-2.12.0-brightgreen.svg)](package.json)

**[English](README.md)** | **[Português do Brasil](README.pt-BR.md)**

A portable automation suite, diagnostic toolkit, and multi-agent AI plugin for **KDE Plasma 6 (Wayland)**. It repairs broken keyboard shortcuts, resolves dead modifier keys on Tongfang/Avell laptops, manages smart keyboard power, configures native dead-key cedilla (`ç`) on US-intl without input methods, handles Wayland clipboard deadlocks, sets up smooth 3/4-finger touchpad gestures, configures Logitech MX Master 3S mice, and audits battery consumption.

Compatible as a native plugin for **Oh My Pi (OMP)**, **Claude Code**, **Cursor IDE & CLI**, **Google Antigravity**, and **OpenCode**, as well as a standalone terminal CLI (`kde-config`) and `Makefile`.

---

## 🎯 Problems Solved & Features

### 1. Tongfang / Avell / Clevo Hardware Keyboard Matrix Fix
* **Problem:** On laptops using Tongfang chassis (Avell A62 LIV, GK5, GM5, Tuxedo Pulse, Schenker), the physical `Left Ctrl` key generates zero input events in `evtest`/`xev` because the Linux `i8042` driver and ACPI DSDT drop packets from I/O port `0x60`.
* **Fix:** `./bin/kde-config fix-tongfang` injects `i8042.nopnp=1 i8042.nomux=1 i8042.reset=1 atkbd.reset=1 acpi_osi='Windows 2020'` into GRUB, unlocking the full matrix.

### 2. Smart Dynamic Keyboard Power Management (`anti-latch`)
* **Problem:** Under Linux Runtime Power Management, the PS/2 `serio0` port enters idle sleep (`power/control = auto`), causing the first single-byte modifier press (`Left Ctrl`) to lag while waking the bus.
* **Fix:** `./bin/kde-config smart-keyboard-power --apply` installs a dynamic udev rule that keeps the bus in `power/control = on` (zero latency) when using the laptop standalone, and automatically switches to `auto` (power saver) whenever an external USB/Bluetooth keyboard is connected.
### 3. Smart Dynamic Wi-Fi Power Management (`smart-wifi-power`)
* **Problem:** Under default power saving policies, Wi-Fi radios (`iwlwifi`, etc.) sleep between beacon intervals and the PCIe bus enters `D3hot`. When accessing the machine remotely (e.g. Orca IDE on port `6768`, SSH, streaming), incoming connections experience high initial latency, dropped packets, or connection timeouts.
* **Fix:** `./bin/linux-wayland-config smart-wifi-power --apply` installs a dynamic udev rule, NetworkManager dispatcher, and sleep hook:
  - **On AC (Charger):** Automatically disables 802.11 power saving (`power_save off`) and keeps PCIe bus awake (`power/control = on`) for zero latency and rock-solid incoming connections.
  - **On Battery:** Automatically re-enables 802.11 power saving (`power_save on`) and PCIe runtime PM (`power/control = auto`) for maximum battery life.

### 4. CPU Turbo Boost Management & Thermal Watchdog (`turbo`)
* **Problem:** Laptops with high-TDP processors under sustained load or looping background processes (e.g. hung Chromium/Electron renderers, runaway webviews) lock CPU frequencies at 4.0+ GHz. Power draw climbs to 60W+, triggering aggressive fan noise and temperatures reaching 85°C–90°C.
* **Fix:** `./bin/linux-wayland-config turbo` provides hardware-agnostic control (Intel `intel_pstate` & AMD `cpufreq/boost`) to toggle between Quiet/Cool mode (base clock, ~50°C, silent fans) and High Performance mode. Includes an in-memory Runaway Watchdog scanning `/proc` in ~15ms to catch looping processes, and an optional systemd boot persistence unit.

### 5. Broken `Ctrl+C` / `Ctrl+<key>` Shortcuts in ABNT2 (`br`)
* **Problem:** Legacy input method modules (`GTK_IM_MODULE=cedilla` / `QT_IM_MODULE=cedilla`) or running `fcitx5` under Wayland grab the keyboard and swallow Ctrl key combinations across Qt, GTK, and Electron apps.
* **Fix:** Eliminates legacy IM environment variables and masks the `fcitx5` system autostart.

### 6. Native Cedilla on US-intl (`' + c` $\to$ `ç` in Qt, GTK, Chrome, Orca IDE, Electron)
* **OS-Level Problem:** The default `en_US` compose table maps `<dead_acute> <c>` to `ć` (c-acute).
* **OS-Level Fix (`fix-keyboard`):** Native composition **without any input method**. The system's pt_BR compose table (`/usr/share/X11/locale/pt_BR.UTF-8/Compose`) already maps `<dead_acute> <c>` to `ç`. The suite configures `LC_CTYPE=pt_BR.UTF-8` in `~/.config/environment.d/cedilla.conf` for Qt, GTK, and Konsole.
* **Chromium/Electron Wayland Problem:** Under native Wayland (`--ozone-platform=wayland`), Chromium and Electron apps bypass `libxkbcommon` and system compose tables, using an internal `ui::CharacterComposer` table that hardcodes `<dead_acute> <c>` $\to$ `ć` (Chromium Issue 40272818).
* **Binary Patch & Pacman Autorepair (`patch-cedilla`):** Powered by the upstream byte-pattern patch created by [Leandro Cassa](https://github.com/lcassa/chromium-wayland-cedilla-fix) (`chromium-cedilla-patch` on AUR). `./bin/linux-wayland-config patch-cedilla --apply` executes the byte-pattern replacement (`63 00 07 01` $\to$ `63 00 e7 00`) directly on installed Chromium/Electron ELF binaries and registers `/etc/pacman.d/hooks/99-cedilla-wayland.hook`. Whenever `pacman` or `paru` upgrades any browser or Electron package, the patch is automatically reapplied post-transaction.
  - **Google Chrome** (`/opt/google/chrome/chrome`)
  - **Orca IDE** (`/usr/lib/electron43/electron`)
  - **Visual Studio Code** (`/usr/share/code/code`)
  - **Discord** (`~/.config/discord/app-*/Discord`)
  - **Google Antigravity Platform & IDE** (`/opt/Antigravity/antigravity`, `/opt/antigravity-ide/antigravity-ide`)
  - **Brave Browser** (`/opt/brave-bin/brave`)
  - **System Electron Runtimes** (`electron37`, `electron39`, `electron40`, `electron42`, `electron43`)

### 7. Wayland Clipboard Deadlock Repair
* **Problem:** Zombie `xsel` processes freeze terminal clipboard pipelines.
* **Fix:** Cleans hung processes and ensures native `wl-clipboard` (`wl-copy`/`wl-paste`) backend operation.

### 8. Conflict-Free 3 & 4-Finger Touchpad Gestures
* **Fix:** Maps 3-finger (swipe workspaces, overview) and 4-finger gestures complementary to native KWin 1:1 animations via `libinput-gestures` and KWin D-Bus (`qdbus6`).

### 9. Logitech MX Master 3S Button & Scroll Configuration
* **Fix:** Installs `logiops`, configures the thumb gesture button for Desktop Grid and Overview, fixes SmartShift free-spin mode, and enables `PerOutputVirtualDesktops=true` for multi-monitor setups.

### 10. Battery & Hybrid GPU Power Diagnostics
* **Fix:** Audits primary GPU compositor selection on Intel/NVIDIA/AMD hybrid laptops, PCIe ASPM policies, PCI runtime power management, and battery health (`battery-status`).

### 11. AI Host Harness Detection & Model Role Profiling
* **Fix:** Dynamically detects host agents (OMP, Claude Code, Cursor, Antigravity), maps model roles (Reasoning, Code, Review, Security), and audits environment alignment in real-time.

### 12. Machine Profiling & Modular Setup (`init` & `setup`)
* **Architecture:** In `v2.2.0+`, `./bin/linux-wayland-config init` (or `scan`) performs safe, 100% non-destructive hardware inspection, saving `~/.config/linux-wayland-suite/machine-profile.json`. `./bin/linux-wayland-config setup` reads this profile and provides a contextual configuration wizard tailored exclusively to your detected hardware.

### 13. Internal Display Refresh Rate Switcher (`screen-hz`)
* **Fix:** `./bin/linux-wayland-config screen-hz 60` or `120` switches internal display refresh rate between high refresh rate (120Hz/144Hz) and battery power-saver mode (60Hz, saving ~2W-3W).

### 14. Numbered Interactive Report Engine
* **Fix:** Structured event runlogs saved in `~/.local/state/linux-wayland-suite/runs/`. Features interactive selection (`report --select`), indexed viewing (`report 3`), and actionable remediation commands for any warnings.

### 15. Multi-Shell Terminal Visual Identity & Fastfetch Logo Switcher (`terminal-fetch` / `cosmetic`)
* **Problem:** Terminal greetings and logos are hardcoded in distribution files (e.g. Garuda Mokka forcing a pastel cat mascot over the iconic Dr460nized neon eagle, or `.zshrc` hardcoding `--config mokka` while `.bashrc` lacks greeting hooks entirely).
* **Fix:** `./bin/linux-wayland-config cosmetic` (or `make cosmetic`) provides an interactive menu to choose between the Dr460nized low-poly neon eagle (`garuda-purple.png`), Mokka mascot cat (`mokka-fastfetch.png`), modern hexagonal "G" emblem, classic ASCII dragon, or custom PNG/SVG images. It audits all installed shells (**Fish**, **Zsh**, **Bash**), cleans hardcoded presets, prompts for multi-shell synchronization, and provides atomic user-space rollback (`--revert`).

### 16. Central Interactive Control Portal (`menu`)
* **Problem:** Remembering separate CLI flags or running modules blindly without knowing the current hardware status increases cognitive load and causes accidental misconfigurations.
* **Fix:** Running `./bin/linux-wayland-config` without arguments in any interactive terminal (or `./bin/linux-wayland-config menu`) launches the Central Control Portal (`portal_menu.py`). It displays a real-time system context card (Hardware, Active KWin Layout, Battery/AC state, and Cedilla patch status) and an intuitive numbered menu with rich module descriptions, non-blocking execution loops, and full bilingual localization (`en` and `pt-BR`).
---

## 🧪 Tested & Verified in Production

This suite is continuously tested and verified in real-world production setups:

| Category | Verified Hardware & Environment |
| :--- | :--- |
| **AI Hosts & Harnesses** | • **Verified in Production:** **Oh My Pi (OMP) + Google Antigravity** (`gemini-3.7-flash`) and **Claude Code (CLI)** (`claude-3-7-sonnet`)<br/>• **Architecturally Compatible:** Cursor IDE & Agent, Google Antigravity CLI, and OpenCode |
| **Desktop Environment & OS** | • **KDE Plasma:** 6.7.x / 6.7.4 (KWin Wayland native)<br/>• **Linux Distribution:** Garuda Linux / Arch Linux (Rolling release)<br/>• **Kernel:** `7.2.x-zen` (Linux Zen) / Linux Mainline `6.12+` |
| **Laptop / Chassis** | • **Avell A62 LIV** (Chassis **Tongfang GK5MQX** / GK5 / GM5 Series)<br/>• **CPU/GPU:** Intel Core i7-10750H + NVIDIA GeForce GTX 1650 Mobile / Intel UHD 630 (Hybrid graphics) |
| **Integrated Keyboard** | • **AT Translated Set 2 keyboard** (`isa0060/serio0` via ITE IT5570E/IT8528 Embedded Controller)<br/>• Layouts: Brazilian ABNT2 (`br`) & US-International (`us alt-intl`) |
| **Mouse & Touchpad** | • **Mouse:** Logitech MX Master 3S (Bluetooth / Logi Bolt via `logiops`)<br/>• **Touchpad:** Uniwill Precision Touchpad (`i2c-UNIW0001:00 093A:0255` via `libinput-gestures`) |

---

## 🚀 Quick Start (CLI & Makefile)

```bash
# Clone the repository
git clone https://github.com/renanbs/linux-wayland-suite.git ~/src/linux-wayland-suite
cd ~/src/linux-wayland-suite

# 1. Step 1: Scan hardware and generate machine profile (safe, non-destructive)
./bin/linux-wayland-config init
# or: make init (or: make scan)

# 2. Step 2: Contextual modular setup wizard (select what you want to configure)
./bin/linux-wayland-config setup
# or: make setup

# 3. Step 3: Run unified health audit
./bin/linux-wayland-config status
# or: make status
```
---

## 🛠️ CLI Command Reference

| Command | Makefile Target | Description |
| :--- | :--- | :--- |
| `linux-wayland-config menu` | `make menu` | Interactive central control portal with real-time hardware status summary |
| `linux-wayland-config init` / `scan` | `make init` / `make scan` | Non-destructive hardware inspection & machine profiling (`machine-profile.json`) |
| `linux-wayland-config setup` | `make setup` | Contextual modular configuration wizard based on detected hardware |
| `linux-wayland-config status` | `make status` | 7-stage unified health audit of hardware, DMI, power, Wi-Fi, IM, cedilla, and gestures |
| `linux-wayland-config smart-wifi-power` | `make smart-wifi-power` | Dynamic Wi-Fi power management (`off` on AC for zero latency, `on` on battery) |
| `linux-wayland-config screen-hz [60\|120]` | `make screen-60` / `screen-120` | Switches internal display refresh rate (60 Hz vs 120 Hz) |
| `linux-wayland-config fix-keyboard` | `make fix-keyboard` | Fixes `Ctrl+C` on ABNT2, sets up native cedilla, and masks fcitx5 |
| `linux-wayland-config patch-cedilla` | `make patch-cedilla` | Byte-pattern patch for Chromium/Electron (`'+c -> ç`) + Pacman autorepair hook |
| `linux-wayland-config fix-tongfang` | `make fix-tongfang` | Unlocks keyboard matrix in GRUB for Tongfang/Avell/Clevo laptops |
| `linux-wayland-config smart-keyboard-power` | `make smart-keyboard-power` | Dynamic keyboard power management (`on` standalone, `auto` with USB/BT keyboard) |
| `linux-wayland-config configure-harness` | — | Configures and syncs AI host harness profile and model roles |
| `linux-wayland-config battery-status` | `make battery-status` | Read-only battery, hybrid GPU, and PCIe ASPM diagnostic |
| `linux-wayland-config battery-apply` | `make battery-apply` | Applies user-chosen battery optimizations (`BATTERY_FIX_*`) |
| `linux-wayland-config turbo` | `make turbo` | CPU Turbo Boost management, quiet mode & runaway process watchdog |
| `linux-wayland-config gestures` | `make gestures` | Configures 3 & 4-finger touchpad gestures (`libinput-gestures`) |
| `linux-wayland-config mouse` | `make mouse` | Configures Logitech MX Master 3S thumb button and SmartShift via `logiops` |
| `linux-wayland-config test-keyboard` | `make test-keyboard` | Real-time interactive key event monitor (`/dev/input/eventX`) |
| `linux-wayland-config monitor-irq` | `make monitor-irq` | Real-time hardware electric interrupt monitor on IRQ 1 (`i8042`) |
| `linux-wayland-config switch [br\|us]` | `make switch-br` | Switches active KWin layout via D-Bus (0=br abnt2, 1=us alt-intl) |
| `linux-wayland-config report` | `make report` | Displays latest run report, historical metrics, and actionable recommendations |
| `linux-wayland-config report --list` | — | Lists recent numbered reports (`[1..N]`) |
| `linux-wayland-config report <N>` | — | Displays the N-th most recent report in detail |
| `linux-wayland-config report --select` | — | Interactive terminal menu to choose and view any report |
| `linux-wayland-config upgrade` | `make upgrade` | Checks and applies updates from GitHub and marketplace |
| `linux-wayland-config rollback` | `make rollback` | Restores previous configuration snapshot from backup |
| `linux-wayland-config cosmetic` / `terminal-fetch` | `make cosmetic` / `make terminal-fetch` | Fastfetch terminal identity interactive menu & logo switcher |
| `linux-wayland-config install` | `make install` / `make install-dev` | Installs suite permanently and configures PATH across all shells |
| `linux-wayland-config help` | `make help` | Displays full command help manual |
---

## 🤖 Installation & AI Tools Integration
### Global CLI Installation & PATH Configuration
To run suite commands (`linux-wayland-config` or `kde-config`) from any directory in your terminal:
```bash
# Permanent standalone installation (copies engine to ~/.local/share, independent of git branches):
make install

# Or development mode (symlinks ~/.local/bin directly to your active git worktree):
make install-dev
```
* Automatically registers `~/.local/bin` into `$PATH` across **Fish** (`~/.config/fish/conf.d/linux-wayland-suite-path.fish`), **Bash** (`~/.bashrc`), **Zsh** (`~/.zshrc`), and **Wayland/PAM** (`~/.config/environment.d/10-local-bin.conf`).


### 1. Oh My Pi (OMP)
Install directly from the remote marketplace:
```bash
# In OMP terminal:
omp plugin marketplace add renanbs/linux-wayland-suite
omp plugin install linux-wayland-suite@linux-wayland-suite

# Upgrade:
omp plugin marketplace update linux-wayland-suite
omp plugin upgrade linux-wayland-suite@linux-wayland-suite
```
* **Available Slash Commands:** `/linux-wayland-suite:status`, `/linux-wayland-suite:init`, `/linux-wayland-suite:patch-cedilla`, `/linux-wayland-suite:fix-keyboard`, `/linux-wayland-suite:fix-tongfang`, `/linux-wayland-suite:smart-keyboard-power`, `/linux-wayland-suite:configure-harness`, `/linux-wayland-suite:battery`, `/linux-wayland-suite:turbo`, `/linux-wayland-suite:install`, `/linux-wayland-suite:report`, `/linux-wayland-suite:help`, `/linux-wayland-suite:upgrade`.
* **Skills:** `skill://linux-wayland-suite`, `skill://linux-wayland-suite-architecture`.

### 2. Claude Code
```bash
/plugin marketplace add renanbs/linux-wayland-suite
/plugin install linux-wayland-suite@linux-wayland-suite
```

### 3. Cursor IDE & Agent
```bash
# 1. Install CLI
cd ~/src/kde-wayland-suite && make install-cli

# 2. Link rules globally for all Cursor projects
mkdir -p ~/.cursor/rules
cp .cursor/rules/kde-wayland-suite.mdc ~/.cursor/rules/
```

### 4. Google Antigravity & OpenCode
Registered automatically via workspace root `antigravity/plugin.json` and `opencode/skills/`.

---

## 📐 Architecture & Engineering Discipline

This repository follows strict engineering standards defined in **`skills/kde-wayland-suite-architecture`**:
1. **Canonical Source in `base/`:** All `.md` commands live in `base/commands/`, scripts in `base/shared/`, and skills in `base/skills/`. All platform directories use relative symlinks.
2. **4-Phase Output Contract (`OUTPUT-CONTRACT.md`):** Every command output by AI agents strictly follows:
   * `### 1. Plano` (Command, Action, Reversibility)
   * `### 2. Execução` (`✅`, `⏭️`, `⚠️`, `❌`)
   * `### 3. Resumo` (Table: Changed, Unchanged, Backup, Saved Report, Revert, Requires)
   * `### 4. Ações Recomendadas` (Mandatory if `⚠️` or `❌` occur, with exact 1-liner fixes)
3. **Structured Event Logs:** Persisted in `~/.local/state/kde-wayland-suite/runs/<timestamp>-<cmd>/events.tsv`.

---
## 👏 Acknowledgments & Upstream Credits
* **Chromium Wayland Cedilla Fix:** Special thanks to **Leandro Cassa** ([lcassa/chromium-wayland-cedilla-fix](https://github.com/lcassa/chromium-wayland-cedilla-fix)) for the ingenious byte-pattern patch of `ui::CharacterComposer`.
* **Logitech MX Master 3S:** Powered by [logiops](https://github.com/PixlOne/logiops) by PixlOne.
* **Touchpad Gestures:** Powered by [libinput-gestures](https://github.com/bulletmark/libinput-gestures) by Mark Blakeney.

---


## 📄 License

MIT © [Renan BS](https://github.com/renanbs)

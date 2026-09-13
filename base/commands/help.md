---
description: Displays the full reference manual of commands, shortcuts, solutions, and guided workflows for the Linux Wayland Suite.
---

# /help

Displays the quick reference help center for all commands available in the **Linux Wayland Suite**:

```bash
./bin/linux-wayland-config help
```

---

## Unified Command & Solutions Matrix

| CLI Command | Slash Command | Function / Action | When to Use |
| :--- | :--- | :--- | :--- |
| `./bin/linux-wayland-config menu` | — | Interactive central control portal with real-time status summary | When running without arguments or to access all modules from one screen |
| `./bin/linux-wayland-config init` | `/init` (or `/scan`) | Non-destructive hardware inspection & machine profiling | On first-time setup or to inspect all hardware safe & read-only |
| `./bin/linux-wayland-config setup` | `/setup` | Contextual modular configuration wizard based on detected hardware | To apply recommended settings for keyboards, Wi-Fi, gestures, etc. |
| `./bin/linux-wayland-config status` | `/check-status` | Unified 7-stage health audit across environment | To check keyboard, DMI, power, Wi-Fi, IM, cedilla, and gestures |
| `./bin/linux-wayland-config smart-wifi-power` | `/smart-wifi-power` | Dynamic Wi-Fi power (`off` on AC for zero latency, `on` on battery) | To prevent radio sleep/timeout for Orca, SSH and remote access |
| `./bin/linux-wayland-config screen-hz [60\|120]` | — | Switches internal display refresh rate (60 Hz vs 120 Hz) | To save 2W-3W on battery or restore high refresh rate |
| `./bin/linux-wayland-config fix-keyboard` | `/fix-keyboard` | Fixes `Ctrl+C` on ABNT2, native cedilla on US-intl, masks fcitx5 | When shortcuts fail or dead-key acute outputs `ć` instead of `ç` |
| `./bin/linux-wayland-config patch-cedilla` | `/patch-cedilla` | Byte-pattern patch for Chromium/Electron + Pacman autorepair hook | When `' + c` outputs `ć` in Chrome, Orca, VS Code, Discord, Brave on Wayland |
| `./bin/linux-wayland-config fix-tongfang` | `/fix-tongfang` | Unlocks matrix in GRUB for Tongfang/Avell laptops | If the physical notebook Control key does not respond |
| `./bin/linux-wayland-config smart-keyboard-power` | `/smart-keyboard-power` | Dynamic bus power (`on` standalone, `auto` with USB/BT keyboard) | To eliminate Left Ctrl latency/latch without battery waste |
| `./bin/linux-wayland-config battery-status` | `/battery` | Battery, hybrid GPU, and PCIe ASPM diagnostics (read-only) | To audit power consumption and battery health |
| `./bin/linux-wayland-config battery-apply` | `/battery` | Applies user-selected battery optimizations | To save power after inspecting diagnostics |
| `./bin/linux-wayland-config turbo` | `/turbo` | CPU Turbo Boost management, quiet mode & runaway process watchdog | To silence cooling fans, cool down CPU, and detect looping processes |
| `./bin/linux-wayland-config gestures` | `/configure-gestures` | Configures 3/4-finger touchpad gestures in KWin | To enable smooth workspace swipe and overview gestures |
| `./bin/linux-wayland-config mouse` | `/configure-mouse` | Configures Logitech MX Master 3S mouse via logiops | To map thumb gesture button and free-spin SmartShift |
| `./bin/linux-wayland-config test-keyboard` | `/test-keyboard` | Real-time key event monitor | To test whether any physical key is active |
| `./bin/linux-wayland-config monitor-irq` | `/monitor-irq` | Real-time hardware electric pulse monitor on IRQ 1 (i8042) | To test motherboard electric interrupts |
| `./bin/linux-wayland-config switch [br\|us]` | — | Switches active KWin layout via D-Bus | To switch layouts without relying on physical shortcuts |
| `./bin/linux-wayland-config report` | `/report` | Latest run report + historical trends & recommendations | To inspect execution history and solve warnings/failures |
| `./bin/linux-wayland-config upgrade` | `/upgrade` | Checks and applies updates from GitHub and marketplace | To upgrade the suite to the latest release |
| `./bin/linux-wayland-config rollback` | — | Restores previous configuration snapshot from backup | To revert changes made by the suite |
| `./bin/linux-wayland-config terminal-fetch` | `/terminal-fetch` | Fastfetch terminal identity menu & logo switch (Eagle, Cat Mokka, Dragon, etc.) | To customize or restore the terminal logo and greeting |
| `./bin/linux-wayland-config install` | `/install` | Installs suite permanently and configures PATH across all shells | To run suite commands from any directory |

---

## Standard Output Format (Evidence-First Verdict)

Every command response must follow this structured, evidence-based format:

### 🎯 Verdict: [ ✅ SUCCESS | ❌ FAILURE | ⚠️ PARTIAL SUCCESS ]
*One clear sentence summarizing the real, observable outcome of the operation.*

---

#### 📋 Execution Breakdown:
* **✅ Applied Successfully:**
  - `<Component Name>`: Concise description of exact changes made and verified.
* **❌ Failure / Hardware Rejection:**
  - `<Component Name>`: **NOT APPLIED**.
    - **Raw Driver / Command Error:** `<exact error output or exit reason>`
    - **Technical Root Cause:** `<hardware/kernel explanation>`
    - **System Impact:** `<confirm system safely remained in prior valid state>`
* **🔒 Manual Permission Required (Root):**
  - `<Component Name>`: Explanation of why elevation could not run in the non-interactive agent subshell.

---

#### 🔬 Technical Evidence & Ground Truth:
| Component | Verified State | Observable Proof / Command | How to Revert |
| :--- | :--- | :--- | :--- |
| `<Name>` | `<Active / Inactive>` | `<Command and exact verified output>` | `<Exact 1-line reversal command>` |

---

#### 💡 Daily Impact & Practical Benefits:
* **<Impact Details>:** Clear explanation of what changes in user experience and workflow.

---

#### 👉 Action Required (Mandatory if manual action, ⚠️ or ❌ occurs):
```bash
linux-wayland-config <subcommand>
```
*(Execution note: run directly in your terminal without typing sudo; elevation is requested internally using the fully-resolved path).*

---

### Rules & Failure Discipline (Inviolable)

1. **Never declare success without verification:** Run the corresponding `status` check or re-read the modified system file before marking `✅`.
2. **Explicit Failure Reporting:** Any action that failed, timed out, was rejected by a kernel driver, or could not be completed MUST be marked with `❌`. NEVER soften or mask a failure as a warning (`⚠️`) or skip (`⏭️`).
3. **Prominent User Notification:** Whenever an operation fails, the AI agent MUST prominently and unambiguously state in the narrative that the action **FAILED** and that **NO CHANGE was applied** to that component, explaining the exact technical reason.
4. **Sudo Command Guidelines:** When an operation requires root privileges and cannot be executed in a non-interactive subshell, instruct the user to run `linux-wayland-config <subcommand>` directly in their terminal. **Do not prepend `sudo`**, because `sudo`'s `secure_path` often omits `~/.local/bin`. The script internally handles elevation via `exec sudo "$0" "$@"` using its fully-resolved path.
5. **Requires field:** If a fix requires a logout or reboot to take effect, explicitly state it in both the breakdown and the daily impact text.

---
description: Non-destructive hardware inspection and machine profiling for Linux Wayland environments (detects GPUs, displays, Wi-Fi, keyboards, and saves machine-profile.json).
---

# /init (or /scan)

Performs a full, 100% safe and non-destructive inspection of your machine's hardware and environment:
- Identifies OS, kernel, compositor session, active AI host harness, and language preference.
- Inspects CPU vendor, model, scaling driver, Turbo Boost state, and package temperature.
- Inspects power supply, battery health, and charging threshold support.
- Detects GPUs (iGPU / dGPU), KWin DRM devices, and internal display refresh modes (60 Hz vs high Hz).
- Detects wireless interfaces (`wlo1`), drivers, 802.11 power saving state, and PCIe bus runtime PM.
- Detects keyboards (i8042 bus, Tongfang/Avell matrix, external keyboards), touchpad, and Logitech mice.
- Saves the structured profile to:
  `~/.config/linux-wayland-suite/machine-profile.json`

```bash
./bin/linux-wayland-config init
```

---

## Guided Flow (Mandatory for AI Agents)

Before running `init`, the agent **must use `AskUserQuestion` (or `ask`)** to confirm language preference:

### Question 1 — Language Preference (`language`) (singleSelect):
- **"English (en) (Recommended)"** — Standard English. All internal configs, runlogs, and contracts remain canonical English.
- **"Português do Brasil (pt-BR)"** — Brazilian Portuguese. Internal operations remain in English; user-facing dialogue and summaries are localized.

### Next Step After `/init`:
Once `/init` completes and the machine profile is saved:
1. Explain the detected hardware findings to the user.
2. Proceed to `/setup` (`commands/setup.md`) or use `linux-wayland-config setup` to apply user-selected optimizations.

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

---
description: Manages CPU Turbo Boost (Intel/AMD), monitors CPU frequencies and package temperatures, detects runaway/looping processes via in-memory watchdog, and configures optional boot persistence via systemd.
---

# /turbo

Manages CPU Turbo Boost states (Quiet/Cool vs High Performance), monitors core thermals, and audits runaway processes:

```bash
./bin/kde-config turbo
```

---

## Mandatory AI Agent Workflow

**Never change CPU Turbo Boost state or install persistence services without asking the user first.** This command follows Progressive Disclosure and User Sovereignty:

1. Run `./bin/kde-config turbo-status` (or `./bin/kde-config turbo --watch`) to inspect the current state silently without root.
2. Present empirical findings to the user:
   - Current Turbo Boost status (`ACTIVE` vs `DISABLED`).
   - CPU package temperature and core frequencies.
   - Runaway process watchdog results (PIDs, CPU %, memory usage).
   - Boot persistence status (`enabled` vs `disabled`).
3. Use `AskUserQuestion` (or `ask`) to prompt the user for their desired decision:
   - **Action Choice:** Disable Turbo Boost (Quiet & Cool) [Recommended], Enable Turbo Boost (High Performance), or Keep current state.
   - **Persistence Choice:** Persist on boot via systemd service [Recommended], apply only for current session, or remove persistence.
   - **Process Action (Conditional):** If runaway processes (>30% CPU) are detected, ask whether to warn or terminate with `kill`.
4. Execute the chosen action via CLI:

```bash
# Disable Turbo Boost immediately (Quiet & Cool mode)
sudo ./bin/kde-config turbo-off

# Enable Turbo Boost immediately (High Performance)
sudo ./bin/kde-config turbo-on

# Toggle state
sudo ./bin/kde-config turbo-toggle

# Persist current state across reboots
sudo ./bin/kde-config turbo-persist

# Run runaway watchdog scan
./bin/kde-config turbo-watch
```

5. Report results strictly adhering to the Evidence-First Verdict output contract.

---

## Technical Architecture & Capabilities

- **Multi-Vendor Hardware Abstraction:** Automatically adapts to:
  * **Intel:** `/sys/devices/system/cpu/intel_pstate/no_turbo` (or `acpi-cpufreq`)
  * **AMD:** `/sys/devices/system/cpu/cpufreq/boost` (or `amd-pstate`)
- **Fast Runaway Watchdog:** Directly scans `/proc` in memory in ~15ms, identifying looping processes without spawning heavy subshells (`ps | awk | grep`).
- **Systemd Persistence Unit:** `/etc/systemd/system/linux-wayland-cpu-turbo.service` applies the configured state early in boot (`sysinit.target`).
- **Default-on-Enter Ergonomics:** When executed interactively, pressing `<Enter>` selects the recommended default choice without requiring manual typing.

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
| `CPU Turbo Boost` | `<Active / Disabled>` | `cat /sys/devices/system/cpu/intel_pstate/no_turbo` | `./bin/kde-config turbo-toggle` |
| `Thermal State` | `<Temperature °C>` | `sensors | grep Package` | `N/A` |
| `Boot Persistence` | `<Enabled / Disabled>` | `systemctl is-enabled linux-wayland-cpu-turbo` | `./bin/kde-config turbo remove-persist` |

---

#### 🏛️ 7-Pillars Architectural Compliance Gate:
| Pillar | Requirement | Verified Status | Evidence File / Artifact |
| :--- | :--- | :--- | :--- |
| **1. Canonical Script** | `base/shared/<name>.sh` / `.py` | ✅ COMPLIANT | `base/shared/manage-cpu-turbo.py` & `.sh` |
| **2. CLI Orchestrator** | `kde-config` dispatch & usage | ✅ COMPLIANT | `base/bin/kde-config` (`turbo`, `turbo-status`) |
| **3. Makefile Target** | `.PHONY` & `make help` entry | ✅ COMPLIANT | `Makefile` (`turbo`, `turbo-status`, `turbo-off`) |
| **4. Structured Events** | TSV runlog events emitted | ✅ COMPLIANT | `events.tsv` (`turbo_status`, `turbo_off`) |
| **5. Health Audit** | Integrated into status audit | ✅ COMPLIANT | `shared/check-status.py` & `diagnose-battery.py` |
| **6. AI Command Doc** | Standardized markdown contract | ✅ COMPLIANT | `base/commands/turbo.md` + symlinks |
| **7. Central Help & Docs** | Help matrix & README sync | ✅ COMPLIANT | `commands/help.md`, `README.md`, `README.pt-BR.md` |

---

#### 💡 Daily Impact & Practical Benefits:
* **Acoustic Comfort:** Disabling Turbo drops CPU package temperatures from ~85-90°C to ~50-55°C, silencing cooling fans in thin chassis (e.g. Tongfang/Avell).
* **Thermal Throttling Prevention:** Keeps the CPU in its optimal thermal envelope without premature frequency drops under sustained load.
* **Rapid Anomaly Detection:** Catches hung webviews (e.g. WhatsApp Web / QtWebEngine) and Electron renderers before they drain battery and overheat the laptop.

---

#### 👉 Action Required:
Run the command directly in your terminal:
```bash
./bin/kde-config turbo
```

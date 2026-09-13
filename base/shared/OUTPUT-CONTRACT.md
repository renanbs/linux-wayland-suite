# Standardized Evidence-First Verdict Output Contract

Canonical source for the report format that **every** command/skill in this suite must follow across **all** tools (Claude Code, Cursor, OMP, OpenCode, Antigravity). The block below is mirrored at the end of each command and skill `.md` file.

The goal is for every execution to provide **immediate verdict clarity**, **unvarnished technical evidence**, and **actionable next steps** without bureaucratic filler or hidden failures.

> **Internationalization Note:** Internal contracts, command specifications, and event logs are strictly defined in English. The AI agent translates user-facing messages into the user's selected language (e.g. `pt-BR`) whenever communicating with the user.

---

## Standard Output Format (Mandatory across all tools)

Every command response must be presented in this structured format:

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

#### 🏛️ 7-Pillars Architectural Compliance Gate (Mandatory for Feature Deliveries):
| Pillar | Scope | Verified File / Component | Status |
| :--- | :--- | :--- | :---: |
| **1. Canonical Script** | `base/shared/` | `base/shared/<name>.py` (or `.sh`) | `[✅ / N/A]` |
| **2. CLI Orchestrator** | `base/bin/` | `linux-wayland-config` (`usage`, `cmd`, `dispatch`) | `[✅ / N/A]` |
| **3. Makefile Target** | `Makefile` | `make <target>` declared & documented | `[✅ / N/A]` |
| **4. Structured Events** | `lib-runlog` / `lib_suite` | `log_event()` calls emitting to `events.tsv` | `[✅ / N/A]` |
| **5. Health Audit** | `check-status` | Verified in `base/shared/check-status.py` | `[✅ / N/A]` |
| **6. AI Command Spec** | `base/commands/` | `commands/<name>.md` + all platform symlinks | `[✅ / N/A]` |
| **7. Central Integration** | `/init`, `/setup`, `/help`, `/report`, READMEs | `profile-machine.py` (`machine-profile.json`), `setup-suite.py`, `help.md`, `report.py`, `README.md` + `README.pt-BR.md` | `[✅ / N/A]` |
---

#### 💡 Daily Impact & Practical Benefits:
* **<Scenario 1 (e.g. AC / Plugged in)>:** Real-world benefit (e.g. zero radio sleep, no Orca/SSH timeouts).
* **<Scenario 2 (e.g. Battery / Mobile)>:** Real-world benefit (e.g. maximum power savings preserved).

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
6. **Mandatory 7-Pillars Pre-Delivery Gate:** Never yield a feature, script, or architectural delivery as complete without including the `#### 🏛️ 7-Pillars Architectural Compliance Gate` table proving that all 7 layers have been updated, synchronized, and verified. If any pillar is incomplete, the delivery is blocked.

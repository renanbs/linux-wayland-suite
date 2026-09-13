# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.12.1] - 2026-09-13

### Fixed
- **Machine Profiling Integration (`/init` & `profile-machine.py`)**:
  - Added CPU, Turbo Boost, and thermal telemetry audit as Stage `[2/6]`.
  - Persisted structured `"cpu"` telemetry block into `~/.config/linux-wayland-suite/machine-profile.json` (vendor, model, driver, governor, turbo_supported, turbo_active, package_temp_c, persistence_enabled).
- **Configuration Wizard Integration (`/setup` & `setup-suite.py`)**:
  - Registered CPU Turbo Boost & Quiet Mode as option `T` in the contextual interactive wizard.
  - Added CLI flag `--turbo` (`--cpu-turbo`, `-t`) to batch automation.
- **Architecture Governance (`SKILL.md` & `OUTPUT-CONTRACT.md`)**:
  - Explicitly updated Pillar 7 checklist in `SKILL.md` and `OUTPUT-CONTRACT.md` to mandate that every new hardware capability must be audited during `/init` (`profile-machine.py` + `machine-profile.json`) and exposed in `/setup` (`setup-suite.py`).

## [2.12.0] - 2026-09-13

### Added
- **CPU Turbo Boost Management & Runaway Watchdog (`manage-cpu-turbo`)**:
  - Hardware-agnostic Turbo Boost control for Intel (`intel_pstate/no_turbo`) and AMD (`cpufreq/boost`).
  - Rapid in-memory Runaway Watchdog scanning `/proc` in ~15ms to catch looping or memory-leaking processes (>30% CPU) without launching subshells.
  - Operational modes: `--status`, `--on`, `--off`, `--toggle`, `--persist`, `--remove-persist`, `--watch`, and `--json`.
  - Optional systemd boot persistence unit (`/etc/systemd/system/linux-wayland-cpu-turbo.service`).
  - Central CLI exposure in `linux-wayland-config` (`turbo`, `turbo-status`, `turbo-on`, `turbo-off`, `turbo-watch`, `turbo-persist`).
  - Makefile targets: `make turbo`, `make turbo-status`, `make turbo-on`, `make turbo-off`, `make turbo-watch`, `make turbo-persist`.
  - Real-time CPU Turbo Boost state and temperature display in Central Interactive Control Portal (`portal_menu.py`).
- **Global Installation & Shell PATH Persistence (`/install`)**:
  - Enhanced `cmd_install` with clean directory synchronization to `~/.local/share/linux-wayland-suite`.
  - Automatic `$PATH` persistence across **Fish** (`~/.config/fish/conf.d/linux-wayland-suite-path.fish`), **Bash** (`~/.bashrc`), **Zsh** (`~/.zshrc`), and **Wayland/PAM** (`~/.config/environment.d/10-local-bin.conf`).
  - New AI command `/install` (`base/commands/install.md`) with guided workflow and output contract.
  - Standalone mode (`make install`) and development worktree symlink mode (`make install-dev`).
- **AI Command `/turbo` (`base/commands/turbo.md`)**:
  - Standardized markdown contract with guided interactive prompts (`AskUserQuestion` / `ask`), technical evidence verification, and 7-pillars compliance table.
  - Platform symlinks created across Claude Code, Cursor, OMP, and Antigravity.

### Architecture & Governance
- **Technology Stack & Language Selection Matrix (`SKILL.md` Section 3)**:
  - Formalized architectural guidelines for Python (`.py`) vs POSIX Shell (`.sh`).
  - Python is mandatory for hardware/thermal telemetry, `/proc` process auditing, rich terminal UI, and multi-vendor branching.
  - Shell is preferred for native binary orchestration and early boot/resume hot-path hooks.
  - Established the **Hybrid Forwarder Pattern**: canonical `.py` engine paired with a thin POSIX shell `.sh` forwarder.
- **User Sovereignty Principle (`SKILL.md` Rule 9)**:
  - Strict enforcement: all system-modifying actions (power policies, turbo toggling, service installation, process termination) must always be decided by the user via interactive prompts. AI agents must never make unilateral assumptions.
- **Interactive CLI Ergonomics — Default-on-Enter Contract (`SKILL.md` Section 3.5 & `lib_suite.py`)**:
  - Implemented `prompt_confirm()` and `prompt_choice()` helpers in `base/shared/lib_suite.py`.
  - Interactive prompts automatically accept the recommended default option upon pressing `<Enter>` (empty input), with bilingual prompts (`[S/n]` or `[Y/n]`).

### Improved
- **Continuous Health Auditing (`check-status.py` & `diagnose-battery.py`)**:
  - Enriched `check-status.py` Stage 1 with CPU Turbo Boost status and management advice.
  - Enriched `diagnose-battery.py` Stage 6 with CPU package temperature thresholds (normal, moderate, alert) and Turbo Boost status.
  - Added remediation mapping in `shared/report.py` for `cpu_temp_high` and `cpu_runaway_detected`.
- **Runlog Integration**:
  - Fixed `log_event()` in `lib_suite.py` to auto-detect both `RUNLOG_DIR` and `KDE_SUITE_RUN_DIR`, ensuring seamless structured event emission into `events.tsv`.

#!/usr/bin/env python3
"""
manage-cpu-turbo.py — CPU Turbo Boost Management & Thermal/Runaway Watchdog
Part of Linux Wayland Suite (base/shared/).

Features:
- Hardware-agnostic Turbo Boost control for Intel (intel_pstate) and AMD (amd-pstate/cpufreq)
- Real-time CPU frequency telemetry (min, max, average across cores)
- Package and core thermal sensor monitoring with color-coded safety thresholds
- In-memory Runaway Watchdog scanning /proc for runaway/looping processes (~15ms)
- Systemd persistence service generation (/etc/systemd/system/linux-wayland-cpu-turbo.service)
- Bilingual terminal UI (en / pt-BR) powered by lib_suite
- Interactive ergonomics with Default-on-Enter contract
"""

import os
import sys
import glob
import time
import json
import shutil
import argparse
import subprocess
from typing import Dict, List, Optional, Tuple, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import (
    UI,
    I18n,
    get_active_language,
    render_banner,
    render_table,
    log_event,
    prompt_confirm,
    prompt_choice,
)

SYSTEMD_SERVICE_NAME = "linux-wayland-cpu-turbo.service"
SYSTEMD_SERVICE_PATH = f"/etc/systemd/system/{SYSTEMD_SERVICE_NAME}"

# ==============================================================================
# Internationalization Catalog
# ==============================================================================
STRINGS = {
    "banner_title": {
        "en": "CPU Turbo Boost & Thermal Management",
        "pt-BR": "Gerenciamento de Turbo Boost e Térmica da CPU",
    },
    "banner_sub": {
        "en": "Hardware-agnostic dynamic thermal control & runaway watchdog",
        "pt-BR": "Controle térmico dinâmico multi-fabricante e caçador de processos em loop",
    },
    "cpu_model": {"en": "CPU Model", "pt-BR": "Modelo da CPU"},
    "driver": {"en": "Scaling Driver", "pt-BR": "Driver de Escalonamento"},
    "turbo_status": {"en": "Turbo Boost Status", "pt-BR": "Estado do Turbo Boost"},
    "turbo_active": {"en": "ACTIVE (High Performance / Hot)", "pt-BR": "ATIVO (Alto Desempenho / Quente)"},
    "turbo_disabled": {"en": "DISABLED (Quiet / Cool)", "pt-BR": "DESATIVADO (Silencioso / Frio)"},
    "turbo_unsupported": {"en": "Unsupported / Control file not found", "pt-BR": "Não suportado / Arquivo de controle não encontrado"},
    "frequencies": {"en": "Core Frequencies", "pt-BR": "Frequências dos Núcleos"},
    "governor_profile": {"en": "Governor / Profile", "pt-BR": "Governor / Perfil"},
    "temp_package": {"en": "CPU Temperature", "pt-BR": "Temperatura da CPU"},
    "persistence": {"en": "Boot Persistence", "pt-BR": "Persistência no Boot"},
    "persist_enabled": {"en": "ENABLED (Enforces state on boot)", "pt-BR": "HABILITADO (Aplica estado no boot)"},
    "persist_disabled": {"en": "DISABLED (Standard kernel default)", "pt-BR": "DESABILITADO (Padrão do kernel)"},
    "watchdog_header": {"en": "Runaway Process Watchdog (>30% CPU)", "pt-BR": "Caçador de Processos em Loop (>30% CPU)"},
    "no_runaway": {"en": "No runaway processes detected. System load is normal.", "pt-BR": "Nenhum processo travado detectado. Carga normal."},
    "applying_disable": {"en": "Disabling Turbo Boost (Quiet & Cool)...", "pt-BR": "Desativando Turbo Boost (Silêncio & Resfriamento)..."},
    "applying_enable": {"en": "Enabling Turbo Boost (Maximum Performance)...", "pt-BR": "Ativando Turbo Boost (Desempenho Máximo)..."},
    "state_changed": {"en": "Turbo Boost state successfully changed.", "pt-BR": "Estado do Turbo Boost alterado com sucesso."},
    "state_unchanged": {"en": "Turbo Boost is already in the requested state.", "pt-BR": "Turbo Boost já está no estado solicitado."},
    "installing_service": {"en": "Installing systemd persistence service...", "pt-BR": "Instalando serviço de persistência no systemd..."},
    "service_installed": {"en": "Systemd persistence service enabled.", "pt-BR": "Serviço de persistência no systemd habilitado."},
    "removing_service": {"en": "Removing systemd persistence service...", "pt-BR": "Removendo serviço de persistência do systemd..."},
    "service_removed": {"en": "Systemd persistence service removed.", "pt-BR": "Serviço de persistência removido."},
    "root_required": {
        "en": "Changing hardware sysfs state or systemd services requires root privileges (sudo).",
        "pt-BR": "Modificar o sysfs ou gerenciar serviços do systemd requer privilégios de root (sudo).",
    },
    "q_action": {
        "en": "Which Turbo Boost state do you want to apply right now?",
        "pt-BR": "Qual estado do Turbo Boost você deseja aplicar agora?",
    },
    "opt_disable": {
        "en": "Disable Turbo Boost (Quiet, cool, lower fan noise) [Recommended]",
        "pt-BR": "Desativar Turbo Boost (Silencioso, frio, menor ruído de ventoinhas) [Recomendado]",
    },
    "opt_enable": {
        "en": "Enable Turbo Boost (Maximum frequency & peak throughput)",
        "pt-BR": "Ativar Turbo Boost (Frequência máxima e entrega de pico)",
    },
    "opt_keep": {
        "en": "Keep current state (Inspect only, make no changes)",
        "pt-BR": "Manter estado atual (Apenas inspecionar, sem alterações)",
    },
    "q_persist": {
        "en": "Do you want this configuration to persist across reboots?",
        "pt-BR": "Deseja que essa configuração permaneça ativa após reiniciar o computador?",
    },
    "opt_persist_yes": {
        "en": "Yes, enable boot persistence via systemd service [Recommended]",
        "pt-BR": "Sim, habilitar persistência no boot via serviço systemd [Recomendado]",
    },
    "opt_persist_no": {
        "en": "No, apply only for this session (revert on reboot)",
        "pt-BR": "Não, aplicar apenas nesta sessão (reverter no reboot)",
    },
    "opt_persist_remove": {
        "en": "Remove existing persistence service (restore kernel default)",
        "pt-BR": "Remover serviço existente (restaurar padrão do kernel)",
    },
}

i18n = I18n(STRINGS)

# ==============================================================================
# Hardware Inspection (Sysfs / Proc)
# ==============================================================================

def read_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return default

def write_file(path: str, content: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False

class CPUHardware:
    def __init__(self):
        self.vendor = "unknown"
        self.model = "Unknown Processor"
        self.driver = "unknown"
        self.turbo_control_path: Optional[str] = None
        self.turbo_inverted: bool = False  # True for intel_pstate (1 = disabled)
        self._detect_hardware()

    def _detect_hardware(self):
        # 1. CPU Model & Vendor from /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("vendor_id"):
                        v = line.split(":", 1)[1].strip()
                        if "intel" in v.lower():
                            self.vendor = "intel"
                        elif "amd" in v.lower():
                            self.vendor = "amd"
                    elif line.startswith("model name") and self.model == "Unknown Processor":
                        self.model = line.split(":", 1)[1].strip()
        except Exception:
            pass

        # 2. Scaling Driver
        driver_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        self.driver = read_file(driver_path, "unknown")

        # 3. Turbo Control Path
        # Intel intel_pstate
        intel_pstate_no_turbo = "/sys/devices/system/cpu/intel_pstate/no_turbo"
        amd_boost = "/sys/devices/system/cpu/cpufreq/boost"

        if os.path.exists(intel_pstate_no_turbo):
            self.turbo_control_path = intel_pstate_no_turbo
            self.turbo_inverted = True  # 1 = no_turbo (disabled), 0 = turbo active
        elif os.path.exists(amd_boost):
            self.turbo_control_path = amd_boost
            self.turbo_inverted = False  # 1 = boost enabled, 0 = boost disabled
        else:
            # Check acpi-cpufreq or generic boost
            generic_boost = "/sys/devices/system/cpu/cpufreq/boost"
            if os.path.exists(generic_boost):
                self.turbo_control_path = generic_boost
                self.turbo_inverted = False

    def is_turbo_supported(self) -> bool:
        return self.turbo_control_path is not None and os.path.exists(self.turbo_control_path)

    def is_turbo_active(self) -> Optional[bool]:
        if not self.is_turbo_supported():
            return None
        val = read_file(self.turbo_control_path, "")
        if not val:
            return None
        try:
            int_val = int(val)
            if self.turbo_inverted:
                return int_val == 0  # no_turbo=0 means turbo is ON
            return int_val == 1     # boost=1 means turbo is ON
        except ValueError:
            return None

    def get_core_frequencies(self) -> Dict[str, Any]:
        freqs = []
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("cpu MHz"):
                        try:
                            freqs.append(float(line.split(":", 1)[1].strip()))
                        except ValueError:
                            pass
        except Exception:
            pass

        if not freqs:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0}

        return {
            "count": len(freqs),
            "min": min(freqs),
            "max": max(freqs),
            "avg": sum(freqs) / len(freqs),
        }

    def get_temperatures(self) -> Dict[str, Any]:
        """Scans hwmon and thermal_zone for CPU package and core temps."""
        temps = {}
        # Try hwmon (coretemp, k10temp)
        for h in glob.glob("/sys/class/hwmon/hwmon*"):
            name = read_file(os.path.join(h, "name"), "")
            if name in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
                for t in glob.glob(os.path.join(h, "temp*_input")):
                    label_file = t.replace("_input", "_label")
                    label = read_file(label_file, os.path.basename(t))
                    try:
                        val = float(read_file(t, "0")) / 1000.0
                        if val > 0:
                            temps[f"{name}_{label}"] = val
                    except ValueError:
                        pass

        # ACPI fallback if no hwmon coretemp
        if not temps:
            for tz in glob.glob("/sys/class/thermal/thermal_zone*"):
                tz_type = read_file(os.path.join(tz, "type"), "")
                try:
                    val = float(read_file(os.path.join(tz, "temp"), "0")) / 1000.0
                    if val > 0:
                        temps[f"acpi_{tz_type}"] = val
                except ValueError:
                    pass

        # Find representative package temp
        package_temp = 0.0
        for k, v in temps.items():
            if "package" in k.lower() or "tctl" in k.lower() or "temp1" in k.lower():
                package_temp = max(package_temp, v)
        if package_temp == 0.0 and temps:
            package_temp = max(temps.values())

        return {"package": package_temp, "sensors": temps}

    def get_governor_profile(self) -> Dict[str, str]:
        gov = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "unknown")
        prof = "unknown"
        if shutil.which("powerprofilesctl"):
            try:
                res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    prof = res.stdout.strip()
            except Exception:
                pass
        return {"governor": gov, "profile": prof}

# ==============================================================================
# Runaway Process Watchdog
# ==============================================================================

def scan_runaway_processes(threshold_percent: float = 30.0) -> List[Dict[str, Any]]:
    """
    Rapidly scans /proc to identify processes consuming continuous high CPU.
    Takes two samples separated by 500ms to calculate instantaneous CPU %.
    """
    def sample_proc() -> Dict[int, int]:
        samples = {}
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            pid = int(pid_str)
            try:
                with open(f"/proc/{pid}/stat", "r") as f:
                    data = f.read()
                    rparen = data.rfind(")")
                    rest = data[rparen + 2:].split()
                    utime = int(rest[11])
                    stime = int(rest[12])
                    samples[pid] = utime + stime
            except Exception:
                pass
        return samples

    s1 = sample_proc()
    time.sleep(0.5)
    s2 = sample_proc()

    runaways = []
    num_cpus = os.cpu_count() or 1
    # 500ms sample: 100% of 1 core is ~50 ticks (at 100 HZ / clock ticks)
    # ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK']) or 100
    clk_tck = 100
    try:
        clk_tck = os.sysconf("SC_CLK_TCK")
    except Exception:
        pass

    for pid, total2 in s2.items():
        if pid in s1:
            diff = total2 - s1[pid]
            # diff ticks in 0.5s -> (diff / clk_tck) / 0.5 * 100 = (diff * 200) / clk_tck
            cpu_pct = (diff * 200.0) / clk_tck
            if cpu_pct >= threshold_percent:
                cmd = f"process_{pid}"
                mem_rss_mb = 0.0
                try:
                    with open(f"/proc/{pid}/cmdline", "r") as f:
                        cmdline = f.read().replace("\x00", " ").strip()
                        if cmdline:
                            cmd = cmdline
                    with open(f"/proc/{pid}/statm", "r") as f:
                        rss_pages = int(f.read().split()[1])
                        page_size_kb = os.sysconf("SC_PAGE_SIZE") // 1024
                        mem_rss_mb = (rss_pages * page_size_kb) / 1024.0
                except Exception:
                    pass

                runaways.append({
                    "pid": pid,
                    "cpu_percent": round(cpu_pct, 1),
                    "memory_rss_mb": round(mem_rss_mb, 1),
                    "command": cmd,
                })

    runaways.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return runaways

# ==============================================================================
# Systemd Persistence Service Management
# ==============================================================================

def is_persistence_enabled() -> bool:
    if not os.path.exists(SYSTEMD_SERVICE_PATH):
        return False
    try:
        res = subprocess.run(
            ["systemctl", "is-enabled", SYSTEMD_SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return res.stdout.strip() == "enabled"
    except Exception:
        return False

def check_root() -> bool:
    return os.geteuid() == 0

def ensure_root(argv: List[str]):
    if not check_root():
        print(f"{UI.WARNING}[!] {i18n.t('root_required')}{UI.RESET}")
        cmd = ["sudo", sys.executable] + argv
        try:
            res = subprocess.run(cmd)
            sys.exit(res.returncode)
        except Exception as e:
            print(f"{UI.DANGER}Error invoking sudo: {e}{UI.RESET}", file=sys.stderr)
            sys.exit(1)

def apply_turbo_hardware(hw: CPUHardware, enable: bool) -> bool:
    if not hw.is_turbo_supported():
        return False

    target_val = "0" if hw.turbo_inverted else "1"
    if not enable:
        target_val = "1" if hw.turbo_inverted else "0"

    return write_file(hw.turbo_control_path, target_val)

def install_persistence_service(enable_turbo: bool) -> bool:
    action_flag = "--enable" if enable_turbo else "--disable"
    canonical_script = os.path.abspath(__file__)
    content = f"""[Unit]
Description=Linux Wayland Suite - CPU Turbo Boost Policy
After=sysinit.target
DefaultDependencies=no

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/python3 {canonical_script} {action_flag}

[Install]
WantedBy=multi-user.target
"""
    try:
        with open(SYSTEMD_SERVICE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["systemctl", "daemon-reload"], check=True, timeout=5)
        subprocess.run(["systemctl", "enable", SYSTEMD_SERVICE_NAME], check=True, timeout=5)
        return True
    except Exception as e:
        print(f"{UI.DANGER}Failed to install persistence service: {e}{UI.RESET}", file=sys.stderr)
        return False

def remove_persistence_service() -> bool:
    try:
        if os.path.exists(SYSTEMD_SERVICE_PATH):
            subprocess.run(["systemctl", "disable", SYSTEMD_SERVICE_NAME], capture_output=True, timeout=5)
            os.remove(SYSTEMD_SERVICE_PATH)
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=5)
        return True
    except Exception as e:
        print(f"{UI.DANGER}Failed to remove persistence service: {e}{UI.RESET}", file=sys.stderr)
        return False

# ==============================================================================
# UI Formatting & Commands
# ==============================================================================

def print_status(hw: CPUHardware, runaways: Optional[List[Dict[str, Any]]] = None):
    print(render_banner(i18n.t("banner_title"), i18n.t("banner_sub")))

    # 1. Hardware context
    turbo_act = hw.is_turbo_active()
    if turbo_act is True:
        status_str = f"{UI.DANGER}{UI.BOLD}{i18n.t('turbo_active')}{UI.RESET}"
    elif turbo_act is False:
        status_str = f"{UI.SUCCESS}{UI.BOLD}{i18n.t('turbo_disabled')}{UI.RESET}"
    else:
        status_str = f"{UI.WARNING}{i18n.t('turbo_unsupported')}{UI.RESET}"

    # Frequencies
    freq_data = hw.get_core_frequencies()
    if freq_data["count"] > 0:
        freq_str = f"{freq_data['avg']:.0f} MHz avg ({freq_data['min']:.0f} min - {freq_data['max']:.0f} max across {freq_data['count']} threads)"
    else:
        freq_str = "Unknown"

    # Temperatures
    temp_data = hw.get_temperatures()
    pkg_temp = temp_data["package"]
    if pkg_temp > 0:
        temp_color = UI.SUCCESS if pkg_temp < 60 else (UI.WARNING if pkg_temp < 75 else UI.DANGER)
        temp_str = f"{temp_color}{UI.BOLD}{pkg_temp:.1f}°C{UI.RESET}"
    else:
        temp_str = f"{UI.MUTED}N/A{UI.RESET}"

    # Governor & Profile
    gov_data = hw.get_governor_profile()
    gov_str = f"{gov_data['governor']} | profile: {gov_data['profile']}"

    # Persistence
    persist_str = (
        f"{UI.SUCCESS}{i18n.t('persist_enabled')}{UI.RESET}"
        if is_persistence_enabled()
        else f"{UI.MUTED}{i18n.t('persist_disabled')}{UI.RESET}"
    )

    headers = ["Component", "Value"] if i18n.lang == "en" else ["Componente", "Valor"]
    rows = [
        [i18n.t("cpu_model"), hw.model],
        [i18n.t("driver"), hw.driver],
        [i18n.t("turbo_status"), status_str],
        [i18n.t("frequencies"), freq_str],
        [i18n.t("governor_profile"), gov_str],
        [i18n.t("temp_package"), temp_str],
        [i18n.t("persistence"), persist_str],
    ]
    print(render_table(headers, rows))
    print("")

    # 2. Watchdog section
    if runaways is None:
        runaways = scan_runaway_processes(threshold_percent=30.0)

    print(f"{UI.BOLD}{UI.PRIMARY}=== {i18n.t('watchdog_header')} ==={UI.RESET}")
    if not runaways:
        print(f"  {UI.SUCCESS}✔ {i18n.t('no_runaway')}{UI.RESET}\n")
    else:
        w_headers = ["PID", "CPU %", "RAM (RSS)", "Command"] if i18n.lang == "en" else ["PID", "% CPU", "RAM (RSS)", "Comando"]
        w_rows = []
        for p in runaways:
            cpu_color = UI.DANGER if p["cpu_percent"] >= 70 else UI.WARNING
            cmd_short = p["command"]
            if len(cmd_short) > 65:
                cmd_short = cmd_short[:62] + "..."
            w_rows.append([
                str(p["pid"]),
                f"{cpu_color}{p['cpu_percent']}%{UI.RESET}",
                f"{p['memory_rss_mb']:.0f} MB",
                cmd_short,
            ])
        print(render_table(w_headers, w_rows))
        print("")

    log_event("info", "turbo_status", f"active={turbo_act} temp={pkg_temp}C persist={is_persistence_enabled()}")

# ==============================================================================
# Interactive Flow (Default-on-Enter Contract)
# ==============================================================================

def run_interactive(hw: CPUHardware):
    print_status(hw)

    # 1. Action question
    current_turbo = hw.is_turbo_active()
    options = [
        i18n.t("opt_disable"),
        i18n.t("opt_enable"),
        i18n.t("opt_keep"),
    ]
    # Default is disable (index 0) if currently active, or keep (index 2) if already disabled
    default_idx = 0 if (current_turbo is True or current_turbo is None) else 2
    choice = prompt_choice(i18n.t("q_action"), options, default_index=default_idx)

    target_enable: Optional[bool] = None
    if choice == 0:
        target_enable = False
    elif choice == 1:
        target_enable = True
    else:
        print(f"\n{UI.MUTED}Nenhuma alteração realizada.{UI.RESET}\n" if i18n.lang == "pt-BR" else f"\n{UI.MUTED}No changes made.{UI.RESET}\n")
        return

    # Apply immediate action
    if target_enable is not None:
        if not check_root():
            ensure_root(["--disable" if not target_enable else "--enable", "--interactive-persist"])
            return

        apply_turbo_hardware(hw, target_enable)
        log_event("ok", "turbo_apply", f"enable={target_enable}")
        print(f"\n{UI.SUCCESS}✔ {i18n.t('state_changed')}{UI.RESET}")

    # 2. Persistence question
    persist_opts = [
        i18n.t("opt_persist_yes"),
        i18n.t("opt_persist_no"),
    ]
    if is_persistence_enabled():
        persist_opts.append(i18n.t("opt_persist_remove"))

    persist_choice = prompt_choice(i18n.t("q_persist"), persist_opts, default_index=0)
    if persist_choice == 0:
        install_persistence_service(target_enable)
        log_event("ok", "turbo_persist", f"enable={target_enable}")
        print(f"{UI.SUCCESS}✔ {i18n.t('service_installed')}{UI.RESET}\n")
    elif persist_choice == 2:
        remove_persistence_service()
        log_event("ok", "turbo_remove_persist", "")
        print(f"{UI.SUCCESS}✔ {i18n.t('service_removed')}{UI.RESET}\n")
    else:
        print("")

# ==============================================================================
# CLI Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CPU Turbo Boost Management & Runaway Watchdog (Linux Wayland Suite)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--status", action="store_true", help="Display current Turbo Boost and thermal status")
    group.add_argument("--off", "--disable", action="store_true", help="Disable CPU Turbo Boost (Quiet & Cool)")
    group.add_argument("--on", "--enable", action="store_true", help="Enable CPU Turbo Boost (Maximum Performance)")
    group.add_argument("--toggle", action="store_true", help="Toggle current Turbo Boost state")
    group.add_argument("--persist", action="store_true", help="Install systemd persistence service for current state")
    group.add_argument("--remove-persist", action="store_true", help="Remove systemd persistence service")
    group.add_argument("--watch", action="store_true", help="Scan and display runaway processes (>30% CPU)")
    group.add_argument("--json", action="store_true", help="Output machine-readable JSON status")
    group.add_argument("--interactive", action="store_true", help="Launch interactive guided prompt")
    parser.add_argument("--interactive-persist", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()
    hw = CPUHardware()

    # JSON Output
    if args.json:
        runaways = scan_runaway_processes(threshold_percent=30.0)
        out = {
            "vendor": hw.vendor,
            "model": hw.model,
            "driver": hw.driver,
            "turbo_supported": hw.is_turbo_supported(),
            "turbo_active": hw.is_turbo_active(),
            "frequencies": hw.get_core_frequencies(),
            "temperatures": hw.get_temperatures(),
            "governor_profile": hw.get_governor_profile(),
            "persistence_enabled": is_persistence_enabled(),
            "runaway_processes": runaways,
        }
        print(json.dumps(out, indent=2))
        return 0

    # Watchdog only
    if args.watch:
        print(render_banner(i18n.t("banner_title"), i18n.t("watchdog_header")))
        runaways = scan_runaway_processes(threshold_percent=25.0)
        if not runaways:
            print(f"  {UI.SUCCESS}✔ {i18n.t('no_runaway')}{UI.RESET}\n")
        else:
            w_headers = ["PID", "% CPU", "RAM (RSS)", "Comando" if i18n.lang == "pt-BR" else "Command"]
            w_rows = [[str(p["pid"]), f"{p['cpu_percent']}%", f"{p['memory_rss_mb']:.0f} MB", p["command"][:60]] for p in runaways]
            print(render_table(w_headers, w_rows))
            print("")
        return 0

    # Explicit Mutating Flags
    if args.off:
        ensure_root(["--off"])
        if apply_turbo_hardware(hw, False):
            log_event("ok", "turbo_off", "success")
            print(f"{UI.SUCCESS}✔ {i18n.t('state_changed')} [Turbo: OFF]{UI.RESET}")
            return 0
        sys.exit(1)

    if args.on:
        ensure_root(["--on"])
        if apply_turbo_hardware(hw, True):
            log_event("ok", "turbo_on", "success")
            print(f"{UI.SUCCESS}✔ {i18n.t('state_changed')} [Turbo: ON]{UI.RESET}")
            return 0
        sys.exit(1)

    if args.toggle:
        current = hw.is_turbo_active()
        target = not current if current is not None else False
        flag = "--enable" if target else "--disable"
        ensure_root([flag])
        apply_turbo_hardware(hw, target)
        print(f"{UI.SUCCESS}✔ {i18n.t('state_changed')} [Turbo: {'ON' if target else 'OFF'}]{UI.RESET}")
        return 0

    if args.persist:
        ensure_root(["--persist"])
        current_state = hw.is_turbo_active()
        target = current_state if current_state is not None else False
        if install_persistence_service(target):
            log_event("ok", "turbo_persist", f"enable={target}")
            print(f"{UI.SUCCESS}✔ {i18n.t('service_installed')} (Enforcing Turbo: {'ON' if target else 'OFF'}){UI.RESET}")
            return 0
        sys.exit(1)

    if args.remove_persist:
        ensure_root(["--remove-persist"])
        if remove_persistence_service():
            log_event("ok", "turbo_remove_persist", "success")
            print(f"{UI.SUCCESS}✔ {i18n.t('service_removed')}{UI.RESET}")
            return 0
        sys.exit(1)

    if args.interactive_persist:
        # Re-invoked under sudo from run_interactive
        persist_opts = [i18n.t("opt_persist_yes"), i18n.t("opt_persist_no")]
        if is_persistence_enabled():
            persist_opts.append(i18n.t("opt_persist_remove"))
        p_choice = prompt_choice(i18n.t("q_persist"), persist_opts, default_index=0)
        target = hw.is_turbo_active()
        if p_choice == 0:
            install_persistence_service(target if target is not None else False)
            print(f"{UI.SUCCESS}✔ {i18n.t('service_installed')}{UI.RESET}\n")
        elif p_choice == 2:
            remove_persistence_service()
            print(f"{UI.SUCCESS}✔ {i18n.t('service_removed')}{UI.RESET}\n")
        return 0

    # Interactive vs Status
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()
    if args.interactive or (is_tty and len(sys.argv) == 1):
        run_interactive(hw)
    else:
        print_status(hw)

    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
profile-machine.py — Non-destructive Machine Profiler & Scanner for linux-wayland-suite
Inspects hardware, system environment, batteries, GPUs, Wi-Fi, input devices, and Chromium apps.
Saves structured JSON profile to ~/.config/linux-wayland-suite/machine-profile.json.
Bilingual support (en / pt-BR).
"""

import os
import re
import sys
import glob
import json
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, log_event, app_display_name

PROFILE_DIR = os.path.expanduser("~/.config/linux-wayland-suite")
PROFILE_FILE = os.path.join(PROFILE_DIR, "machine-profile.json")

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "banner_title": {
        "en": "Linux Wayland Suite — Machine Profiler & Scan",
        "pt-BR": "Linux Wayland Suite — Machine Profiler & Scan",
    },
    "sec1_sys": {
        "en": "[1/6] Identifying System, Session, and Environment...",
        "pt-BR": "[1/6] Identificando Sistema, Sessão e Ambiente...",
    },
    "lbl_hardware": {"en": "Hardware", "pt-BR": "Hardware"},
    "lbl_board": {"en": "Board", "pt-BR": "Placa"},
    "lbl_system": {"en": "System", "pt-BR": "Sistema"},
    "lbl_session": {"en": "Session", "pt-BR": "Sessão"},
    "lbl_harness": {"en": "Harness", "pt-BR": "Harness"},
    "lbl_lang": {"en": "Language", "pt-BR": "Idioma"},
    "sec2_cpu": {
        "en": "[2/6] Inspecting CPU, Turbo Boost, and Thermals...",
        "pt-BR": "[2/6] Inspecionando CPU, Turbo Boost e Térmica...",
    },
    "cpu_model": {
        "en": "Processor: {model} (Driver: {driver})",
        "pt-BR": "Processador: {model} (Driver: {driver})",
    },
    "cpu_turbo_on": {
        "en": "Turbo Boost: ACTIVE (High Performance / Increased heat)",
        "pt-BR": "Turbo Boost: ATIVO (Alto Desempenho / Aquecimento rápido)",
    },
    "cpu_turbo_off": {
        "en": "Turbo Boost: DISABLED (Quiet & Cool mode)",
        "pt-BR": "Turbo Boost: DESATIVADO (Modo Silencioso / Frio)",
    },
    "cpu_temp": {
        "en": "CPU Package Temperature: {temp}°C",
        "pt-BR": "Temperatura da CPU: {temp}°C",
    },
    "sec3_power": {
        "en": "[3/6] Inspecting Battery and Power Management...",
        "pt-BR": "[3/6] Inspecionando Bateria e Gerenciamento de Energia...",
    },
    "bat_present": {
        "en": "Battery: Present | Health: {health}% | Charge: {charge}% ({state})",
        "pt-BR": "Bateria: Presente | Saúde: {health}% | Carga: {charge}% ({state})",
    },
    "bat_missing": {
        "en": "Battery: Not detected (Desktop / Direct AC power)",
        "pt-BR": "Bateria: Não detectada (Desktop / Alimentação AC Direta)",
    },
    "current_source": {
        "en": "Current Power Source: {source}",
        "pt-BR": "Fonte de Alimentação Atual: {source}",
    },
    "sec4_gpu": {
        "en": "[4/6] Inspecting GPUs and Internal Display...",
        "pt-BR": "[4/6] Inspecionando Placas de Vídeo e Tela Interna...",
    },
    "gpu_entry": {
        "en": "GPU: {vendor} ({card}, PCI {pci}, driver {driver})",
        "pt-BR": "GPU: {vendor} ({card}, PCI {pci}, driver {driver})",
    },
    "panel_tag": {"en": "[Internal Panel]", "pt-BR": "[Painel Interno]"},
    "display_entry": {
        "en": "Internal Display: {name} | Current: {hz} Hz",
        "pt-BR": "Tela Interna: {name} | Taxa atual: {hz} Hz",
    },
    "disp_rejected": {
        "en": "(Fixed native rate, driver rejects 60 Hz)",
        "pt-BR": "(Taxa nativa fixa, driver rejeita 60 Hz)",
    },
    "sec5_wifi": {
        "en": "[5/6] Inspecting Wi-Fi Adapter and Power Management...",
        "pt-BR": "[5/6] Inspecionando Placa Wi-Fi e Gerenciamento de Energia...",
    },
    "wifi_none": {
        "en": "Wi-Fi: No wireless network interfaces detected",
        "pt-BR": "Wi-Fi: Nenhuma interface de rede sem fio detectada",
    },
    "sec6_input": {
        "en": "[6/6] Inspecting Keyboards, Touchpad, and Input Devices...",
        "pt-BR": "[6/6] Inspecionando Teclado, Touchpad e Dispositivos de Entrada...",
    },
    "smart_wifi_active": {
        "en": "Smart Wi-Fi Power: [ACTIVE] (Dynamic AC vs Battery switching installed)",
        "pt-BR": "Smart Wi-Fi Power: [ATIVO] (Alternância automática AC vs Bateria instalada)",
    },
    "smart_wifi_inactive": {
        "en": "Smart Wi-Fi Power: [INACTIVE] (Available for setup)",
        "pt-BR": "Smart Wi-Fi Power: [INATIVO] (Disponível para configuração)",
    },
    "i8042_bus": {"en": "i8042 Bus: {state}", "pt-BR": "Barramento i8042: {state}"},
    "tongfang_detected": {
        "en": "Tongfang/Avell Chassis: Detected (GRUB Unlock: {status})",
        "pt-BR": "Chassis Tongfang/Avell: Detectado (Desbloqueio GRUB: {status})",
    },
    "touchpad": {"en": "Touchpad: {state}", "pt-BR": "Touchpad: {state}"},
    "mouse_mx": {
        "en": "Logitech MX Master 3S Mouse: {state}",
        "pt-BR": "Mouse Logitech MX Master 3S: {state}",
    },
    "autoheal": {
        "en": "Layout Auto-Heal (KWin Protection): {state}",
        "pt-BR": "Layout Auto-Heal (Proteção KWin): {state}",
    },
    "chromium_detected": {
        "en": "Chromium/Electron Apps Detected: {count} app(s) ({names})",
        "pt-BR": "Apps Chromium/Electron detectados: {count} app(s) ({names})",
    },
    "present": {"en": "Present", "pt-BR": "Presente"},
    "absent": {"en": "Absent", "pt-BR": "Ausente"},
    "detected": {"en": "Detected", "pt-BR": "Detectado"},
    "not_detected": {"en": "Not detected", "pt-BR": "Não detectado"},
    "installed": {"en": "[INSTALLED]", "pt-BR": "[INSTALADO]"},
    "not_installed": {"en": "[NOT INSTALLED]", "pt-BR": "[NÃO INSTALADO]"},
    "ok_tag": {"en": "[OK]", "pt-BR": "[OK]"},
    "pending_tag": {"en": "[Pending]", "pt-BR": "[Pendente]"},
    "success_saved": {
        "en": "✔ Machine profile saved successfully to: {path}",
        "pt-BR": "✔ Perfil da máquina salvo com sucesso em: {path}",
    },
    "setup_hint": {
        "en": "To configure and apply recommended optimizations:\n  Run: ./bin/linux-wayland-config setup (or 'make setup')",
        "pt-BR": "Para configurar e aplicar as otimizações recomendadas:\n  Execute: ./bin/linux-wayland-config setup (ou 'make setup')",
    },
}

i18n = I18n(STRINGS)

def read_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return default

def get_os_release() -> Dict[str, str]:
    data = {}
    if os.path.isfile("/etc/os-release"):
        for line in read_file("/etc/os-release").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"')
    return data

def check_battery_upower() -> Dict[str, Any]:
    res = {
        "has_battery": False,
        "health": None,
        "rate": None,
        "charge": None,
        "state": None,
    }
    if not shutil.which("upower"):
        return res

    try:
        out = subprocess.check_output(["upower", "-e"], text=True, stderr=subprocess.DEVNULL)
        bat_lines = [l.strip() for l in out.splitlines() if "battery" in l.lower()]
        if not bat_lines:
            return res

        bat_path = bat_lines[0]
        res["has_battery"] = True
        info = subprocess.check_output(["upower", "-i", bat_path], text=True, stderr=subprocess.DEVNULL)

        e_full, e_design = None, None
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("energy-full:") and not line.startswith("energy-full-design:"):
                val = re.search(r"[\d.,]+", line)
                if val: e_full = float(val.group(0).replace(",", "."))
            elif line.startswith("energy-full-design:"):
                val = re.search(r"[\d.,]+", line)
                if val: e_design = float(val.group(0).replace(",", "."))
            elif line.startswith("energy-rate:"):
                val = re.search(r"[\d.,]+", line)
                if val: res["rate"] = float(val.group(0).replace(",", "."))
            elif line.startswith("percentage:"):
                val = re.search(r"\d+", line)
                if val: res["charge"] = int(val.group(0))
            elif line.startswith("state:"):
                parts = line.split(":", 1)
                if len(parts) > 1: res["state"] = parts[1].strip()

        if e_full and e_design and e_design > 0:
            res["health"] = round((e_full * 100.0) / e_design, 1)

    except Exception:
        pass
    return res

def get_kscreen_refresh_modes() -> Dict[str, Any]:
    res = {
        "edp_name": None,
        "current_hz": None,
        "current_mode_id": None,
        "mode_60_id": None,
        "mode_high_id": None,
    }
    if not shutil.which("kscreen-doctor"):
        return res

    try:
        out = subprocess.check_output(["kscreen-doctor", "-o"], text=True, stderr=subprocess.DEVNULL)
        clean = re.sub(r"\x1b\[[0-9;]*m", "", out)
        edp_m = re.search(r"Output:\s+\d+\s+(eDP[^\s]*)", clean)
        if not edp_m:
            return res

        res["edp_name"] = edp_m.group(1)
        # Scan modes
        modes = re.findall(r"(\d+)\s+(\d+)x(\d+)@(\d+)\s*(?:[^\n]*)", clean)
        highest_hz = 0
        for m_id, w, h, hz in modes:
            hz_int = int(hz)
            if "@" + hz in clean and "*current*" in clean:
                res["current_hz"] = hz_int
            if hz_int == 60 and not res["mode_60_id"]:
                res["mode_60_id"] = m_id
            if hz_int > highest_hz:
                highest_hz = hz_int
                res["mode_high_id"] = m_id
    except Exception:
        pass
    return res

def discover_chromium_apps() -> List[str]:
    search_globs = [
        "/opt/*/*",
        "/opt/*/*/*",
        "/usr/lib/electron*/electron",
        "/usr/lib/chromium/chromium",
        "/usr/share/code/code",
        "/usr/share/code-insiders/code-insiders",
        "/usr/share/vscodium*/codium*",
        os.path.expanduser("~/.config/discord/app-*/Discord"),
        "/usr/lib/discord/Discord",
        "/opt/discord/Discord",
    ]
    found = set()
    for pat in search_globs:
        for p in glob.glob(pat):
            if os.path.isfile(p) and os.access(p, os.X_OK):
                if p.endswith(".orig") or ".bak-" in p or ".tmp-" in p or p.endswith(".bak"):
                    continue
                try:
                    rp = os.path.realpath(p)
                    if os.path.getsize(rp) > 25 * 1024 * 1024:
                        with open(rp, "rb") as f:
                            if f.read(4) == b"\x7fELF":
                                found.add(rp)
                except Exception:
                    continue
    return sorted(list(found))


def main():
    print(render_banner(i18n.t("banner_title")))

    # 1. System, Session & Harness
    print(f"{UI.BOLD}{i18n.t('sec1_sys')}{UI.RESET}")
    hostname_str = read_file("/etc/hostname", "localhost")
    kernel_str = os.uname().release
    arch_str = os.uname().machine
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")

    os_info = get_os_release()
    distro_id = os_info.get("ID", "unknown")
    distro_name = os_info.get("PRETTY_NAME") or os_info.get("NAME", "Linux")

    active_harness = "terminal"
    active_lang = get_active_language()

    # DMI
    dmi_vendor = read_file("/sys/class/dmi/id/sys_vendor", "unknown")
    dmi_product = read_file("/sys/class/dmi/id/product_name", "unknown")
    dmi_board = read_file("/sys/class/dmi/id/board_name", "unknown")
    chassis_type = read_file("/sys/class/dmi/id/chassis_type", "0")
    is_laptop = chassis_type in ("8", "9", "10", "11", "12", "14", "31", "32")

    print(f"  • {i18n.t('lbl_hardware')}: {UI.BOLD}{dmi_vendor} / {dmi_product}{UI.RESET} ({i18n.t('lbl_board')}: {dmi_board})")
    print(f"  • {i18n.t('lbl_system')}:  {UI.BOLD}{distro_name}{UI.RESET} (Kernel {kernel_str}, {arch_str})")
    print(f"  • {i18n.t('lbl_session')}:   {UI.BOLD}{desktop}{UI.RESET} ({session_type})")
    print(f"  • {i18n.t('lbl_harness')}:  {UI.BOLD}{active_harness}{UI.RESET} ({i18n.t('lbl_lang')}: {active_lang})")

    # 2. CPU, Turbo Boost & Thermals
    print(f"\n{UI.BOLD}{i18n.t('sec2_cpu')}{UI.RESET}")
    cpu_vendor = "unknown"
    cpu_model = "Unknown Processor"
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("vendor_id") and cpu_vendor == "unknown":
                    v = line.split(":", 1)[1].strip().lower()
                    if "intel" in v: cpu_vendor = "intel"
                    elif "amd" in v: cpu_vendor = "amd"
                elif line.startswith("model name") and cpu_model == "Unknown Processor":
                    cpu_model = line.split(":", 1)[1].strip()
    except Exception:
        pass

    intel_no_turbo = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    amd_boost = "/sys/devices/system/cpu/cpufreq/boost"
    turbo_supported = False
    turbo_active = None
    if os.path.exists(intel_no_turbo):
        turbo_supported = True
        turbo_active = (read_file(intel_no_turbo) != "1")
    elif os.path.exists(amd_boost):
        turbo_supported = True
        turbo_active = (read_file(amd_boost) == "1")

    pkg_temp = 0.0
    for h in glob.glob("/sys/class/hwmon/hwmon*"):
        name = read_file(os.path.join(h, "name"))
        if name in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
            for t in glob.glob(os.path.join(h, "temp*_input")):
                try:
                    val = float(read_file(t, "0")) / 1000.0
                    if val > pkg_temp:
                        pkg_temp = val
                except ValueError:
                    pass

    driver = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver", "unknown")
    gov = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "unknown")
    persist = os.path.exists("/etc/systemd/system/linux-wayland-cpu-turbo.service")

    cpu_data = {
        "vendor": cpu_vendor,
        "model": cpu_model,
        "driver": driver,
        "governor": gov,
        "turbo_supported": turbo_supported,
        "turbo_active": turbo_active,
        "package_temp_c": round(pkg_temp, 1) if pkg_temp > 0 else None,
        "persistence_enabled": persist,
    }

    print(f"  • {i18n.t('cpu_model', model=f'{UI.BOLD}{cpu_model}{UI.RESET}', driver=driver)}")
    if turbo_supported:
        t_color = UI.WARNING if turbo_active else UI.SUCCESS
        t_msg = i18n.t("cpu_turbo_on") if turbo_active else i18n.t("cpu_turbo_off")
        print(f"  • {t_color}[{ 'ATIVO' if turbo_active else 'DESATIVADO' }]{UI.RESET} {t_msg}")
    if pkg_temp > 0:
        temp_color = UI.SUCCESS if pkg_temp < 60 else (UI.WARNING if pkg_temp < 75 else UI.DANGER)
        print(f"  • {i18n.t('cpu_temp', temp=f'{temp_color}{UI.BOLD}{pkg_temp:.1f}{UI.RESET}')}")

    # 3. Battery & Power
    print(f"\n{UI.BOLD}{i18n.t('sec3_power')}{UI.RESET}")
    has_ac = False
    for p_sup in glob.glob("/sys/class/power_supply/*"):
        t = read_file(os.path.join(p_sup, "type"))
        if t in ("Mains", "AC", "ADP0", "ADP1"):
            if read_file(os.path.join(p_sup, "online")) == "1":
                has_ac = True

    current_source = "AC" if has_ac else "BATTERY"
    bat_data = check_battery_upower()
    thresh_supported = len(glob.glob("/sys/class/power_supply/BAT*/charge_control_end_threshold")) > 0

    if bat_data["has_battery"]:
        health_str = f"{bat_data['health']}" if bat_data['health'] is not None else "N/A"
        charge_str = f"{bat_data['charge']}" if bat_data['charge'] is not None else "N/A"
        state_str = bat_data['state'] or "unknown"
        print(f"  • {i18n.t('bat_present', health=health_str, charge=charge_str, state=state_str)}")
        print(f"  • {i18n.t('current_source', source=f'{UI.BOLD}{current_source}{UI.RESET}')}")
    else:
        print(f"  • {i18n.t('bat_missing')}")
        print(f"  • {i18n.t('current_source', source=f'{UI.BOLD}{current_source}{UI.RESET}')}")

    # 3. GPUs, Compositor & Internal Display
    print(f"\n{UI.BOLD}{i18n.t('sec4_gpu')}{UI.RESET}")
    edp_pci = None
    for st in glob.glob("/sys/class/drm/card*-eDP-*/status"):
        if read_file(st) == "connected":
            card_dir = os.path.dirname(st)
            card = os.path.basename(card_dir).split("-")[0]
            try:
                edp_pci = os.path.basename(os.path.realpath(f"/sys/class/drm/{card}/device"))
            except Exception:
                pass
            break

    gpus = []
    for card_dir in sorted(glob.glob("/sys/class/drm/card[0-9]")):
        c_name = os.path.basename(card_dir)
        try:
            pci_addr = os.path.basename(os.path.realpath(f"{card_dir}/device"))
            driver = os.path.basename(os.path.realpath(f"{card_dir}/device/driver"))
            v_id = read_file(f"{card_dir}/device/vendor").lower()
            v_name = "Intel" if "8086" in v_id else ("NVIDIA" if "10de" in v_id else ("AMD" if "1002" in v_id else "Other"))
            is_panel = (edp_pci is not None) and (pci_addr == edp_pci)
            gpus.append({
                "vendor": v_name,
                "card": c_name,
                "pci": pci_addr,
                "driver": driver,
                "is_panel": is_panel
            })
            tag = f" {UI.CYAN}{i18n.t('panel_tag')}{UI.RESET}" if is_panel else ""
            print(f"  • {i18n.t('gpu_entry', vendor=f'{UI.BOLD}{v_name}{UI.RESET}', card=c_name, pci=pci_addr, driver=driver)}{tag}")
        except Exception:
            continue

    disp_info = get_kscreen_refresh_modes()
    # Check if rejected in previous profile
    mode_60_rejected = False
    if os.path.isfile(PROFILE_FILE):
        try:
            with open(PROFILE_FILE) as f:
                d = json.load(f)
                mode_60_rejected = bool(d.get("display", {}).get("mode_60_rejected"))
        except Exception:
            pass

    if disp_info["edp_name"]:
        hz_disp = f"{UI.BOLD}{disp_info['current_hz'] or 60}{UI.RESET}"
        edp_title = f"{UI.BOLD}{disp_info['edp_name']}{UI.RESET}"
        rej_note = f" {UI.DIM}{i18n.t('disp_rejected')}{UI.RESET}" if mode_60_rejected else ""
        print(f"  • {i18n.t('display_entry', name=edp_title, hz=hz_disp)}{rej_note}")

    # 4. Wi-Fi
    print(f"\n{UI.BOLD}{i18n.t('sec5_wifi')}{UI.RESET}")
    wifi_interfaces = []
    smart_wifi_active = os.path.isfile("/etc/udev/rules.d/90-linux-wayland-smart-wifi-power.rules")

    for iface_dir in glob.glob("/sys/class/net/*"):
        if os.path.isdir(f"{iface_dir}/wireless") or os.path.isdir(f"{iface_dir}/phy80211"):
            w_name = os.path.basename(iface_dir)
            try:
                driver = os.path.basename(os.path.realpath(f"{iface_dir}/device/driver"))
                pci = os.path.basename(os.path.realpath(f"{iface_dir}/device"))
                pm_file = f"{iface_dir}/device/power/control"
                pm_status = read_file(pm_file, "unknown")
                ps = "unknown"
                if shutil.which("iw"):
                    try:
                        iw_out = subprocess.check_output(["iw", "dev", w_name, "get", "power_save"], text=True, stderr=subprocess.DEVNULL)
                        ps = "on" if "on" in iw_out.lower() else ("off" if "off" in iw_out.lower() else ps)
                    except Exception:
                        pass
                wifi_interfaces.append({
                    "name": w_name,
                    "driver": driver,
                    "pci": pci,
                    "power_save": ps,
                    "pci_power_pm": pm_status
                })
                print(f"  • Interface: {UI.BOLD}{w_name}{UI.RESET} (Driver: {driver}, PCI: {pci})")
                print(f"    - 802.11 Power Save: {UI.BOLD}{ps}{UI.RESET} | PCIe Runtime PM: {pm_status}")
            except Exception:
                continue

    if wifi_interfaces:
        status_line = i18n.t("smart_wifi_active") if smart_wifi_active else i18n.t("smart_wifi_inactive")
        color = UI.SUCCESS if smart_wifi_active else UI.WARNING
        print(f"  • {color}{status_line}{UI.RESET}")
    else:
        print(f"  • {UI.MUTED}{i18n.t('wifi_none')}{UI.RESET}")

    # 5. Keyboards & Input
    print(f"\n{UI.BOLD}{i18n.t('sec6_input')}{UI.RESET}")
    i8042_present = os.path.exists("/sys/devices/platform/i8042/serio0")
    print(f"  • {i18n.t('i8042_bus', state=(UI.SUCCESS + i18n.t('present') + UI.RESET) if i8042_present else (UI.MUTED + i18n.t('absent') + UI.RESET))}")

    # Tongfang check
    dmi_str = f"{dmi_vendor} {dmi_product} {dmi_board}".lower()
    is_tongfang = any(k in dmi_str for k in ("tongfang", "avell", "clevo", "tuxedo", "schenker", "uniwill", "gk5", "gm5", "qc7"))
    cmdline = read_file("/proc/cmdline")
    tongfang_unlocked = ("i8042.nopnp=1" in cmdline) and ("acpi_osi=" in cmdline)

    if is_tongfang:
        tf_status = (UI.SUCCESS + i18n.t("ok_tag") + UI.RESET) if tongfang_unlocked else (UI.WARNING + i18n.t("pending_tag") + UI.RESET)
        print(f"  • {i18n.t('tongfang_detected', status=tf_status)}")

    # Touchpad
    touchpad_present = False
    mx_master_present = False
    for n_file in glob.glob("/sys/class/input/input*/name"):
        name_content = read_file(n_file).lower()
        if any(t in name_content for t in ("touchpad", "synaptics", "alps", "elan", "glidepoint")):
            touchpad_present = True
        if "mx master" in name_content:
            mx_master_present = True

    print(f"  • {i18n.t('touchpad', state=(UI.SUCCESS + i18n.t('detected') + UI.RESET) if touchpad_present else (UI.MUTED + i18n.t('not_detected') + UI.RESET))}")
    print(f"  • {i18n.t('mouse_mx', state=(UI.SUCCESS + i18n.t('detected') + UI.RESET) if mx_master_present else (UI.MUTED + i18n.t('not_detected') + UI.RESET))}")

    autoheal_installed = os.path.isfile(os.path.expanduser("~/.config/autostart/kde-wayland-suite-restore-layout.desktop")) or \
                         os.path.isfile(os.path.expanduser("~/.config/autostart/linux-wayland-layout-autoheal.desktop"))
    ah_badge = (UI.SUCCESS + i18n.t("installed") + UI.RESET) if autoheal_installed else (UI.WARNING + i18n.t("not_installed") + UI.RESET)
    print(f"  • {i18n.t('autoheal', state=ah_badge)}")

    # Chromium/Electron Apps
    chromium_apps = discover_chromium_apps()
    names = set()
    for ap in chromium_apps:
        names.add(app_display_name(ap))
    names_str = ", ".join(sorted(list(names))) if names else "N/A"
    print(f"  • {UI.BOLD}{i18n.t('chromium_detected', count=len(chromium_apps), names=names_str)}{UI.RESET}")

    # Build Structured JSON
    profile = {
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "hostname": hostname_str,
            "distro_id": distro_id,
            "distro_name": distro_name,
            "kernel": kernel_str,
            "arch": arch_str,
            "session_type": session_type,
            "desktop": desktop,
            "active_harness": active_harness,
            "active_language": active_lang
        },
        "dmi": {
            "vendor": dmi_vendor,
            "product": dmi_product,
            "board": dmi_board,
            "chassis_type": chassis_type,
            "is_laptop": is_laptop
        },
        "cpu": cpu_data,
        "power": {
            "has_battery": bat_data["has_battery"],
            "current_source": current_source,
            "battery_health_percent": bat_data["health"],
            "battery_charge_percent": bat_data["charge"],
            "battery_state": bat_data["state"],
            "charge_threshold_supported": thresh_supported
        },
        "display": {
            "edp_name": disp_info["edp_name"],
            "current_hz": disp_info["current_hz"],
            "mode_60_available": False if mode_60_rejected else bool(disp_info["mode_60_id"]),
            "mode_60_rejected": mode_60_rejected,
            "mode_high_available": bool(disp_info["mode_high_id"]),
            "kwin_gpu_mismatch": False,
            "kwin_drm_configured": None
        },
        "wifi": {
            "interfaces": wifi_interfaces,
            "smart_wifi_power_installed": smart_wifi_active
        },
        "input": {
            "i8042_present": i8042_present,
            "is_tongfang_candidate": is_tongfang,
            "tongfang_grub_unlocked": tongfang_unlocked,
            "smart_keyboard_power_installed": os.path.isfile("/etc/udev/rules.d/90-kde-smart-keyboard-power.rules"),
            "touchpad_present": touchpad_present,
            "mx_master_present": mx_master_present,
            "layout_autoheal_installed": autoheal_installed
        },
        "chromium_apps": {
            "count": len(chromium_apps),
            "installed_binaries": chromium_apps,
            "cedilla_hook_installed": os.path.isfile("/etc/pacman.d/hooks/99-cedilla-wayland.hook")
        }
    }

    os.makedirs(PROFILE_DIR, exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    log_event("ok", "machine_profile_saved", PROFILE_FILE)
    print(f"\n{UI.SUCCESS}{i18n.t('success_saved', path=UI.BOLD + PROFILE_FILE + UI.RESET)}{UI.RESET}")
    print(f"\n{i18n.t('setup_hint')}\n")

    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)

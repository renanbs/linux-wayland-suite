#!/usr/bin/env python3
"""
diagnose-battery.py — Battery, Power Consumption & Hybrid GPU Diagnostic for linux-wayland-suite
Audits battery health, compositor primary GPU vs internal panel eDP, PCIe ASPM policies,
PCI runtime power management, idle radios, and CPU governors. Read-only.
Bilingual support (en / pt-BR).
"""

import os
import re
import sys
import glob
import shutil
import subprocess
from typing import Dict, List, Optional, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, log_event

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "banner_title": {
        "en": "Battery & Power Consumption Diagnostic",
        "pt-BR": "Diagnóstico de Bateria / Consumo de Energia",
    },
    "sec1_bat": {"en": "[1/6] Battery", "pt-BR": "[1/6] Bateria"},
    "sec2_gpu": {
        "en": "[2/6] Compositor Primary GPU (Hybrid Intel/NVIDIA/AMD)",
        "pt-BR": "[2/6] GPU Primária do Compositor (híbrido Intel/NVIDIA/AMD)",
    },
    "sec3_aspm": {
        "en": "[3/6] PCIe ASPM (Active State Power Management)",
        "pt-BR": "[3/6] PCIe ASPM (economia de energia do barramento PCIe)",
    },
    "sec4_runtime_pm": {
        "en": "[4/6] PCI Device Runtime Power Management",
        "pt-BR": "[4/6] Runtime Power Management de dispositivos PCI",
    },
    "sec5_radios": {
        "en": "[5/6] Idle Radios and Services",
        "pt-BR": "[5/6] Rádios e Serviços",
    },
    "sec6_cpu": {"en": "[6/6] CPU", "pt-BR": "[6/6] CPU"},
    "done": {
        "en": "✔ Diagnostic completed.",
        "pt-BR": "✔ Diagnóstico concluído.",
    },
}

i18n = I18n(STRINGS)

FINDINGS_FILE = os.environ.get("DIAGNOSE_BATTERY_FINDINGS_FILE", "")

def emit_finding(finding_id: str, detail: str = ""):
    if FINDINGS_FILE:
        try:
            with open(FINDINGS_FILE, "a", encoding="utf-8") as f:
                f.write(f"FINDING:{finding_id}:{detail}\n")
        except Exception:
            pass
    log_event("warn", finding_id, detail)


def read_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return default


def audit_battery():
    print(f"{UI.BOLD}{i18n.t('sec1_bat')}{UI.RESET}")
    bat_path = None
    if shutil.which("upower"):
        try:
            out = subprocess.check_output(["upower", "-e"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "battery" in line.lower():
                    bat_path = line.strip()
                    break
        except Exception:
            pass

    if bat_path and shutil.which("upower"):
        try:
            info = subprocess.check_output(["upower", "-i", bat_path], text=True, stderr=subprocess.DEVNULL)
            e_full, e_design, rate, pct, state = None, None, None, None, None
            for line in info.splitlines():
                line = line.strip()
                if line.startswith("energy-full:") and not line.startswith("energy-full-design:"):
                    m = re.search(r"[\d.,]+", line)
                    if m: e_full = float(m.group(0).replace(",", "."))
                elif line.startswith("energy-full-design:"):
                    m = re.search(r"[\d.,]+", line)
                    if m: e_design = float(m.group(0).replace(",", "."))
                elif line.startswith("energy-rate:"):
                    m = re.search(r"[\d.,]+", line)
                    if m: rate = float(m.group(0).replace(",", "."))
                elif line.startswith("percentage:"):
                    m = re.search(r"\d+", line)
                    if m: pct = int(m.group(0))
                elif line.startswith("state:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1: state = parts[1].strip()

            if e_full and e_design and e_design > 0:
                health = round((e_full * 100.0) / e_design, 1)
                print(f"  • Capacidade real: {e_full} Wh / projeto: {e_design} Wh ({UI.BOLD}{health}%{UI.RESET} de saúde)" if i18n.lang == "pt-BR" else f"  • Real Capacity: {e_full} Wh / Design: {e_design} Wh ({UI.BOLD}{health}%{UI.RESET} health)")
                log_event("metric", "battery_health_percent", str(health))
                log_event("metric", "battery_energy_full_wh", str(e_full))
                if health < 80:
                    print(f"    {UI.YELLOW}[INFO]{UI.RESET} Bateria com desgaste considerável (físico)." if i18n.lang == "pt-BR" else f"    {UI.YELLOW}[INFO]{UI.RESET} Significant battery degradation (physical cell wear).")
                    emit_finding("battery_health_degraded", f"health={health}%")

            if state and rate:
                print(f"  • Estado: {state} | Consumo: {UI.BOLD}{rate} W{UI.RESET} | Carga: {pct}%" if i18n.lang == "pt-BR" else f"  • State: {state} | Discharge rate: {UI.BOLD}{rate} W{UI.RESET} | Charge: {pct}%")
                log_event("metric", "battery_rate_w", str(rate))
                log_event("metric", "battery_charge_percent", str(pct or 0))
        except Exception:
            pass
    else:
        print(f"  • {UI.YELLOW}[INFO]{UI.RESET} Nenhuma bateria detectada via upower." if i18n.lang == "pt-BR" else f"  • {UI.YELLOW}[INFO]{UI.RESET} No battery detected via upower.")

    # Charge threshold
    thresh_files = glob.glob("/sys/class/power_supply/BAT*/charge_control_end_threshold")
    if thresh_files:
        val = read_file(thresh_files[0])
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Suporte a limite de carga disponível: {thresh_files[0]} (atual: {val})" if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Charge threshold supported: {thresh_files[0]} (current: {val})")
    else:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Sem suporte a limite de carga em sysfs." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} No charge threshold support in sysfs.")


def audit_gpu():
    print(f"\n{UI.BOLD}{i18n.t('sec2_gpu')}{UI.RESET}")
    # Locate KWIN_DRM_DEVICES
    kwin_env_file = None
    kwin_drm_value = None
    env_dir = os.path.expanduser("~/.config/plasma-workspace/env")
    if os.path.isdir(env_dir):
        for f in glob.glob(os.path.join(env_dir, "*.sh")):
            content = read_file(f)
            if "KWIN_DRM_DEVICES" in content:
                kwin_env_file = f
                for line in content.splitlines():
                    if "KWIN_DRM_DEVICES" in line:
                        m = re.search(r'KWIN_DRM_DEVICES=["\']?([^"\']+)["\']?', line)
                        if m: kwin_drm_value = m.group(1)
                break

    if not kwin_drm_value:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Nenhum KWIN_DRM_DEVICES customizado encontrado (GPU única ou KWin escolhe automaticamente)." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} No custom KWIN_DRM_DEVICES found (single GPU or automatic selection).")
        return

    # Split DRM devices
    sentinel = "\x01"
    clean = kwin_drm_value.replace(r"\:", sentinel)
    first_dev = clean.split(":")[0].replace(sentinel, ":")
    try:
        first_real = os.path.realpath(first_dev)
        first_card = os.path.basename(first_real)
        first_pci = os.path.basename(os.path.realpath(f"/sys/class/drm/{first_card}/device"))
    except Exception:
        first_card = "?"
        first_pci = "?"

    # eDP card
    edp_card = None
    edp_pci = None
    for st in glob.glob("/sys/class/drm/card*-eDP-*/status"):
        if read_file(st) == "connected":
            card_dir = os.path.dirname(st)
            edp_card = os.path.basename(card_dir).split("-")[0]
            try:
                edp_pci = os.path.basename(os.path.realpath(f"/sys/class/drm/{edp_card}/device"))
            except Exception:
                pass
            break

    if not edp_card:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Nenhuma saída eDP conectada encontrada." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} No connected eDP display found.")
        return

    print(f"  • Arquivo com KWIN_DRM_DEVICES: {kwin_env_file}" if i18n.lang == "pt-BR" else f"  • File with KWIN_DRM_DEVICES: {kwin_env_file}")
    print(f"  • GPU primária configurada: {first_card} (PCI {first_pci})" if i18n.lang == "pt-BR" else f"  • Configured primary GPU: {first_card} (PCI {first_pci})")
    print(f"  • GPU que atende o painel interno (eDP): {edp_card} (PCI {edp_pci})" if i18n.lang == "pt-BR" else f"  • Internal panel GPU (eDP): {edp_card} (PCI {edp_pci})")

    if first_pci == edp_pci:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} A GPU primária do KWin já é a mesma do painel interno. Sem cópia extra de frames." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} KWin primary GPU matches the internal panel GPU. No extra frame copy overhead.")
        log_event("ok", "gpu_primary", f"primária={first_card}")
    else:
        print(f"  • {UI.DANGER}[FALHA]{UI.RESET} A GPU primária do KWin ({first_card}) é diferente da do painel interno ({edp_card})." if i18n.lang == "pt-BR" else f"  • {UI.DANGER}[FAIL]{UI.RESET} KWin primary GPU ({first_card}) differs from the internal panel GPU ({edp_card}).")
        emit_finding("gpu_primary_mismatch", f"current={kwin_drm_value};edp_pci={edp_pci}")


def audit_aspm():
    print(f"\n{UI.BOLD}{i18n.t('sec3_aspm')}{UI.RESET}")
    aspm_file = "/sys/module/pcie_aspm/parameters/policy"
    if not os.path.isfile(aspm_file):
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Suporte a ASPM ausente no kernel." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} ASPM sysfs policy file not present.")
        return

    raw = read_file(aspm_file)
    m = re.search(r"\[([a-z]+)\]", raw)
    current = m.group(1) if m else "unknown"
    print(f"  • Política atual: {UI.BOLD}{current}{UI.RESET} (opções: {raw})" if i18n.lang == "pt-BR" else f"  • Current policy: {UI.BOLD}{current}{UI.RESET} (options: {raw})")

    # Check dmesg / journalctl for firmware refusal
    no_control = False
    try:
        kmsg = subprocess.check_output(["journalctl", "-k", "-b"], text=True, stderr=subprocess.DEVNULL)
        if any(msg in kmsg for msg in ("does not support PCIe ASPM", "doesn't support PCIe ASPM", "FADT indicates ASPM is unsupported")):
            no_control = True
    except Exception:
        pass

    if no_control:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} O firmware desta máquina declara não suportar PCIe ASPM." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} System firmware reports PCIe ASPM is unsupported.")
        log_event("info", "pcie_aspm", "unsupported_firmware")
    elif current in ("performance", "default"):
        print(f"  • {UI.YELLOW}[INFO]{UI.RESET} Política '{current}' não é a mais econômica ('powersave' recomendado)." if i18n.lang == "pt-BR" else f"  • {UI.YELLOW}[INFO]{UI.RESET} Current policy '{current}' is not the most power efficient ('powersave' recommended).")
        emit_finding("pcie_aspm_not_powersave", f"current={current}")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Já em modo econômico ({current})." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Already in powersave mode ({current}).")
        log_event("ok", "pcie_aspm", current)


def audit_runtime_pm():
    print(f"\n{UI.BOLD}{i18n.t('sec4_runtime_pm')}{UI.RESET}")
    pci_controls = glob.glob("/sys/bus/pci/devices/*/power/control")
    not_auto = []
    for f in pci_controls:
        if read_file(f) != "auto":
            dev_addr = os.path.basename(os.path.dirname(os.path.dirname(f)))
            not_auto.append(dev_addr)

    if not pci_controls:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Nenhum dispositivo PCI com controle de runtime PM." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} No PCI devices with runtime PM controls found.")
        return

    total = len(pci_controls)
    if not not_auto:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Todos os {total} dispositivos PCI já estão com runtime PM em 'auto'." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} All {total} PCI devices have runtime PM set to 'auto'.")
        log_event("ok", "pci_runtime_pm", f"{total}/{total} auto")
        log_event("metric", "pci_devices_on_instead_of_auto", "0")
    else:
        print(f"  • {UI.YELLOW}[INFO]{UI.RESET} {len(not_auto)} de {total} dispositivos PCI com runtime PM fixo em 'on':" if i18n.lang == "pt-BR" else f"  • {UI.YELLOW}[INFO]{UI.RESET} {len(not_auto)} of {total} PCI devices have runtime PM fixed in 'on':")
        for addr in not_auto[:5]:
            print(f"      - {addr}")
        if len(not_auto) > 5:
            print(f"      - ... ({len(not_auto) - 5} outros)")
        emit_finding("pci_runtime_pm_not_auto", f"count={len(not_auto)}")
        log_event("metric", "pci_devices_on_instead_of_auto", str(len(not_auto)))


def audit_radios():
    print(f"\n{UI.BOLD}{i18n.t('sec5_radios')}{UI.RESET}")
    bt_active = False
    try:
        res = subprocess.run(["systemctl", "is-active", "--quiet", "bluetooth.service"])
        bt_active = (res.returncode == 0)
    except Exception:
        pass

    if bt_active:
        bt_conn = ""
        try:
            bt_conn = subprocess.check_output(["bluetoothctl", "devices", "Connected"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            pass
        if bt_conn:
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Bluetooth ativo com dispositivo(s) conectado(s)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Bluetooth active with connected device(s).")
        else:
            print(f"  • {UI.YELLOW}[INFO]{UI.RESET} Bluetooth ativo, mas sem dispositivos conectados." if i18n.lang == "pt-BR" else f"  • {UI.YELLOW}[INFO]{UI.RESET} Bluetooth active with no connected devices.")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Bluetooth desligado." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Bluetooth powered off.")

    docker_active = False
    try:
        res = subprocess.run(["systemctl", "is-active", "--quiet", "docker.service"])
        docker_active = (res.returncode == 0)
    except Exception:
        pass

    if docker_active:
        n_c = 0
        try:
            ps_out = subprocess.check_output(["docker", "ps", "-q"], text=True, stderr=subprocess.DEVNULL)
            n_c = len([l for l in ps_out.splitlines() if l.strip()])
        except Exception:
            pass
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Docker ativo ({n_c} container(s) rodando)." if i18n.lang == "pt-BR" else f"  • {UI.PRIMARY}[INFO]{UI.RESET} Docker daemon active ({n_c} running container(s)).")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Docker daemon inativo." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Docker daemon inactive.")


def audit_cpu():
    print(f"\n{UI.BOLD}{i18n.t('sec6_cpu')}{UI.RESET}")
    gov = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "?")
    prof = "?"
    if shutil.which("powerprofilesctl"):
        try:
            prof = subprocess.check_output(["powerprofilesctl", "get"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            pass

    # 1. Turbo Boost check
    intel_no_turbo = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    amd_boost = "/sys/devices/system/cpu/cpufreq/boost"
    turbo_state = None
    if os.path.exists(intel_no_turbo):
        turbo_state = (read_file(intel_no_turbo) != "1")
    elif os.path.exists(amd_boost):
        turbo_state = (read_file(amd_boost) == "1")

    turbo_msg = f"{UI.PRIMARY}[INFO]{UI.RESET} Turbo Boost: N/A"
    if turbo_state is True:
        turbo_msg = (
            f"  • {UI.WARNING}[INFO]{UI.RESET} Turbo Boost: ATIVO (Alto Desempenho / Aquecimento rápido)."
            if i18n.lang == "pt-BR"
            else f"  • {UI.WARNING}[INFO]{UI.RESET} Turbo Boost: ACTIVE (High Performance / Increased heat)."
        )
    elif turbo_state is False:
        turbo_msg = (
            f"  • {UI.SUCCESS}[OK]{UI.RESET} Turbo Boost: DESATIVADO (Modo Silencioso / Baixo consumo)."
            if i18n.lang == "pt-BR"
            else f"  • {UI.SUCCESS}[OK]{UI.RESET} Turbo Boost: DISABLED (Quiet / Cool mode)."
        )

    # 2. Temperature check
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

    temp_msg = ""
    if pkg_temp > 0:
        if pkg_temp >= 78.0:
            temp_msg = (
                f"  • {UI.DANGER}[ALERTA]{UI.RESET} Temperatura da CPU elevada: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET} (Coolers acionados no máximo)."
                if i18n.lang == "pt-BR"
                else f"  • {UI.DANGER}[ALERT]{UI.RESET} Elevated CPU temperature: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET} (Fans triggered)."
            )
            log_event("warn", "cpu_temp_high", f"{pkg_temp}C")
        elif pkg_temp >= 62.0:
            temp_msg = (
                f"  • {UI.WARNING}[AVISO]{UI.RESET} Temperatura da CPU moderada: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET}."
                if i18n.lang == "pt-BR"
                else f"  • {UI.WARNING}[WARN]{UI.RESET} Moderate CPU temperature: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET}."
            )
            log_event("info", "cpu_temp_moderate", f"{pkg_temp}C")
        else:
            temp_msg = (
                f"  • {UI.SUCCESS}[OK]{UI.RESET} Temperatura da CPU controlada: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET} (Frio/Silencioso)."
                if i18n.lang == "pt-BR"
                else f"  • {UI.SUCCESS}[OK]{UI.RESET} Controlled CPU temperature: {UI.BOLD}{pkg_temp:.1f}°C{UI.RESET} (Cool/Quiet)."
            )
            log_event("ok", "cpu_temp_normal", f"{pkg_temp}C")

    print(f"  • Governor: {UI.BOLD}{gov}{UI.RESET} | Perfil de energia: {UI.BOLD}{prof}{UI.RESET}" if i18n.lang == "pt-BR" else f"  • Scaling Governor: {UI.BOLD}{gov}{UI.RESET} | Power Profile: {UI.BOLD}{prof}{UI.RESET}")
    if temp_msg:
        print(temp_msg)
    print(turbo_msg)
    log_event("info", "cpu_governor", f"{gov} / {prof}")

def main():
    print(render_banner(i18n.t("banner_title")))
    audit_battery()
    audit_gpu()
    audit_aspm()
    audit_runtime_pm()
    audit_radios()
    audit_cpu()
    print(f"\n{UI.BOLD}{UI.SUCCESS}{i18n.t('done')}{UI.RESET}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)

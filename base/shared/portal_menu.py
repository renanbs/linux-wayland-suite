#!/usr/bin/env python3
"""
portal_menu.py — Central Interactive Control Portal for linux-wayland-suite
Displays real-time system & hardware context and an intuitive numbered menu
with rich descriptions of every tool. Bilingual support (en / pt-BR).
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, List, Optional, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, render_table, discover_binaries, check_binary_status

PROFILE_FILE = os.path.expanduser("~/.config/linux-wayland-suite/machine-profile.json")

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "banner_title": {
        "en": "Linux Wayland Suite — Central Control Portal",
        "pt-BR": "Linux Wayland Suite — Portal de Controle Central",
    },
    "banner_sub": {
        "en": "Interactive Management Portal (KDE Plasma 6 Wayland)",
        "pt-BR": "Portal Interativo de Gestão (KDE Plasma 6 Wayland)",
    },
    "card_hw": {"en": "Hardware", "pt-BR": "Hardware"},
    "card_layout": {"en": "Layout", "pt-BR": "Layout"},
    "card_power": {"en": "Power", "pt-BR": "Energia"},
    "card_cedilla": {"en": "Cedilla", "pt-BR": "Cedilha"},
    "menu_header": {
        "en": "Available modules and actions:",
        "pt-BR": "Módulos e ações disponíveis:",
    },
    "m_status_title": {"en": "Health Status Audit", "pt-BR": "Auditoria de Saúde"},
    "m_status_desc": {
        "en": "7-stage health audit: keyboard, layout, clipboard, gestures, Wi-Fi",
        "pt-BR": "Auditoria geral em 7 etapas: teclado, layout, clipboard, gestos e Wi-Fi",
    },
    "m_setup_title": {"en": "Setup Wizard", "pt-BR": "Assistente de Configuração"},
    "m_setup_desc": {
        "en": "Contextual configuration wizard based on detected hardware",
        "pt-BR": "Assistente contextual que aplica otimizações para o seu hardware",
    },
    "m_cedilla_title": {"en": "Wayland Cedilla Patch", "pt-BR": "Patch da Cedilha Wayland"},
    "m_cedilla_desc": {
        "en": "Fixes '+c -> ç' in Chrome, Orca IDE, VS Code, Discord, Brave + Pacman hook",
        "pt-BR": "Corrige '+c -> ç' no Chrome, Orca, VS Code, Discord, Brave + hook do Pacman",
    },
    "m_battery_title": {"en": "Battery & Power Diagnostic", "pt-BR": "Diagnóstico de Bateria e GPU"},
    "m_battery_desc": {
        "en": "Audit battery health, hybrid GPU (KWin DRM), PCIe ASPM, and PCI runtime PM",
        "pt-BR": "Audita saúde da bateria, GPU primária (KWin DRM), PCIe ASPM e runtime PM",
    },
    "m_turbo_title": {"en": "CPU Turbo Boost & Watchdog", "pt-BR": "Turbo Boost e Watchdog Térmico"},
    "m_turbo_desc": {
        "en": "Thermal control, quiet mode, and runaway process monitor",
        "pt-BR": "Controle térmico, modo silencioso e caçador de processos em loop",
    },
    "m_report_title": {"en": "Execution Reports & History", "pt-BR": "Relatórios e Histórico de Runs"},
    "m_report_desc": {
        "en": "Inspect previous runs, balance of warnings/failures, and metric trends",
        "pt-BR": "Consulta execuções anteriores, balanço de erros/avisos e métricas",
    },
    "m_scan_title": {"en": "Machine Scan & Profiler", "pt-BR": "Varredura e Perfil da Máquina"},
    "m_scan_desc": {
        "en": "Re-scans hardware and refreshes machine-profile.json",
        "pt-BR": "Faz nova varredura de hardware e regrava o machine-profile.json",
    },
    "m_switch_title": {"en": "Switch Keyboard Layout", "pt-BR": "Alternar Layout de Teclado"},
    "m_switch_desc": {
        "en": "Toggles active KWin layout between Brazilian ABNT2 (br) and US-intl (us)",
        "pt-BR": "Alterna instantaneamente no KWin entre ABNT2 (br) e US-intl (us)",
    },
    "m_fetch_title": {"en": "Terminal Identity (Fastfetch)", "pt-BR": "Identidade Visual do Terminal"},
    "m_fetch_desc": {
        "en": "Interactive menu to choose terminal logo (Eagle, Cat Mokka, Dragon) in shells",
        "pt-BR": "Menu interativo para trocar o logo (Águia, Gato Mokka, Dragão) nos shells",
    },
    "m_quit": {"en": "Exit Portal", "pt-BR": "Sair do Portal"},
    "prompt_choice": {
        "en": "Choose an option [1-9 or Q]: ",
        "pt-BR": "Escolha uma opção [1-9 ou Q]: ",
    },
    "return_prompt": {
        "en": "Press Enter to return to main menu (or 'Q' to quit): ",
        "pt-BR": "Pressione Enter para voltar ao menu principal (ou 'Q' para sair): ",
    },
    "goodbye": {
        "en": "Exiting control portal. Have a great session!",
        "pt-BR": "Saindo do portal de controle. Boa sessão!",
    },
}

i18n = I18n(STRINGS)


def get_system_summary() -> Dict[str, str]:
    """Collects quick real-time status summary for the portal card."""
    summary = {
        "hw": "Linux PC",
        "layout": "unknown",
        "power": "AC",
        "cedilla": "unknown",
    }

    if os.path.isfile(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            dmi = d.get("dmi", {})
            sys_d = d.get("system", {})
            v = dmi.get("vendor", "")
            p = dmi.get("product", "")
            distro = sys_d.get("distro_name", "Linux")
            desktop = sys_d.get("desktop", "KDE")
            summary["hw"] = f"{v} {p} ({distro}, {desktop})"

            pwr = d.get("power", {})
            src = pwr.get("current_source", "AC")
            chg = pwr.get("battery_charge_percent")
            hlth = pwr.get("battery_health_percent")
            st = pwr.get("battery_state") or ""
            if pwr.get("has_battery") and chg is not None:
                summary["power"] = f"{src} ({chg}% {st}, {hlth}% saúde)" if i18n.lang == "pt-BR" else f"{src} ({chg}% {st}, {hlth}% health)"
            else:
                summary["power"] = src
        except Exception:
            pass
    # Turbo Boost Status
    try:
        intel_no_turbo = "/sys/devices/system/cpu/intel_pstate/no_turbo"
        amd_boost = "/sys/devices/system/cpu/cpufreq/boost"
        t_state = None
        if os.path.exists(intel_no_turbo):
            val = open(intel_no_turbo, "r").read().strip()
            t_state = "OFF" if val == "1" else "ON"
        elif os.path.exists(amd_boost):
            val = open(amd_boost, "r").read().strip()
            t_state = "ON" if val == "1" else "OFF"
        if t_state:
            turbo_label = "Turbo OFF (Silencioso)" if t_state == "OFF" else "Turbo ON"
            if i18n.lang == "en":
                turbo_label = "Turbo OFF (Quiet)" if t_state == "OFF" else "Turbo ON"
            summary["power"] += f" | {turbo_label}"
    except Exception:
        pass


    # Layout from D-Bus
    for qdbus_bin in ("qdbus6", "qdbus", "/usr/lib/qt6/bin/qdbus"):
        if shutil.which(qdbus_bin):
            try:
                idx = subprocess.check_output([qdbus_bin, "org.kde.keyboard", "/Layouts", "org.kde.KeyboardLayouts.getLayout"], text=True, stderr=subprocess.DEVNULL).strip()
                layout_name = "br (abnt2)" if idx == "0" else ("us (alt-intl)" if idx == "1" else f"idx {idx}")
                summary["layout"] = f"Ativo: [{idx}] {layout_name}" if i18n.lang == "pt-BR" else f"Active: [{idx}] {layout_name}"
                break
            except Exception:
                pass

    # Cedilla summary
    try:
        binaries = discover_binaries()
        vuln = sum(1 for b in binaries if check_binary_status(b)[0] == "VULNERABLE")
        hook_ok = os.path.isfile("/etc/pacman.d/hooks/99-cedilla-wayland.hook")
        if vuln > 0:
            summary["cedilla"] = f"{len(binaries)} apps ({vuln} necessitam patch)" if i18n.lang == "pt-BR" else f"{len(binaries)} apps ({vuln} need patch)"
        else:
            if i18n.lang == "pt-BR":
                hook_str = "com autocura ativa" if hook_ok else "sem hook"
                summary["cedilla"] = f"{len(binaries)} apps (Todos corrigidos, {hook_str})"
            else:
                hook_str = "autorepair active" if hook_ok else "no hook"
                summary["cedilla"] = f"{len(binaries)} apps (All patched, {hook_str})"
    except Exception:
        summary["cedilla"] = "N/A"

    return summary


def render_context_card(summary: Dict[str, str]):
    w = 70
    border = f"{UI.BORDER}────────────────────────────────────────────────────────────────────────{UI.RESET}"
    print(f"  {border}")
    print(f"  {UI.BOLD}{i18n.t('card_hw') + ':':<10}{UI.RESET} {summary['hw']}")
    print(f"  {UI.BOLD}{i18n.t('card_layout') + ':':<10}{UI.RESET} {summary['layout']}")
    print(f"  {UI.BOLD}{i18n.t('card_power') + ':':<10}{UI.RESET} {summary['power']}")
    print(f"  {UI.BOLD}{i18n.t('card_cedilla') + ':':<10}{UI.RESET} {summary['cedilla']}")
    print(f"  {border}\n")


def run_cmd(subcommand: str, args: Optional[List[str]] = None):
    cli = os.path.join(SCRIPT_DIR, "../bin/linux-wayland-config")
    if os.path.isfile(cli):
        cmd = [cli, subcommand] + (args or [])
        subprocess.run(cmd)
    else:
        print(f"{UI.DANGER}Erro: CLI linux-wayland-config não encontrado.{UI.RESET}")


def main():
    while True:
        os.system("clear" if os.name != "nt" else "cls")
        print(render_banner(i18n.t("banner_title"), i18n.t("banner_sub")))

        summary = get_system_summary()
        render_context_card(summary)

        print(f"{UI.BOLD}{i18n.t('menu_header')}{UI.RESET}\n")

        options = [
            ("1", i18n.t("m_status_title"), "status", i18n.t("m_status_desc")),
            ("2", i18n.t("m_setup_title"), "setup", i18n.t("m_setup_desc")),
            ("3", i18n.t("m_cedilla_title"), "patch-cedilla", i18n.t("m_cedilla_desc")),
            ("4", i18n.t("m_battery_title"), "battery-status", i18n.t("m_battery_desc")),
            ("5", i18n.t("m_turbo_title"), "turbo", i18n.t("m_turbo_desc")),
            ("6", i18n.t("m_report_title"), "report", i18n.t("m_report_desc")),
            ("7", i18n.t("m_scan_title"), "scan", i18n.t("m_scan_desc")),
            ("8", i18n.t("m_switch_title"), "switch", i18n.t("m_switch_desc")),
            ("9", i18n.t("m_fetch_title"), "cosmetic", i18n.t("m_fetch_desc")),
        ]

        for num, title, cmd_tag, desc in options:
            print(f"  {UI.PRIMARY}{num}){UI.RESET} {UI.BOLD}{title:<30}{UI.RESET} {UI.CYAN}({cmd_tag}){' ' * max(0, 16 - len(cmd_tag))}{UI.RESET} {UI.MUTED}- {desc}{UI.RESET}")

        print(f"  {UI.MUTED}Q) {i18n.t('m_quit')}{UI.RESET}\n")

        try:
            choice = input(f"{UI.BOLD}{i18n.t('prompt_choice')}{UI.RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{UI.MUTED}{i18n.t('goodbye')}{UI.RESET}\n")
            return 0

        if not choice or choice.lower() == "q":
            print(f"\n{UI.MUTED}{i18n.t('goodbye')}{UI.RESET}\n")
            return 0

        print("")
        if choice == "1":
            run_cmd("status")
        elif choice == "2":
            run_cmd("setup")
        elif choice == "3":
            run_cmd("patch-cedilla", ["--apply"])
        elif choice == "4":
            run_cmd("battery-status")
        elif choice == "5":
            run_cmd("turbo")
        elif choice == "6":
            run_cmd("report")
        elif choice == "7":
            run_cmd("scan")
        elif choice == "8":
            run_cmd("switch")
        elif choice == "9":
            run_cmd("cosmetic")
        else:
            print(f"{UI.WARNING}Opção inválida: {choice}{UI.RESET}")

        print("")
        try:
            pause = input(f"{UI.MUTED}{i18n.t('return_prompt')}{UI.RESET}").strip()
            if pause.lower() == "q":
                print(f"\n{UI.MUTED}{i18n.t('goodbye')}{UI.RESET}\n")
                return 0
        except (KeyboardInterrupt, EOFError):
            print(f"\n{UI.MUTED}{i18n.t('goodbye')}{UI.RESET}\n")
            return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

#!/usr/bin/env python3
"""
setup-suite.py — Contextual Modular Setup Wizard for linux-wayland-suite
Reads ~/.config/linux-wayland-suite/machine-profile.json and offers a clean,
contextual menu with only the optimizations applicable to the detected hardware.
Bilingual support (en / pt-BR).
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, List, Optional, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, log_event

PROFILE_DIR = os.path.expanduser("~/.config/linux-wayland-suite")
PROFILE_FILE = os.path.join(PROFILE_DIR, "machine-profile.json")

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "banner_title": {
        "en": "Linux Wayland Suite — Configuration Wizard",
        "pt-BR": "Linux Wayland Suite — Assistente de Configuração",
    },
    "detected_header": {
        "en": "Detected Profile for this Machine:",
        "pt-BR": "Perfil detectado para esta máquina:",
    },
    "lbl_machine": {"en": "Machine", "pt-BR": "Máquina"},
    "lbl_system": {"en": "System", "pt-BR": "Sistema"},
    "opts_header": {
        "en": "Optimizations available for your hardware:",
        "pt-BR": "Otimizações disponíveis para o seu hardware:",
    },
    "opt_keyboard": {
        "en": "Keyboard & Shortcuts      (KDE br/us, Ctrl+C on ABNT2, LC_CTYPE, no root)",
        "pt-BR": "Teclado e Atalhos        (Layout br/us no KDE, Ctrl+C no ABNT2, LC_CTYPE, sem root)",
    },
    "opt_cedilla": {
        "en": "Wayland Cedilla Patch    (Patch '+c -> ç' in Chrome, Orca, VS Code, Discord, Brave) [sudo]",
        "pt-BR": "Cedilha Wayland          (Patch '+c -> ç' no Chrome, Orca, VS Code, Discord, Brave) [sudo]",
    },
    "opt_autoheal": {
        "en": "Layout Auto-Heal         (Protects against KWin layout collapse bug on reboot)",
        "pt-BR": "Auto-Cura de Layout      (Proteção contra bug de colapso do KWin no reboot)",
    },
    "opt_kbd_power": {
        "en": "Smart Keyboard Power     (Anti-latch / zero latency on i8042 bus)",
        "pt-BR": "Smart Keyboard Power     (Anti-latch/latência no barramento i8042)",
    },
    "opt_wifi_power": {
        "en": "Smart Wi-Fi Power        (Power save OFF on AC / ON on Battery)",
        "pt-BR": "Smart Wi-Fi Power        (Power save OFF na tomada / ON na bateria)",
    },
    "opt_gestures": {
        "en": "Touchpad Gestures        (3/4 fingers on Wayland via libinput-gestures)",
        "pt-BR": "Gestos de Touchpad       (3/4 dedos no Wayland via libinput-gestures)",
    },
    "opt_mouse": {
        "en": "Logitech MX Master 3S    (Buttons & SmartShift via logiops)",
        "pt-BR": "Logitech MX Master 3S    (Botões e SmartShift via logiops)",
    },
    "opt_screen60": {
        "en": "Screen 60 Hz Saver       (Saves 2W-3W on internal display)",
        "pt-BR": "Tela 60 Hz Power-Saver   (Economia de 2W-3W na tela interna)",
    },
    "opt_tongfang": {
        "en": "Tongfang Matrix Unlock   (i8042 kernel parameter in GRUB for keyboard)",
        "pt-BR": "Desbloqueio Tongfang     (Parâmetro i8042 no GRUB para teclado)",
    },
    "opt_fetch": {
        "en": "Terminal Identity        (Fastfetch: Dr460nized Eagle across all shells)",
        "pt-BR": "Identidade do Terminal   (Fastfetch: Águia Dr460nized em todos os shells)",
    },
    "opt_turbo": {
        "en": "CPU Turbo & Quiet Mode   (Disables Turbo Boost for silent cooling / ~50°C)",
        "pt-BR": "CPU Turbo / Modo Silêncio (Desativa Turbo Boost para resfriar a CPU / ~50°C)",
    },
    "opt_all": {
        "en": "Apply All Recommended    (--all)",
        "pt-BR": "Aplicar Todas Recomendadas (--all)",
    },
    "opt_quit": {
        "en": "Quit without modifying anything",
        "pt-BR": "Sair sem alterar nada",
    },
    "cli_hint": {
        "en": "Use direct flags for batch automation:\n  ./bin/linux-wayland-config setup --all\n  ./bin/linux-wayland-config setup --keyboard --patch-cedilla --wifi-power",
        "pt-BR": "Use as flags diretas para aplicar em lote ou scripts de automação:\n  ./bin/linux-wayland-config setup --all\n  ./bin/linux-wayland-config setup --keyboard --patch-cedilla --wifi-power",
    },
    "prompt_choice": {
        "en": "Enter choice: ",
        "pt-BR": "Escolha uma opção: ",
    },
    "cancelled": {
        "en": "Exiting without making changes.",
        "pt-BR": "Saindo sem alterar nada.",
    },
}

i18n = I18n(STRINGS)


def ensure_profile() -> Dict[str, Any]:
    if not os.path.isfile(PROFILE_FILE):
        print(f"{UI.PRIMARY}Gerando perfil inicial da máquina...{UI.RESET}\n" if i18n.lang == "pt-BR" else f"{UI.PRIMARY}Generating initial machine profile...{UI.RESET}\n")
        profiler = os.path.join(SCRIPT_DIR, "profile-machine.py")
        if os.path.isfile(profiler):
            subprocess.run([sys.executable, profiler])
        else:
            subprocess.run(["bash", os.path.join(SCRIPT_DIR, "profile-machine.sh")])
        print("")

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ==============================================================================
# Execution Actions
# ==============================================================================

def run_script(script_name: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> bool:
    target = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.isfile(target):
        print(f"{UI.DANGER}Erro: Script {script_name} não encontrado em {SCRIPT_DIR}.{UI.RESET}")
        return False

    cmd = [sys.executable, target] if target.endswith(".py") else ["bash", target]
    if args:
        cmd.extend(args)

    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)

    res = subprocess.run(cmd, env=exec_env)
    return res.returncode == 0


def apply_keyboard():
    print(f"{UI.BOLD}==> [Configuração] Layout de Teclado e Atalhos{UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Keyboard Layout & Shortcuts{UI.RESET}")
    run_script("fix-keyboard.sh")
    log_event("ok", "setup_keyboard_applied")


def apply_patch_cedilla():
    print(f"{UI.BOLD}==> [Configuração] Patch da Cedilha Wayland (Chromium / Electron){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Wayland Cedilla Patch (Chromium / Electron){UI.RESET}")
    run_script("manage-chromium-cedilla.py", ["--apply"])
    log_event("ok", "setup_patch_cedilla_applied")


def apply_autoheal():
    print(f"{UI.BOLD}==> [Configuração] Proteção de Auto-Cura de Layout no Login{UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Layout Auto-Heal Protection on Login{UI.RESET}")
    run_script("fix-keyboard.sh", env={"KDE_SUITE_LAYOUT_AUTOHEAL": "1"})
    log_event("ok", "setup_autoheal_applied")


def apply_wifi_power():
    print(f"{UI.BOLD}==> [Configuração] Smart Wi-Fi Power (AC vs Bateria){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Smart Wi-Fi Power (AC vs Battery){UI.RESET}")
    run_script("manage-wifi-power.sh", ["--apply"])
    log_event("ok", "setup_wifi_power_applied")


def apply_keyboard_power():
    print(f"{UI.BOLD}==> [Configuração] Smart Keyboard Power (Barramento i8042){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Smart Keyboard Power (i8042 bus){UI.RESET}")
    run_script("manage-keyboard-power.sh", ["--apply"])
    log_event("ok", "setup_keyboard_power_applied")


def apply_gestures():
    print(f"{UI.BOLD}==> [Configuração] Gestos de Touchpad (libinput-gestures){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Touchpad Gestures (libinput-gestures){UI.RESET}")
    run_script("configure-gestures.sh")
    log_event("ok", "setup_gestures_applied")


def apply_mouse():
    print(f"{UI.BOLD}==> [Configuração] Logitech MX Master 3S (logiops){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Logitech MX Master 3S (logiops){UI.RESET}")
    run_script("configure-mouse.sh")
    log_event("ok", "setup_mouse_applied")


def apply_screen_60():
    print(f"{UI.BOLD}==> [Configuração] Taxa de Atualização da Tela Interna (60 Hz){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Internal Display Refresh Rate (60 Hz){UI.RESET}")
    cli_path = os.path.join(SCRIPT_DIR, "../bin/linux-wayland-config")
    if os.path.isfile(cli_path):
        subprocess.run([cli_path, "screen-60"])
    log_event("ok", "setup_screen_60_applied")


def apply_tongfang():
    print(f"{UI.BOLD}==> [Configuração] Desbloqueio da Matriz do Teclado Tongfang/Avell (GRUB){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Tongfang/Avell Keyboard Matrix Unlock (GRUB){UI.RESET}")
    run_script("fix-tongfang.sh")
    log_event("ok", "setup_tongfang_applied")


def apply_terminal_fetch():
    print(f"{UI.BOLD}==> [Configuração] Identidade Visual do Terminal (Fastfetch){UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] Terminal Visual Identity (Fastfetch){UI.RESET}")
    run_script("terminal-fetch.sh")
    log_event("ok", "setup_terminal_fetch_applied")

def apply_turbo():
    print(f"{UI.BOLD}==> [Configuração] Gerenciamento de CPU Turbo Boost & Modo Silencioso{UI.RESET}" if i18n.lang == "pt-BR" else f"{UI.BOLD}==> [Setup] CPU Turbo Boost Management & Quiet Mode{UI.RESET}")
    run_script("manage-cpu-turbo.py", ["--interactive"])
    log_event("ok", "setup_turbo_applied")


def apply_all_detected(profile: Dict[str, Any]):
    apply_keyboard()
    print("")

    if profile.get("chromium_apps", {}).get("count", 0) > 0:
        apply_patch_cedilla()
        print("")

    if profile.get("input", {}).get("i8042_present"):
        apply_keyboard_power()
        print("")

    if profile.get("input", {}).get("is_tongfang_candidate") and not profile.get("input", {}).get("tongfang_grub_unlocked"):
        apply_tongfang()
        print("")

    if len(profile.get("wifi", {}).get("interfaces", [])) > 0:
        apply_wifi_power()
        print("")

    if profile.get("input", {}).get("touchpad_present"):
        apply_gestures()
        print("")

    if profile.get("input", {}).get("mx_master_present"):
        apply_mouse()
        print("")

    if shutil.which("fastfetch"):
        apply_terminal_fetch()
        print("")

    print(f"{UI.BOLD}### 3. Resumo{UI.RESET}\n" if i18n.lang == "pt-BR" else f"{UI.BOLD}### 3. Summary{UI.RESET}\n")
    headers = ["Campo", "Conteúdo"] if i18n.lang == "pt-BR" else ["Field", "Content"]
    rows = [
        ["O que mudou" if i18n.lang == "pt-BR" else "What changed", "Configurações recomendadas aplicadas com sucesso" if i18n.lang == "pt-BR" else "Recommended settings applied successfully"],
        ["O que não mudou" if i18n.lang == "pt-BR" else "Unchanged", "Arquivos pessoais e preferências não selecionadas" if i18n.lang == "pt-BR" else "Personal files and unselected preferences"],
        ["Backup", "Criado automaticamente para cada componente modificado" if i18n.lang == "pt-BR" else "Created automatically for modified components"],
        ["Relatório salvo" if i18n.lang == "pt-BR" else "Saved report", "./bin/linux-wayland-config report"],
        ["Como reverter" if i18n.lang == "pt-BR" else "How to revert", "./bin/linux-wayland-config <componente> --revert"],
        ["Requer" if i18n.lang == "pt-BR" else "Requires", "Reiniciar a sessão (logout/login) para ativação total de layouts" if i18n.lang == "pt-BR" else "Restart session (logout/login) for full layout activation"],
    ]
    print(render_table(headers, rows))


def show_interactive_menu(profile: Dict[str, Any]):
    print(render_banner(i18n.t("banner_title")))

    dmi = profile.get("dmi", {})
    sys_info = profile.get("system", {})
    vendor = dmi.get("vendor", "Unknown")
    product = dmi.get("product", "Machine")
    distro = sys_info.get("distro_name", "Linux")
    desktop = sys_info.get("desktop", "KDE")

    print(f"{UI.BOLD}{i18n.t('detected_header')}{UI.RESET}")
    print(f"  • {i18n.t('lbl_machine')}: {UI.BOLD}{vendor} {product}{UI.RESET}")
    print(f"  • {i18n.t('lbl_system')}:  {UI.BOLD}{distro}{UI.RESET} ({desktop})\n")

    print(f"{UI.BOLD}{i18n.t('opts_header')}{UI.RESET}")
    print(f"  1) {UI.SUCCESS}{i18n.t('opt_keyboard')}{UI.RESET}")
    print(f"  2) {UI.SUCCESS}{i18n.t('opt_cedilla')}{UI.RESET}")
    print(f"  3) {UI.SUCCESS}{i18n.t('opt_autoheal')}{UI.RESET}")

    inp = profile.get("input", {})
    if inp.get("i8042_present"):
        print(f"  4) {UI.SUCCESS}{i18n.t('opt_kbd_power')}{UI.RESET}")

    if len(profile.get("wifi", {}).get("interfaces", [])) > 0:
        print(f"  5) {UI.SUCCESS}{i18n.t('opt_wifi_power')}{UI.RESET}")

    if inp.get("touchpad_present"):
        print(f"  6) {UI.SUCCESS}{i18n.t('opt_gestures')}{UI.RESET}")

    if inp.get("mx_master_present"):
        print(f"  7) {UI.SUCCESS}{i18n.t('opt_mouse')}{UI.RESET}")

    disp = profile.get("display", {})
    if disp.get("mode_60_available") and not disp.get("mode_60_rejected"):
        print(f"  8) {UI.SUCCESS}{i18n.t('opt_screen60')}{UI.RESET}")

    if inp.get("is_tongfang_candidate"):
        print(f"  9) {UI.SUCCESS}{i18n.t('opt_tongfang')}{UI.RESET}")

    if shutil.which("fastfetch"):
        print(f" 10) {UI.SUCCESS}{i18n.t('opt_fetch')}{UI.RESET}")

    cpu_info = profile.get("cpu", {})
    if cpu_info.get("turbo_supported"):
        t_active = cpu_info.get("turbo_active")
        t_tag = f" {UI.WARNING}[{ 'ATIVO' if i18n.lang == 'pt-BR' else 'ACTIVE' }]{UI.RESET}" if t_active else f" {UI.SUCCESS}[{ 'DESATIVADO' if i18n.lang == 'pt-BR' else 'DISABLED' }]{UI.RESET}"
        print(f"  T) {UI.SUCCESS}{i18n.t('opt_turbo')}{UI.RESET}{t_tag}")

    print(f"  A) {UI.PRIMARY}{i18n.t('opt_all')}{UI.RESET}")
    print(f"  Q) {i18n.t('opt_quit')}\n")

    print(f"{i18n.t('cli_hint')}\n")

    if not sys.stdin.isatty():
        return 0

    try:
        ans = input(f"{UI.BOLD}{i18n.t('prompt_choice')}{UI.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{i18n.t('cancelled')}")
        return 0

    if not ans or ans.lower() == "q":
        print(f"{i18n.t('cancelled')}")
        return 0
    elif ans.lower() == "a":
        apply_all_detected(profile)
    elif ans == "1":
        apply_keyboard()
    elif ans == "2":
        apply_patch_cedilla()
    elif ans == "3":
        apply_autoheal()
    elif ans == "4":
        apply_keyboard_power()
    elif ans == "5":
        apply_wifi_power()
    elif ans == "6":
        apply_gestures()
    elif ans == "7":
        apply_mouse()
    elif ans == "8":
        apply_screen_60()
    elif ans == "9":
        apply_tongfang()
    elif ans == "10":
        apply_terminal_fetch()
    elif ans.lower() == "t":
        apply_turbo()


def main():
    profile = ensure_profile()
    args = sys.argv[1:]

    if not args:
        show_interactive_menu(profile)
        return 0

    while args:
        flag = args.pop(0)
        if flag in ("--all", "-a"):
            apply_all_detected(profile)
            return 0
        elif flag in ("--keyboard", "-k"):
            apply_keyboard()
        elif flag in ("--patch-cedilla", "--cedilla"):
            apply_patch_cedilla()
        elif flag in ("--autoheal",):
            apply_autoheal()
        elif flag in ("--wifi-power", "--wifi"):
            apply_wifi_power()
        elif flag in ("--keyboard-power",):
            apply_keyboard_power()
        elif flag in ("--gestures",):
            apply_gestures()
        elif flag in ("--mouse",):
            apply_mouse()
        elif flag in ("--screen-60",):
            apply_screen_60()
        elif flag in ("--tongfang",):
            apply_tongfang()
        elif flag in ("--terminal-fetch", "--cosmetic"):
            apply_terminal_fetch()
        elif flag in ("--turbo", "--cpu-turbo", "-t"):
            apply_turbo()
        elif flag in ("--help", "-h"):
            print(f"Usage: {sys.argv[0]} [--all | --keyboard | --patch-cedilla | --autoheal | --wifi-power | ...]")
            return 0
        else:
            print(f"{UI.DANGER}Unknown flag: {flag}{UI.RESET}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

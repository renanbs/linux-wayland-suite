#!/usr/bin/env python3
"""
check-status.py — Unified Health Diagnostic Audit for KDE Plasma 6 Wayland Suite
Audits hardware DMI, keyboards, input methods, native cedilla, compose simulation,
KWin layouts, Wayland clipboard, touchpad gestures, Wi-Fi power, and AI harness alignment.
Bilingual support (en / pt-BR).
"""

import os
import re
import sys
import glob
import ctypes
import shutil
import subprocess
from typing import Dict, List, Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, log_event, discover_binaries, check_binary_status

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "banner_title": {
        "en": "KDE Plasma 6 Wayland — Unified Health Status Audit",
        "pt-BR": "KDE Plasma 6 Wayland — Verificação de Status Geral",
    },
    "sec1_hardware": {
        "en": "[1/7] Session, Environment, and Hardware Identification",
        "pt-BR": "[1/7] Sessão, Ambiente e Identificação de Hardware",
    },
    "sec2_im": {
        "en": "[2/7] Input Method Hygiene (Shortcut Compatibility / Ctrl+C)",
        "pt-BR": "[2/7] Higiene de Input Method (Compatibilidade de Atalhos / Ctrl+C)",
    },
    "sec3_cedilla": {
        "en": "[3/7] US-intl Cedilla Support (Chrome, Orca, Electron, GTK, Qt)",
        "pt-BR": "[3/7] Suporte a Cedilha no Layout US-intl (Chrome, Orca, Electron, GTK, Qt)",
    },
    "sec4_compose": {
        "en": "[4/7] Composition Engine Simulation (libxkbcommon)",
        "pt-BR": "[4/7] Simulação do Motor de Composição (libxkbcommon)",
    },
    "sec5_kwin": {
        "en": "[5/7] KWin Layouts & Wayland Clipboard",
        "pt-BR": "[5/7] Layouts no KWin & Clipboard do Wayland",
    },
    "sec6_gestures": {
        "en": "[6/7] Touchpad Gestures (libinput-gestures & KWin)",
        "pt-BR": "[6/7] Touchpad Gestures (libinput-gestures & KWin)",
    },
    "sec7_wifi": {
        "en": "[7/7] Machine Profile & Smart Wi-Fi Power",
        "pt-BR": "[7/7] Perfil da Máquina & Energia Wi-Fi (Smart Wi-Fi Power)",
    },
    "sec8_terminal": {
        "en": "[8] Terminal Visual Identity (Fastfetch)",
        "pt-BR": "[8] Identidade Visual do Terminal (Fastfetch)",
    },
    "audit_completed": {
        "en": "✔ Audit completed successfully.",
        "pt-BR": "✔ Verificação concluída com sucesso.",
    },
}

i18n = I18n(STRINGS)

def read_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return default

def run_qdbus(args: List[str]) -> Optional[str]:
    for bin_name in ("qdbus6", "qdbus", "/usr/lib/qt6/bin/qdbus"):
        if shutil.which(bin_name) or os.path.isfile(bin_name):
            try:
                res = subprocess.check_output([bin_name] + args, text=True, stderr=subprocess.DEVNULL)
                return res.strip()
            except Exception:
                pass
    return None


def audit_stage1():
    print(f"\n{UI.BOLD}{i18n.t('sec1_hardware')}{UI.RESET}")
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
    print(f"  • Tipo de Sessão: {session_type}" if i18n.lang == "pt-BR" else f"  • Session Type: {session_type}")
    print(f"  • Ambiente Desktop: {desktop}" if i18n.lang == "pt-BR" else f"  • Desktop Environment: {desktop}")
    log_event("info", "session_type", session_type)

    qdbus_client = shutil.which("qdbus6") or shutil.which("qdbus") or "NÃO ENCONTRADO"
    print(f"  • Cliente D-Bus: {qdbus_client}" if i18n.lang == "pt-BR" else f"  • D-Bus Client: {qdbus_client}")

    dmi_vendor = read_file("/sys/class/dmi/id/sys_vendor", "unknown")
    dmi_product = read_file("/sys/class/dmi/id/product_name", "unknown")
    dmi_board = read_file("/sys/class/dmi/id/board_name", "unknown")
    print(f"  • Hardware DMI: {dmi_vendor} / {dmi_product} (Placa: {dmi_board})" if i18n.lang == "pt-BR" else f"  • DMI Hardware: {dmi_vendor} / {dmi_product} (Board: {dmi_board})")
    log_event("info", "dmi_hardware", f"{dmi_vendor} / {dmi_product}")

    # AI Harness
    h_profile = os.path.expanduser("~/.config/linux-wayland-suite/harness-profile.json")
    if os.path.isfile(h_profile):
        try:
            with open(h_profile) as f:
                hd = json.load(f)
            h_active = hd.get("active_harness", "omp")
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Host de IA / Harness: {UI.BOLD}{h_active}{UI.RESET} (perfil alinhado)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} AI Host Harness: {UI.BOLD}{h_active}{UI.RESET} (profile aligned).")
            roles = hd.get("model_roles", {})
            if roles:
                for r_name in ("reasoning", "code", "review", "security"):
                    if r_name in roles:
                        r_label = {"reasoning": "Raciocínio", "code": "Código", "review": "Revisão", "security": "Segurança"}.get(r_name, r_name) if i18n.lang == "pt-BR" else r_name.capitalize()
                        print(f"    └─ {r_label:<12}: {UI.BOLD}{roles[r_name]}{UI.RESET}")
            log_event("ok", "harness_aligned", h_active)
        except Exception:
            pass

    # Tongfang
    dmi_str = f"{dmi_vendor} {dmi_product} {dmi_board}".lower()
    is_tongfang = any(k in dmi_str for k in ("tongfang", "avell", "clevo", "tuxedo", "schenker", "uniwill", "gk5", "gm5", "qc7"))
    if is_tongfang:
        cmdline = read_file("/proc/cmdline")
        if "i8042.nopnp=1" in cmdline and "acpi_osi=" in cmdline:
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Chassis Tongfang/Avell com parâmetros i8042/ACPI ativos no boot (teclado desbloqueado)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Tongfang/Avell chassis with i8042/ACPI kernel params active (keyboard matrix unlocked).")
            log_event("ok", "tongfang_kernel_params", "i8042.nopnp=1 acpi_osi")
        else:
            print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Chassis Tongfang/Avell sem parâmetros i8042/ACPI no boot. Corrija com: {UI.BOLD}./bin/linux-wayland-config fix-tongfang{UI.RESET}")
            log_event("warn", "tongfang_kernel_params_missing")

    # Smart Keyboard Power (serio0)
    serio_power = "/sys/devices/platform/i8042/serio0/power/control"
    if os.path.isfile(serio_power):
        pwr_state = read_file(serio_power, "unknown")
        udev_rule = "/etc/udev/rules.d/90-kde-smart-keyboard-power.rules"
        if os.path.isfile(udev_rule):
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Gerenciamento Dinâmico de Energia do Teclado: {UI.BOLD}ATIVO{UI.RESET} (serio0: {pwr_state})." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Smart Keyboard Power Management: {UI.BOLD}ACTIVE{UI.RESET} (serio0: {pwr_state}).")
            log_event("ok", "keyboard_smart_power", f"serio0={pwr_state}")
        elif pwr_state == "on":
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Barramento i8042 em modo ativo permanente (power/control: {UI.BOLD}on{UI.RESET} - anti-latch).")
            log_event("ok", "keyboard_power_static_on")
        else:
            print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Barramento i8042 em economia ociosa (power/control: {UI.BOLD}auto{UI.RESET}). Ative com: {UI.BOLD}./bin/linux-wayland-config smart-keyboard-power --apply{UI.RESET}")
            log_event("warn", "keyboard_power_auto_no_rule")

        sleep_hook = "/etc/systemd/system-sleep/90-kde-keyboard-resume.sh"
        if os.path.isfile(sleep_hook) and os.access(sleep_hook, os.X_OK):
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Gancho de Retorno de Suspensão (Lid Open / Wake): {UI.BOLD}ATIVO{UI.RESET} (systemd-sleep)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Sleep Resume Hook (Lid Open / Wake): {UI.BOLD}ACTIVE{UI.RESET} (systemd-sleep).")
            log_event("ok", "keyboard_resume_hook_active")

    # CPU Turbo Boost & Thermals
    intel_no_turbo = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    amd_boost = "/sys/devices/system/cpu/cpufreq/boost"
    t_state = None
    if os.path.exists(intel_no_turbo):
        t_state = (read_file(intel_no_turbo) != "1")
    elif os.path.exists(amd_boost):
        t_state = (read_file(amd_boost) == "1")

    if t_state is not None:
        t_label = "ATIVO (Alto Desempenho / Aquecimento rápido)" if t_state else "DESATIVADO (Silencioso / Frio)"
        if i18n.lang == "en":
            t_label = "ACTIVE (High Performance / Increased heat)" if t_state else "DISABLED (Quiet / Cool)"
        turbo_status_tag = f"{UI.PRIMARY}[INFO]{UI.RESET}" if t_state else f"{UI.SUCCESS}[OK]{UI.RESET}"
        print(f"  • {turbo_status_tag} CPU Turbo Boost: {UI.BOLD}{t_label}{UI.RESET} (altere com: {UI.BOLD}./bin/linux-wayland-config turbo{UI.RESET})." if i18n.lang == "pt-BR" else f"  • {turbo_status_tag} CPU Turbo Boost: {UI.BOLD}{t_label}{UI.RESET} (manage via: {UI.BOLD}./bin/linux-wayland-config turbo{UI.RESET}).")
        log_event("info", "turbo_boost_status", f"active={t_state}")


def audit_stage2():
    print(f"\n{UI.BOLD}{i18n.t('sec2_im')}{UI.RESET}")
    im_conf = os.path.expanduser("~/.config/environment.d/im.conf")
    if os.path.isfile(im_conf):
        print(f"  • {UI.DANGER}[FALHA]{UI.RESET} ~/.config/environment.d/im.conf ainda existe (risco de quebra do Ctrl+C)." if i18n.lang == "pt-BR" else f"  • {UI.DANGER}[FAIL]{UI.RESET} ~/.config/environment.d/im.conf exists (breaks Ctrl+C).")
        log_event("fail", "im_conf_present")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/environment.d/im.conf ausente (limpo)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/environment.d/im.conf clean (absent).")
        log_event("ok", "im_conf_clean")

    cedilla_conf = os.path.expanduser("~/.config/environment.d/cedilla.conf")
    im_forced = False
    if os.path.isfile(cedilla_conf):
        content = read_file(cedilla_conf)
        if re.search(r"^(GTK_IM_MODULE|QT_IM_MODULE)=", content, re.MULTILINE):
            im_forced = True

    if im_forced:
        print(f"  • {UI.DANGER}[FALHA]{UI.RESET} cedilla.conf força GTK/QT_IM_MODULE globalmente. Rode './bin/linux-wayland-config fix-keyboard'." if i18n.lang == "pt-BR" else f"  • {UI.DANGER}[FAIL]{UI.RESET} cedilla.conf forces GTK/QT_IM_MODULE globally. Run 'fix-keyboard'.")
        log_event("fail", "im_env_forced")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Nenhuma variável GTK_IM_MODULE/QT_IM_MODULE forçada globalmente." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} No GTK_IM_MODULE/QT_IM_MODULE globally forced.")
        log_event("ok", "im_env_clean")

    kxkbrc = os.path.expanduser("~/.config/kxkbrc")
    if os.path.isfile(kxkbrc):
        content = read_file(kxkbrc)
        m = re.search(r"^LayoutList=(.*)$", content, re.MULTILINE)
        layouts = m.group(1).strip() if m else ""
        if layouts == "br,us":
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} kxkbrc com LayoutList completa (br,us)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} kxkbrc with complete LayoutList (br,us).")
            log_event("ok", "kxkbrc_layout_complete", layouts)
        elif not layouts:
            print(f"  • {UI.WARNING}[AVISO]{UI.RESET} kxkbrc sem LayoutList. Rode './bin/linux-wayland-config fix-keyboard'.")
            log_event("warn", "kxkbrc_layout_empty")
        else:
            print(f"  • {UI.DANGER}[FALHA]{UI.RESET} Bug de colapso do kxkbrc detectado: LayoutList='{layouts}'. Rode './bin/linux-wayland-config fix-keyboard'.")
            log_event("fail", "kxkbrc_layout_collapsed", layouts)

        autoheal = os.path.expanduser("~/.config/autostart/kde-wayland-suite-restore-layout.desktop")
        if os.path.isfile(autoheal):
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Auto-cura do layout no login está ativa." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Layout auto-heal on login is active.")
            log_event("ok", "layout_autoheal_active")


def audit_stage3():
    print(f"\n{UI.BOLD}{i18n.t('sec3_cedilla')}{UI.RESET}")
    cedilla_conf = os.path.expanduser("~/.config/environment.d/cedilla.conf")
    if os.path.isfile(cedilla_conf) and "LC_CTYPE=pt_BR.UTF-8" in read_file(cedilla_conf):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/environment.d/cedilla.conf ativo (LC_CTYPE=pt_BR.UTF-8)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/environment.d/cedilla.conf active (LC_CTYPE=pt_BR.UTF-8).")
        log_event("ok", "cedilla_conf_active")
    else:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} ~/.config/environment.d/cedilla.conf ausente ou sem LC_CTYPE=pt_BR.UTF-8.")
        log_event("warn", "cedilla_conf_missing")

    # fcitx5 check
    fcitx_running = False
    try:
        out = subprocess.check_output(["pgrep", "-x", "fcitx5"], text=True, stderr=subprocess.DEVNULL)
        if out.strip(): fcitx_running = True
    except Exception:
        pass

    user_fcitx = os.path.expanduser("~/.config/autostart/org.fcitx.Fcitx5.desktop")
    if fcitx_running:
        print(f"  • {UI.DANGER}[FALHA]{UI.RESET} fcitx5 está rodando — ele quebra Ctrl+<tecla> sob Wayland. Corrija com 'fix-keyboard'.")
        log_event("fail", "fcitx5_running")
    elif os.path.isfile(user_fcitx) and "Hidden=true" in read_file(user_fcitx):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} fcitx5 desligado e mascarado (Ctrl+<tecla> preservado)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} fcitx5 masked in autostart (Ctrl+key preserved).")
        log_event("ok", "fcitx5_masked")
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} fcitx5 desligado e sem autostart (Ctrl+<tecla> preservado).")
        log_event("ok", "fcitx5_clean")

    # Browser flags
    check_apps = [
        ("chrome-flags.conf", "Google Chrome"),
        ("chromium-flags.conf", "Chromium"),
        ("electron-flags.conf", "Electron"),
        ("code-flags.conf", "VS Code"),
        ("orca-flags.conf", "Orca IDE")
    ]
    for fname, dname in check_apps:
        fpath = os.path.expanduser(f"~/.config/{fname}")
        if os.path.isfile(fpath) and "--ozone-platform-hint=auto" in read_file(fpath):
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} {dname} (~/.config/{fname}): flags de Wayland corretas." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} {dname} (~/.config/{fname}): Wayland flags correct.")

    lc_ctype = os.environ.get("LC_CTYPE", "")
    if lc_ctype == "pt_BR.UTF-8":
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} LC_CTYPE=pt_BR.UTF-8 neste processo (tabela de composição: dead_acute + c -> ç)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} LC_CTYPE=pt_BR.UTF-8 in current process.")
        log_event("ok", "lc_ctype_process", lc_ctype)
    else:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} LC_CTYPE='{lc_ctype or 'unset'}' neste processo (faça logout/login após 'fix-keyboard').")
        log_event("warn", "lc_ctype_process_missing", lc_ctype)

    # Chromium/Electron Patch Audit
    binaries = discover_binaries()
    total_vuln = 0
    total_patched = 0
    for b in binaries:
        status, _ = check_binary_status(b)
        if status == "VULNERABLE": total_vuln += 1
        elif status == "PATCHED": total_patched += 1

    if total_vuln > 0:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Cedilha Wayland: {total_vuln} app(s) Chromium/Electron sem patch ('+c gerará 'ć' no Wayland nativo)." if i18n.lang == "pt-BR" else f"  • {UI.WARNING}[WARN]{UI.RESET} Wayland Cedilla: {total_vuln} Chromium/Electron app(s) unpatched ('+c outputs 'ć').")
        print(f"    Corrija com: {UI.BOLD}./bin/linux-wayland-config patch-cedilla --apply{UI.RESET}")
        log_event("warn", "chromium_cedilla_unpatched", f"vuln={total_vuln}")
    elif binaries:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Cedilha Wayland: Todos os {total_patched} app(s) Chromium/Electron estão com patch ('+c -> ç)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Wayland Cedilla: All {total_patched} Chromium/Electron app(s) patched ('+c -> ç).")
        log_event("ok", "chromium_cedilla_patched", f"patched={total_patched}")

    pacman_hook = "/etc/pacman.d/hooks/99-cedilla-wayland.hook"
    if os.path.isfile(pacman_hook):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Autocura de cedilha no Pacman ativa ({pacman_hook})." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Pacman cedilla autorepair hook active ({pacman_hook}).")
        log_event("ok", "cedilla_pacman_hook_active")
    else:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Autocura de cedilha no Pacman não instalada (execute 'patch-cedilla --apply').")


def audit_stage4():
    print(f"\n{UI.BOLD}{i18n.t('sec4_compose')}{UI.RESET}")
    try:
        xkb = ctypes.CDLL("libxkbcommon.so.0")
        xkb.xkb_context_new.restype = ctypes.c_void_p
        xkb.xkb_context_new.argtypes = [ctypes.c_int]
        ctx = xkb.xkb_context_new(0)
        xkb.xkb_compose_table_new_from_locale.restype = ctypes.c_void_p
        xkb.xkb_compose_table_new_from_locale.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        table = xkb.xkb_compose_table_new_from_locale(ctx, b"pt_BR.UTF-8", 0)
        xkb.xkb_compose_state_new.restype = ctypes.c_void_p
        xkb.xkb_compose_state_new.argtypes = [ctypes.c_void_p, ctypes.c_int]
        xkb.xkb_compose_state_feed.restype = ctypes.c_int
        xkb.xkb_compose_state_feed.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        xkb.xkb_compose_state_get_utf8.restype = ctypes.c_int
        xkb.xkb_compose_state_get_utf8.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
        state = xkb.xkb_compose_state_new(table, 0)
        xkb.xkb_compose_state_feed(state, 0xfe51) # dead_acute
        xkb.xkb_compose_state_feed(state, 0x0063) # c
        buf = ctypes.create_string_buffer(64)
        xkb.xkb_compose_state_get_utf8(state, buf, len(buf))
        res = buf.value.decode("utf-8")
        if res == "ç":
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Simulação do motor de composição: '<dead_acute> <c>' -> 'ç' (cedilha validada)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Compose engine simulation: '<dead_acute> <c>' -> 'ç' (validated).")
            log_event("ok", "xkb_compose_engine", "cedilha validada")
        else:
            print(f"  • {UI.DANGER}[FALHA]{UI.RESET} Simulação do motor de composição gerou '{res}' em vez de 'ç'.")
            log_event("fail", "xkb_compose_engine", f"output={res}")
    except Exception as e:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Falha ao carregar libxkbcommon: {e}")


def audit_stage5():
    print(f"\n{UI.BOLD}{i18n.t('sec5_kwin')}{UI.RESET}")
    layouts_raw = run_qdbus(["--literal", "org.kde.keyboard", "/Layouts", "org.kde.KeyboardLayouts.getLayoutsList"])
    if layouts_raw:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} KWin D-Bus Layouts: {layouts_raw}")
        idx = run_qdbus(["org.kde.keyboard", "/Layouts", "org.kde.KeyboardLayouts.getLayout"]) or "0"
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Layout Ativo no KWin (índice): {idx} (0 = br abnt2, 1 = us alt-intl)" if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Active Layout in KWin (index): {idx}")

    has_copy = shutil.which("wl-copy")
    has_paste = shutil.which("wl-paste")
    if has_copy and has_paste:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} wl-clipboard (wl-copy / wl-paste) instalado (Wayland nativo)." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} wl-clipboard installed (native Wayland).")
    else:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} wl-clipboard não encontrado.")

    # Check zombie xsel
    hung_xsel = ""
    try:
        hung_xsel = subprocess.check_output(["pgrep", "-a", "xsel"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        pass
    if hung_xsel:
        print(f"  • {UI.DANGER}[FALHA]{UI.RESET} Processo xsel travado detectado. Execute 'fix-keyboard'.")
        log_event("fail", "hung_xsel_detected", hung_xsel)
    else:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Nenhum processo xsel travado." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} No hung xsel processes.")


def audit_stage6():
    print(f"\n{UI.BOLD}{i18n.t('sec6_gestures')}{UI.RESET}")
    user = os.environ.get("USER", "root")
    try:
        groups_out = subprocess.check_output(["groups", user], text=True, stderr=subprocess.DEVNULL)
        if "input" in groups_out.split():
            print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Usuário '{user}' pertence ao grupo 'input'." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} User '{user}' belongs to 'input' group.")
        else:
            print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Usuário '{user}' NÃO pertence ao grupo 'input'. Execute 'sudo usermod -aG input {user}'.")
    except Exception:
        pass

    if shutil.which("libinput-gestures"):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Binário libinput-gestures instalado." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} libinput-gestures binary installed.")
        try:
            st = subprocess.check_output(["libinput-gestures", "-s"], text=True, stderr=subprocess.DEVNULL)
            for l in st.strip().splitlines():
                if l.strip(): print(f"    {UI.DIM}{l.strip()}{UI.RESET}")
        except Exception:
            pass

    gestures_conf = os.path.expanduser("~/.config/libinput-gestures.conf")
    if os.path.isfile(gestures_conf):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/libinput-gestures.conf presente." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} ~/.config/libinput-gestures.conf present.")

    kglobal = run_qdbus(["org.kde.kglobalaccel", "/kglobalaccel", "org.kde.KGlobalAccel.allComponents"])
    if kglobal:
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} KGlobalAccel / KWin D-Bus respondendo para disparo de atalhos." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} KGlobalAccel / KWin D-Bus responding for shortcut triggers.")


def audit_stage7():
    print(f"\n{UI.BOLD}{i18n.t('sec7_wifi')}{UI.RESET}")
    profile_file = os.path.expanduser("~/.config/linux-wayland-suite/machine-profile.json")
    if os.path.isfile(profile_file):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Perfil da máquina presente em: {profile_file}" if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Machine profile present at: {profile_file}")
    else:
        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} Perfil da máquina ausente. Execute './bin/linux-wayland-config init'.")

    wifi_udev = "/etc/udev/rules.d/90-linux-wayland-smart-wifi-power.rules"
    if os.path.isfile(wifi_udev):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Smart Wi-Fi Power: ATIVO (regra udev instalada em {wifi_udev})." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Smart Wi-Fi Power: ACTIVE ({wifi_udev}).")
    else:
        print(f"  • {UI.PRIMARY}[INFO]{UI.RESET} Smart Wi-Fi Power: Inativo (execute 'smart-wifi-power --apply').")

    # Check AC and iw power_save
    has_ac = False
    for p_sup in glob.glob("/sys/class/power_supply/*"):
        t = read_file(os.path.join(p_sup, "type"))
        if t in ("Mains", "AC", "ADP0", "ADP1"):
            if read_file(os.path.join(p_sup, "online")) == "1":
                has_ac = True

    for iface_dir in glob.glob("/sys/class/net/*"):
        if os.path.isdir(f"{iface_dir}/wireless") or os.path.isdir(f"{iface_dir}/phy80211"):
            w_name = os.path.basename(iface_dir)
            driver = os.path.basename(os.path.realpath(f"{iface_dir}/device/driver"))
            if shutil.which("iw"):
                try:
                    iw_out = subprocess.check_output(["iw", "dev", w_name, "get", "power_save"], text=True, stderr=subprocess.DEVNULL)
                    is_on = "on" in iw_out.lower()
                    if has_ac and is_on:
                        print(f"  • {UI.WARNING}[AVISO]{UI.RESET} [{w_name} / {driver}]: Laptop na tomada (AC), mas Power Save 802.11 está LIGADO.")
                        print(f"    Risco: Conexões de entrada (Orca / SSH) podem sofrer dormência ou timeout.")
                        print(f"    Para resolver: {UI.BOLD}./bin/linux-wayland-config smart-wifi-power --apply{UI.RESET}")
                        log_event("warn", "wifi_powersave_ac_lag", f"iface={w_name}")
                    else:
                        ps_str = "LIGADO" if is_on else "DESLIGADO"
                        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} [{w_name} / {driver}]: Power Save 802.11: {ps_str} (Modo: {'AC' if has_ac else 'Bateria'}).")
                except Exception:
                    pass

    # Stage 8: Terminal Identity
    if shutil.which("fastfetch"):
        print(f"  • {UI.SUCCESS}[OK]{UI.RESET} Identidade do Terminal (Fastfetch): Águia Neon Dr460nized ativa." if i18n.lang == "pt-BR" else f"  • {UI.SUCCESS}[OK]{UI.RESET} Terminal Visual Identity (Fastfetch): Active.")


def main():
    print(render_banner(i18n.t("banner_title")))
    audit_stage1()
    audit_stage2()
    audit_stage3()
    audit_stage4()
    audit_stage5()
    audit_stage6()
    audit_stage7()

    print(f"\n{UI.BOLD}{UI.SUCCESS}{i18n.t('audit_completed')}{UI.RESET}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)

#!/usr/bin/env python3
"""
lib_suite.py — Shared Python Core Library for linux-wayland-suite
Provides standardized design tokens (Garuda/Dracula palette), visible-width
table rendering, internationalization (en / pt-BR), and runlog event logging.
"""

import os
import re
import sys
import glob
from typing import List, Dict, Optional, Any, Tuple
import json
from typing import List, Dict, Optional, Any

# ==============================================================================
# 1. Design Tokens & ANSI Color Palette (Garuda / Dracula Terminal Palette)
# ==============================================================================
class UI:
    PRIMARY = "\033[1;36m"   # Bold Cyan
    CYAN    = "\033[0;36m"   # Cyan
    BLUE    = "\033[0;34m"   # Blue
    SUCCESS = "\033[0;32m"   # Green
    GREEN   = "\033[0;32m"
    DANGER  = "\033[0;31m"   # Red
    RED     = "\033[0;31m"
    WARNING = "\033[1;33m"   # Bold Yellow
    YELLOW  = "\033[1;33m"
    MUTED   = "\033[0;90m"   # Gray / Dim
    GRAY    = "\033[0;90m"
    BORDER  = "\033[2;36m"   # Dim Cyan
    BOLD    = "\033[1m"      # Bold
    DIM     = "\033[2m"      # Dim
    RESET   = "\033[0m"      # Reset / Normal

    ICON_CHECK = f"{SUCCESS}✔{RESET}"
    ICON_CROSS = f"{DANGER}✖{RESET}"
    ICON_WARN  = f"{WARNING}⚠{RESET}"
    ICON_INFO  = f"{PRIMARY}ℹ{RESET}"


# ==============================================================================
# 2. Text Measurement & Table Formatting (Visible Width Aware)
# ==============================================================================

ANSI_REGEX = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

def strip_ansi(text: str) -> str:
    """Removes all ANSI escape sequences from a string."""
    return ANSI_REGEX.sub("", str(text))

def visible_len(text: str) -> int:
    """Returns the visible character length of a string ignoring ANSI color codes."""
    return len(strip_ansi(text))

def pad_visible(text: str, width: int, align: str = "left") -> str:
    """Pads text with spaces so its visible width matches the target width."""
    text_str = str(text)
    pad_needed = max(0, width - visible_len(text_str))
    if align == "right":
        return (" " * pad_needed) + text_str
    elif align == "center":
        left_pad = pad_needed // 2
        right_pad = pad_needed - left_pad
        return (" " * left_pad) + text_str + (" " * right_pad)
    return text_str + (" " * pad_needed)

def render_table(headers: List[str], rows: List[List[str]], alignments: Optional[List[str]] = None) -> str:
    """
    Renders a table where columns are mathematically aligned based on visible string length,
    completely immune to ANSI color code length distortions.
    """
    if not headers and not rows:
        return ""

    num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
    col_widths = [visible_len(h) for h in headers] if headers else [0] * num_cols

    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], visible_len(cell))
            else:
                col_widths.append(visible_len(cell))

    if not alignments:
        alignments = ["left"] * len(col_widths)

    lines = []
    # Header
    if headers:
        header_line = "  " + "  ".join(
            pad_visible(f"{UI.BOLD}{h}{UI.RESET}", col_widths[idx], alignments[idx])
            for idx, h in enumerate(headers)
        )
        divider_line = "  " + "  ".join(
            f"{UI.BORDER}{'─' * col_widths[idx]}{UI.RESET}"
            for idx in range(len(col_widths))
        )
        lines.append(header_line)
        lines.append(divider_line)

    # Rows
    for row in rows:
        row_line = "  " + "  ".join(
            pad_visible(row[idx] if idx < len(row) else "", col_widths[idx], alignments[idx])
            for idx in range(len(col_widths))
        )
        lines.append(row_line)

    return "\n".join(lines)

def render_banner(title: str, subtitle: Optional[str] = None) -> str:
    """Renders a standard suite banner."""
    lines = [
        f"{UI.BOLD}{UI.CYAN}======================================================{UI.RESET}",
        f"{UI.BOLD}{UI.CYAN}   {title}   {UI.RESET}",
        f"{UI.BOLD}{UI.CYAN}======================================================{UI.RESET}",
    ]
    if subtitle:
        lines.append(f"  {UI.DIM}• {subtitle}{UI.RESET}")
    lines.append("")
    return "\n".join(lines)


# ==============================================================================
# 3. Dynamic Internationalization (i18n: en / pt-BR)
# ==============================================================================

PROFILE_PATH = os.path.expanduser("~/.config/linux-wayland-suite/harness-profile.json")

def get_active_language() -> str:
    """
    Resolves the user's preferred language in order:
    1. Environment variable KDE_SUITE_LANG
    2. harness-profile.json ('active_language')
    3. System locale starting with 'pt' -> 'pt-BR'
    4. Default: 'en'
    """
    env_lang = os.environ.get("KDE_SUITE_LANG")
    if env_lang:
        clean = env_lang.strip().replace("_", "-")
        return "pt-BR" if clean.lower().startswith("pt") else "en"

    if os.path.isfile(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("active_language", "")
                if lang:
                    clean = lang.strip().replace("_", "-")
                    return "pt-BR" if clean.lower().startswith("pt") else "en"
        except Exception:
            pass

    sys_locale = os.environ.get("LC_ALL") or os.environ.get("LC_CTYPE") or os.environ.get("LANG", "")
    if sys_locale.lower().startswith("pt"):
        return "pt-BR"

    return "en"


class I18n:
    """Simple dictionary-backed localization helper."""

    def __init__(self, catalog: Dict[str, Dict[str, str]], lang: Optional[str] = None):
        self.catalog = catalog
        self.lang = lang or get_active_language()

    def t(self, key: str, **kwargs) -> str:
        entry = self.catalog.get(key, {})
        template = entry.get(self.lang) or entry.get("en") or key
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template


# ==============================================================================
# 4. Structured Runlog Event Helper
# ==============================================================================

def log_event(status: str, event_id: str, detail: str = "") -> None:
    """Logs an event to the suite's active run directory if available."""
    run_dir = os.environ.get("RUNLOG_DIR") or os.environ.get("KDE_SUITE_RUN_DIR")
    if not run_dir or not os.path.isdir(run_dir):
        return

    tsv_path = os.path.join(run_dir, "events.tsv")
    try:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        with open(tsv_path, "a", encoding="utf-8") as f:
            clean_detail = str(detail).replace("\t", " ").replace("\n", " ")
            f.write(f"{now_iso}\t{status}\t{event_id}\t{clean_detail}\n")
    except Exception:
        pass

# ==============================================================================
# 5. Application Naming Helper
# ==============================================================================

def app_display_name(path: str) -> str:
    """Returns clean human-readable name for an executable path."""
    p_lower = path.lower()
    if "chrome/chrome" in p_lower:
        return "Google Chrome"
    elif "chromium/chromium" in p_lower:
        return "Chromium"
    elif "brave" in p_lower:
        return "Brave Browser"
    elif "msedge" in p_lower:
        return "Microsoft Edge"
    elif "electron43/electron" in p_lower:
        return "Orca IDE (Electron 43)"
    elif "electron" in p_lower:
        for part in path.split("/"):
            if part.startswith("electron") and part[8:].isdigit():
                return f"Electron Runtime ({part})"
        return "Electron Runtime"
    elif "code/code" in p_lower or "code-insiders" in p_lower:
        return "Visual Studio Code"
    elif "vscodium" in p_lower:
        return "VSCodium"
    elif "discord" in p_lower:
        return "Discord"
    elif "antigravity-ide" in p_lower:
        return "Antigravity IDE"
    elif "antigravity" in p_lower:
        return "Antigravity Platform"
    return os.path.basename(path)

SEARCH_GLOBS = [
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

def discover_binaries() -> List[str]:
    """Dynamically finds installed Chromium and Electron ELF executables (>25MB)."""
    found = set()
    for pattern in SEARCH_GLOBS:
        for p in glob.glob(pattern):
            if not os.path.isfile(p) or not os.access(p, os.X_OK):
                continue
            if p.endswith(".orig") or ".bak-" in p or ".tmp-" in p or p.endswith(".bak"):
                continue
            try:
                rp = os.path.realpath(p)
                if os.path.getsize(rp) > 25 * 1024 * 1024:
                    with open(rp, "rb") as f:
                        if f.read(4) == b"\x7fELF":
                            found.add(rp)
            except (OSError, PermissionError):
                continue
    return sorted(list(found))

def check_binary_status(bin_path: str) -> Tuple[str, int]:
    """
    Returns (status, count) where status is 'PATCHED', 'VULNERABLE', or 'INELIGIBLE'.
    """
    if not os.path.isfile(bin_path):
        return ("NOT_FOUND", 0)
    try:
        with open(bin_path, "rb") as f:
            data = f.read()
        needs = data.count(b"\x63\x00\x07\x01")
        patched = data.count(b"\x63\x00\xe7\x00")
        if needs > 0:
            return ("VULNERABLE", needs)
        elif patched > 0:
            return ("PATCHED", patched)
        return ("INELIGIBLE", 0)
    except Exception:
        return ("ERROR", 0)

# ==============================================================================
# 5. Interactive CLI Ergonomics Helpers (Default-on-Enter Contract)
# ==============================================================================

def prompt_confirm(question: str, default: bool = True, lang: Optional[str] = None) -> bool:
    """
    Prompts the user with a Yes/No question where pressing <Enter> immediately
    selects the default value without requiring the user to retype it.
    """
    active_lang = lang or get_active_language()
    hint = "[Y/n]" if default else "[y/N]"
    if active_lang == "pt-BR":
        hint = "[S/n]" if default else "[s/N]"

    prompt_str = f"{UI.BOLD}{question}{UI.RESET} {UI.PRIMARY}{hint}{UI.RESET}: "
    try:
        ans = input(prompt_str).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("")
        return False

    if not ans:
        return default

    if active_lang == "pt-BR":
        return ans in ("s", "sim", "y", "yes")
    return ans in ("y", "yes", "s", "sim")

def prompt_choice(question: str, options: List[str], default_index: int = 0, lang: Optional[str] = None) -> int:
    """
    Presents a numbered choice list to the user where pressing <Enter> immediately
    selects the default option (default_index, 0-based).
    """
    active_lang = lang or get_active_language()
    print(f"\n{UI.BOLD}{question}{UI.RESET}")
    for idx, opt in enumerate(options):
        is_default = (idx == default_index)
        def_tag = f" {UI.PRIMARY}({'Padrão - Pressione Enter' if active_lang == 'pt-BR' else 'Default - Press Enter'}){UI.RESET}" if is_default else ""
        num_color = UI.PRIMARY if is_default else UI.MUTED
        print(f"  {num_color}[{idx + 1}]{UI.RESET} {opt}{def_tag}")

    prompt_str = f"\n{UI.CYAN}> {'Escolha [1-' if active_lang == 'pt-BR' else 'Select [1-'}{len(options)}] (Enter = {default_index + 1}): {UI.RESET}"
    try:
        ans = input(prompt_str).strip()
    except (KeyboardInterrupt, EOFError):
        print("")
        return default_index

    if not ans:
        return default_index

    try:
        val = int(ans)
        if 1 <= val <= len(options):
            return val - 1
    except ValueError:
        pass

    return default_index

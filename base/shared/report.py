#!/usr/bin/env python3
"""
report.py — Execution Report, History, and Interactive Inspector for linux-wayland-suite
Reads structured run logs recorded by lib-runlog.sh and generates detailed reports
with actionable remediation steps. Bilingual support (en / pt-BR).
"""

import os
import sys
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib_suite import UI, I18n, get_active_language, render_banner, render_table

RUNLOG_ROOT = os.environ.get("LINUX_WAYLAND_SUITE_RUNLOG_ROOT") or \
              os.environ.get("KDE_SUITE_RUNLOG_ROOT") or \
              os.path.expanduser("~/.local/state/linux-wayland-suite/runs")

if not os.path.isdir(RUNLOG_ROOT) and os.path.isdir(os.path.expanduser("~/.local/state/kde-wayland-suite/runs")):
    RUNLOG_ROOT = os.path.expanduser("~/.local/state/kde-wayland-suite/runs")

# ==============================================================================
# Internationalization Catalog
# ==============================================================================

STRINGS = {
    "title_report": {
        "en": "Linux Wayland Suite — Execution Report",
        "pt-BR": "Linux Wayland Suite — Relatório de Execução",
    },
    "title_history": {
        "en": "Historical Trends (Metrics)",
        "pt-BR": "Tendência Histórica (Métricas)",
    },
    "title_list": {
        "en": "Recent Execution Reports (History)",
        "pt-BR": "Relatórios de Execuções Recentes (Histórico)",
    },
    "no_runs": {
        "en": "No execution runs recorded yet in {root}.\nRun any suite command (e.g. './bin/linux-wayland-config status') and try again.",
        "pt-BR": "Nenhuma execução registrada ainda em {root}.\nRode qualquer comando da suíte (ex: './bin/linux-wayland-config status') e tente de novo.",
    },
    "lbl_report": {"en": "Report", "pt-BR": "Relatório"},
    "lbl_command": {"en": "Command", "pt-BR": "Comando"},
    "lbl_when": {"en": "When", "pt-BR": "Quando"},
    "lbl_exit": {"en": "Result", "pt-BR": "Saída"},
    "success": {"en": "success (code 0)", "pt-BR": "sucesso (código 0)"},
    "failure": {"en": "failure (code {code})", "pt-BR": "falha (código {code})"},
    "no_events": {
        "en": "ℹ This command did not record structured events.",
        "pt-BR": "ℹ Este comando não registrou eventos estruturados.",
    },
    "raw_output": {"en": "Raw output saved at: {path}", "pt-BR": "Saída bruta preservada em: {path}"},
    "summary_stats": {
        "en": "Balance: {ok} ok · {fail} failure(s) · {warn} warning(s) · {skip} skipped",
        "pt-BR": "Balanço: {ok} ok · {fail} falha(s) · {warn} aviso(s) · {skip} pulado(s)",
    },
    "remediations_header": {
        "en": "How to resolve non-compliant items (Recommended Actions):",
        "pt-BR": "Como resolver pontos não conformes (Ações Recomendadas):",
    },
    "no_metrics": {
        "en": "ℹ No metrics recorded yet.",
        "pt-BR": "ℹ Nenhuma métrica registrada ainda.",
    },
    "samples": {"en": "sample(s)", "pt-BR": "amostra(s)"},
    "first": {"en": "first", "pt-BR": "primeiro"},
    "last": {"en": "last", "pt-BR": "último"},
    "variation": {"en": "delta", "pt-BR": "variação"},
    "no_change": {"en": "no change", "pt-BR": "sem mudança"},
    "col_idx": {"en": "INDEX", "pt-BR": "ÍNDICE"},
    "col_time": {"en": "DATE & TIME", "pt-BR": "DATA & HORA"},
    "col_cmd": {"en": "COMMAND", "pt-BR": "COMANDO"},
    "col_status": {"en": "STATUS", "pt-BR": "STATUS"},
    "interactive_prompt": {
        "en": "Enter the report number to view (or 'Q' to quit) [1-{max}]: ",
        "pt-BR": "Digite o número do relatório para exibir (ou 'Q' para sair) [1-{max}]: ",
    },
}

i18n = I18n(STRINGS)


def format_time(ts_str: str) -> str:
    try:
        ts = float(ts_str)
        dt = datetime.fromtimestamp(ts)
        fmt = "%d/%m/%Y às %H:%M:%S" if i18n.lang == "pt-BR" else "%Y-%m-%d %H:%M:%S"
        return dt.strftime(fmt)
    except Exception:
        return ts_str


def get_all_runs_sorted() -> List[str]:
    if not os.path.isdir(RUNLOG_ROOT):
        return []
    dirs = [
        d for d in glob.glob(os.path.join(RUNLOG_ROOT, "*"))
        if os.path.isdir(d)
    ]
    return sorted(dirs, reverse=True)


def get_recommendation(event_id: str, detail: str) -> str:
    recs = {
        "wifi_powersave_on_ac": {
            "en": f"{UI.WARNING}Wi-Fi Power (stability and low latency on AC):{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config smart-wifi-power --apply{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Energia do Wi-Fi (estabilidade e baixa latência na tomada):{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config smart-wifi-power --apply{UI.RESET}'",
        },
        "smart_wifi_power_missing": {
            "en": f"{UI.WARNING}Wi-Fi Power:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config smart-wifi-power --apply{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Energia do Wi-Fi:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config smart-wifi-power --apply{UI.RESET}'",
        },
        "machine_profile_missing": {
            "en": f"{UI.WARNING}Machine Profile:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config scan{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Perfil da Máquina:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config scan{UI.RESET}'",
        },
        "keyboard_power_auto_no_rule": {
            "en": f"{UI.WARNING}Keyboard Power (anti-latch / zero latency):{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config smart-keyboard-power --apply{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Energia do Teclado (anti-latch / zero latência):{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config smart-keyboard-power --apply{UI.RESET}'",
        },
        "tongfang_kernel_params_missing": {
            "en": f"{UI.WARNING}Tongfang/Avell Keyboard Matrix:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config fix-tongfang{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Teclado Tongfang/Avell:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config fix-tongfang{UI.RESET}'",
        },
        "chromium_cedilla_unpatched": {
            "en": f"{UI.WARNING}Chromium/Electron Cedilla Patch:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config patch-cedilla --apply{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Cedilha Wayland em Chromium/Electron:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config patch-cedilla --apply{UI.RESET}'",
        },
        "cedilla_hook_missing": {
            "en": f"{UI.WARNING}Pacman Cedilla Autorepair Hook:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config patch-cedilla --apply{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Autocura da Cedilha no Pacman:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config patch-cedilla --apply{UI.RESET}'",
        },
        "harness_mismatch": {
            "en": f"{UI.WARNING}AI Harness Alignment:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config configure-harness --sync{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Alinhamento de Harness/IA:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config configure-harness --sync{UI.RESET}'",
        },
        "fcitx5_running": {
            "en": f"{UI.DANGER}Input Method Conflict (fcitx5 breaks Ctrl+C):{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config fix-keyboard{UI.RESET}'",
            "pt-BR": f"{UI.DANGER}Conflito de Input Method (fcitx5 quebra Ctrl+C):{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config fix-keyboard{UI.RESET}'",
        },
        "im_conf_present": {
            "en": f"{UI.DANGER}Legacy IM Config:{UI.RESET} run '{UI.BOLD}./bin/linux-wayland-config fix-keyboard{UI.RESET}'",
            "pt-BR": f"{UI.DANGER}Configuração Legada de IM:{UI.RESET} execute '{UI.BOLD}./bin/linux-wayland-config fix-keyboard{UI.RESET}'",
        },
        "cpu_temp_high": {
            "en": f"{UI.DANGER}CPU Overheating:{UI.RESET} High CPU temperature detected. Check runaway processes and consider disabling Turbo: '{UI.BOLD}./bin/linux-wayland-config turbo{UI.RESET}'",
            "pt-BR": f"{UI.DANGER}Superaquecimento de CPU:{UI.RESET} Temperatura elevada detectada. Verifique processos em loop e desative o Turbo Boost: '{UI.BOLD}./bin/linux-wayland-config turbo{UI.RESET}'",
        },
        "cpu_runaway_detected": {
            "en": f"{UI.WARNING}Runaway Process Loop:{UI.RESET} Inspect and terminate runaway processes: '{UI.BOLD}./bin/linux-wayland-config turbo --watch{UI.RESET}'",
            "pt-BR": f"{UI.WARNING}Processo em Loop Infinito:{UI.RESET} Inspecione e encerre processos em loop: '{UI.BOLD}./bin/linux-wayland-config turbo --watch{UI.RESET}'",
        },
    }

    if event_id in recs:
        return recs[event_id].get(i18n.lang, recs[event_id]["en"])
    elif detail:
        return f"{event_id}: {detail}"
    return event_id


def show_run(run_dir: str) -> int:
    meta_file = os.path.join(run_dir, "meta.env")
    events_file = os.path.join(run_dir, "events.tsv")

    if not os.path.isdir(run_dir):
        print(f"{UI.DANGER}Erro: Diretório de relatório não encontrado: {run_dir}{UI.RESET}")
        return 1

    meta = {}
    if os.path.isfile(meta_file):
        try:
            with open(meta_file, encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        meta[k] = v.strip('"')
        except Exception:
            pass

    cmd_name = meta.get("COMMAND", "?")
    exit_code = meta.get("EXIT_CODE", "?")
    started = meta.get("STARTED_AT", "")
    duration = meta.get("DURATION_SECONDS", "?")

    folder_name = os.path.basename(run_dir)
    print(render_banner(i18n.t("title_report")))
    print(f"  • {UI.BOLD}{i18n.t('lbl_report')}:{UI.RESET} {folder_name}")
    print(f"  • {UI.BOLD}{i18n.t('lbl_command')}:{UI.RESET}   {cmd_name}")
    if started:
        print(f"  • {UI.BOLD}{i18n.t('lbl_when')}:{UI.RESET}    {format_time(started)} ({duration}s)")

    if exit_code == "0":
        print(f"  • {UI.BOLD}{i18n.t('lbl_exit')}:{UI.RESET}     {UI.SUCCESS}{i18n.t('success')}{UI.RESET}")
    else:
        print(f"  • {UI.BOLD}{i18n.t('lbl_exit')}:{UI.RESET}     {UI.DANGER}{i18n.t('failure', code=exit_code)}{UI.RESET}")
    print("")

    if not os.path.isfile(events_file) or os.path.getsize(events_file) == 0:
        print(f"  {i18n.t('no_events')}")
        out_log = os.path.join(run_dir, "output.log")
        if os.path.isfile(out_log):
            print(f"  {i18n.t('raw_output', path=out_log)}")
        return 0

    n_ok = n_fail = n_warn = n_skip = 0
    recommendations = []

    with open(events_file, encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            status = parts[1]
            event_id = parts[2]
            detail = parts[3] if len(parts) > 3 else ""

            if status == "metric":
                continue

            if status == "ok":
                n_ok += 1
                marker = f"{UI.SUCCESS}✅{UI.RESET}"
            elif status == "fail":
                n_fail += 1
                marker = f"{UI.DANGER}❌{UI.RESET}"
                recommendations.append(get_recommendation(event_id, detail))
            elif status == "warn":
                n_warn += 1
                marker = f"{UI.WARNING}⚠️{UI.RESET}"
                recommendations.append(get_recommendation(event_id, detail))
            elif status == "skip":
                n_skip += 1
                marker = f"{UI.PRIMARY}⏭️{UI.RESET}"
            else:
                marker = f"{UI.MUTED}•{UI.RESET}"

            detail_str = f" — {detail}" if detail else ""
            print(f"  {marker} {event_id}{detail_str}")

    print("")
    balance = i18n.t(
        "summary_stats",
        ok=f"{UI.SUCCESS}{n_ok}{UI.RESET}",
        fail=f"{UI.DANGER}{n_fail}{UI.RESET}",
        warn=f"{UI.WARNING}{n_warn}{UI.RESET}",
        skip=f"{UI.PRIMARY}{n_skip}{UI.RESET}",
    )
    print(f"  {UI.BOLD}{balance}{UI.RESET}")

    if recommendations:
        print(f"\n  {UI.BOLD}{UI.WARNING}{i18n.t('remediations_header')}{UI.RESET}")
        for rec in recommendations:
            print(f"  👉 {rec}")

    out_log = os.path.join(run_dir, "output.log")
    if os.path.isfile(out_log):
        print(f"\n  {UI.MUTED}{i18n.t('raw_output', path=out_log)}{UI.RESET}")

    return 0


def list_runs(limit: int = 10) -> List[str]:
    all_runs = get_all_runs_sorted()
    if not all_runs:
        print(f"{UI.WARNING}{i18n.t('no_runs', root=RUNLOG_ROOT)}{UI.RESET}")
        return []

    print(render_banner(i18n.t("title_list")))

    headers = [
        i18n.t("col_idx"),
        i18n.t("col_time"),
        i18n.t("col_cmd"),
        i18n.t("col_status"),
    ]

    rows = []
    selected = all_runs[:limit]

    for idx, run_dir in enumerate(selected, 1):
        meta_file = os.path.join(run_dir, "meta.env")
        events_file = os.path.join(run_dir, "events.tsv")

        cmd = "?"
        exit_code = "?"
        started = ""
        if os.path.isfile(meta_file):
            try:
                with open(meta_file) as f:
                    for line in f:
                        if line.startswith("COMMAND="):
                            cmd = line.split("=", 1)[1].strip().strip('"')
                        elif line.startswith("EXIT_CODE="):
                            exit_code = line.split("=", 1)[1].strip().strip('"')
                        elif line.startswith("STARTED_AT="):
                            started = line.split("=", 1)[1].strip().strip('"')
            except Exception:
                pass

        n_fail = n_warn = 0
        if os.path.isfile(events_file):
            try:
                with open(events_file) as f:
                    for line in f:
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            if parts[1] == "fail": n_fail += 1
                            elif parts[1] == "warn": n_warn += 1
            except Exception:
                pass

        if exit_code != "0" or n_fail > 0:
            status_desc = f"{UI.DANGER}❌ failure ({exit_code}){UI.RESET}" if i18n.lang == "en" else f"{UI.DANGER}❌ falha ({exit_code}){UI.RESET}"
        elif n_warn > 0:
            status_desc = f"{UI.WARNING}⚠️ warning ({n_warn}){UI.RESET}" if i18n.lang == "en" else f"{UI.WARNING}⚠️ aviso ({n_warn}){UI.RESET}"
        else:
            status_desc = f"{UI.SUCCESS}✅ success{UI.RESET}" if i18n.lang == "en" else f"{UI.SUCCESS}✅ sucesso{UI.RESET}"

        time_str = format_time(started) if started else "?"
        idx_str = f"[{UI.PRIMARY}{idx:2d}{UI.RESET}]"
        rows.append([idx_str, time_str, f"{UI.BOLD}{cmd}{UI.RESET}", status_desc])

    print(render_table(headers, rows))
    print(f"\n  {UI.MUTED}💡 linux-wayland-config report <index>  (e.g. report 1){UI.RESET}")
    print(f"  {UI.MUTED}💡 linux-wayland-config report --select (interactive menu){UI.RESET}\n")

    return selected


def select_run_interactive():
    selected = list_runs(15)
    if not selected:
        return 0

    try:
        choice = input(f"{UI.BOLD}{i18n.t('interactive_prompt', max=len(selected))}{UI.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print("")
        return 0

    if not choice or choice.lower() == "q":
        return 0

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(selected):
            print("")
            return show_run(selected[idx - 1])

    print(f"{UI.WARNING}Invalid selection.{UI.RESET}")
    return 1


def show_history() -> int:
    print(render_banner(i18n.t("title_history")))
    all_runs = get_all_runs_sorted()
    if not all_runs:
        print(f"  {i18n.t('no_metrics')}\n")
        return 0

    metrics: Dict[str, List[Tuple[str, str]]] = {}
    for r in all_runs:
        tsv = os.path.join(r, "events.tsv")
        if os.path.isfile(tsv):
            try:
                with open(tsv) as f:
                    for line in f:
                        parts = line.strip().split("\t")
                        if len(parts) >= 4 and parts[1] == "metric":
                            m_ts, m_id, m_val = parts[0], parts[2], parts[3]
                            metrics.setdefault(m_id, []).append((m_ts, m_val))
            except Exception:
                pass

    if not metrics:
        print(f"  {i18n.t('no_metrics')}\n")
        return 0

    for m_id, series in sorted(metrics.items()):
        # chronological order
        series = sorted(series, key=lambda x: x[0])
        first = series[0]
        last = series[-1]
        n_samples = len(series)

        print(f"\n  {UI.BOLD}{m_id}{UI.RESET}  ({n_samples} {i18n.t('samples')})")
        print(f"    {i18n.t('first')}: {first[1]} ({format_time(first[0])})")
        print(f"    {i18n.t('last')}:  {last[1]} ({format_time(last[0])})")

        try:
            val_a = float(first[1])
            val_b = float(last[1])
            delta = val_b - val_a
            if abs(delta) < 0.001:
                diff_str = f"{UI.PRIMARY}{i18n.t('no_change')}{UI.RESET}"
            else:
                diff_str = f"{UI.WARNING}{delta:+.2f}{UI.RESET}"
            print(f"    {i18n.t('variation')}: {diff_str}")
        except Exception:
            pass

    print("")
    return 0


def main():
    if not os.path.isdir(RUNLOG_ROOT):
        print(f"{UI.WARNING}{i18n.t('no_runs', root=RUNLOG_ROOT)}{UI.RESET}")
        return 0

    if len(sys.argv) == 1:
        # Default: show latest run
        runs = get_all_runs_sorted()
        if not runs:
            print(f"{UI.WARNING}{i18n.t('no_runs', root=RUNLOG_ROOT)}{UI.RESET}")
            return 0
        return show_run(runs[0])

    arg = sys.argv[1]
    if arg in ("--list", "-l", "list"):
        limit = 10
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            limit = int(sys.argv[2])
        list_runs(limit)
        return 0
    elif arg in ("--select", "-s", "select"):
        return select_run_interactive()
    elif arg in ("--history", "-h", "history"):
        return show_history()
    elif arg.isdigit():
        idx = int(arg)
        runs = get_all_runs_sorted()
        if 1 <= idx <= len(runs):
            return show_run(runs[idx - 1])
        else:
            print(f"{UI.DANGER}Índice fora do intervalo [1..{len(runs)}]{UI.RESET}")
            return 1
    else:
        # Check by folder name or path
        target = arg if os.path.isdir(arg) else os.path.join(RUNLOG_ROOT, arg)
        if os.path.isdir(target):
            return show_run(target)
        else:
            print(f"{UI.DANGER}Relatório não encontrado: {arg}{UI.RESET}")
            return 1


if __name__ == "__main__":
    sys.exit(main() or 0)

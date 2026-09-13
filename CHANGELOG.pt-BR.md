# Registro de Alterações (Changelog)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/).

## [2.12.1] - 2026-09-13

### Corrigido
- **Integração no Perfil da Máquina (`/init` & `profile-machine.py`)**:
  - Adicionada etapa `[2/6]` para auditoria de CPU, Turbo Boost e telemetria térmica em tempo real.
  - Persistido bloco estruturado `"cpu"` em `~/.config/linux-wayland-suite/machine-profile.json` (fabricante, modelo, driver, governor, turbo_supported, turbo_active, package_temp_c, persistence_enabled).
- **Integração no Assistente de Configuração (`/setup` & `setup-suite.py`)**:
  - Registrado CPU Turbo Boost & Modo Silencioso como opção `T` no assistente interativo contextual.
  - Adicionada flag `--turbo` (`--cpu-turbo`, `-t`) para automação e execuções em lote.
- **Governança Arquitetural (`SKILL.md` & `OUTPUT-CONTRACT.md`)**:
  - Atualizado explicitamente o checklist do Pilar 7 na skill de arquitetura e no `OUTPUT-CONTRACT.md` tornando obrigatório que qualquer nova capacidade de hardware seja inspecionada no `/init` (`profile-machine.py` + `machine-profile.json`) e exposta no `/setup` (`setup-suite.py`).

## [2.12.0] - 2026-09-13

### Adicionado
- **Gerenciamento de CPU Turbo Boost e Watchdog de Processos (`manage-cpu-turbo`)**:
  - Controle agnóstico de Turbo Boost para Intel (`intel_pstate/no_turbo`) e AMD (`cpufreq/boost`).
  - Watchdog veloz em memória varrendo o `/proc` em ~15ms para identificar processos em loop ou com vazamento de memória (>30% CPU) sem disparar subshells.
  - Modos de operação: `--status`, `--on`, `--off`, `--toggle`, `--persist`, `--remove-persist`, `--watch` e `--json`.
  - Unidade opcional de persistência no boot via systemd (`/etc/systemd/system/linux-wayland-cpu-turbo.service`).
  - Comandos integrados na CLI `linux-wayland-config` (`turbo`, `turbo-status`, `turbo-on`, `turbo-off`, `turbo-watch`, `turbo-persist`).
  - Alvos no Makefile: `make turbo`, `make turbo-status`, `make turbo-on`, `make turbo-off`, `make turbo-watch`, `make turbo-persist`.
  - Exibição em tempo real do estado do Turbo e temperatura no Portal Central de Controle (`portal_menu.py`).
- **Instalação Global e Persistência do PATH nos Shells (`/install`)**:
  - Melhorado o `cmd_install` com sincronização limpa para `~/.local/share/linux-wayland-suite`.
  - Persistência automática do `$PATH` no **Fish** (`~/.config/fish/conf.d/linux-wayland-suite-path.fish`), **Bash** (`~/.bashrc`), **Zsh** (`~/.zshrc`) e **Wayland/PAM** (`~/.config/environment.d/10-local-bin.conf`).
  - Novo comando de IA `/install` (`base/commands/install.md`) com fluxo guiado e contrato de output.
  - Modo standalone (`make install`) e modo de desenvolvimento com symlink para a worktree (`make install-dev`).
- **Comando de IA `/turbo` (`base/commands/turbo.md`)**:
  - Contrato padronizado em Markdown com perguntas interativas guiadas (`AskUserQuestion` / `ask`), evidências técnicas e tabela de conformidade dos 7 pilares.
  - Links simbólicos relativos criados para Claude Code, Cursor, OMP e Antigravity.

### Arquitetura e Governança
- **Matriz de Escolha de Tecnologia & Linguagem (`SKILL.md` Seção 3)**:
  - Diretrizes arquiteturais formalizadas para escolha entre Python (`.py`) e Shell POSIX (`.sh`).
  - Python é obrigatório para telemetria de hardware/térmica, auditoria de processos via `/proc`, interfaces ricas e abstrações multi-fabricante.
  - Shell é preferido para orquestração sequencial de binários nativos e ganchos em hot-path de boot/resume.
  - Formalizado o **Padrão Híbrido de Encapsulamento**: motor canônico em `.py` acompanhado de um despachante fino `.sh`.
- **Princípio de Soberania do Usuário (`SKILL.md` Regra 9)**:
  - Regra estrita: qualquer alteração de estado do sistema (políticas de energia, Turbo Boost, serviços systemd, encerramento de processos) deve ser decidida ativamente pelo usuário via perguntas interativas. O agente nunca toma decisões unilaterais.
- **Ergonomia de CLI — Contrato Default-on-Enter (`SKILL.md` Seção 3.5 & `lib_suite.py`)**:
  - Implementados helpers utilitários `prompt_confirm()` e `prompt_choice()` no `base/shared/lib_suite.py`.
  - Prompts interativos aceitam `<Enter>` (input vazio) como seleção imediata da opção recomendada, com suporte bilíngue (`[S/n]` ou `[Y/n]`).

### Aprimorado
- **Auditoria Contínua de Saúde (`check-status.py` e `diagnose-battery.py`)**:
  - Etapa 1 do `check-status.py` enriquecida com o estado do Turbo Boost e recomendação de comando.
  - Etapa 6 do `diagnose-battery.py` enriquecida com limites térmicos da CPU (normal, moderado, alerta) e estado do Turbo.
  - Adicionado mapeamento de remediação no `shared/report.py` para `cpu_temp_high` e `cpu_runaway_detected`.
- **Integração de Runlog**:
  - Corrigido `log_event()` no `lib_suite.py` para reconhecer tanto `RUNLOG_DIR` quanto `KDE_SUITE_RUN_DIR`, garantindo registro estruturado em `events.tsv`.

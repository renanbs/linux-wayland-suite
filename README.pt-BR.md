# KDE Plasma 6 Wayland Suite: Entrada, Hardware e Reparo de Teclado

[![Idioma: Inglês](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Idioma: Português](https://img.shields.io/badge/Idioma-Portugu%C3%AAs%20do%20Brasil-green.svg)](README.pt-BR.md)
[![KDE Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6-blue.svg)](https://kde.org/plasma-desktop/)
[![Wayland Ready](https://img.shields.io/badge/Wayland-Native-success.svg)](https://wayland.freedesktop.org/)
[![Multi-Harness Plugin](https://img.shields.io/badge/AI%20Harnesses-OMP%20%7C%20Claude%20%7C%20Cursor%20%7C%20Antigravity%20%7C%20OpenCode-purple.svg)](#-instalação-e-integração-com-ferramentas-de-ia)
[![Versão](https://img.shields.io/badge/Vers%C3%A3o-2.12.1-brightgreen.svg)](package.json)

**[English](README.md)** | **[Português do Brasil](README.pt-BR.md)**

Uma suíte de automação portátil, kit de diagnósticos e plugin multi-agente de IA para o **KDE Plasma 6 (Wayland)**. Projetada para corrigir atalhos corrompidos, resolver teclas modificadoras mortas em laptops Tongfang/Avell, gerenciar a energia do teclado de forma dinâmica, configurar a cedilha nativa (`ç`) no layout US-intl sem depender de input methods, eliminar travamentos de clipboard no Wayland, configurar gestos de 3 e 4 dedos no touchpad, mapear mouses Logitech MX Master 3S e auditar o consumo de bateria.

Compatível como plugin nativo para **Oh My Pi (OMP)**, **Claude Code**, **Cursor IDE & CLI**, **Google Antigravity** e **OpenCode**, além de funcionar diretamente pelo terminal via CLI (`kde-config`) e `Makefile`.

---

## 🎯 Problemas Resolvidos e Funcionalidades

### 1. Desbloqueio de Matriz de Teclado em Laptops Tongfang / Avell / Clevo
* **Problema:** Em notebooks com chassi Tongfang (Avell A62 LIV, GK5, GM5, Tuxedo Pulse, Schenker), a tecla `Left Ctrl` física não gera nenhum evento de entrada no `evtest`/`xev` porque o driver `i8042` e o DSDT ACPI do Linux descartam pacotes da porta I/O `0x60`.
* **Solução:** `./bin/kde-config fix-tongfang` injeta `i8042.nopnp=1 i8042.nomux=1 i8042.reset=1 atkbd.reset=1 acpi_osi='Windows 2020'` no GRUB, desbloqueando a matriz completa.

### 2. Gerenciamento Inteligente de Energia do Teclado (`anti-latch`)
* **Problema:** Sob o Runtime Power Management do Linux, o barramento PS/2 `serio0` entra em suspensão ociosa (`power/control = auto`), fazendo com que o primeiro pressionamento de modificadores de byte único (`Left Ctrl`) sofra atraso para acordar a porta.
* **Solução:** `./bin/linux-wayland-config smart-keyboard-power --apply` instala uma regra udev dinâmica que mantém o barramento em `power/control = on` (zero latência) quando o notebook é usado sozinho, e alterna automaticamente para `auto` (economia de bateria) sempre que um teclado externo USB ou Bluetooth for conectado.

### 3. Gerenciamento Inteligente de Energia do Wi-Fi (`smart-wifi-power`)
* **Problema:** Sob as políticas padrão de economia de energia, o rádio Wi-Fi (`iwlwifi`, etc.) dorme entre intervalos de beacons e o barramento PCIe entra em `D3hot`. Ao acessar a máquina remotamente (ex.: Orca IDE na porta `6768`, SSH, streaming), conexões de entrada sofrem latência inicial, pacotes descartados ou perda de conexão (*timeout*).
* **Solução:** `./bin/linux-wayland-config smart-wifi-power --apply` instala regra udev dinâmica, dispatcher do NetworkManager e gancho systemd-sleep:
  - **Na Tomada (AC):** Desativa automaticamente a economia de energia 802.11 (`power_save off`) e mantém o barramento PCIe ativo (`power/control = on`), garantindo zero dormência e estabilidade total em conexões de entrada.
  - **Na Bateria:** Reativa automaticamente o power save 802.11 (`power_save on`) e o PCIe runtime PM (`power/control = auto`) para economia máxima de bateria.

### 4. Gerenciamento de Turbo Boost e Watchdog Térmico (`turbo`)
* **Problema:** Laptops com processadores de alto TDP sob carga contínua ou processos em loop infinito (como renderizadores do Chromium/Electron e webviews travadas) travam as frequências da CPU em 4.0+ GHz. O consumo elétrico sobe para 60W+, disparando as ventoinhas no máximo e levando a temperatura a 85°C–90°C.
* **Solução:** `./bin/linux-wayland-config turbo` oferece controle multi-fabricante (Intel `intel_pstate` e AMD `cpufreq/boost`) para alternar entre o modo Silencioso/Frio (clock base, ~50°C, coolers desligados) e Alto Desempenho. Inclui um Watchdog em memória que varre o `/proc` em ~15ms para caçar processos em loop, além de persistência no boot via serviço systemd.

### 5. Atalhos `Ctrl+C` / `Ctrl+<tecla>` Quebrados no Layout ABNT2 (`br`)
* **Problema:** Módulos legados de input method (`GTK_IM_MODULE=cedilla` / `QT_IM_MODULE=cedilla`) ou o `fcitx5` ativo sob Wayland fazem *grab* do teclado e engolem combinações com Ctrl em apps Qt, GTK e Electron.
* **Solução:** Elimina variáveis nocivas de IM e mascara o autostart do `fcitx5` no sistema.

### 6. Cedilha Nativa no Layout US-intl (`' + c` $\to$ `ç` em Qt, GTK, Chrome, Orca IDE, Electron)
* **Problema no Nível do SO:** A tabela padrão `en_US` mapeia `<dead_acute> <c>` para `ć` (c com agudo).
* **Correção no Nível do SO (`fix-keyboard`):** Composição nativa **sem nenhum input method**. A tabela pt_BR do sistema (`/usr/share/X11/locale/pt_BR.UTF-8/Compose`) já mapeia `<dead_acute> <c>` para `ç`. A suite configura `LC_CTYPE=pt_BR.UTF-8` em `~/.config/environment.d/cedilla.conf` para Qt, GTK e Konsole.
* **Problema no Chromium/Electron sob Wayland:** No Wayland nativo (`--ozone-platform=wayland`), o Chromium e apps Electron ignoram o `libxkbcommon` e as tabelas de compose do sistema, usando um módulo interno próprio (`ui::CharacterComposer`) que tem `dead_acute + c` $\to$ `ć` chumbado no código-fonte (Issue Chromium 40272818).
* **Patch de Bytes e Autocura no Pacman (`patch-cedilla`):** `./bin/linux-wayland-config patch-cedilla --apply` aplica a substituição do padrão de bytes (`63 00 07 01` $\to$ `63 00 e7 00`) diretamente nos binários ELF instalados e registra o gancho `/etc/pacman.d/hooks/99-cedilla-wayland.hook`. Toda vez que o `pacman` ou `paru` atualizar qualquer navegador ou runtime Electron, o patch é reaplicado automaticamente pós-transação.
* **Aplicativos Detectados Dinamicamente e Verificados:**
  - **Google Chrome** (`/opt/google/chrome/chrome`)
  - **Orca IDE** (`/usr/lib/electron43/electron`)
  - **Visual Studio Code** (`/usr/share/code/code`)
  - **Discord** (`~/.config/discord/app-*/Discord`)
  - **Google Antigravity Platform & IDE** (`/opt/Antigravity/antigravity`, `/opt/antigravity-ide/antigravity-ide`)
  - **Brave Browser** (`/opt/brave-bin/brave`)
  - **Runtimes Electron do Sistema** (`electron37`, `electron39`, `electron40`, `electron42`, `electron43`)

### 7. Reparo de Deadlocks de Clipboard no Wayland
* **Problema:** Processos zumbis do `xsel` congelam comandos de cópia e colagem no terminal.
* **Solução:** Elimina processos travados e assegura o funcionamento nativo do backend `wl-clipboard` (`wl-copy`/`wl-paste`).

### 8. Gestos de Touchpad de 3 e 4 Dedos sem Conflito
* **Solução:** Mapeia gestos de 3 dedos (troca de workspace, Overview) e 4 dedos complementares às animações 1:1 nativas do KWin via `libinput-gestures` e KWin D-Bus (`qdbus6`).

### 9. Configuração de Botões e Rolagem do Logitech MX Master 3S
* **Solução:** Instala o `logiops`, configura o botão de polegar para Grade de Telas e Overview, fixa o SmartShift em rolagem livre e habilita `PerOutputVirtualDesktops=true` para setups multi-monitor.

### 10. Diagnóstico de Bateria e GPU Híbrida
* **Solução:** Audita a GPU primária do compositor em laptops híbridos Intel/NVIDIA/AMD, políticas de PCIe ASPM, runtime PM de dispositivos PCI e a saúde da bateria (`battery-status`).

### 11. Detecção de Host de IA (Harness) e Perfil de Modelos
* **Solução:** Detecta automaticamente o host ativo (OMP, Claude Code, Cursor, Antigravity), mapeia os papéis de modelos (Raciocínio, Código, Revisão, Segurança) e audita o alinhamento do ambiente em tempo real.

### 12. Perfil da Máquina e Setup Modular Contextual (`init` & `setup`)
* **Arquitetura:** Na `v2.2.0+`, `./bin/linux-wayland-config init` (ou `scan`) faz a varredura não-destrutiva e salva o perfil em `~/.config/linux-wayland-suite/machine-profile.json`. O comando `./bin/linux-wayland-config setup` lê esse perfil e exibe um assistente contextual com apenas as opções aplicáveis ao seu hardware.

### 13. Alternador de Taxa de Atualização da Tela Interna (`screen-hz`)
* **Solução:** `./bin/linux-wayland-config screen-hz 60` ou `120` alterna entre alta taxa (120Hz/144Hz) e o modo econômico de bateria (60Hz, economizando ~2W-3W).

### 14. Motor de Relatórios Numerados e Interativos
* **Solução:** Registros estruturados salvos em `~/.local/state/linux-wayland-suite/runs/`. Permite seleção interativa (`report --select`), consulta indexada (`report 3`) e gera ações recomendadas de 1 linha para qualquer aviso ou falha.

### 15. Identidade Visual Multi-Shell do Terminal & Alternador de Logo do Fastfetch (`terminal-fetch` / `cosmetic`)
* **Problema:** A apresentação inicial do terminal é engessada ou sobreposta em atualizações da distribuição (ex: Garuda Mokka forçando o mascote do gato pastel sobre a águia neon do Dr460nized, o `.zshrc` com chamada fixa `--config mokka` ignorando arquivos de usuário e o `.bashrc` sem hook automático).
* **Solução:** `./bin/linux-wayland-config cosmetic` (ou `make cosmetic`) oferece um menu interativo para alternar entre a Águia low-poly neon Dr460nized (`garuda-purple.png`), o Gato Mascote Mokka (`mokka-fastfetch.png`), o Emblema Hexagonal 'G', o Dragão ASCII nativo ou imagens personalizadas. Detecta todos os shells instalados (**Fish**, **Zsh**, **Bash**), limpa chamadas forçadas de sistema, pergunta se o usuário deseja sincronizar os demais shells e oferece reversão atômica (`--revert`).

### 16. Portal Central de Controle Interativo (`menu`)
* **Problema:** Lembrar de comandos isolados ou executar ações no escuro sem saber o estado atual do hardware aumenta a carga cognitiva e induz a alterações não planejadas.
* **Solução:** Executar `./bin/linux-wayland-config` sem argumentos no terminal (ou `./bin/linux-wayland-config menu`) abre o Portal de Controle Central (`portal_menu.py`). Ele exibe um card com o resumo em tempo real do sistema (Hardware, Layout ativo no KWin, Fonte de Energia/Bateria e Estado da Cedilha) e um menu numerado com descrições ricas de cada módulo, loops de execução sem perda de histórico e bilinguismo completo (`pt-BR` e `en`).
---

## 🧪 Testado e Comprovado em Produção

Esta suite é continuamente testada e validada em hardware e ambientes reais de produção:

| Categoria | Hardware e Ambiente Verificado |
| :--- | :--- |
| **Hosts de IA (Harnesses)** | • **Testado e Comprovado em Produção:** **Oh My Pi (OMP) + Google Antigravity** (`gemini-3.7-flash`) e **Claude Code (CLI)** (`claude-3-7-sonnet`)<br/>• **Suportado por Arquitetura:** Cursor IDE & Agent, Google Antigravity CLI e OpenCode |
| **Ambiente Gráfico & SO** | • **KDE Plasma:** 6.7.x / 6.7.4 (KWin Wayland nativo)<br/>• **Distribuição Linux:** Garuda Linux / Arch Linux (Rolling release)<br/>• **Kernel:** `7.2.x-zen` (Linux Zen) / Linux Mainline `6.12+` |
| **Laptop / Chassi** | • **Avell A62 LIV** (Chassi **Tongfang GK5MQX** / Séries GK5 / GM5)<br/>• **CPU/GPU:** Intel Core i7-10750H + NVIDIA GeForce GTX 1650 Mobile / Intel UHD 630 (Gráficos híbridos) |
| **Teclado Integrado** | • **AT Translated Set 2 keyboard** (`isa0060/serio0` via chip EC ITE IT5570E/IT8528)<br/>• Layouts: Brasileiro ABNT2 (`br`) e US-Internacional (`us alt-intl`) |
| **Mouse & Touchpad** | • **Mouse:** Logitech MX Master 3S (Bluetooth / Logi Bolt Receiver via `logiops`)<br/>• **Touchpad:** Uniwill Precision Touchpad (`i2c-UNIW0001:00 093A:0255` via `libinput-gestures`) |

---

## 🚀 Uso Rápido (CLI e Makefile)

```bash
# Clonar o repositório
git clone https://github.com/renanbs/linux-wayland-suite.git ~/src/linux-wayland-suite
cd ~/src/linux-wayland-suite

# 1. Passo 1: Varredura de hardware e geração do perfil da máquina (leitura pura)
./bin/linux-wayland-config init
# ou: make init (ou: make scan)

# 2. Passo 2: Assistente de configuração modular (escolha o que deseja aplicar)
./bin/linux-wayland-config setup
# ou: make setup

# 3. Passo 3: Auditoria de saúde geral do ambiente
./bin/linux-wayland-config status
# ou: make status
```

---

## 🛠️ Tabela Geral de Comandos da CLI

| Comando | Alvo Makefile | Descrição |
| :--- | :--- | :--- |
| `linux-wayland-config menu` | `make menu` | Portal de controle central interativo com resumo de hardware em tempo real |
| `linux-wayland-config init` / `scan` | `make init` / `make scan` | Varredura de hardware não-destrutiva & perfil da máquina (`machine-profile.json`) |
| `linux-wayland-config setup` | `make setup` | Assistente de configuração modular contextual baseado no hardware |
| `linux-wayland-config status` | `make status` | Auditoria unificada em 7 etapas: hardware, DMI, energia, Wi-Fi, IM, cedilha e gestos |
| `linux-wayland-config smart-wifi-power` | `make smart-wifi-power` | Gerenciamento dinâmico de Wi-Fi (`off` na tomada para zero latência, `on` na bateria) |
| `linux-wayland-config screen-hz [60\|120]` | `make screen-60` / `screen-120` | Alterna a taxa de atualização da tela interna (60 Hz vs 120 Hz) |
| `linux-wayland-config fix-keyboard` | `make fix-keyboard` | Corrige `Ctrl+C` no ABNT2, configura a cedilha nativa e mascara o fcitx5 |
| `linux-wayland-config patch-cedilla` | `make patch-cedilla` | Patch de bytes no Chromium/Electron (`'+c -> ç`) + gancho de autocura no Pacman |
| `linux-wayland-config fix-tongfang` | `make fix-tongfang` | Desbloqueia a matriz no GRUB para laptops Tongfang/Avell/Clevo |
| `linux-wayland-config smart-keyboard-power` | `make smart-keyboard-power` | Gestão dinâmica de energia (`on` sozinho, `auto` com teclado USB/BT) |
| `linux-wayland-config configure-harness` | — | Configura e sincroniza o perfil do host de IA e papéis de modelos |
| `linux-wayland-config battery-status` | `make battery-status` | Diagnóstico de bateria, GPU híbrida e PCIe ASPM (somente leitura) |
| `linux-wayland-config battery-apply` | `make battery-apply` | Aplica otimizações de bateria escolhidas pelo usuário (`BATTERY_FIX_*`) |
| `linux-wayland-config turbo` | `make turbo` | Gerenciamento de Turbo Boost, modo silencioso e caçador de processos em loop |
| `linux-wayland-config gestures` | `make gestures` | Configura gestos de 3 e 4 dedos no touchpad (`libinput-gestures`) |
| `linux-wayland-config mouse` | `make mouse` | Configura botão de polegar e SmartShift do Logitech MX Master 3S via `logiops` |
| `linux-wayland-config test-keyboard` | `make test-keyboard` | Monitor interativo de eventos de teclado em tempo real (`/dev/input/eventX`) |
| `linux-wayland-config monitor-irq` | `make monitor-irq` | Monitor elétrico de hardware no IRQ 1 (`i8042`) |
| `linux-wayland-config switch [br\|us]` | `make switch-br` | Alterna o layout ativo no KWin via D-Bus (0=br abnt2, 1=us alt-intl) |
| `linux-wayland-config report` | `make report` | Exibe o relatório da última execução, métricas e ações recomendadas |
| `linux-wayland-config report --list` | — | Lista os relatórios recentes numerados (`[1..N]`) |
| `linux-wayland-config report <N>` | — | Exibe detalhadamente o N-ésimo relatório mais recente |
| `linux-wayland-config report --select` | — | Menu interativo no terminal para escolher qualquer relatório |
| `linux-wayland-config upgrade` | `make upgrade` | Verifica e aplica atualizações do GitHub e marketplace |
| `linux-wayland-config rollback` | `make rollback` | Restaura o snapshot anterior a partir do backup |
| `linux-wayland-config cosmetic` / `terminal-fetch` | `make cosmetic` / `make terminal-fetch` | Menu interativo de identidade visual e troca de logo do Fastfetch |
| `linux-wayland-config install` | `make install` / `make install-dev` | Instala a suíte de forma permanente e configura o PATH em todos os shells |
| `linux-wayland-config help` | `make help` | Exibe o manual completo de ajuda |
---

## 🤖 Instalação e Integração com Ferramentas de IA
### Instalação Global da CLI e Configuração de PATH
Para executar os comandos da suíte (`linux-wayland-config` ou `kde-config`) a partir de qualquer diretório no seu terminal:
```bash
# Instalação permanente standalone (copia os motores para ~/.local/share, independente do git):
make install

# Ou modo de desenvolvimento (cria symlinks em ~/.local/bin apontando para esta worktree):
make install-dev
```
* Registra automaticamente `~/.local/bin` no `$PATH` do **Fish** (`~/.config/fish/conf.d/linux-wayland-suite-path.fish`), **Bash** (`~/.bashrc`), **Zsh** (`~/.zshrc`) e **Wayland/PAM** (`~/.config/environment.d/10-local-bin.conf`).


### 1. Oh My Pi (OMP)
Instale diretamente pelo marketplace remoto:
```bash
# No terminal do OMP:
omp plugin marketplace add renanbs/linux-wayland-suite
omp plugin install linux-wayland-suite@linux-wayland-suite

# Atualizar versão:
omp plugin marketplace update linux-wayland-suite
omp plugin upgrade linux-wayland-suite@linux-wayland-suite
```
* **Comandos Slash Disponíveis:** `/linux-wayland-suite:status`, `/linux-wayland-suite:init`, `/linux-wayland-suite:patch-cedilla`, `/linux-wayland-suite:fix-keyboard`, `/linux-wayland-suite:fix-tongfang`, `/linux-wayland-suite:smart-keyboard-power`, `/linux-wayland-suite:configure-harness`, `/linux-wayland-suite:battery`, `/linux-wayland-suite:turbo`, `/linux-wayland-suite:install`, `/linux-wayland-suite:report`, `/linux-wayland-suite:help`, `/linux-wayland-suite:upgrade`.
* **Skills:** `skill://linux-wayland-suite`, `skill://linux-wayland-suite-architecture`.

### 2. Claude Code
```bash
/plugin marketplace add renanbs/linux-wayland-suite
/plugin install linux-wayland-suite@linux-wayland-suite
```

### 3. Cursor IDE & Agent
```bash
# 1. Instalar CLI global
cd ~/src/kde-wayland-suite && make install-cli

# 2. Habilitar regras globais para todos os projetos no Cursor
mkdir -p ~/.cursor/rules
cp .cursor/rules/kde-wayland-suite.mdc ~/.cursor/rules/
```

### 4. Google Antigravity & OpenCode
Reconhecido automaticamente pela raiz do workspace via `antigravity/plugin.json` e `opencode/skills/`.

---

## 📐 Arquitetura e Disciplina de Engenharia

Este repositório segue a constituição arquitetural definida em **`skills/kde-wayland-suite-architecture`**:
1. **Fonte Canônica em `base/`:** Todos os comandos `.md` residem em `base/commands/`, scripts em `base/shared/` e skills em `base/skills/`. Todas as pastas de plataforma usam symlinks relativos.
2. **Contrato de Saída Tetra-Fásico (`OUTPUT-CONTRACT.md`):** Todo comando executado por IAs segue rigorosamente:
   * `### 1. Plano` (Comando, Faz, Reversível)
   * `### 2. Execução` (`✅`, `⏭️`, `⚠️`, `❌`)
   * `### 3. Resumo` (Tabela: O que mudou, O que não mudou, Backup, Relatório salvo, Reverter, Requer)
   * `### 4. Ações Recomendadas` (Obrigatório se houver `⚠️` ou `❌`, com comando de 1 linha)
3. **Eventos Estruturados:** Salvos em `~/.local/state/kde-wayland-suite/runs/<data_hora>-<cmd>/events.tsv`.

---

## 📄 Licença

MIT © [Renan BS](https://github.com/renanbs)

---
description: Installs Linux Wayland Suite permanently into ~/.local/share, symlinks CLI binaries to ~/.local/bin, and configures user shells (Fish, Bash, Zsh) and Wayland environment.d for global PATH access.
---

# /install

Installs the Linux Wayland Suite permanently to your user environment so commands can be executed from any terminal and directory:

```bash
linux-wayland-config install
```

---

## Mandatory AI Agent Workflow

1. Check current installation status and whether `~/.local/bin` is in the user's active `$PATH`:
   ```bash
   which linux-wayland-config
   ```
2. Prompt the user using `AskUserQuestion` (or `ask`):
   - **Standalone Mode (Recommended):** Copies files permanently to `~/.local/share/linux-wayland-suite/`, independent of git branches or worktrees.
   - **Development Mode (`--dev`):** Symlinks directly to the active git repository worktree so edits take effect immediately system-wide.
3. Run the installation:
   ```bash
   # Standalone permanent installation
   ./bin/linux-wayland-config install

   # Or development symlink mode
   ./bin/linux-wayland-config install --dev
   ```
4. Verify that `linux-wayland-config status` and `linux-wayland-config turbo` can be invoked from outside the repository (e.g. from `/tmp`).
5. Report the result adhering to the Evidence-First Verdict format.

---

## What is Configured

- **Canonical Engine:** Copied to `~/.local/share/linux-wayland-suite/{bin,shared,commands}/`.
- **User Executables in `~/.local/bin/`:**
  * `linux-wayland-config`
  * `kde-config`
  * `wayland-config`
- **Shell PATH Persistence:**
  * **Wayland & PAM:** `~/.config/environment.d/10-local-bin.conf`
  * **Fish Shell:** `~/.config/fish/conf.d/linux-wayland-suite-path.fish` (`fish_add_path -g ~/.local/bin`)
  * **Bash:** Appends to `~/.bashrc` if not present.
  * **Zsh:** Appends to `~/.zshrc` if not present.

---

## Standard Output Format (Evidence-First Verdict)

Every command response must follow this structured, evidence-based format:

### 🎯 Verdict: [ ✅ SUCCESS | ❌ FAILURE | ⚠️ PARTIAL SUCCESS ]
*One clear sentence summarizing the real, observable outcome of the installation.*

---

#### 📋 Execution Breakdown:
* **✅ Applied Successfully:**
  - `<Component Name>`: Concise description of exact changes made and verified.

---

#### 🔬 Technical Evidence & Ground Truth:
| Component | Verified State | Observable Proof / Command | How to Revert |
| :--- | :--- | :--- | :--- |
| `CLI Binary` | `Installed` | `which linux-wayland-config` | `rm -f ~/.local/bin/linux-wayland-config` |
| `Engine Files` | `~/.local/share` | `ls ~/.local/share/linux-wayland-suite` | `rm -rf ~/.local/share/linux-wayland-suite` |
| `Shell PATH` | `Configured` | `echo $PATH` | `rm ~/.config/environment.d/10-local-bin.conf` |

---

#### 👉 Action Required:
Test the command from any terminal:
```bash
linux-wayland-config status
```

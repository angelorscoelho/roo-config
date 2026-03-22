#!/usr/bin/env python3
"""
Roo Code Global Budget Config Installer — v3
=============================================
Cross-platform (Windows / macOS / Linux) | Python 3.8+
Upgrades cleanly from v1 and v2 installations.
Does NOT touch API keys — those live in OS environment variables.

Commands:
  python install.py                    Global install / upgrade
  python install.py --dry-run          Preview without writing
  python install.py --undo             Restore backups from last install
  python install.py --init-project     Scaffold project in current directory
  python install.py --init-project PATH  Scaffold specific project path
  python install.py --check-env        Verify environment variables

Python MCP Servers:
  For Python-based MCP servers (e.g., duckduckgo-mcp), use 'uv + venv':
    1. cd /path/to/project
    2. uv venv              → creates .venv
    3. uv pip install <pkg> → installs to .venv automatically
    4. Add entry to mcp_settings.json with "uv" command + "run" args
  See install_python_mcp_server() function for programmatic usage.
"""

import sys
import os
import shutil
import platform
import argparse
import json
from pathlib import Path
from datetime import datetime

# ─── Colour helpers ──────────────────────────────────────────────────────────
ANSI = sys.stdout.isatty() and (
    platform.system() != "Windows"
    or bool(os.environ.get("WT_SESSION"))
    or bool(os.environ.get("TERM_PROGRAM"))
)

def c(text, code):  return f"\033[{code}m{text}\033[0m" if ANSI else text
def ok(msg):        print(c(f"  ✔  {msg}", "32"))
def warn(msg):      print(c(f"  ⚠  {msg}", "33"))
def err(msg):       print(c(f"  ✘  {msg}", "31"), file=sys.stderr)
def info(msg):      print(c(f"  →  {msg}", "36"))
def head(msg):      print(c(f"\n{'─'*60}\n  {msg}\n{'─'*60}", "1"))
def step(n, msg):   print(c(f"\n  [{n}] {msg}", "1;33"))

# ─── OS-specific paths ───────────────────────────────────────────────────────

def get_vscode_globalStorage() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "Code" / "User" / "globalStorage"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "Code" / "User" / "globalStorage"

def get_roo_settings_dir() -> Path:
    return get_vscode_globalStorage() / "rooveterinaryinc.roo-cline" / "settings"

def get_roo_mcp_settings_path() -> Path:
    return get_roo_settings_dir() / "cline_mcp_settings.json"

def get_roo_global_rules_dir() -> Path:
    return Path.home() / ".roo" / "rules"

# ─── File locations ───────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
CONFIGS_DIR  = SCRIPT_DIR / "configs"
TEMPLATE_DIR = CONFIGS_DIR / "project-template"

SOURCE_MODES = CONFIGS_DIR / "custom_modes.yaml"
SOURCE_RULES = CONFIGS_DIR / "00-global-budget-rules.md"
SOURCE_MCP   = CONFIGS_DIR / "mcp_settings.json"

LOG_PATH     = SCRIPT_DIR / ".install_log"

# ─── Safety: verify no credentials in config files ───────────────────────────

CREDENTIAL_PATTERNS = ["ghp_", "ghs_", "sk-", "BSA7", "AIza", "xoxb-", "xoxp-"]

def check_no_credentials(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="ignore")
    found = [p for p in CREDENTIAL_PATTERNS if p in content]
    if found:
        err(f"CREDENTIAL DETECTED in {path.name}: patterns {found}")
        err("  This file must use ${{env:VAR}} references only. Aborting.")
        return False
    return True

# ─── Helpers ─────────────────────────────────────────────────────────────────

# ─── Python-based MCP Server Installer ───────────────────────────────────────

def install_python_mcp_server(package_name: str, mcp_config_path: Path) -> bool:
    """
    Helper for installing Python-based MCP servers that require uv + virtual environment.

    CRITICAL: 'uv pip' requires a virtual environment. Without it, installation fails.
    The correct workflow is:
        1. uv venv          → creates .venv in current directory
        2. uv pip install <package>   → installs to .venv automatically (no --system needed)

    Args:
        package_name: The pip package name (e.g., "duckduckgo-mcp", "some-mcp-server")
        mcp_config_path: Path to the MCP settings JSON to update (e.g., globalStorage mcp_settings)

    Returns:
        True if installation succeeded, False otherwise.

    Example usage after successful install:
        # Add to your mcp_settings.json manually:
        {
          "mcpServers": {
            "duckduckgo-mcp": {
              "command": "uv",
              "args": ["--directory", "/path/to/your/project", "run", "duckduckgo-mcp"]
            }
          }
        }

    NOTE: If uv is not installed, install it first:
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    """
    import subprocess

    print()
    head(f"Installing Python MCP Server: {package_name}")

    # Step 1: Create virtual environment if it doesn't exist
    venv_path = Path(".venv")
    if venv_path.exists():
        ok(f"Virtual environment already exists: {venv_path}")
    else:
        info("Creating virtual environment with 'uv venv'...")
        result = subprocess.run(["uv", "venv"], capture_output=True, text=True)
        if result.returncode != 0:
            err(f"Failed to create venv: {result.stderr}")
            err("Make sure uv is installed: powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            return False
        ok("Created .venv")

    # Step 2: Install the package
    info(f"Installing {package_name} with 'uv pip install'...")
    result = subprocess.run(["uv", "pip", "install", package_name], capture_output=True, text=True)
    if result.returncode != 0:
        err(f"Failed to install {package_name}: {result.stderr}")
        return False
    ok(f"Installed: {package_name}")

    # Step 3: Verify installation
    info("Verifying installation...")
    verify_result = subprocess.run(["uv", "pip", "show", package_name], capture_output=True, text=True)
    if verify_result.returncode == 0:
        ok(f"Verified: {package_name}")
    else:
        warn(f"Could not verify {package_name} — check manually with 'uv pip show {package_name}'")

    print()
    info("Next step: Add to your mcp_settings.json:")
    print(f"       \"{package_name}\": {{")
    print(f"         \"command\": \"uv\",")
    print(f"         \"args\": [\"run\", \"{package_name}\"]")
    print(f"       }}")

    if mcp_config_path.exists():
        info(f"MCP config location: {mcp_config_path}")
    else:
        warn(f"MCP config not found at expected path: {mcp_config_path}")
        warn("Add the entry above to your mcp_settings.json manually.")

    return True


def backup(target: Path) -> "Path | None":
    if not target.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = target.with_suffix(f".bak_{ts}")
    shutil.copy2(target, bak)
    return bak

def install_file(src: Path, dst: Path, dry_run: bool) -> "Path | None":
    if not src.exists():
        err(f"Source not found: {src}")
        sys.exit(1)
    if not check_no_credentials(src):
        sys.exit(1)
    bak = None
    if dst.exists():
        if not dry_run:
            bak = backup(dst)
        warn(f"Backed up existing: {dst.name} → {bak.name if bak else '(dry-run)'}")
    if dry_run:
        info(f"[dry-run] {src.name} → {dst}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ok(f"Installed: {dst}")
    return bak

def copy_tree_template(src: Path, dst: Path, dry_run: bool, skip_existing=True):
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if skip_existing and target.exists():
            info(f"[skip existing] {rel}")
            continue
        if dry_run:
            info(f"[dry-run] {rel} → {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            ok(f"Created: {target}")

def record_install(entries: "list[tuple[Path, Path | None]]"):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        for dst, bak in entries:
            f.write(f"{dst}|{bak or 'NONE'}\n")

def undo_install():
    if not LOG_PATH.exists():
        err("No install log found. Nothing to undo.")
        sys.exit(1)
    head("Undoing previous install")
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    for line in lines:
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        dst, bak_str = Path(parts[0]), parts[1]
        if bak_str == "NONE":
            if dst.exists():
                dst.unlink()
                ok(f"Removed: {dst}")
        else:
            bak = Path(bak_str)
            if bak.exists():
                shutil.copy2(bak, dst)
                bak.unlink()
                ok(f"Restored: {dst}")
            else:
                err(f"Backup not found: {bak}")
    LOG_PATH.unlink(missing_ok=True)
    ok("Undo complete.")

def validate_yaml(path: Path):
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        modes = data.get("customModes", [])
        ok(f"YAML valid — {len(modes)} modes")
        return True
    except ImportError:
        warn("PyYAML not available — skipping YAML validation")
        return True
    except Exception as e:
        err(f"YAML invalid: {e}")
        return False

def validate_json(path: Path):
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
        ok(f"JSON valid: {path.name}")
        return True
    except Exception as e:
        err(f"JSON invalid ({path.name}): {e}")
        return False

# ─── Environment variable check ───────────────────────────────────────────────

REQUIRED_ENV = {
    "GITHUB_PERSONAL_ACCESS_TOKEN": (
        "GitHub PAT — https://github.com/settings/tokens\n"
        "       Scopes: repo, read:org, read:user"
    ),
    "BRAVE_API_KEY": (
        "Brave Search key — https://api.search.brave.com/app/keys"
    ),
}

def check_env(verbose=True) -> bool:
    if verbose:
        head("Environment Variable Check")
    missing = []
    for var, desc in REQUIRED_ENV.items():
        val = os.environ.get(var, "")
        if val and len(val) > 8:
            if verbose:
                ok(f"{var} ✓  ({val[:4]}...{val[-4:]})")
        else:
            missing.append(var)
            if verbose:
                err(f"{var} NOT SET")
                for line in desc.splitlines():
                    print(f"       {line}")
    if missing and verbose:
        print()
        warn("On Windows — set in System Environment Variables:")
        print("  Win+R → sysdm.cpl → Advanced → Environment Variables → User variables → New")
        print()
        warn("Or temporarily in PowerShell (this session only):")
        for var in missing:
            print(f'  $env:{var} = "YOUR_VALUE"')
        print()
        warn("RESTART VS Code after setting — it does not inherit mid-session.")
    return len(missing) == 0

# ─── MCP settings merge (preserve structure, never touch credentials) ─────────

def install_mcp_settings(src: Path, dst: Path, dry_run: bool) -> "Path | None":
    """
    Install MCP settings. Since v3 uses env vars exclusively,
    we simply overwrite — no credential merging needed.
    We DO warn if the destination has raw credentials (v1 format).
    """
    if not src.exists():
        err(f"Source not found: {src}")
        sys.exit(1)

    bak = None

    if dst.exists():
        # Warn if old file had hardcoded credentials (v1 format)
        old_content = dst.read_text(encoding="utf-8", errors="ignore")
        legacy_creds = [p for p in CREDENTIAL_PATTERNS if p in old_content]
        if legacy_creds:
            warn("Old mcp_settings.json had hardcoded credentials.")
            warn("Those are no longer needed — credentials now come from env vars.")
            warn("Make sure you've already rotated those keys (GitHub PAT + Brave key).")

        if not dry_run:
            bak = backup(dst)
        warn(f"Backed up: {dst.name} → {bak.name if bak else '(dry-run)'}")

    if dry_run:
        info(f"[dry-run] mcp_settings.json → {dst}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ok(f"Installed: {dst}")

    return bak

# ─── Global install ───────────────────────────────────────────────────────────

def run_global_install(dry_run: bool):
    head("Roo Code Global Budget Config — v3 Installer")
    print(f"  Platform : {platform.system()} {platform.machine()}")
    print(f"  Python   : {sys.version.split()[0]}")
    if dry_run:
        print(c("  Mode     : DRY RUN", "33"))
    print(f"  Upgrades : cleanly overrides v1 and v2 installations")
    print(f"  API Keys : NOT touched (stored in OS env vars)")

    dst_modes = get_roo_settings_dir() / "custom_modes.yaml"
    dst_rules = get_roo_global_rules_dir() / "00-global-budget-rules.md"
    dst_mcp   = get_roo_mcp_settings_path()

    head("Target Paths")
    info(f"Custom modes  → {dst_modes}")
    info(f"Global rules  → {dst_rules}")
    info(f"MCP settings  → {dst_mcp}")

    head("Preflight Validation")
    yaml_ok = validate_yaml(SOURCE_MODES)
    json_ok = validate_json(SOURCE_MCP)
    if not (yaml_ok and json_ok):
        err("Validation failed. Aborting.")
        sys.exit(1)

    if not get_roo_settings_dir().exists() and not dry_run:
        warn("Roo Code globalStorage not found — will be created.")
        warn("Launch VS Code with Roo Code installed first, then re-run if issues occur.")
    else:
        ok("Roo Code globalStorage found")

    head("Installing Global Files")
    log = []

    bak1 = install_file(SOURCE_MODES, dst_modes, dry_run)
    log.append((dst_modes, bak1))

    bak2 = install_file(SOURCE_RULES, dst_rules, dry_run)
    log.append((dst_rules, bak2))

    bak3 = install_mcp_settings(SOURCE_MCP, dst_mcp, dry_run)
    log.append((dst_mcp, bak3))

    if not dry_run:
        record_install(log)

    check_env(verbose=True)

    head("Manual Steps Required")

    steps = [
        (
            "1", "Reload VS Code",
            "Ctrl+Shift+P → 'Developer: Reload Window'\n"
            "     All 10 custom modes appear in Roo Code mode selector immediately."
        ),
        (
            "2", "Install uv (Serena dependency) — if not already done",
            "PowerShell:\n"
            "     powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n"
            "     Verify: uvx --version   (restart terminal after install)"
        ),
        (
            "3", "Assign OpenRouter models per mode — Sticky Models, set ONCE",
            "Switch to each mode → click model selector → OpenRouter → paste ID → set temp:\n\n"
            "     MODE              MODEL ID                            TEMP  REASONING  ROUTING\n"
            "     ──────────────── ─────────────────────────────────  ─────  ─────────  ───────\n"
            "     🏛️ Architect     google/gemini-2.5-flash              0.3   None       google-vertex\n"
            "     ⚡ Code           minimax/minimax-m2.7                 0.05  None       [default]\n"
            "     ❓ Ask            google/gemini-2.5-flash-lite         0.5   None       google-vertex\n"
            "     🐛 Debug         deepseek/deepseek-v3.2               0.0   Low        [default]\n"
            "     🎯 Orchestrator  minimax/minimax-m2.7                 0.2   None       [default]\n"
            "     🔀 Merge Res.    deepseek/deepseek-v3.1-terminus      0.0   None       [default]\n"
            "     📄 Docs          google/gemini-2.5-flash-lite         0.6   None       google-vertex\n"
            "     📋 User Story    google/gemini-2.5-flash-lite         0.7   None       google-vertex\n"
            "     ⚙️ DevOps        deepseek/deepseek-v3.2               0.1   Low        [default]\n"
            "     🔒 Security      deepseek/deepseek-v3.2               0.0   Medium     [default]\n\n"
            "     NOTE on deepseek-v3.2-speciale: acceptable alternative to deepseek-v3.2.\n"
            "     NOTE on minimax-m2.7: confirmed good choice over m2.5 (5% cost delta, better quality).\n"
            "     NOTE on Reasoning: Low = controlled CoT | Medium = deeper analysis | None = pure output.\n"
            "          WHY NOT R1 for Debug/Security: R1 loops far more aggressively than v3.2+Low."
        ),
        (
            "4", "Configure Advanced Settings in Roo Code (per mode)",
            "For EACH mode, open Advanced Settings and set:\n"
            "     ✓ Enable todo list tool → ON (prevents loop drift on complex tasks)\n"
            "     ✓ Use custom temperature → ON, then set the temperature from table above\n"
            "     ✓ Error & Repetition Limit → 3 (safety net against loops)\n"
            "     ✓ Rate limit → 1s (prevents API rate-limit errors on fast models)\n"
            "     ✓ OpenRouter Provider Routing → see table above (google-vertex for Gemini models)"
        ),
        (
            "5", "Optional community MCP servers to install manually",
            "These are NOT in the automated config (unverified package names) but highly recommended:\n\n"
            "     Ref.tools — 95% fewer tokens than Context7 for doc lookups:\n"
            "       → Visit https://ref.tools and follow their MCP setup guide\n"
            "       → Add to your mcp_settings.json manually after verifying the install command\n\n"
            "     CRASH-MCP — token-efficient reasoning scaffold (replaces Sequential Thinking):\n"
            "       → Search reddit.com/r/ClaudeAI for 'CRASH-MCP' for current install instructions\n"
            "       → Once confirmed, add to mcp_settings.json with 'disabled: true' in global,\n"
            "         enable only in projects that need deep reasoning chains (e.g. complex debugging)"
        ),
        (
            "6", "Initialize each project (run once per project)",
            "cd to your project root, then:\n"
            "     python path/to/roo-config/install.py --init-project\n"
            "     Fill in memory-bank/productContext.md and projectBrief.md\n"
            "     git add .roo/ memory-bank/ projectBrief.md && git commit"
        ),
    ]

    for num, title, detail in steps:
        step(num, title)
        for line in detail.splitlines():
            print(f"     {line}")

    print()
    if dry_run:
        warn("DRY RUN — no files written.")
    else:
        ok("Install v3 complete.")
        info("To undo: python install.py --undo")
    print()

# ─── Project init ─────────────────────────────────────────────────────────────

def run_init_project(project_path: Path, dry_run: bool):
    head(f"Project Init: {project_path.name}")

    if not project_path.exists():
        err(f"Path does not exist: {project_path}")
        sys.exit(1)
    if not (project_path / ".git").exists():
        warn("No .git found. Memory bank won't be source-controlled without git init.")

    if dry_run:
        print(c("  Mode: DRY RUN", "33"))

    copy_tree_template(TEMPLATE_DIR, project_path, dry_run, skip_existing=True)

    # Update .gitignore for Serena
    gitignore = project_path / ".gitignore"
    serena_lines = [
        "\n# Serena MCP — cache files only (memories are committed)",
        ".serena/*.log",
        ".serena/server_state.json",
        ".serena/index/",
    ]
    if not dry_run:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        if ".serena" not in existing:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n".join(serena_lines) + "\n")
            ok(".gitignore updated with Serena exclusions")
        else:
            info(".gitignore already has .serena — skipped")
    else:
        info("[dry-run] Would update .gitignore")

    head("Commit These Files")
    commit_files = [
        ".roo/mcp.json                  ← Serena project MCP config (no credentials)",
        ".roo/rules/01-memory-bank-protocol.md  ← MCP decision tree + memory rules",
        "memory-bank/productContext.md  ← FILL IN FIRST",
        "memory-bank/activeContext.md   ← Updated by UMB command",
        "memory-bank/decisionLog.md     ← Architectural decisions",
        "memory-bank/progress.md        ← Task tracker",
        "memory-bank/systemPatterns.md  ← Coding conventions",
        "projectBrief.md                ← FILL IN FIRST",
        ".serena/memories/              ← After Serena onboarding (auto-generated)",
    ]
    for f in commit_files:
        info(f)

    head("Next Steps for This Project")
    proj_steps = [
        ("1", "Fill in projectBrief.md + memory-bank/productContext.md",
         "Most important step. These are read at EVERY session start.\n"
         "     The quality of these files = the quality of every Roo session."),
        ("2", "Run Serena onboarding",
         'In Roo Code chat: "Activate this project with Serena and perform onboarding"\n'
         "     Serena indexes the codebase → creates .serena/memories/\n"
         "     Commit .serena/memories/ immediately after."),
        ("3", "Commit everything",
         "git add .roo/ memory-bank/ projectBrief.md .serena/\n"
         "     git commit -m 'chore: initialize Roo Code v3 memory bank'\n"
         "     Any machine that clones this repo gets full Roo Code context."),
        ("4", "UMB habit",
         'Type "UMB" at end of every Roo session. Commit memory-bank/ changes.\n'
         "     This is the difference between €0.05 sessions and €5 sessions."),
    ]
    for num, title, detail in proj_steps:
        step(num, title)
        for line in detail.splitlines():
            print(f"     {line}")

    print()
    if dry_run:
        warn("DRY RUN — no files written.")
    else:
        ok("Project initialized.")
    print()

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Roo Code v3 Installer")
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--undo",         action="store_true")
    parser.add_argument("--init-project", nargs="?", const=".", metavar="PATH")
    parser.add_argument("--check-env",    action="store_true")
    args = parser.parse_args()

    if args.undo:
        undo_install(); return
    if args.check_env:
        ok_flag = check_env(verbose=True)
        sys.exit(0 if ok_flag else 1)
    if args.init_project is not None:
        run_init_project(Path(args.init_project).resolve(), args.dry_run); return

    run_global_install(args.dry_run)

if __name__ == "__main__":
    main()

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
  python install.py --install-mcp      Install all MCP servers from config
  python install.py --test-mcp         Test connectivity of all MCP servers
  python install.py --install-cline    Install Cline global rules and skills

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
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# ─── Colour helpers ──────────────────────────────────────────────────────────
ANSI = sys.stdout.isatty() and (
    platform.system() != "Windows"
    or bool(os.environ.get("WT_SESSION"))
    or bool(os.environ.get("TERM_PROGRAM"))
)

def c(text, code):  return f"\033[{code}m{text}\033[0m" if ANSI else text

def clean_text(text):
    """Replace Unicode characters with ASCII alternatives when ANSI is disabled."""
    if ANSI:
        return text
    # Replace common Unicode symbols with ASCII equivalents
    replacements = {
        "→": "->",
        "─": "-",
        "—": "-",
        "✔": "[OK]",
        "✓": "[OK]",
        "⚠": "[WARN]",
        "✘": "[ERR]",
        "✗": "[ERR]",
        "🏛️": "[ARCH]",
        "⚡": "[CODE]",
        "❓": "[ASK]",
        "🐛": "[DEBUG]",
        "🎯": "[ORCH]",
        "🔀": "[MERGE]",
        "📄": "[DOCS]",
        "📋": "[STORY]",
        "⚙️": "[DEVOPS]",
        "🔒": "[SECURITY]",
    }
    result = text
    for uni, ascii_repl in replacements.items():
        result = result.replace(uni, ascii_repl)
    return result

def ok(msg):        
    symbol = "✓" if ANSI else "[OK]"
    print(c(f"  {symbol}  {clean_text(msg)}", "32"))
def warn(msg):      
    symbol = "⚠" if ANSI else "[WARN]"
    print(c(f"  {symbol}  {clean_text(msg)}", "33"))
def err(msg):       
    symbol = "✗" if ANSI else "[ERR]"
    print(c(f"  {symbol}  {clean_text(msg)}", "31"), file=sys.stderr)
def info(msg):      
    symbol = "→" if ANSI else "->"
    print(c(f"  {symbol}  {clean_text(msg)}", "36"))
def head(msg):      
    line_char = "─" if ANSI else "-"
    print(c(f"\n{line_char*60}\n  {clean_text(msg)}\n{line_char*60}", "1"))
def step(n, msg):   print(c(f"\n  [{n}] {clean_text(msg)}", "1;33"))

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

# ─── Cline-specific paths ─────────────────────────────────────────────────────

def get_cline_settings_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"

def get_cline_mcp_settings_path() -> Path:
    return get_cline_settings_dir() / "cline_mcp_settings.json"

def get_cline_global_rules_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        docs = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
    else:
        docs = Path.home() / "Documents"
    return docs / "Cline" / "Rules"

def get_cline_global_skills_dir() -> Path:
    return Path.home() / ".cline" / "skills"

# ─── File locations ───────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
CONFIGS_DIR  = SCRIPT_DIR / "configs"
TEMPLATE_DIR = CONFIGS_DIR / "project-template"

SOURCE_MODES = CONFIGS_DIR / "custom_modes.yaml"
SOURCE_RULES = CONFIGS_DIR / "00-global-budget-rules.md"
SOURCE_MCP   = CONFIGS_DIR / "mcp_settings.json"

# Cline sources
CLINE_RULES_DIR  = CONFIGS_DIR / "cline" / "rules"
CLINE_SKILLS_DIR = CONFIGS_DIR / "cline" / "skills"
SOURCE_CLINE_MCP = CONFIGS_DIR / "mcp_settings.json"   # same MCP settings file — shared

LOG_PATH     = SCRIPT_DIR / ".install_log"

# ─── Safety: verify no credentials in config files ───────────────────────────

CREDENTIAL_PATTERNS = ["ghp_", "ghs_", "sk-", "BSA7", "AIza", "xoxb-", "xoxp-"]


# ─── WSL / Windows env helpers ──────────────────────────────────────────────
def is_wsl() -> bool:
    """Return True if running under WSL (Linux on Windows)."""
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def fetch_windows_user_env_vars(var_names: List[str]) -> None:
    """When running under WSL, attempt to import Windows *user* environment
    variables via PowerShell and set them in the WSL environment.

    Only best-effort: if PowerShell isn't available from WSL the function will
    warn and return without failing.
    """
    # Only attempt on WSL (Linux-on-Windows)
    if platform.system() != "Linux" or not is_wsl():
        return

    info("Detected WSL — attempting to import Windows user env vars")
    for var in var_names:
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command",
                 f"[System.Environment]::GetEnvironmentVariable('{var}', 'User')"],
                capture_output=True, text=True, timeout=5,
            )
            if proc.returncode == 0:
                val = proc.stdout.strip()
                if val:
                    os.environ[var] = val
                    ok(f"Imported Windows user env var: {var}")
                else:
                    info(f"Windows user env var not set: {var}")
            else:
                info(f"Could not read {var} via PowerShell: {proc.stderr.strip()}")
        except FileNotFoundError:
            warn("powershell.exe not available from WSL — cannot import Windows user env vars")
            break
        except Exception as e:
            warn(f"Error reading Windows env var {var}: {e}")


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


# ─── MCP Server Definitions ───────────────────────────────────────────────────

MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    # ── uvx-based servers ────────────────────────────────────────────────────
    "serena": {
        "_doc": "PRIMARY: Semantic LSP code search. Replaces most read_file calls. Use before any file read.",
        "type": "uvx",
        "package": None,
        "install_cmd": ["uvx", "--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"],
        "config": {
            "command": "uvx",
            "args": [
                "--from", "git+https://github.com/oraios/serena",
                "serena", "start-mcp-server",
                "--context", "ide-assistant",
                "--project-from-cwd",
                "--no-open-browser"
            ]
        },
        "env_vars": [],
        "test_url": None,
    },

    # ── npm-based servers ─────────────────────────────────────────────────────
    "fetch": {
      "_doc": "FREE: Official MCP fetch — converts any URL to clean Markdown. Zero cost, zero API key. Use BEFORE duckduckgo-mcp.",
      "type": "npx",
      "package": "mcp-fetch-server",
      "install_cmd": ["npx", "-y", "mcp-fetch-server"],
      "config": {
        "command": "npx",
        "args": ["-y", "mcp-fetch-server"]
      },
      "env_vars": [],
      "test_url": None,
    },

    "context7": {
      "_doc": "DOCS: Version-accurate library documentation. Use for API lookups, not broad research.",
      "type": "npx",
      "package": "@upstash/context7-mcp",
      "install_cmd": ["npx", "-y", "@upstash/context7-mcp"],
      "config": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"]
      },
      "env_vars": [],
      "test_url": None,
    },


    # ── HTTP-based servers (external service) ─────────────────────────────────
    "ref.tools": {
      "_doc": "DOCS: Token-efficient doc lookups. 95% fewer tokens than Context7. Requires API key from ref.tools website.",
      "type": "npx",
      "package": "ref-tools-mcp",
      "install_cmd": ["npx", "-y", "ref-tools-mcp"],
      "config": {
        "command": "npx",
        "args": ["-y", "ref-tools-mcp"],
        "env": {
          "REF_TOOLS_API_KEY": "${env:REF_TOOLS_API_KEY}"
        }
      },
      "env_vars": ["REF_TOOLS_API_KEY"],
      "test_url": None,
    },

    # ── Python/uv-based servers ───────────────────────────────────────────────
    "duckduckgo-mcp": {
        "_doc": "SEARCH: PRIMARY web search. Privacy-safe, no API key required. Use instead of brave-search.",
        "type": "uvx",
        "package": "duckduckgo-mcp",
        "install_cmd": ["uvx", "--from", "duckduckgo-mcp", "duckduckgo-mcp"],
        "config": {
            "command": "uvx",
            "args": ["--from", "duckduckgo-mcp", "duckduckgo-mcp"]
        },
        "env_vars": [],
        "test_url": None,
    },

    "crash-mcp": {
        "_doc": "REASONING: Token-efficient reasoning scaffold. Replaces verbose chain-of-thought. Python/uv-based.",
        "type": "uvx",
        "package": "crash-mcp",
        "install_cmd": ["uvx", "--from", "crash-mcp", "crash-mcp"],
        "config": {
            "command": "uvx",
            "args": ["--from", "crash-mcp", "crash-mcp"]
        },
        "env_vars": [],
        "test_url": None,
    },

    # ── Docker-based servers ─────────────────────────────────────────────────
    "github": {
        "_doc": "REPO: GitHub issues, PRs, code. Dynamic toolsets = loads tools on demand (~4 at start).",
        "type": "docker",
        "package": None,
        "install_cmd": None,  # Docker image pulled at runtime
        "config": {
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e", "GITHUB_DYNAMIC_TOOLSETS",
                "ghcr.io/github/github-mcp-server"
            ],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}",
                "GITHUB_DYNAMIC_TOOLSETS": "1"
            }
        },
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "test_url": None,
    },

    # ── memory-bank (project init script, not a server) ─────────────────────
    "memory-bank": {
        "_doc": "PROJECT: Memory bank scaffolding via install.py --init-project. Not an MCP server — a project template.",
        "type": "external",
        "package": None,
        "install_cmd": None,
        "config": {},
        "env_vars": [],
        "test_url": None,
    },

    # ── SSE-based servers (disabled by default) ───────────────────────────────
    "figma-dev-mode": {
        "_doc": "UI: Figma Dev Mode integration. Enable per-project when doing UI work.",
        "type": "sse",
        "package": None,
        "install_cmd": None,
        "config": {
            "type": "sse",
            "url": "http://127.0.0.1:3845/sse",
            "disabled": True
        },
        "env_vars": [],
        "test_url": None,
    },
}


def install_mcp_server(server_name: str, server_config: Dict[str, Any], dry_run: bool = False) -> bool:
    """
    Install a single MCP server based on its type.
    
    Args:
        server_name: Name of the server (e.g., "duckduckgo-mcp")
        server_config: Dict containing server metadata from MCP_SERVERS
        dry_run: If True, only show what would be done
    
    Returns:
        True if installation succeeded or not needed, False on error
    """
    srv_type = server_config.get("type", "unknown")
    pkg = server_config.get("package")
    install_cmd = server_config.get("install_cmd")
    env_vars = server_config.get("env_vars", [])
    
    head(f"Installing MCP Server: {server_name}")
    info(f"Type: {srv_type}")
    if pkg:
        info(f"Package: {pkg}")
    
    # Check required env vars
    missing_env = [e for e in env_vars if not os.environ.get(e)]
    if missing_env:
        warn(f"Missing env vars (server will work once set): {missing_env}")
    
    if srv_type == "python":
        # Python package via uv
        if not install_cmd:
            err(f"No install command for {server_name}")
            return False
        
        # Create venv if needed
        venv_path = Path(".venv")
        if not venv_path.exists():
            info("Creating .venv with uv...")
            if not dry_run:
                result = subprocess.run(["uv", "venv"], capture_output=True, text=True)
                if result.returncode != 0:
                    err(f"Failed to create venv: {result.stderr}")
                    return False
            ok("Created .venv")
        else:
            info(".venv already exists")
        
        # Install package
        info(f"Installing {pkg}...")
        if not dry_run:
            result = subprocess.run(["uv", "pip", "install", pkg], capture_output=True, text=True)
            if result.returncode != 0:
                err(f"Install failed: {result.stderr}")
                return False
        ok(f"Installed {pkg}")
        return True
    
    elif srv_type == "python_module":
        # Python module that runs via `python -m <module>`
        if not install_cmd:
            err(f"No install command for {server_name}")
            return False
        
        venv_path = Path(".venv")
        if not venv_path.exists():
            info("Creating .venv with uv...")
            if not dry_run:
                result = subprocess.run(["uv", "venv"], capture_output=True, text=True)
                if result.returncode != 0:
                    err(f"Failed to create venv: {result.stderr}")
                    return False
            ok("Created .venv")
        
        info(f"Installing {pkg}...")
        if not dry_run:
            result = subprocess.run(["uv", "pip", "install", pkg], capture_output=True, text=True)
            if result.returncode != 0:
                err(f"Install failed: {result.stderr}")
                return False
        ok(f"Installed {pkg}")
        return True
    
    elif srv_type == "uvx":
        # uvx runs directly, no installation needed
        info("uvx servers run directly — no installation needed")
        info("Verify uvx is available:")
        if not dry_run:
            result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                ok(f"uvx available: {result.stdout.strip()}")
            else:
                err("uvx not found. Install uv first.")
                return False
        return True
    
    elif srv_type == "npx":
        # npx runs directly
        info("npx servers run directly — no installation needed")
        info("Verify npx is available:")
        if not dry_run:
            # On Windows, npx is npx.cmd
            npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
            result = subprocess.run([npx_cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                ok(f"npx available: {result.stdout.strip()}")
            else:
                err("npx not found. Install Node.js.")
                return False
        return True
    
    elif srv_type == "docker":
        info("Docker servers pull images at runtime")
        info("Verify Docker is available:")
        if not dry_run:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                ok(f"Docker available: {result.stdout.strip()}")
            else:
                err("Docker not found or not running.")
                return False
        return True
    
    elif srv_type == "http":
        info("HTTP/SSE servers are external services")
        info(f"Test URL: {server_config.get('test_url')}")
        info("No local installation needed")
        return True
    
    elif srv_type == "external":
        info("External server — installation varies")
        info("Check server documentation for install instructions")
        return True
    
    else:
        err(f"Unknown server type: {srv_type}")
        return False


def run_mcp_install(dry_run: bool = False):
    """Install all MCP servers from the config."""
    head("MCP Server Installation")
    
    if dry_run:
        warn("DRY RUN — no changes will be made")
    
    # Ensure uv is available
    info("Checking uv availability...")
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        err("uv not installed. Install first:")
        info("Windows: powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        info("macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh")
        if not dry_run:
            return
    else:
        ok(f"uv: {result.stdout.strip()}")
    
    # Check for uvx (used by serena)
    result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        warn("uvx not available — serena may not work")
    
    results = {}
    for name, config in MCP_SERVERS.items():
        print()
        success = install_mcp_server(name, config, dry_run=dry_run)
        results[name] = success
        if success:
            ok(f"{name}: ready")
        else:
            err(f"{name}: failed")
    
    print()
    head("Installation Summary")
    for name, success in results.items():
        status = "✓" if success else "✗"
        info(f"  {status} {name}")
    
    if all(results.values()):
        ok("All MCP servers installed successfully")
    else:
        warn("Some servers failed — check above for details")
        info("Note: Some servers need API keys set as environment variables")


def test_mcp_server_connectivity(server_name: str, server_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connectivity for a single MCP server.
    
    Returns dict with:
        - success: bool
        - message: str
        - details: dict (optional)
    """
    srv_type = server_config.get("type")
    test_url = server_config.get("test_url")
    env_vars = server_config.get("env_vars", [])
    
    result = {
        "success": False,
        "message": "",
        "details": {}
    }
    
    # Check env vars
    missing = [e for e in env_vars if not os.environ.get(e)]
    if missing:
        result["message"] = f"Missing env vars: {missing}"
        result["details"]["missing_env"] = missing
        return result
    
    if srv_type == "http" and test_url:
        # Test HTTP endpoint
        try:
            req = urllib.request.Request(test_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result["success"] = True
                result["message"] = f"HTTP {resp.status}"
                result["details"]["status_code"] = resp.status
        except urllib.error.HTTPError as e:
            result["message"] = f"HTTP {e.code}"
            result["details"]["http_error"] = e.code
        except Exception as e:
            result["message"] = str(e)
        return result
    
    elif srv_type in ("uvx", "npx"):
        # Just verify the command exists
        cmd = server_config["config"]["command"]
        # On Windows, npx is npx.cmd
        if cmd == "npx" and platform.system() == "Windows":
            cmd = "npx.cmd"
        try:
            proc = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = f"{cmd} available"
                result["details"]["version"] = proc.stdout.strip()
            else:
                result["message"] = f"{cmd} not available"
        except Exception as e:
            result["message"] = str(e)
        return result
    
    elif srv_type == "docker":
        # Check docker
        try:
            proc = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = "Docker available"
            else:
                result["message"] = "Docker not available"
        except Exception as e:
            result["message"] = str(e)
        return result
    
    elif srv_type in ("python", "python_module"):
        # Check if package is installed in venv
        pkg = server_config.get("package")
        if pkg:
            try:
                proc = subprocess.run(
                    ["uv", "pip", "show", pkg],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode == 0:
                    result["success"] = True
                    result["message"] = f"{pkg} installed"
                    result["details"]["package_info"] = proc.stdout.split("\n")[0] if proc.stdout else ""
                else:
                    result["message"] = f"{pkg} not installed"
            except Exception as e:
                result["message"] = str(e)
        return result
    
    elif srv_type == "external":
        # External servers (e.g., HTTP/SSE-based) are configured but not locally installed
        result["success"] = True
        result["message"] = "External server (configured in mcp_settings.json)"
        return result
    
    result["message"] = f"Unknown type: {srv_type}"
    return result


def test_mcp_servers():
    """Test connectivity for all configured MCP servers."""
    head("MCP Server Connectivity Test")
    
    # Check env vars first
    info("Checking environment variables...")
    all_env_vars = set()
    for cfg in MCP_SERVERS.values():
        all_env_vars.update(cfg.get("env_vars", []))
    
    for var in sorted(all_env_vars):
        val = os.environ.get(var, "")
        if val and len(val) > 8:
            ok(f"{var}: {'*' * (len(val) - 8)}{val[-8:]}")
        else:
            warn(f"{var}: NOT SET")
    
    print()
    head("Testing Server Connectivity")
    
    results = {}
    for name, config in MCP_SERVERS.items():
        print()
        info(f"Testing {name}...")
        test_result = test_mcp_server_connectivity(name, config)
        results[name] = test_result
        
        if test_result["success"]:
            ok(f"  {test_result['message']}")
        else:
            warn(f"  {test_result['message']}")
        
        if test_result.get("details"):
            for k, v in test_result["details"].items():
                print(f"       {k}: {v}")
    
    print()
    head("Test Summary")
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    info(f"Passed: {passed}/{total}")
    
    for name, r in results.items():
        status = "✓" if r["success"] else "⚠"
        info(f"  {status} {name}: {r['message']}")
    
    return results


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
    "REF_TOOLS_API_KEY": (
        "Ref.tools API key — https://ref.tools (95% fewer tokens than Context7)\n"
        "       Sign up at ref.tools to get your API key (free tier available)"
    ),
    "GITHUB_PERSONAL_ACCESS_TOKEN": (
        "GitHub PAT — https://github.com/settings/tokens\n"
        "       Scopes: repo, read:org, read:user"
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
        print("  Win+R -> sysdm.cpl -> Advanced -> Environment Variables -> User variables -> New")
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

# ─── Cline install ───────────────────────────────────────────────────────────

def run_cline_install(dry_run: bool):
    """Install Cline global rules and skills."""
    head("Cline Global Config Installer")
    print(f"  Platform : {platform.system()} {platform.machine()}")
    if dry_run:
        print(c("  Mode     : DRY RUN", "33"))

    dst_rules_dir  = get_cline_global_rules_dir()
    dst_skills_dir = get_cline_global_skills_dir()
    dst_mcp        = get_cline_mcp_settings_path()

    head("Target Paths")
    info(f"Global rules  → {dst_rules_dir}/")
    info(f"Global skills → {dst_skills_dir}/")
    info(f"MCP settings  → {dst_mcp}")

    log = []

    # Install global rules
    head("Installing Global Rules")
    if CLINE_RULES_DIR.exists():
        for rule_file in sorted(CLINE_RULES_DIR.glob("*.md")):
            dst = dst_rules_dir / rule_file.name
            bak = install_file(rule_file, dst, dry_run)
            log.append((dst, bak))
    else:
        warn(f"Cline rules source not found: {CLINE_RULES_DIR}")

    # Install global skills
    head("Installing Global Skills")
    if CLINE_SKILLS_DIR.exists():
        for skill_dir in sorted(CLINE_SKILLS_DIR.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    dst = dst_skills_dir / skill_dir.name / "SKILL.md"
                    bak = install_file(skill_md, dst, dry_run)
                    log.append((dst, bak))
    else:
        warn(f"Cline skills source not found: {CLINE_SKILLS_DIR}")

    # Install MCP settings
    head("Installing MCP Settings")
    bak = install_mcp_settings(SOURCE_CLINE_MCP, dst_mcp, dry_run)
    log.append((dst_mcp, bak))

    if not dry_run:
        record_install(log)

    check_env(verbose=True)

    head("Manual Steps Required")
    cline_steps = [
        ("1", "Reload VS Code",
         "Ctrl+Shift+P → 'Developer: Reload Window'\n"
         "     Global rules appear in Cline's Rules panel (scale icon) immediately."),
        ("2", "Verify Skills in Cline",
         "Open Cline → Skills panel → you should see all 8 skills listed.\n"
         "     Skills activate automatically when your request matches their domain."),
        ("3", "MCP servers — same stack as Roo Code",
         "serena, fetch, ref.tools, context7, duckduckgo-mcp, crash-mcp, github\n"
         "     All configured in the shared mcp_settings.json installed above.\n"
         "     Run: python install.py --test-mcp to verify all servers are live."),
        ("4", "Initialize each project for Cline",
         "cd to project root, then:\n"
         "     python install.py --init-project\n"
         "     This creates .clinerules/ in addition to .roo/rules/"),
    ]
    for num, title, detail in cline_steps:
        step(num, title)
        for line in detail.splitlines():
            print(f"     {clean_text(line)}")

    print()
    if dry_run:
        warn("DRY RUN — no files written.")
    else:
        ok("Cline install complete.")
    print()

# ─── Global install ───────────────────────────────────────────────────────────

def run_global_install(dry_run: bool):
    head("Roo Code Global Budget Config — v3 Installer")
    print(f"  Platform : {platform.system()} {platform.machine()}")
    print(f"  Python   : {sys.version.split()[0]}")
    if dry_run:
        print(c("  Mode     : DRY RUN", "33"))
    # Try to import Windows user environment variables when running under WSL.
    # This is best-effort and won't fail the installer if unavailable.
    try:
        fetch_windows_user_env_vars(list(REQUIRED_ENV.keys()))
    except NameError:
        # REQUIRED_ENV may be defined later in the file; if so, fetching will
        # occur at runtime when run_global_install is invoked.
        pass
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

    # If running interactively and required env vars are missing, warn the
    # user and require they set the Windows *User* env vars before proceeding.
    missing_required = [v for v in REQUIRED_ENV.keys() if not os.environ.get(v)]
    if missing_required and not dry_run:
        head("Required Environment Variables Missing")
        warn("The following REQUIRED environment variables are not present in the current environment:")
        for v in missing_required:
            print(f"     - {v}")
        print()
        print("Please set these as Windows USER environment variables (Win+R → sysdm.cpl → Advanced → Environment Variables → New) and then restart VS Code or import them into WSL via WSLENV.")
        print("After setting the variables, press Enter to continue, or Ctrl+C to abort the installation.")
        try:
            input("Press Enter to continue after setting env vars (or Ctrl+C to abort)...")
        except KeyboardInterrupt:
            err("Installation aborted by user.")
            sys.exit(1)
        except EOFError:
            err("Interactive input not available — aborting.")
            sys.exit(1)

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
            "5", "MCP servers (duckduckgo-mcp, crash-mcp) — installed via uvx automatically",
            "Both are installed via uvx — no separate install step needed.\n\n"
            "     duckduckgo-mcp — PRIMARY web search, no API key required:\n"
            "       → uvx --from duckduckgo-mcp duckduckgo-mcp  (auto-runs)\n\n"
            "     crash-mcp — token-efficient reasoning scaffold:\n"
            "       → uvx --from crash-mcp crash-mcp  (auto-runs)\n\n"
            "     ref.tools — 95% fewer tokens than Context7 (optional API key):\n"
            "       → Set REF_TOOLS_API_KEY env var, then reload VS Code\n"
            "       → Free tier available without key; key unlocks higher rate limits"
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
            print(f"     {clean_text(line)}")

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

    # Also scaffold Cline project rules
    cline_template = TEMPLATE_DIR / ".clinerules"
    if cline_template.exists():
        dst_clinerules = project_path / ".clinerules"
        copy_tree_template(cline_template, dst_clinerules, dry_run, skip_existing=True)
        ok("Scaffolded .clinerules/")

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
        ".clinerules/02-memory-bank-protocol.md ← Cline memory bank protocol",
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
         "git add .roo/ .clinerules/ memory-bank/ projectBrief.md .serena/\n"
         "     git commit -m 'chore: initialize Roo Code v3 memory bank'\n"
         "     Any machine that clones this repo gets full Roo Code context."),
        ("4", "UMB habit",
         'Type "UMB" at end of every Roo session. Commit memory-bank/ changes.\n'
         "     This is the difference between €0.05 sessions and €5 sessions."),
    ]
    for num, title, detail in proj_steps:
        step(num, title)
        for line in detail.splitlines():
            print(f"     {clean_text(line)}")

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
    parser.add_argument("--install-mcp",  action="store_true", help="Install all MCP servers")
    parser.add_argument("--test-mcp",     action="store_true", help="Test MCP server connectivity")
    parser.add_argument("--install-cline", action="store_true", help="Install Cline global rules and skills")
    args = parser.parse_args()

    if args.undo:
        undo_install(); return
    if args.check_env:
        ok_flag = check_env(verbose=True)
        sys.exit(0 if ok_flag else 1)
    if args.init_project is not None:
        run_init_project(Path(args.init_project).resolve(), args.dry_run); return
    if args.install_mcp:
        run_mcp_install(dry_run=args.dry_run); return
    if args.test_mcp:
        test_mcp_servers(); return
    if args.install_cline:
        run_cline_install(dry_run=args.dry_run); return

    run_global_install(args.dry_run)

if __name__ == "__main__":
    main()

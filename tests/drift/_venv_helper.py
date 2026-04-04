"""Venv helper for drift tests — auto-loads .venv if present and not already active.

Usage: Add the following at the top of any test file (after __future__ imports):

    from __future__ import annotations
    from tests.drift import _venv_helper  # noqa: F401
    _venv_helper.ensure_venv()

This is a no-op if:
- The .venv directory doesn't exist
- Already running inside a virtual environment (VIRTUAL_ENV is set)
- The .venv is already active in sys.path
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_repo_root() -> Path | None:
    """Find the repo root from this file's location."""
    # This file is at tests/drift/_venv_helper.py
    # Repo root is 3 levels up
    try:
        return Path(__file__).resolve().parents[2]
    except Exception:
        return None


def _is_venv_active() -> bool:
    """Check if a virtual environment is already active."""
    # Check VIRTUAL_ENV environment variable
    if os.environ.get("VIRTUAL_ENV"):
        return True
    # Check if sys.executable is inside a venv
    exe_path = Path(sys.executable)
    if ".venv" in str(exe_path) or "venv" in str(exe_path):
        return True
    # Check if site-packages path contains .venv
    for path in sys.path:
        if ".venv" in path or "site-packages" in path:
            if Path(path).exists() and ".venv" in str(Path(path).resolve()):
                return True
    return False


def _is_venv_already_in_path(venv_path: Path) -> bool:
    """Check if the given venv is already in sys.path."""
    venv_str = str(venv_path.resolve())
    for path in sys.path:
        try:
            if venv_str in str(Path(path).resolve()):
                return True
        except Exception:
            continue
    return False


def ensure_venv() -> None:
    """Activate the .venv if it exists and isn't already active.
    
    This function is idempotent and safe to call multiple times.
    It modifies sys.path and sys.executable to point to the venv.
    """
    # Early exit if already in a venv
    if _is_venv_active():
        return
    
    # Find repo root
    repo_root = _find_repo_root()
    if not repo_root:
        return
    
    # Look for .venv directory
    venv_path = repo_root / ".venv"
    if not venv_path.exists():
        return
    
    # Check if already in path
    if _is_venv_already_in_path(venv_path):
        return
    
    # Determine platform-specific paths
    is_windows = sys.platform == "win32"
    
    if is_windows:
        venv_python = venv_path / "Scripts" / "python.exe"
        venv_site_packages = venv_path / "Lib" / "site-packages"
    else:
        venv_python = venv_path / "bin" / "python"
        # Find site-packages (may vary by Python version)
        lib_path = venv_path / "lib"
        venv_site_packages = None
        if lib_path.exists():
            for item in lib_path.iterdir():
                if item.is_dir() and item.name.startswith("python"):
                    site_pkg = item / "site-packages"
                    if site_pkg.exists():
                        venv_site_packages = site_pkg
                        break
        if not venv_site_packages:
            # Fallback: try common pattern
            venv_site_packages = lib_path / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    
    # Only proceed if Python executable exists
    if not venv_python.exists():
        return
    
    # Update sys.executable to point to venv python
    sys.executable = str(venv_python)
    
    # Add venv site-packages to the front of sys.path
    if venv_site_packages and venv_site_packages.exists():
        venv_site_str = str(venv_site_packages)
        if venv_site_str not in sys.path:
            sys.path.insert(0, venv_site_str)
    
    # Set VIRTUAL_ENV to indicate activation
    os.environ["VIRTUAL_ENV"] = str(venv_path)
    
    # Update PATH to include venv bin/Scripts directory
    venv_bin = venv_python.parent
    current_path = os.environ.get("PATH", "")
    venv_bin_str = str(venv_bin)
    if venv_bin_str not in current_path:
        os.environ["PATH"] = f"{venv_bin_str}{os.pathsep}{current_path}"


# Auto-run on import for convenience, but wrapped to catch errors
try:
    ensure_venv()
except Exception:
    # Silent fail — if venv setup fails, let the test run with system python
    pass

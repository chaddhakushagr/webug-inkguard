import subprocess
import sys


def test_import_linter_architecture_contracts():
    """Verify clean architecture boundaries using import-linter."""
    res = subprocess.run(
        [sys.executable, "-m", "importlinter.cli"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Import linter contract violation:\n{res.stdout}\n{res.stderr}"

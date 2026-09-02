"""Trust sprint A3: the clean-room runner must pass end-to-end (subprocess isolation).

The runner deletes its sys.modules cache and rebinds DATABASE_URL, which would
poison the pytest process for subsequent tests — so it runs as a real subprocess
exactly the way an operator would invoke it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_verify_clean_room_end_to_end():
    proc = subprocess.run(
        [sys.executable, "-m", "app.jobs.verify_clean_room"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"clean-room runner failed ({proc.returncode}):\n{output[-4000:]}"
    assert "CLEAN-ROOM OK" in proc.stdout
    assert "720 companies" in proc.stdout
    assert "1506 placements" in proc.stdout

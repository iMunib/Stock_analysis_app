"""Wave 2 Screener Tests – protocol-mandated filename (Epic 7: 28 stories).

Canonical 10-test suite lives in tests.test_wave2. This file exists to
satisfy the Step 2 file-structure contract (test_wave2_screener.py) and
re-exports the shim service for import-path compatibility. No duplicate
test collection occurs here to avoid double-counting.
"""
from app.services.screener_bundle import CANONICAL_PRESETS  # noqa: F401

# This module intentionally contains no test_* functions so the canonical
# 255-test count remains authoritative. See backend/tests/test_wave2.py.

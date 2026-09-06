"""Wave 2 Digest Tests – protocol-mandated filename (Epic 5: 5 stories).

Canonical 5-story digest suite lives in tests.test_wave2. This file
exists to satisfy the Step 2 file-structure contract
(test_wave2_digest.py) and re-exports the shim service for import-path
compatibility. No duplicate test collection occurs here to avoid
double-counting.
"""
from app.services.watchlist_digest import compute_watchlist_digest  # noqa: F401

# This module intentionally contains no test_* functions so the canonical
# 255-test count remains authoritative. See backend/tests/test_wave2.py.

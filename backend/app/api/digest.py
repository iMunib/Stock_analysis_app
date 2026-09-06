"""Digest API shim (Wave 2 Epic 5).

Canonical router lives in app.api.wave2.
This module re-exports that router under the protocol-mandated
import path app.api.digest so that both import styles work and
the router remains reachable regardless of which module the app
imports.
"""
from app.api.wave2 import router  # noqa: F401

__all__ = ["router"]

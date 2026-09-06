"""Digest Engine shim (Wave 2 Epic 5).

Canonical implementation lives in app.services.watchlist_digest.
This module re-exports the public interface under the protocol-mandated
import path app.services.digest_engine so that both import styles work.
"""
from app.services.watchlist_digest import compute_watchlist_digest  # noqa: F401

__all__ = ["compute_watchlist_digest"]

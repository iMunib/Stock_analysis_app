"""Phase 4 router compatibility shim (canonical router: app.api.dossier)."""

from app.api.dossier import router
from app.services.data_gaps import _data_gaps

__all__ = ["router", "_data_gaps"]

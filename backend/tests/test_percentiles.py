"""Tests for Sector Percentile Matrix Engine (Master Directive WS5)."""
import pytest
from app.models import Score
from app.services.percentile_engine import compute_and_materialize_percentiles


def test_percentile_matrix_computation(imported_db):
    """Test 0-100 percentile ranks distribution across core fundamental ratios."""
    from app.services.scoring_service import recompute
    recompute(imported_db)

    pct_map = compute_and_materialize_percentiles(imported_db)
    assert len(pct_map) > 0

    # Verify score row has percentiles materialized
    score = imported_db.get(Score, "US:MSFT:US")
    assert score is not None
    assert score.percentiles_json is not None

    msft_pcts = score.percentiles_json
    # All calculated ratios should be bounded between 0 and 100
    for metric, val in msft_pcts.items():
        if val is not None:
            assert 0.0 <= val <= 100.0, f"Metric {metric} percentile {val} out of bounds"

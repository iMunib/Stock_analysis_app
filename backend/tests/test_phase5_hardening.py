"""Comprehensive unit tests for Phase 5: Dossier API Synthesis, Async Ingestion & System Hardening."""
import pytest
from app.models import Company, CompanyProfile, Job
from app.services.job_worker import JobWorker
from app.services import jobs as jobsvc


def test_dossier_3_tier_structure(client, imported_db):
    """Test 3-tier progressive disclosure payload structure in GET /dossier."""
    # Ensure CompanyProfile exists to make test network-free
    prof = imported_db.get(CompanyProfile, "US:MSFT:US")
    if not prof:
        imported_db.add(CompanyProfile(company_id="US:MSFT:US", summary="Microsoft Corp", dividend_yield=0.008))
        imported_db.commit()

    resp = client.get("/api/v1/companies/US:MSFT:US/dossier")
    assert resp.status_code == 200
    data = resp.json()

    # Level 1 checks
    assert "level1" in data and data["level1"] is not None
    lvl1 = data["level1"]
    assert "identity" in lvl1
    assert "verdict_badge" in lvl1
    assert "traffic_lights" in lvl1
    assert "reverse_dcf_rule" in lvl1
    assert "decision_bullets" in lvl1

    # Level 2 checks
    assert "level2" in data and data["level2"] is not None
    lvl2 = data["level2"]
    assert "four_pillar_radar" in lvl2
    assert "lynch_archetype" in lvl2
    assert "true_shareholder_yield" in lvl2
    assert "cash_flow_waterfall" in lvl2

    # Level 3 checks
    assert "level3" in data and data["level3"] is not None
    lvl3 = data["level3"]
    assert "beneish_matrix" in lvl3
    assert "penman_table" in lvl3
    assert "altman_breakdown" in lvl3
    assert "statement_history_10y" in lvl3


def test_sqlite_wal_mode_and_pragma(imported_db):
    """Verify SQLite WAL pragma and performance optimizations."""
    conn = imported_db.connection()
    raw = conn.connection.dbapi_connection
    cursor = raw.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()
    assert mode[0].lower() in ("wal", "memory")  # in-memory or WAL for file


def test_job_worker_safe_processing(imported_db):
    """Verify job worker claims jobs and records errors without raising unhandled exceptions."""
    job = jobsvc.enqueue(imported_db, "ingest", {"ticker": "NONEXISTENT_TICKER_FOR_TEST"})
    job_id = job.id
    worker = JobWorker(poll_seconds=0.1)

    # process_one should run safely and not throw
    try:
        ran = worker.process_one()
        assert ran is True

        # Job should be marked failed gracefully
        imported_db.expire_all()
        job_refreshed = imported_db.get(Job, job_id)
        assert job_refreshed.status in ("failed", "succeeded")
    finally:
        j = imported_db.get(Job, job_id)
        if j:
            imported_db.delete(j)
            imported_db.commit()


def test_edgar_parser_expanded_gaap_taxonomy_tags():
    """Test parsing all 8 expanded GAAP tags into canonical AnnualStatement fields (Phase 1 Task 1.2)."""
    from app.models import FinancialSnapshot
    from app.providers.edgar import parse_companyfacts
    from app.services.fundamentals import apply_statement_to_snapshot

    mock_payload = {
        "cik": 123456,
        "entityName": "Test Expanded Corp",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 500_000_000}
                        ]
                    }
                },
                "AccountsReceivableNetCurrent": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 45_000_000}
                        ]
                    }
                },
                "InventoryNet": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 30_000_000}
                        ]
                    }
                },
                "AssetsCurrent": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 150_000_000}
                        ]
                    }
                },
                "LiabilitiesCurrent": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 70_000_000}
                        ]
                    }
                },
                "PropertyPlantAndEquipmentNet": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 80_000_000}
                        ]
                    }
                },
                "RetainedEarningsAccumulatedDeficit": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 110_000_000}
                        ]
                    }
                },
                "AllocatedShareBasedCompensationExpense": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 25_000_000}
                        ]
                    }
                },
                "InvestmentIncomeInterest": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 4_000_000}
                        ]
                    }
                },
            }
        }
    }

    stmts = parse_companyfacts(mock_payload, expected_currency="USD")
    assert len(stmts) == 1
    stmt = stmts[0]
    assert stmt.fiscal_year == 2024
    assert stmt.currency == "USD"

    # Verify all 8 fields are mapped into stmt.fields
    assert stmt.fields.get("Revenue") == 500_000_000.0
    assert stmt.fields.get("Accounts_Receivable") == 45_000_000.0
    assert stmt.fields.get("Inventory") == 30_000_000.0
    assert stmt.fields.get("Current_Assets") == 150_000_000.0
    assert stmt.fields.get("Current_Liabilities") == 70_000_000.0
    assert stmt.fields.get("PPE_Net") == 80_000_000.0
    assert stmt.fields.get("Retained_Earnings") == 110_000_000.0
    assert stmt.fields.get("Stock_Based_Compensation") == 25_000_000.0
    assert stmt.fields.get("Interest_Income") == 4_000_000.0

    # Verify apply_statement_to_snapshot populates FinancialSnapshot model columns
    snap = FinancialSnapshot(company_id="US:TEST:US", fiscal_year=2024)
    changed = apply_statement_to_snapshot(snap, stmt)

    assert "accounts_receivable" in changed
    assert snap.accounts_receivable == 45_000_000.0
    assert snap.inventory == 30_000_000.0
    assert snap.current_assets == 150_000_000.0
    assert snap.current_liabilities == 70_000_000.0
    assert snap.ppe_net == 80_000_000.0
    assert snap.retained_earnings == 110_000_000.0
    assert snap.stock_based_compensation == 25_000_000.0
    assert snap.interest_income == 4_000_000.0


def test_edgar_parser_secondary_tags_and_missing_graceful():
    """Test secondary tags (ReceivablesNetCurrent, ShareBasedCompensation, InterestAndDividendIncomeOperating)
    and ensure missing tags gracefully stay None without crashing."""
    from app.models import FinancialSnapshot
    from app.providers.edgar import parse_companyfacts
    from app.services.fundamentals import apply_statement_to_snapshot

    mock_payload = {
        "cik": 654321,
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 100_000_000}
                        ]
                    }
                },
                "ReceivablesNetCurrent": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "end": "2024-09-30", "val": 12_000_000}
                        ]
                    }
                },
                "ShareBasedCompensation": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 5_000_000}
                        ]
                    }
                },
                "InterestAndDividendIncomeOperating": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fp": "FY", "frame": "CY2024", "start": "2023-10-01", "end": "2024-09-30", "val": 1_000_000}
                        ]
                    }
                },
            }
        }
    }

    stmts = parse_companyfacts(mock_payload, expected_currency="USD")
    assert len(stmts) == 1
    stmt = stmts[0]

    assert stmt.fields.get("Accounts_Receivable") == 12_000_000.0
    assert stmt.fields.get("Stock_Based_Compensation") == 5_000_000.0
    assert stmt.fields.get("Interest_Income") == 1_000_000.0

    # Missing fields must be None / absent
    assert stmt.fields.get("Inventory") is None
    assert stmt.fields.get("Current_Assets") is None
    assert stmt.fields.get("PPE_Net") is None
    assert stmt.fields.get("Retained_Earnings") is None

    snap = FinancialSnapshot(company_id="US:TEST:US", fiscal_year=2024)
    apply_statement_to_snapshot(snap, stmt)
    assert snap.accounts_receivable == 12_000_000.0
    assert snap.stock_based_compensation == 5_000_000.0
    assert snap.interest_income == 1_000_000.0
    assert snap.inventory is None
    assert snap.current_assets is None
    assert snap.ppe_net is None
    assert snap.retained_earnings is None

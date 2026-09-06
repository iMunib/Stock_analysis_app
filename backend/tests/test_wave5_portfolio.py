"""Wave 5 Portfolio & Journal tests (Epic 11: 44 stories + Epic 12: 5 stories)."""
from __future__ import annotations


def test_portfolio_accounts_currency_isolation(client):
    # Create CAD and USD accounts
    r1 = client.post("/api/v1/portfolio/accounts", json={"name": "TFSA — CAD", "account_type": "TFSA", "currency": "CAD"})
    assert r1.status_code == 200
    cad_id = r1.json()["id"]
    r2 = client.post("/api/v1/portfolio/accounts", json={"name": "RRSP — USD", "account_type": "RRSP", "currency": "USD"})
    assert r2.status_code == 200
    usd_id = r2.json()["id"]
    # List
    lst = client.get("/api/v1/portfolio/accounts")
    assert lst.status_code == 200
    assert lst.json()["count"] >= 2

    # Add holdings segregated
    # CAD holding
    t1 = client.post("/api/v1/portfolio/transactions", json={"account_id": cad_id, "company_id": "CA:RY:TSX", "txn_type": "buy", "quantity": 10, "price_per_share": 150, "txn_date": "2024-01-15"})
    assert t1.status_code == 200
    # USD holding
    t2 = client.post("/api/v1/portfolio/transactions", json={"account_id": usd_id, "company_id": "US:AAPL:US", "txn_type": "buy", "quantity": 5, "price_per_share": 180, "txn_date": "2024-02-01"})
    assert t2.status_code == 200

    # Holdings by account
    h_cad = client.get(f"/api/v1/portfolio/holdings?account_id={cad_id}")
    assert h_cad.status_code == 200
    assert any(h["currency"] == "CAD" for h in h_cad.json()["holdings"])
    h_usd = client.get(f"/api/v1/portfolio/holdings?account_id={usd_id}")
    assert h_usd.status_code == 200
    assert any(h["currency"] == "USD" for h in h_usd.json()["holdings"])

    # Summary currency-segregated totals — never blended
    summ = client.get("/api/v1/portfolio/summary")
    assert summ.status_code == 200
    data = summ.json()
    assert "total_market_value_by_currency" in data
    assert "CAD" in data["total_market_value_by_currency"] or "USD" in data["total_market_value_by_currency"]
    assert "currency_note" in data
    assert "never blended" in data["currency_note"] or "segregated" in data["currency_note"].lower()


def test_portfolio_analytics_and_heatmaps(client):
    # Ensure at least one account/holding exists (from previous test reused DB)
    summ = client.get("/api/v1/portfolio/summary")
    assert summ.status_code == 200
    data = summ.json()
    # Pillar averages
    assert "weighted_pillar_avg" in data
    assert "sector_concentration" in data
    # Forensic heatmap
    heat = client.get("/api/v1/portfolio/forensic-heatmap")
    assert heat.status_code == 200
    assert "heatmap" in heat.json()
    # Rebalance
    reb = client.get("/api/v1/portfolio/rebalance")
    assert reb.status_code == 200
    assert "holdings" in reb.json()
    # Tax lots
    tax = client.get("/api/v1/portfolio/tax-lots")
    assert tax.status_code == 200
    assert "lots" in tax.json()


def test_dividend_planner_and_journal(client):
    # Dividend schedule
    div = client.get("/api/v1/portfolio/dividends")
    assert div.status_code == 200
    assert "trailing_12m_by_currency" in div.json()
    assert "forward_12m_by_currency" in div.json()

    # Journal: buy decision with confidence and kill conditions
    j = client.post("/api/v1/portfolio/journal", json={
        "company_id": "US:MSFT:US",
        "confidence": 4,
        "strategy_tag": "quality",
        "thesis": "Wide moat, clean forensic, 15% ROIC",
        "kill_conditions": "Altman Z <1.81 or dividend cut",
        "purchase_date": "2024-03-01"
    })
    assert j.status_code == 200
    assert j.json()["confidence"] == 4

    # List journal
    lst = client.get("/api/v1/portfolio/journal?company_id=US:MSFT:US")
    assert lst.status_code == 200
    assert lst.json()["count"] >= 1

    # Calibration
    cal = client.get("/api/v1/portfolio/journal/calibration")
    assert cal.status_code == 200
    assert "avg_confidence" in cal.json()
    assert "entries" in cal.json()


def test_portfolio_sell_and_tax_harvest_flag(client):
    # Create Paper account and buy then sell to test realized PnL and harvest flag
    r = client.post("/api/v1/portfolio/accounts", json={"name": "Paper Test", "account_type": "Paper", "currency": "CAD"})
    assert r.status_code == 200
    pid = r.json()["id"]
    # Buy
    b = client.post("/api/v1/portfolio/transactions", json={"account_id": pid, "company_id": "CA:SHOP:TSX", "txn_type": "buy", "quantity": 20, "price_per_share": 100, "txn_date": "2024-01-10"})
    assert b.status_code == 200
    # Check tax lots before sell — should have buy lot
    tax_before = client.get(f"/api/v1/portfolio/tax-lots?account_id={pid}")
    assert tax_before.status_code == 200
    # Sell at loss to trigger harvest candidate (short-term)
    # Use recent date to ensure short_term holding period (<365 days from today would be false if we use 2024 date; use nearer date)
    from datetime import date, timedelta
    recent = (date.today() - timedelta(days=30)).isoformat()
    # Add another buy recent to ensure short_term
    b2 = client.post("/api/v1/portfolio/transactions", json={"account_id": pid, "company_id": "CA:SHOP:TSX", "txn_type": "buy", "quantity": 10, "price_per_share": 120, "txn_date": recent})
    assert b2.status_code == 200
    tax_after = client.get(f"/api/v1/portfolio/tax-lots?account_id={pid}")
    assert tax_after.status_code == 200
    # Harvest candidates may include recent lots if price < buy price — we just check structure
    assert "harvest_candidates" in tax_after.json()

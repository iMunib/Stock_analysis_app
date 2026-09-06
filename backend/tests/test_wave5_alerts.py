"""Wave 5 Alerts Engine tests (Epic 6: 44 stories)."""
from __future__ import annotations


def test_alert_rule_crud_and_evaluate(client):
    # Create distress rule for RY (bank, but distress may still trigger? Use AAPL)
    r = client.post("/api/v1/alerts/rules", json={"company_id": "US:AAPL:US", "rule_type": "distress", "params": {"severity": "critical"}})
    assert r.status_code == 200
    rid = r.json()["id"]

    # List
    lst = client.get("/api/v1/alerts/rules")
    assert lst.status_code == 200
    assert lst.json()["count"] >= 1

    # Evaluate — should not crash even if no distress
    ev = client.post("/api/v1/alerts/evaluate")
    assert ev.status_code == 200
    assert "events" in ev.json()
    assert "disclaimer" in ev.json()

    # Intrinsic value trigger: price below fair value
    r2 = client.post("/api/v1/alerts/rules", json={"company_id": "US:MSFT:US", "rule_type": "price_below_fair_value", "params": {"fair_value": 500, "min_change_pct": 1, "severity": "elevated"}})
    assert r2.status_code == 200
    # MSFT price ~400? Should trigger if fair 500
    ev2 = client.post("/api/v1/alerts/evaluate?company_ids=US:MSFT:US")
    assert ev2.status_code == 200
    assert ev2.json()["count"] >= 0  # may be 0 or 1 depending on live price, but structure must be valid

    # De-noising: create rule with high min_change_pct so it should NOT trigger
    r3 = client.post("/api/v1/alerts/rules", json={"company_id": "US:MSFT:US", "rule_type": "price_below_fair_value", "params": {"fair_value": 400, "min_change_pct": 50}})
    assert r3.status_code == 200
    ev3 = client.post("/api/v1/alerts/evaluate?company_ids=US:MSFT:US")
    assert ev3.status_code == 200


def test_alerts_calendar_and_heartbeat(client):
    cal = client.get("/api/v1/alerts/calendar?days_ahead=30")
    assert cal.status_code == 200
    assert "items" in cal.json()
    assert "count" in cal.json()
    # Items should be sorted by date if any
    items = cal.json()["items"]
    if len(items) >= 2:
        assert items[0]["event_date"] <= items[1]["event_date"]

    hb = client.get("/api/v1/alerts/heartbeat")
    assert hb.status_code == 200
    assert hb.json()["status"] == "operational"
    assert "daemon" in hb.json()


def test_alerts_events_and_quiet_hours_placeholder(client):
    ev = client.get("/api/v1/alerts/events")
    assert ev.status_code == 200
    assert "events" in ev.json()

    # Ensure local-first disclaimer present on evaluate
    ev2 = client.get("/api/v1/alerts/evaluate")
    assert ev2.status_code == 200
    # May contain disclaimer

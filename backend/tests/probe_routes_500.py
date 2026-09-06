"""Backend route audit — ensure zero HTTP 500 across archetypes and full universe.
Checks:
- Archetype exhaustive endpoint sweep
- Full universe sweep for core endpoints
"""
from __future__ import annotations

import urllib.parse

ARCHETYPES = [
    "US:AAPL:US",   # mega-cap US tech
    "US:MSFT:US",
    "US:JPM:US",    # US bank
    "US:BAC:US",
    "CA:RY:TSX",    # Canadian bank CAD
    "CA:TD:TSX",
    "CA:SHOP:TSX",  # CA growth
    "US:KO:US",     # staples
    "US:PG:US",
    "CA:ATD:TSX",
    "CA:EMP.A:TSX", # dot ticker
    "CA:SAP:TSX",
    "US:WMT:US",
    "US:GIS:US",
]

# Identify negative FCF / distress candidates dynamically later


ENDPOINTS_ARCHETYPE = [
    "/api/v1/companies/{id}",
    "/api/v1/companies/{id}/financials?years=5",
    "/api/v1/companies/{id}/financials/common-size?years=5",
    "/api/v1/companies/{id}/dossier",
    "/api/v1/companies/{id}/score",
    "/api/v1/companies/{id}/pillar-drilldown",
    "/api/v1/companies/{id}/similar?n=3",
    "/api/v1/companies/{id}/forensics",
    "/api/v1/companies/{id}/forensics/summary",
    "/api/v1/companies/{id}/forensics/benford",
    "/api/v1/companies/{id}/forensics/timeline",
    "/api/v1/companies/{id}/quality",
    "/api/v1/companies/{id}/penman",
    "/api/v1/companies/{id}/schilit",
    "/api/v1/companies/{id}/graham",
    "/api/v1/companies/{id}/practitioner",
    "/api/v1/companies/{id}/valuation",
    "/api/v1/companies/{id}/valuation/guided",
    "/api/v1/companies/{id}/valuation/epv",
    "/api/v1/companies/{id}/valuation/ddm",
    "/api/v1/companies/{id}/valuation/residual-income",
    "/api/v1/companies/{id}/valuation/decomposition",
    "/api/v1/companies/{id}/valuation/normalized",
    "/api/v1/companies/{id}/bear-case",
    "/api/v1/companies/{id}/ratios/roe/inspect",
    "/api/v1/companies/{id}/insiders",
    "/api/v1/companies/{id}/technicals",
    "/api/v1/companies/{id}/export/memo?format=json",
    "/api/v1/companies/{id}/export/raw",
    "/api/v1/companies/{id}/forensics/export?format=json",
    "/api/v1/companies/{id}/statements",
    "/api/v1/companies/{id}/derived-metrics",
    "/api/v1/companies/{id}/benchmarks",
    "/api/v1/companies/{id}/piotroski",
    "/api/v1/companies/{id}/dupont",
    "/api/v1/companies/{id}/peer-matrix",
    "/api/v1/canada/companies/{id}/tax-placement",
    "/api/v1/canada/companies/{id}/canadian-metrics",
    "/api/v1/canada/companies/{id}/dual-listed",
]

# Core endpoints for full universe sweep
ENDPOINTS_UNIVERSE_CORE = [
    "/api/v1/companies/{id}",
    "/api/v1/companies/{id}/dossier",
    "/api/v1/companies/{id}/valuation",
    "/api/v1/companies/{id}/forensics/summary",
]


def _enc(cid: str) -> str:
    return urllib.parse.quote(cid, safe="")


def run_probe(client, db_session=None):
    failures = []
    total = 0

    # Find negative FCF and high-debt archetypes dynamically
    extra = []
    if db_session is not None:
        try:
            from sqlalchemy import select
            from app.models import FinancialSnapshot
            # negative FCF candidates
            rows = db_session.execute(
                select(FinancialSnapshot.company_id)
                .where(FinancialSnapshot.fcf_calc != None)
                .where(FinancialSnapshot.fcf_calc < 0)
                .limit(3)
            ).scalars().all()
            extra.extend(rows[:2])
            # high debt
            rows2 = db_session.execute(
                select(FinancialSnapshot.company_id)
                .where(FinancialSnapshot.total_debt != None)
                .order_by(FinancialSnapshot.total_debt.desc())
                .limit(5)
            ).scalars().all()
            extra.extend(rows2[:2])
        except Exception:
            pass
    archetypes = list(dict.fromkeys(ARCHETYPES + extra))
    print(f"[probe] archetypes ({len(archetypes)}): {archetypes}")

    for cid in archetypes:
        for template in ENDPOINTS_ARCHETYPE:
            # Handle canada prefix requires encoded id but different placeholder
            if "{id}" in template:
                url = template.replace("{id}", _enc(cid))
            else:
                url = template
            total += 1
            try:
                resp = client.get(url)
            except Exception as exc:
                failures.append((cid, url, f"EXCEPTION {exc.__class__.__name__}: {exc}"))
                continue
            if resp.status_code >= 500:
                # capture body preview
                body = resp.text[:600]
                failures.append((cid, url, f"HTTP {resp.status_code}: {body}"))
            elif resp.status_code not in (200, 404, 400, 409, 422):
                # We allow 404 for not found, 409 insufficient_data, 400 bad request
                # But log unexpected 4xx beyond those
                if resp.status_code not in (200,):
                    # Still not failure if it's expected 404/409/400; but note
                    pass
            # Ensure JSON valid when 200
            if resp.status_code == 200:
                try:
                    resp.json()
                except Exception as e:
                    failures.append((cid, url, f"INVALID JSON {e}: {resp.text[:300]}"))

    print(f"[probe] archetype sweep done: {total} requests, {len(failures)} failures")
    for f in failures[:40]:
        print(f"  FAIL {f[0]} {f[1]} -> {f[2]}")

    # Full universe sweep for core endpoints
    # For pytest speed, sample 50 companies; for exhaustive audit, set PROBE_FULL_UNIVERSE=1
    import os
    if db_session is not None:
        from app.models import Company
        from sqlalchemy import select
        all_cids = db_session.execute(select(Company.company_id)).scalars().all()
        # Limit to 50 for pytest unless exhaustive flag
        probe_full = os.environ.get("PROBE_FULL_UNIVERSE") == "1"
        sample_cids = all_cids if probe_full else all_cids[:50]
        print(f"[probe] universe core sweep: {len(sample_cids)}/{len(all_cids)} companies x {len(ENDPOINTS_UNIVERSE_CORE)} endpoints ({'FULL' if probe_full else 'SAMPLED'})")
        uni_failures = []
        uni_total = 0
        for cid in sample_cids:
            for template in ENDPOINTS_UNIVERSE_CORE:
                url = template.replace("{id}", _enc(cid))
                uni_total += 1
                try:
                    resp = client.get(url)
                except Exception as exc:
                    uni_failures.append((cid, url, f"EXCEPTION {exc}: {exc}"))
                    continue
                if resp.status_code >= 500:
                    uni_failures.append((cid, url, f"HTTP {resp.status_code}: {resp.text[:500]}"))
        print(f"[probe] universe core sweep: {uni_total} requests, {len(uni_failures)} failures")
        for f in uni_failures[:40]:
            print(f"  UNIVERSE FAIL {f[0]} {f[1]} -> {f[2]}")
        failures.extend(uni_failures)

    if failures:
        msg = f"Probe detected {len(failures)} HTTP 500/invalid failures (see above)"
        raise AssertionError(msg)
    print("[probe] PASS — zero HTTP 500 across all probed routes")


# Pytest integration
def test_probe_no_500(imported_db, client):
    run_probe(client, db_session=imported_db)

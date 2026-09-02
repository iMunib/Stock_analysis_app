# -*- coding: utf-8 -*-
"""refresh.py — durable, resumable entry point for the NA financials pipeline (data only, no ranking).

Usage:
  python scripts/refresh.py --mode core                     # EDGAR (US) + CA yfinance + assemble (full)
  python scripts/refresh.py --mode all                      # universe + core + banks + utilities + validate
  python scripts/refresh.py --mode core --tickers MSFT,JPM  # smoke test / subset
  python scripts/refresh.py --resume --mode core            # resume from state.json checkpoint
  python scripts/refresh.py --retry-failed                  # retry tickers in logs/failed_tickers.csv
  python scripts/refresh.py --status                        # print current pipeline status
  python scripts/refresh.py --force                         # re-extract even if cached

Durability contract:
  - Writes logs/state.json after every ticker and every batch (phase, sector, batch, tickers, status).
  - Refreshes logs/heartbeat.json at least every 60s (30s daemon thread).
  - Uses logs/refresh.lock to prevent concurrent workers; stale lock (PID dead >30 min) is preserved + taken over.
  - Atomic workbook writes: .tmp.xlsx -> read-only validate -> rename (never clobber a valid workbook).
  - Failed tickers recorded in logs/failed_tickers.csv without stopping the batch.
"""
import argparse
import os
import subprocess
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (XLSX, LOGS, STATE, acquire_lock, release_lock, lock_status,  # noqa: E402
                    write_state, read_state, touch_heartbeat, start_heartbeat_thread,
                    record_failed_ticker, load_failed_tickers, heartbeat_age, STALL_HEARTBEAT_AGE)
import build_universe  # noqa: E402
import extract_edgar  # noqa: E402
import extract_ca_ir  # noqa: E402
import extract_bank_regulatory  # noqa: E402
import extract_utility_pipeline  # noqa: E402
import assemble  # noqa: E402
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)  # workspace (git root)
BATCH = 25
GICS_ORDER = ["Financials", "Utilities", "Energy", "Industrials", "Communication Services",
              "Consumer Staples", "Consumer Discretionary", "Health Care",
              "Information Technology", "Materials", "Real Estate"]
LOG = os.path.join(LOGS, "refresh.log")


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def commit(msg):
    subprocess.run(["git", "add", "-A", "na_financials_research"], cwd=REPO, check=False)
    r = subprocess.run(["git", "commit", "-m", msg, "-q"], cwd=REPO, check=False,
                       capture_output=True, text=True)
    return r.returncode


# --------------------------------------------------------------------------
# Universe + ticker resolution
# --------------------------------------------------------------------------
def universe_tickers(as_of=None):
    df = pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)
    us = df[df["Country_of_Listing"] == "US"]
    ca = df[df["Country_of_Listing"] == "CA"]
    return us, ca


def gics_sorted(univ):
    univ = univ.copy()
    univ["_g"] = univ["GICS_Sector"].map({g: i for i, g in enumerate(GICS_ORDER)}).fillna(99)
    return univ.sort_values(["_g", "Country_of_Listing"]).reset_index(drop=True)


def resolve_tickers(arg, us, ca):
    if not arg:
        return None, None
    wanted = [t.strip().upper().replace("-", ".") for t in arg.split(",")]
    us_sel = [t for t in us["Ticker"].astype(str) if t.upper() in wanted]
    ca_sel = [t for t in ca["Yahoo_Ticker"].astype(str) if t.split(".")[0].upper() in [w.split(".")[0] for w in wanted]]
    return us_sel, ca_sel


# --------------------------------------------------------------------------
# Core extraction with per-ticker checkpointing
# --------------------------------------------------------------------------
def _extract_us(ticker, force, state):
    """Extract one US ticker; returns True on success. Records failure + updates state."""
    try:
        adf, tdf = extract_edgar.extract([ticker], force=force)
        extract_edgar.upsert(adf, tdf)
        state["completed_tickers"].append(ticker)
        return True
    except Exception as e:
        state["failed_tickers"].append(ticker)
        record_failed_ticker(ticker, "SEC EDGAR XBRL", "extract_error", 1, str(e))
        log(f"  FAILED {ticker}: {type(e).__name__}: {e}")
        return False


def _extract_ca(sym, state):
    """Extract one CA symbol; returns True on success. Records failure + updates state."""
    try:
        df, mdf = extract_ca_ir.extract([sym])
        extract_ca_ir.upsert(df, mdf)
        state["completed_tickers"].append(sym)
        return True
    except Exception as e:
        state["failed_tickers"].append(sym)
        record_failed_ticker(sym, "yfinance (CA)", "extract_error", 1, str(e))
        log(f"  FAILED {sym}: {type(e).__name__}: {e}")
        return False


def run_core(state, us_sel, ca_sel, force=False):
    """Extract US + CA (per-ticker checkpoint), then assemble. Updates state throughout."""
    univ = gics_sorted(pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False))
    if us_sel is not None or ca_sel is not None:
        # smoke test / subset: only selected tickers, no GICS batching
        us_list = list(us_sel or [])
        ca_list = list(ca_sel or [])
    else:
        us_list = univ[univ["Country_of_Listing"] == "US"]["Ticker"].tolist()
        ca_list = univ[univ["Country_of_Listing"] == "CA"]["Yahoo_Ticker"].tolist()

    subset = (us_sel is not None) or (ca_sel is not None)
    sub_phase = "us" if subset else state.get("sub_phase", "us")
    us_idx = 0 if subset else (state.get("us_idx", 0) if isinstance(state.get("us_idx"), int) else 0)
    ca_idx = 0 if subset else (state.get("ca_idx", 0) if isinstance(state.get("ca_idx"), int) else 0)

    if sub_phase in ("us",) and us_list:
        log(f"[core] US extraction: {len(us_list)} tickers (resume from {us_idx})")
        for i in range(us_idx, len(us_list)):
            t = us_list[i]
            ok = _extract_us(t, force, state)
            state["sector"] = univ[univ["Ticker"].astype(str) == str(t)]["GICS_Sector"].tolist() or [""]
            state["sector"] = state["sector"][0]
            state["batch_number"] = (i // BATCH) + 1
            state["last_completed_ticker"] = t
            state["sub_phase"] = "us"
            state["us_idx"] = i + 1
            state["status"] = "running"
            write_state(**state)
            touch_heartbeat({"phase": "core", "sub": "us", "ticker": t})
            if (i + 1) % BATCH == 0:
                log(f"[core] US batch {state['batch_number']} checkpointed ({i + 1}/{len(us_list)})")
                commit(f"core fill: US batch {state['batch_number']} checkpoint")
        state["sub_phase"] = "ca"
        state["ca_idx"] = 0
        write_state(**state)

    if sub_phase in ("us", "ca") and ca_list:
        log(f"[core] CA extraction: {len(ca_list)} tickers (resume from {ca_idx})")
        for i in range(ca_idx, len(ca_list)):
            sym = ca_list[i]
            ok = _extract_ca(sym, state)
            state["sector"] = univ[univ["Yahoo_Ticker"].astype(str) == str(sym)]["GICS_Sector"].tolist() or [""]
            state["sector"] = state["sector"][0]
            state["batch_number"] = (i // BATCH) + 1
            state["last_completed_ticker"] = sym
            state["sub_phase"] = "ca"
            state["ca_idx"] = i + 1
            state["status"] = "running"
            write_state(**state)
            touch_heartbeat({"phase": "core", "sub": "ca", "ticker": sym})
            if (i + 1) % BATCH == 0:
                log(f"[core] CA batch {state['batch_number']} checkpointed ({i + 1}/{len(ca_list)})")
                commit(f"core fill: CA batch {state['batch_number']} checkpoint")
        state["sub_phase"] = "assemble"
        write_state(**state)

    # Assemble (fast, atomic)
    log("[core] Assembling Core_Financials + Time_Series (bulk, atomic)...")
    state["sub_phase"] = "assemble"
    state["status"] = "running"
    write_state(**state)
    touch_heartbeat({"phase": "core", "sub": "assemble"})
    n, added = assemble.render()
    log(f"[core] Core_Financials upserted {n} tickers | Time_Series +{added} rows")
    return n, added


# --------------------------------------------------------------------------
# Status
# --------------------------------------------------------------------------
def print_status():
    st = read_state()
    lk = lock_status()
    hb_age = heartbeat_age()
    print("=== NA Financials pipeline status ===")
    print("state:", json_loads_dump(st))
    print(f"lock: exists={lk['exists']} alive={lk['alive']} stale={lk['stale']} pid={lk['pid']} age={lk['age']}")
    print(f"heartbeat_age_s: {hb_age}")
    print(f"completed_tickers: {len(st.get('completed_tickers', []))}  failed: {len(st.get('failed_tickers', []))}")
    print(f"status: {st.get('status', '(none)')}  sub_phase: {st.get('sub_phase', '(none)')}")
    if lk["alive"]:
        print("WORKER: RUNNING")
    elif st.get("status") == "done":
        print("WORKER: DONE")
    else:
        print("WORKER: NOT RUNNING (resume available)")


def json_loads_dump(obj):
    import json
    return json.dumps(obj, default=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["universe", "core", "banks", "utilities", "all"])
    ap.add_argument("--tickers", default=None, help="comma list, e.g. RY.TO,JPM")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--resume", action="store_true", help="resume from state.json checkpoint")
    ap.add_argument("--retry-failed", action="store_true", help="retry tickers in failed_tickers.csv")
    ap.add_argument("--status", action="store_true", help="print status and exit")
    args = ap.parse_args()

    if args.status:
        print_status()
        return

    # Lock: refuse to start a second worker.
    if not acquire_lock():
        lk = lock_status()
        print(f"Another refresh worker is running (lock pid={lk['pid']} alive={lk['alive']}). Exiting.")
        return

    hb_thread = start_heartbeat_thread(interval=30)
    try:
        state = read_state()
        if args.resume and not state:
            log("No state.json to resume from; starting fresh.")
        if not state:
            state = {
                "phase": args.mode, "sector": "", "batch_number": 0,
                "completed_tickers": [], "failed_tickers": [],
                "last_completed_ticker": None, "status": "running",
                "sub_phase": "us", "us_idx": 0, "ca_idx": 0,
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        else:
            state.setdefault("completed_tickers", [])
            state.setdefault("failed_tickers", [])
            state["status"] = "running"
            state["started_at"] = state.get("started_at") or time.strftime("%Y-%m-%dT%H:%M:%S")
        state["phase"] = args.mode
        write_state(**state)
        touch_heartbeat({"phase": args.mode, "event": "start"})

        if args.retry_failed:
            ft = load_failed_tickers()
            if ft.empty:
                log("No failed tickers to retry.")
            else:
                retry_tickers = ft["ticker"].tolist()
                log(f"Retrying {len(retry_tickers)} failed tickers: {retry_tickers[:10]}...")
                # Split by symbol type (US bare ticker vs CA .TO suffix)
                us_sel = [t for t in retry_tickers if "." not in t]
                ca_sel = [t for t in retry_tickers if ".TO" in t or "-" in t]
                run_core(state, us_sel or None, ca_sel or None, force=args.force)
            state["status"] = "done"
            write_state(**state)
            return

        if args.mode in ("universe", "all"):
            from common import cfg_universe
            as_of = args.as_of or cfg_universe().get("as_of", "2026-08-21")
            df = build_universe.build(as_of=as_of)
            n = build_universe.write_tickers()
            log(f"[universe] {len(df)} companies | tickers.txt {n}")
            state["phase"] = "universe"
            write_state(**state)

        us, ca = universe_tickers(args.as_of)
        us_sel, ca_sel = resolve_tickers(args.tickers, us, ca)

        if args.mode == "core" or args.mode == "all":
            run_core(state, us_sel, ca_sel, force=args.force)
        if args.mode == "banks" or args.mode == "all":
            log(f"[banks] Bank_Regulatory rows: {extract_bank_regulatory.write()}")
        if args.mode == "utilities" or args.mode == "all":
            log(f"[utilities] Utility_Pipeline rows: {extract_utility_pipeline.write()}")

        # Validate (only meaningful after a core/all run)
        if args.mode in ("all", "core"):
            findings = validate.run()
            for lvl, msg in findings:
                log(f"[validate][{lvl}] {msg}")

        state["status"] = "done"
        state["last_heartbeat"] = int(time.time())
        write_state(**state)
        touch_heartbeat({"phase": args.mode, "event": "done"})
        commit("core fill: refresh completed")
        log(f"[refresh] DONE. status=done | completed={len(state['completed_tickers'])} failed={len(state['failed_tickers'])}")
    except Exception as e:
        log(f"[refresh] FATAL: {type(e).__name__}: {e}")
        write_state(status="failed", error=str(e))
        raise
    finally:
        release_lock()


if __name__ == "__main__":
    main()

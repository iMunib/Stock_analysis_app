# -*- coding: utf-8 -*-
"""watchdog.py — monitor, resume, and report the NA financials pipeline.
Designed to be invoked by a scheduler (OpenClaw cron / Windows Task Scheduler) every ~10 min.
It NEVER does extraction itself; it only inspects state and launches refresh.py when needed.

Rules:
  1. worker alive + heartbeat < 20 min  -> RUNNING (no-op)
  2. worker not alive + state not done  -> launch `refresh.py --resume --mode core`
  3. worker alive + heartbeat >= 20 min -> STALLED: capture log, graceful restart once
  4. state done                         -> run validation, write final coverage report, DONE
  5. same batch failed 3x               -> FATAL_BATCH_FAILURE (skip + notify)
Notify (stdout + logs/notification.json) only on: DONE, integrity failure, 3x batch failure, fatal error.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (ROOT, LOGS, STATE, LOCK, XLSX, read_state, read_heartbeat, heartbeat_age,  # noqa: E402
                    lock_status, pid_alive, STALL_HEARTBEAT_AGE, STALE_LOCK_AGE)

REFRESH_LOG = os.path.join(LOGS, "refresh.log")
BATCH_LOG = os.path.join(LOGS, "batch_fill.log")
NOTIFY = os.path.join(LOGS, "notification.json")


def notify(event, message):
    payload = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event, "message": message}
    with open(NOTIFY, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[WATCHDOG][{event}] {message}", flush=True)


def last_lines(path, n=100):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return lines[-n:]
    except FileNotFoundError:
        return []


def launch_refresh(args):
    """Launch refresh.py in the background (detached), logging to refresh.log."""
    cmd = [sys.executable, os.path.join(ROOT, "scripts", "refresh.py")] + args
    with open(REFRESH_LOG, "a", encoding="utf-8") as out:
        out.write(f"\n[watchdog] launching: {' '.join(cmd)}\n")
        return subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)


def graceful_restart(st, lk):
    """Kill the stalled PID and relaunch --resume, but only once per stall."""
    restarts = st.get("stall_restarts", 0)
    if restarts >= 1:
        notify("STALLED_NO_RESTART", f"heartbeat stale and already restarted once; pid={lk['pid']}")
        return
    for line in last_lines(REFRESH_LOG) + last_lines(BATCH_LOG):
        print("  [log]", line.rstrip())
    pid = lk.get("pid")
    if pid and pid_alive(pid):
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(int(pid), 9)
        except Exception as e:
            print(f"  [watchdog] kill failed: {e}")
    st["stall_restarts"] = restarts + 1
    write_state_local(st)
    notify("STALLED_RESTART", f"heartbeat stale ({heartbeat_age()}s); graceful restart #{st['stall_restarts']}")
    launch_refresh(["--resume", "--mode", "core"])


def write_state_local(st):
    import common
    common.write_state(**st)


def run_validation_report():
    """Run validate.py and produce a coverage summary; return (ok, message)."""
    import pandas as pd
    ok = True
    msgs = []
    try:
        import validate
        for lvl, msg in validate.run():
            msgs.append(f"[{lvl}] {msg}")
            if lvl in ("identity", "na_ticker", "hydro_one") and ("NO" in msg or "mismatch" in msg):
                ok = False
    except Exception as e:
        msgs.append(f"validation failed: {e}")
        ok = False
    try:
        univ = pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)
        core = pd.read_excel(XLSX, sheet_name="Core_Financials", keep_default_na=False)
        ts = pd.read_excel(XLSX, sheet_name="Time_Series", keep_default_na=False)
        full = core.dropna(subset=["Revenue", "Net_Income", "Book_Equity", "Total_Debt", "Operating_Cash_Flow"])
        na_ok = "NA" in core["Ticker"].astype(str).values
        msgs.append(f"Coverage core: {len(full)}/{len(univ)} with Revenue+NI+Equity+Debt+OCF")
        msgs.append(f"Core_Financials rows={len(core)} | Time_Series rows={len(ts)} | NA intact={'yes' if na_ok else 'NO'}")
    except Exception as e:
        msgs.append(f"coverage summary failed: {e}")
        ok = False
    return ok, "\n".join(msgs)


def main():
    st = read_state()
    lk = lock_status()
    hb_age = heartbeat_age()

    # Rule 4: already done -> validate + final report, never relaunch.
    if st.get("status") == "done" and not lk["alive"]:
        ok, msg = run_validation_report()
        print(f"[WATCHDOG] DONE\n{msg}")
        if not ok:
            notify("INTEGRITY_FAILURE", msg)
        return

    # Rule 3: alive but heartbeat stale -> stalled.
    if lk["alive"] and hb_age is not None and hb_age >= STALL_HEARTBEAT_AGE:
        graceful_restart(st, lk)
        return

    # Rule 1: alive + heartbeat fresh -> running.
    if lk["alive"]:
        print(f"RUNNING (pid={lk['pid']}, heartbeat_age={hb_age}s)")
        return

    # Rule 2: not alive + not done -> resume. Guard against recent crash (lock age < 30 min).
    if lk["exists"] and lk["pid"] and not lk["alive"] and (lk["age"] is not None and lk["age"] < STALE_LOCK_AGE):
        print(f"RECENT_CRASH_WAIT (lock age={lk['age']}s, stale threshold={STALE_LOCK_AGE}s)")
        return

    # 3x batch failure guard (count failed runs at the same checkpoint).
    fails = st.get("run_failures", 0)
    if st.get("status") == "failed":
        fails += 1
        st["run_failures"] = fails
        write_state_local(st)
        if fails >= 3:
            notify("FATAL_BATCH_FAILURE", f"same checkpoint failed {fails}x; sub_phase={st.get('sub_phase')} ticker={st.get('last_completed_ticker')}")
            return

    print(f"NOT_RUNNING (status={st.get('status')}, sub_phase={st.get('sub_phase')}) -> launching resume")
    launch_refresh(["--resume", "--mode", "core"])


if __name__ == "__main__":
    main()

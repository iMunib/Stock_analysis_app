# -*- coding: utf-8 -*-
"""Shared helpers: paths, YAML config, HTTP with retry + logging,
durable state (state.json / heartbeat.json / refresh.lock / failed_tickers.csv),
and atomic workbook writes.
"""
import csv, json, os, time, threading, urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # na_financials_research/
RAW = os.path.join(ROOT, "raw")
CFG = os.path.join(ROOT, "config")
MAPS = os.path.join(ROOT, "maps")
SCRIPTS = os.path.join(ROOT, "scripts")
LOGS = os.path.join(ROOT, "logs")
XLSX = os.path.join(ROOT, "NA_Company_Financials.xlsx")
TMP_XLSX = os.path.join(ROOT, "NA_Company_Financials.tmp.xlsx")
os.makedirs(LOGS, exist_ok=True)

HTTP_LOG = os.path.join(LOGS, "http_status.csv")
PARSE_LOG = os.path.join(LOGS, "parse_misses.csv")

# --- Durable state files ---
STATE = os.path.join(LOGS, "state.json")
HEARTBEAT = os.path.join(LOGS, "heartbeat.json")
LOCK = os.path.join(LOGS, "refresh.lock")
FAILED_TICKERS = os.path.join(LOGS, "failed_tickers.csv")

# Thresholds (seconds)
STALE_LOCK_AGE = 30 * 60        # lock considered stale after 30 min if PID dead
STALL_HEARTBEAT_AGE = 20 * 60   # worker considered stalled after 20 min without heartbeat


# --------------------------------------------------------------------------
# YAML config
# --------------------------------------------------------------------------
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cfg_sources():
    return load_yaml(os.path.join(CFG, "sources.yaml"))


def cfg_universe():
    return load_yaml(os.path.join(CFG, "universe.yaml"))


def cfg_fx():
    return load_yaml(os.path.join(CFG, "fx.yaml"))


def xbrl_tags():
    return load_yaml(os.path.join(MAPS, "xbrl_tags.yaml"))


def bank_fields():
    return load_yaml(os.path.join(MAPS, "bank_fields.yaml"))


def industry_overrides():
    return load_yaml(os.path.join(MAPS, "industry_overrides.yaml"))


def canonical_fields():
    return load_yaml(os.path.join(MAPS, "canonical_fields.yaml"))


def canonical_field(name):
    """Map a raw field label (legacy alias / XBRL tag / yfinance label) to its canonical name.
    Unknown or already-canonical names are returned unchanged."""
    if name is None:
        return name
    try:
        reg = canonical_fields()
    except Exception:
        return name
    return reg.get("aliases", {}).get(str(name), str(name))


# --------------------------------------------------------------------------
# HTTP + logging
# --------------------------------------------------------------------------
def log_http(url, status, ok):
    with open(HTTP_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["url", "status", "ok", "ts"])
        w.writerow([url, status, ok, time.strftime("%Y-%m-%d %H:%M:%S")])


def log_parse(ticker, metric, reason):
    with open(PARSE_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["ticker", "metric", "reason", "ts"])
        w.writerow([ticker, metric, reason, time.strftime("%Y-%m-%d %H:%M:%S")])


def get(url, retries=None, timeout=None, binary=True):
    """HTTP GET with retry + status logging. Returns bytes or None."""
    src = cfg_sources()
    edgar = src.get("edgar", {})
    retries = retries if retries is not None else edgar.get("retries", 3)
    timeout = timeout if timeout is not None else edgar.get("timeout_s", 60)
    ua = edgar.get("user_agent", "OpenClaw Research contact@openclaw.local")
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                log_http(url, r.status, True)
                return data
        except Exception as e:
            log_http(url, getattr(e, "code", "ERR"), False)
            if a == retries - 1:
                return None
            time.sleep(1.5)
    return None


def max_bytes():
    return cfg_sources().get("download", {}).get("max_bytes", 8388608)


# --------------------------------------------------------------------------
# JSON state helpers
# --------------------------------------------------------------------------
def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def read_state():
    return read_json(STATE, {})


def write_state(**kw):
    st = read_state()
    st.update(kw)
    st["last_heartbeat"] = int(time.time())
    write_json(STATE, st)
    return st


# --------------------------------------------------------------------------
# Heartbeat
# --------------------------------------------------------------------------
def touch_heartbeat(extra=None):
    hb = {"ts": int(time.time()), "pid": os.getpid()}
    if extra:
        hb.update(extra)
    write_json(HEARTBEAT, hb)


def read_heartbeat():
    return read_json(HEARTBEAT, {})


def heartbeat_age():
    hb = read_heartbeat()
    ts = hb.get("ts")
    if not ts:
        return None  # no heartbeat yet
    return int(time.time()) - int(ts)


def start_heartbeat_thread(interval=30):
    """Daemon thread that refreshes heartbeat.json every `interval` seconds."""
    def _loop():
        while True:
            try:
                touch_heartbeat()
            except Exception:
                pass
            time.sleep(interval)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


# --------------------------------------------------------------------------
# Lock (refresh.lock)
# --------------------------------------------------------------------------
def pid_alive(pid):
    """Best-effort check whether a process with the given PID is still running."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return False
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def lock_status():
    """Return dict describing current lock state."""
    if not os.path.exists(LOCK):
        return {"exists": False, "alive": False, "stale": False, "pid": None, "age": None}
    try:
        data = read_json(LOCK, {})
    except Exception:
        data = {}
    pid = data.get("pid")
    ts = data.get("ts")
    age = (int(time.time()) - int(ts)) if ts else None
    alive = pid_alive(pid) if pid else False
    stale = (not alive) and (age is not None) and (age >= STALE_LOCK_AGE)
    return {"exists": True, "alive": alive, "stale": stale, "pid": pid, "age": age}


def acquire_lock():
    """Acquire refresh.lock. Returns True if acquired, False if another worker holds it."""
    st = lock_status()
    if st["exists"]:
        if st["alive"]:
            return False  # another worker running
        # PID dead: if recent, treat as a crash-in-progress; if stale, preserve + take over
        if not st["stale"]:
            return False
        ts = time.strftime("%Y%m%d-%H%M%S")
        try:
            os.replace(LOCK, f"{LOCK}.stale.{ts}")
        except OSError:
            pass
    write_json(LOCK, {"pid": os.getpid(), "ts": int(time.time()), "phase": "starting"})
    return True


def release_lock():
    try:
        if os.path.exists(LOCK):
            os.remove(LOCK)
    except OSError:
        pass


# --------------------------------------------------------------------------
# Atomic workbook write
# --------------------------------------------------------------------------
def save_workbook_atomic(wb, target=XLSX, required_sheets=("Universe", "Core_Financials", "Time_Series")):
    """Save workbook to .tmp.xlsx, validate read-only, then atomically rename into place.
    Raises RuntimeError if validation fails; leaves the previous valid workbook intact."""
    import openpyxl
    wb.save(TMP_XLSX)
    v = openpyxl.load_workbook(TMP_XLSX, read_only=True)
    try:
        missing = [s for s in required_sheets if s not in v.sheetnames]
    finally:
        v.close()
    if missing:
        raise RuntimeError(f"atomic save validation failed: missing sheets {missing}")
    os.replace(TMP_XLSX, target)
    return target


# --------------------------------------------------------------------------
# Failed tickers
# --------------------------------------------------------------------------
FAILED_HEADER = ["ticker", "source_url", "failure_type", "attempts", "last_attempt", "next_retry", "reason"]


def record_failed_ticker(ticker, source_url, failure_type, attempts, reason, next_retry=None):
    row = {
        "ticker": ticker,
        "source_url": source_url or "",
        "failure_type": failure_type,
        "attempts": attempts,
        "last_attempt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "next_retry": next_retry or "",
        "reason": reason or "",
    }
    exists = os.path.exists(FAILED_TICKERS)
    with open(FAILED_TICKERS, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FAILED_HEADER)
        if not exists:
            w.writeheader()
        w.writerow(row)


def load_failed_tickers():
    import pandas as pd
    if not os.path.exists(FAILED_TICKERS):
        return pd.DataFrame(columns=FAILED_HEADER)
    return pd.read_csv(FAILED_TICKERS, keep_default_na=False)

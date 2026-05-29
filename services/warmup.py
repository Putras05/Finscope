"""Tiered background warmer cho toàn bộ 53 mã HOSE — drain queue ở tốc độ
~17 req/min (dưới ceiling vnstock 20 req/min) để khi user chọn mã bất kỳ
đã có cache nóng.

Tiers (priority asc — số NHỎ chạy trước):
  • USER_PICK = 0  — mã user vừa chọn trong topbar (chen lên đầu queue)
  • HOT       = 10 — top 5 mã default (FPT, HPG, VNM, MWG, MSN)
  • WARM      = 20 — 15 mã thanh khoản tiếp
  • COLD      = 30 — 33 mã còn lại

Worker daemon thread chạy mỗi MIN_INTERVAL = 3.4s/req → 17.6 req/min × 53 mã
= ~3 phút để hoàn tất warmup đầy đủ. Trong khi đó user vẫn dùng app bình
thường — chỉ hơi chậm phần fetch chưa kịp warm.

THAM KHẢO:
  Streamlit official perf docs — caching strategy + bg threading patterns.
  PriorityQueue from queue module — thread-safe.
  add_script_run_ctx để bg thread không gây "missing ScriptRunContext"
  warning khi gọi @st.cache_data.
"""
from __future__ import annotations
import queue
import threading
import time
from typing import Optional

import streamlit as st


# ── Tier priorities ─────────────────────────────────────────────────────
P_USER_PICK = 0       # user vừa chọn trong topbar
P_HOT       = 10
P_WARM      = 20
P_COLD      = 30

MIN_INTERVAL_SEC = 3.4     # 17.6 req/min < 20 ceiling vnstock


# ── Queue + tracker (module-level, share across reruns) ────────────────
_PQ: queue.PriorityQueue = queue.PriorityQueue()
_SEEN: set = set()
_LOCK = threading.Lock()
_STARTED = False
_STATS = {'enqueued': 0, 'done': 0, 'failed': 0, 'cur_tk': None,
           'started_at': None}


def _key(tk: str, ratio: float, p: int) -> tuple:
    return (str(tk).upper(), float(ratio), int(p))


def enqueue(prio: int, tk: str, ratio: float = 0.80, p: int = 1) -> None:
    """Thêm 1 mã vào queue. Idempotent theo key (tk, ratio, p)."""
    k = _key(tk, ratio, p)
    with _LOCK:
        if k in _SEEN:
            return
        _SEEN.add(k)
        _STATS['enqueued'] += 1
    # tiebreak bằng time.time() để FIFO trong cùng priority
    _PQ.put((int(prio), time.time(), tk, float(ratio), int(p)))


def prioritize(tk: str, ratio: float = 0.80, p: int = 1) -> None:
    """User vừa chọn mã trong topbar → chen lên đầu queue (priority 0).
    Không spam: nếu mã đã enqueued thì bỏ qua (đã được pick up sớm).
    """
    enqueue(P_USER_PICK, tk, ratio, p)


def stats() -> dict:
    """Snapshot tiến độ warmup — dùng để render progress chip."""
    with _LOCK:
        return dict(_STATS, qsize=_PQ.qsize(), seen=len(_SEEN))


def _warm_one(tk: str, ratio: float, p: int) -> bool:
    """Warm 1 mã: fetch raw + 8 models. Trả True nếu OK."""
    try:
        from data.fetcher import fetch_data
        df = fetch_data(tk)
        if df is None or len(df) < 50:
            return False
    except Exception:
        return False
    # Train 8 models nối tiếp — mỗi model có @cache_data nên gọi 1 lần thôi.
    # Chỉ chạy AR/MLR/ARIMA (3 core); SARIMA/ETS/GARCH/SARIMAX/GBR để cold-
    # start on-demand vì chậm và ít user dùng so với 3 core.
    try:
        from models.ar import run_ar; run_ar(tk, ratio, p=p)
    except Exception:
        pass
    try:
        from models.mlr import run_mlr; run_mlr(tk, ratio, p=p)
    except Exception:
        pass
    try:
        from models.arima import run_arima; run_arima(tk, ratio, p=p)
    except Exception:
        pass
    # Warm signal engine 8 trụ + Ichimoku + technicals trong background luôn
    try:
        from services.signal_engine import build_signal_report
        build_signal_report(df, tk, include_fundamentals=False)
    except Exception:
        pass
    return True


def _worker() -> None:
    """Daemon thread — drain queue forever, sleep ~MIN_INTERVAL giữa các call."""
    last_call = 0.0
    while True:
        try:
            prio, ts, tk, ratio, p = _PQ.get(timeout=60)
        except queue.Empty:
            continue
        # Throttle: bảo đảm cách lần trước ≥ MIN_INTERVAL
        wait = MIN_INTERVAL_SEC - (time.time() - last_call)
        if wait > 0:
            time.sleep(wait)
        with _LOCK:
            _STATS['cur_tk'] = tk
        ok = _warm_one(tk, ratio, p)
        with _LOCK:
            _STATS['done'] += 1
            if not ok:
                _STATS['failed'] += 1
            _STATS['cur_tk'] = None
        last_call = time.time()
        _PQ.task_done()


@st.cache_resource(show_spinner=False)
def start_warmer():
    """Bootstrap daemon — chỉ 1 instance trên toàn process (st.cache_resource).
    Trả handle thread; gọi nhiều lần safe — chỉ start 1 lần thực.
    """
    global _STARTED
    if _STARTED:
        return None
    _STARTED = True
    with _LOCK:
        _STATS['started_at'] = time.time()
    t = threading.Thread(target=_worker, daemon=True, name='finscope-warmer')
    # add_script_run_ctx để bg thread không gây "missing ScriptRunContext"
    # warnings. Streamlit 1.56 dùng `streamlit.runtime.scriptrunner`.
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx
        add_script_run_ctx(t)
    except Exception:
        pass     # API path đổi giữa Streamlit versions — fallback im lặng
    t.start()
    return t


def seed_queue(default_ticker: str = 'FPT', ratio: float = 0.80, p: int = 1) -> None:
    """Đẩy 53 mã vào queue theo 3 tier. Gọi 1 lần khi splash mở.

    HOT tier (priority 10) — 5 mã default thanh khoản top.
    WARM tier (priority 20) — 15 mã VN30 tiếp theo.
    COLD tier (priority 30) — 33 mã còn lại.
    """
    from core.constants import TICKERS
    HOT  = ['FPT', 'HPG', 'VNM', 'MWG', 'MSN', 'VCB', 'ACB', 'TCB']
    WARM = ['VIC', 'VHM', 'VRE', 'STB', 'CTG', 'BID', 'MBB', 'POW', 'GAS',
            'PLX', 'GVR', 'SAB', 'HVN', 'VJC', 'BCM']
    # Mã user đang xem ưu tiên cao nhất
    if default_ticker:
        enqueue(P_USER_PICK, default_ticker, ratio, p)
    for tk in HOT:
        if tk in TICKERS:
            enqueue(P_HOT, tk, ratio, p)
    for tk in WARM:
        if tk in TICKERS:
            enqueue(P_WARM, tk, ratio, p)
    for tk in TICKERS:
        if tk not in HOT and tk not in WARM:
            enqueue(P_COLD, tk, ratio, p)

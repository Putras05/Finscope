"""Preload data + model results at session start → slider/p changes instant.

Strategy:
  - fetch_data cho 3 tickers (parallel) — warm disk cache
  - run_ar / run_mlr cho 3 tickers × 5 train ratios × 3 p values (1,3,5) — FAST (~ms)
  - run_arima trong daemon thread background — SLOW (auto-order AIC ~2-4s/lần)
  - User đổi ticker / train_ratio / p (thuộc common values) → cache hit → 0s
  - Chỉ khi đổi sang giá trị NGOÀI common → training overlay hiện 3-5s
"""
import streamlit as st
import threading
from concurrent.futures import ThreadPoolExecutor
from data.fetcher import fetch_data
from core.constants import TICKERS

# VN30 có ~30 mã → KHÔNG preload tất cả (sẽ rất chậm). Chỉ warm mã mặc định
# (mã đầu danh sách); các mã khác train on-demand với overlay ~1-3s khi user chọn.
_PRELOAD_TICKERS = TICKERS[:1]
_SLIDER_VALUES = [0.70, 0.75, 0.80, 0.85, 0.90]
_COMMON_P       = [1, 3, 5]                    # common p values — preload hết
_DEFAULT_P      = 1

_arima_threads: list = []


# ── Background ARIMA precompute ──────────────────────────────────────────────
def _bg_arima(ticker: str, ar_order: int,
              date_from=None, date_to=None) -> None:
    """Warm ngầm ARIMA + nhóm nâng cao cho 1 ticker, trong daemon thread.

    Mục tiêu: lần đầu vào Dashboard (mã mặc định) là instant, và đổi
    ticker/ratio/p = cache hit. Warm combo mặc định (p=1, 0.80) toàn bộ 7 mô
    hình trước, rồi mới warm các combo ARIMA còn lại."""
    from models.arima import run_arima
    from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
    from models.ml import run_gbr
    _adv = (run_sarima, run_ets, run_garch, run_sarimax, run_gbr)
    try:
        run_arima(ticker, 0.80, p=1, date_from=date_from, date_to=date_to)
        for _fn in _adv:
            try:
                _fn(ticker, 0.80, p=1, date_from=date_from, date_to=date_to)
            except Exception:
                pass
    except Exception:
        pass
    for p in _COMMON_P:
        for tr in _SLIDER_VALUES:
            if p == 1 and abs(tr - 0.80) < 1e-9:
                continue
            try:
                run_arima(ticker, tr, p=p,
                          date_from=date_from, date_to=date_to)
            except Exception:
                pass


_arima_bg_started: set = set()
_arima_bg_lock = threading.Lock()


def trigger_bg_arima(ticker: str, ar_order: int,
                     date_from=None, date_to=None) -> None:
    """Launch ARIMA background precompute nếu chưa chạy cho ticker này.

    Idempotent qua một set + lock cấp module (thread-safe). Trước đây dùng
    st.session_state nhưng không truy cập được từ daemon thread.
    """
    with _arima_bg_lock:
        if ticker in _arima_bg_started:
            return
        _arima_bg_started.add(ticker)
    th = threading.Thread(
        target=_bg_arima,
        args=(ticker, ar_order, date_from, date_to),
        daemon=True,
    )
    th.start()
    _arima_threads.append(th)


def trigger_bg_arima_all() -> None:
    """Warm ARIMA cho TẤT CẢ tickers preload ở background."""
    for tk in _PRELOAD_TICKERS:
        trigger_bg_arima(tk, _DEFAULT_P)


# ── Parallel ticker fetch — chỉ mã preload (mặc định) ───────────────────────
def _fetch_all_parallel() -> None:
    """Fetch các mã preload đồng thời → giảm thời gian khởi tạo lần đầu."""
    with ThreadPoolExecutor(max_workers=max(1, len(_PRELOAD_TICKERS))) as ex:
        futures = [ex.submit(fetch_data, tk) for tk in _PRELOAD_TICKERS]
        for f in futures:
            try:
                f.result(timeout=30)
            except Exception:
                pass


# ── Main preload ─────────────────────────────────────────────────────────────
# Class-level Event để gate giữa các session/thread (st.session_state không
# truy cập được trong daemon thread). Một process Streamlit chỉ kick-off 1 lần.
_PRELOAD_KICKED = threading.Event()


def _silent_train_models() -> None:
    """Train AR+MLR cho mọi combo trong daemon thread, không animate UI.

    UI render ngay sau khi fetch xong (~1s); train tiếp ở nền. Khi user click
    page Mô hình lần đầu, model có thể chưa warm hết → fallback path tự train
    trên-the-fly (đã có). Lần thứ 2 trở đi cache hit.
    """
    from models.ar  import run_ar
    from models.mlr import run_mlr
    from concurrent.futures import as_completed
    jobs = []
    for tk in _PRELOAD_TICKERS:
        for p in _COMMON_P:
            for tr in _SLIDER_VALUES:
                jobs.append(('AR',  tk, tr, p))
                jobs.append(('MLR', tk, tr, p))

    def _train_one(job):
        kind, tk, tr, p = job
        try:
            if kind == 'AR':
                run_ar(tk, tr, p=p)
            else:
                run_mlr(tk, tr, p=p)
        except Exception:
            pass

    try:
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_train_one, j) for j in jobs]
            for f in as_completed(futs):
                pass
    except Exception:
        pass


def preload_all_tickers() -> None:
    """Khởi động preload mà KHÔNG block main thread.

    1. Fetch dữ liệu mã mặc định đồng bộ (~1s, blocking nhưng nhanh) — cần
       cho chart đầu tiên.
    2. Train AR+MLR và ARIMA precompute trong daemon thread → app render ngay.

    Một process Streamlit chỉ kick-off 1 lần (gated bởi threading.Event ở
    cấp module — st.session_state không truy cập được trong daemon thread).
    """
    if _PRELOAD_KICKED.is_set():
        return
    _PRELOAD_KICKED.set()

    # Step 1 — fetch giá thô đồng bộ. Nhanh (~1s) khi vnstock chưa throttle;
    # cần thiết cho chart đầu tiên trên Dashboard.
    try:
        _fetch_all_parallel()
    except Exception:
        pass

    # Step 2 — train AR/MLR + ARIMA nền. Không block UI.
    threading.Thread(target=_silent_train_models, daemon=True).start()
    threading.Thread(target=trigger_bg_arima_all,  daemon=True).start()

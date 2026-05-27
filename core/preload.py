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


def trigger_bg_arima(ticker: str, ar_order: int,
                     date_from=None, date_to=None) -> None:
    """Launch ARIMA background precompute nếu chưa chạy cho ticker này."""
    bg_key = f'_arima_bg_{ticker}'
    if st.session_state.get(bg_key):
        return
    st.session_state[bg_key] = True
    th = threading.Thread(
        target=_bg_arima,
        args=(ticker, ar_order, date_from, date_to),
        daemon=True,
    )
    th.start()
    _arima_threads.append(th)


def trigger_bg_arima_all() -> None:
    """Warm ARIMA cho TẤT CẢ tickers × p values ở background.

    Gọi sau preload_all_tickers → lúc user đang đọc Dashboard, ARIMA background
    đã train xong cho mọi combo → switch page = instant.
    """
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
def preload_all_tickers() -> None:
    """Warm cache cho 3 tickers × 5 ratios × 3 p values.

    Chạy 1 lần mỗi session (gated bởi session_state `_preloaded`).
    Tổng khoảng 45 model AR + 45 model MLR → ~5-8s trên máy thường.
    CART background song song, không block UI.
    """
    if st.session_state.get('_preloaded'):
        return

    from models.ar  import run_ar
    from models.mlr import run_mlr

    _loader   = st.empty()
    _progress = st.empty()

    with _loader.container():
        st.markdown(
            '<div style="background:rgba(21,101,192,0.08);'
            'border:1px solid rgba(21,101,192,0.2);'
            'border-radius:10px;padding:12px 18px;margin-bottom:8px">'
            '<div style="font-size:12px;font-weight:700;color:#1565C0;'
            'letter-spacing:0.5px;text-transform:uppercase">'
            'Khởi tạo dữ liệu · First launch</div>'
            '<div style="font-size:11px;color:#64748B;margin-top:4px">'
            'Tải dữ liệu mã mặc định + huấn luyện sẵn AR/MLR cho '
            'mọi tỉ lệ và p={1,3,5}...</div>'
            '</div>', unsafe_allow_html=True)

    _bar = _progress.progress(0, text='')

    # Step 1: Fetch mã mặc định
    _bar.progress(5, text='Tải dữ liệu mã mặc định...')
    _fetch_all_parallel()

    # Step 2: AR + MLR song song cho mã mặc định × ratios × p.
    jobs = []
    for tk in _PRELOAD_TICKERS:
        for p in _COMMON_P:
            for tr in _SLIDER_VALUES:
                jobs.append(('AR',  tk, tr, p))
                jobs.append(('MLR', tk, tr, p))
    total = len(jobs)

    def _train_one(job):
        kind, tk, tr, p = job
        try:
            if kind == 'AR':
                run_ar(tk, tr, p=p)
            else:
                run_mlr(tk, tr, p=p)
        except Exception:
            pass

    _bar.progress(10, text=f'Huấn luyện {total} mô hình AR+MLR (song song)...')
    done = 0
    from concurrent.futures import as_completed
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_train_one, j): j for j in jobs}
        for fut in as_completed(futures):
            done += 1
            if done % 6 == 0 or done == total:  # cập nhật progress mỗi 6 jobs
                pct = 10 + int(done / total * 85)
                kind, tk, tr, p = futures[fut]
                _bar.progress(pct,
                              text=f'{kind}({p}) · {tk} · {int(tr*100)}% · {done}/{total}')

    _bar.progress(100, text='Hoàn tất · ARIMA đang precompute ngầm')
    _loader.empty()
    _progress.empty()
    st.session_state['_preloaded'] = True

    # Step 3: ARIMA background cho tất cả tickers × common p
    trigger_bg_arima_all()

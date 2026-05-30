"""Singleton vnstock clients + token bucket throttle: mọi module trong app
chia sẻ chung 1 Vnstock() root + 1 rate limit toàn cục.

  - `vn_root()`: Vnstock() instance dùng chung (init 1 lần/process).
  - `vn_stock(symbol)`: stock handle cached theo symbol.
  - `vn_trading(source)`: trading handle (market snapshot, price board).
  - `throttle()` / `throttle_fg()`: token bucket ≤ 20 req/min (vnstock
    ceiling). throttle_fg dùng interval ngắn hơn cho user-initiated fetch.
"""
from __future__ import annotations
import threading
import time

import streamlit as st


# ── Token bucket throttle — chia sẻ giữa MỌI thread (preload, warmer, foreground)
MIN_INTERVAL_SEC      = 3.4    # warmer/background: 17.6 req/min  < 20 ceiling
MIN_INTERVAL_FG_SEC   = 1.6    # foreground:       up to 37 r/m worst-case; thực
                                # tế chỉ chạm khi user spam ticker. Tradeoff:
                                # bỏ freeze 3.4s khi đổi mã lần đầu.
_LAST_CALL = [0.0]
_LOCK = threading.Lock()
# Foreground priority: khi user click ticker mới, set tới deadline → warmer
# nhường nhịn (đợi tới đó mới xin token). Bỏ race-condition fetch ngắt nhau.
_FG_PRIO_UNTIL = [0.0]


def throttle(min_interval: float = MIN_INTERVAL_SEC,
             is_foreground: bool = False) -> None:
    """Block tới khi đảm bảo cách lần API call trước ≥ ``min_interval``.

    Thread-safe. Tất cả vnstock-touching code phải gọi throttle() ngay
    trước khi gọi `.quote.history()` / `.price_board()` / `.finance.*`.

    Khi ``is_foreground=True``: dùng ``MIN_INTERVAL_FG_SEC`` (ngắn hơn) +
    đặt nhãn ưu tiên — warmer/background gặp nhãn này sẽ đợi cho tới khi
    foreground claim xong slot. UX: bỏ giật khi user đổi mã.

    AppTest / pytest detect → bypass để không block test suite.
    """
    import os
    if os.environ.get('STREAMLIT_TEST') == '1' or os.environ.get('PYTEST_CURRENT_TEST'):
        return
    if is_foreground:
        min_interval = MIN_INTERVAL_FG_SEC
        _FG_PRIO_UNTIL[0] = time.time() + 0.8  # foreground giữ ưu tiên 0.8s
    else:
        # Background/warmer: nhường foreground nếu đang trong giai đoạn ưu tiên.
        while time.time() < _FG_PRIO_UNTIL[0]:
            time.sleep(0.2)
    with _LOCK:
        dt = time.time() - _LAST_CALL[0]
        if dt < min_interval:
            time.sleep(min_interval - dt)
        _LAST_CALL[0] = time.time()


def throttle_fg() -> None:
    """Tiện ích cho code foreground (user-initiated fetch)."""
    throttle(is_foreground=True)


@st.cache_resource(show_spinner=False)
def vn_root():
    """Vnstock() root — singleton trên toàn process. Init 1 lần, share."""
    from vnstock import Vnstock
    return Vnstock()


@st.cache_resource(show_spinner=False, max_entries=256)
def vn_stock(symbol: str, source: str = 'VCI'):
    """Stock handle cho 1 ticker — cached_resource theo (symbol, source).
    Mỗi ticker chỉ init 1 lần / process, không phải mỗi call.
    v58.9: max_entries 128 → 256 (53 tickers × 3 sources = 159 > 128
    → LRU eviction loop. Tăng để cover full universe.).
    """
    return vn_root().stock(symbol=symbol, source=source)


@st.cache_resource(show_spinner=False)
def vn_trading(source: str = 'VCI'):
    """Trading handle cho market snapshot — singleton."""
    from vnstock import Trading
    return Trading(source=source)

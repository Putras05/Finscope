"""Cache fingerprint helpers — single source of truth cho mọi
`@st.cache_data(hash_funcs=...)` trong codebase.

Trước đây 6 module có 6 bản `_df_fingerprint` / `_fingerprint` cùng signature
cùng logic O(1). Hợp nhất ở đây để:
  • Giảm 6 nguồn bug khi fingerprint cần update (vd: thêm column moment-2
    để phá collision như v48 đã làm cho returns_df).
  • Một chỗ test, một chỗ doc.
  • Import gọn: `from core.cache import df_fingerprint, df_hash_funcs`.

Hash chiến lược: O(1) lookup chỉ phụ thuộc shape + biên đầu/cuối + last_close.
Đủ phân biệt giữa các phiên giao dịch khác nhau (sau khi data thay đổi giá
đóng cửa, hash đổi), nhưng KHÔNG scan toàn bộ DataFrame mỗi lần cache check.
"""
from __future__ import annotations
import pandas as pd
from typing import Any


def df_fingerprint(df: pd.DataFrame) -> tuple:
    """Hash O(1) cho DataFrame OHLC (có cột Ngay + Close).

    Trả tuple (len, first_date, last_date, last_close) — phân biệt được giữa:
      - Cùng ticker, khác date range
      - Same range nhưng data đã update (last_close khác)
      - Empty DataFrame (return ('empty',))

    Dùng cho: technicals, ichimoku, signal_engine — input là OHLC từ data.fetcher.
    """
    if len(df) == 0:
        return ('empty',)
    try:
        return (int(len(df)),
                str(df['Ngay'].iloc[0]),
                str(df['Ngay'].iloc[-1]),
                float(df['Close'].iloc[-1]))
    except Exception:
        return (int(len(df)), id(df))


def returns_fingerprint(df: pd.DataFrame) -> tuple:
    """Hash cho returns DataFrame — daily returns cluster gần 0 nên chỉ
    sum(last_row) dễ collision. Dùng (shape, cols, first_idx, last_idx,
    sum, sum²) — moment bậc 2 phá collision về thực tế = 0.

    Dùng cho: optimizer, pca, cointegration — input là returns matrix
    (cols=ticker, values=daily return).
    """
    if len(df) == 0:
        return (df.shape, tuple(df.columns), 'empty')
    try:
        vals = df.iloc[-1].values
        first_idx = str(df.index[0])
        last_idx = str(df.index[-1])
        return (df.shape, tuple(df.columns), first_idx, last_idx,
                float(vals.sum()),
                float((vals * vals).sum()))      # moment bậc 2
    except Exception:
        return (df.shape, tuple(df.columns), id(df))


def state_fingerprint(state: dict) -> tuple:
    """Hash O(1) cho state Paper Trading — phụ thuộc số lệnh + ts cuối +
    cash + initial_capital. Đổi sau mỗi buy/sell.

    Dùng cho: data.paper.equity_curve cached wrapper.
    """
    hist = state.get('history', [])
    return (len(hist),
            (hist[-1].get('ts') if hist else ''),
            float(state.get('cash', 0)),
            float(state.get('initial_capital', 0)))


# Pre-built hash_funcs dict — reusable cho @st.cache_data decorators:
#     @st.cache_data(ttl=900, hash_funcs=df_hash_funcs)
df_hash_funcs: dict = {pd.DataFrame: df_fingerprint}
returns_hash_funcs: dict = {pd.DataFrame: returns_fingerprint}

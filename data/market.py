"""Tổng quan Thị trường — snapshot 53 mã HOSE: giá, % thay đổi, market cap.

Nguồn: vnstock Trading.price_board (1 lệnh gọi cho cả 53 mã → nhẹ hơn fetch
từng mã). Cache 5 phút để không hammer API.

Đây là dữ liệu CƠ BẢN nhất cho app chuyên chứng khoán — thiếu cái này
thì không thấy bức tranh thị trường, chỉ thấy 1 mã đang xem.
"""
import streamlit as st
import pandas as pd
import numpy as np

from core.constants import TICKERS, TICKER_INFO


def _sector_of(tk: str) -> str:
    """Ngành rút gọn (bỏ '· HOSE')."""
    s = TICKER_INFO.get(tk, '')
    return s.split('·')[0].strip() if s else 'Khác'


@st.cache_data(ttl=300, show_spinner=False)
def market_snapshot(symbols: tuple) -> pd.DataFrame:
    """Snapshot toàn bộ symbols → DataFrame:
    ['ticker', 'sector', 'ref_price', 'last_price', 'change', 'change_pct',
     'volume', 'value_M', 'market_cap_B', 'listed_share'].

    Giá ở đơn vị đồng (raw từ price_board). value_M = triệu đ; market_cap_B =
    tỷ đ.
    """
    import contextlib, io
    # v56 — Dùng singleton + throttle (chia rate-limit với fetcher/fundamental/capm)
    from data._clients import vn_trading, throttle
    # ── Fail-safe: nếu VCI Trading down hoặc trả None/schema lạ → DataFrame
    # rỗng có schema đúng. CACHE sẽ giữ failure 5 phút → tránh dồn retry,
    # nhưng app KHÔNG vỡ (các trang gọi market_snapshot sẽ thấy empty df).
    _empty_cols = ['ticker','sector','ref_price','last_price','change',
                   'change_pct','volume','value_M','market_cap_B','listed_share']
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            throttle()
            pb = vn_trading('VCI').price_board(symbols_list=list(symbols))
        if pb is None or len(pb) == 0:
            return pd.DataFrame(columns=_empty_cols)
    except Exception:
        return pd.DataFrame(columns=_empty_cols)
    rows = []
    for _, r in pb.iterrows():
        try:
            tk = str(r[('listing', 'symbol')])
            ref = float(r[('listing', 'ref_price')] or 0)
            shares = float(r[('listing', 'listed_share')] or 0)
            match = float(r[('match', 'match_price')] or 0) or ref
            vol = float(r[('match', 'accumulated_volume')] or 0)
            val = float(r[('match', 'accumulated_value')] or 0)
            chg = match - ref
            pct = (chg / ref * 100) if ref > 0 else 0.0
            mcap_billion = match * shares / 1e9   # đồng → tỷ đồng
            rows.append({
                'ticker':       tk,
                'sector':       _sector_of(tk),
                'ref_price':    ref,
                'last_price':   match,
                'change':       chg,
                'change_pct':   pct,
                'volume':       vol,
                'value_M':      val / 1e3,        # input đã ×1000 → MM đồng
                'market_cap_B': mcap_billion,
                'listed_share': shares,
            })
        except Exception:
            continue
    df = pd.DataFrame(rows)
    return df


def market_kpis(df: pd.DataFrame) -> dict:
    """KPI tổng hợp toàn thị trường mẫu."""
    if df.empty:
        return {'n': 0, 'n_up': 0, 'n_down': 0, 'n_flat': 0,
                'avg_pct': 0.0, 'total_mcap_T': 0.0, 'total_value_B': 0.0}
    n_up = int((df['change_pct'] > 0.05).sum())
    n_down = int((df['change_pct'] < -0.05).sum())
    n_flat = len(df) - n_up - n_down
    return {
        'n':              len(df),
        'n_up':           n_up,
        'n_down':         n_down,
        'n_flat':         n_flat,
        'avg_pct':        float(df['change_pct'].mean()),
        'total_mcap_T':   float(df['market_cap_B'].sum() / 1000),   # tỷ → nghìn tỷ
        'total_value_B':  float(df['value_M'].sum() / 1000),         # MM → tỷ
    }


def sector_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Gộp theo ngành: avg %, tổng market cap, số mã, advancers/decliners."""
    if df.empty:
        return pd.DataFrame()
    g = df.groupby('sector', dropna=False)
    out = g.agg(
        n=('ticker', 'count'),
        avg_pct=('change_pct', 'mean'),
        mcap_B=('market_cap_B', 'sum'),
        value_M=('value_M', 'sum'),
        n_up=('change_pct', lambda s: int((s > 0.05).sum())),
        n_down=('change_pct', lambda s: int((s < -0.05).sum())),
    ).reset_index()
    return out.sort_values('mcap_B', ascending=False).reset_index(drop=True)


def top_movers(df: pd.DataFrame, n: int = 5) -> tuple:
    """(gainers_df, losers_df) — top n theo change_pct."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    return (df.nlargest(n, 'change_pct').reset_index(drop=True),
            df.nsmallest(n, 'change_pct').reset_index(drop=True))

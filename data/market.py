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


_EMPTY_COLS = ['ticker','sector','ref_price','last_price','change',
               'change_pct','volume','value_M','market_cap_B','listed_share']


def _snapshot_fallback_from_history(symbols: tuple) -> pd.DataFrame:
    """Fallback khi MỌI Trading source fail (Streamlit Cloud thường gặp):
    fetch giá đóng cửa mới nhất qua quote.history cho từng mã (cache disk
    24h sẵn nên rất nhanh sau lần đầu). Trả schema giống price_board nhưng
    ref_price = previous close, last_price = latest close, không có
    listed_share/volume realtime → market_cap_B = 0 (caller hide column).
    """
    from data.fetcher import fetch_data
    rows = []
    for tk in symbols:
        try:
            df = fetch_data(tk)
            if df is None or df.empty or len(df) < 2:
                continue
            last = float(df['Close'].iloc[-1]) * 1000  # nghìn đ → đồng
            ref  = float(df['Close'].iloc[-2]) * 1000
            vol  = float(df['Volume'].iloc[-1])
            chg  = last - ref
            pct  = (chg / ref * 100) if ref > 0 else 0.0
            rows.append({
                'ticker': tk, 'sector': _sector_of(tk),
                'ref_price': ref, 'last_price': last, 'change': chg,
                'change_pct': pct, 'volume': vol,
                'value_M': last * vol / 1e6,  # đồng → triệu đ
                'market_cap_B': 0.0,         # cần listed_share — bỏ
                'listed_share': 0.0,
            })
        except Exception:
            continue
    return pd.DataFrame(rows)


def _snapshot_from_static_json(symbols: tuple) -> pd.DataFrame:
    """v58 — LEVEL 5 fallback: đọc snapshot từ data/static/snapshot.json
    commit trong repo. Instant load, hiển thị data ngày commit.

    Generate file bằng cách chạy local (vnstock work):
      python -c "from data.market import market_snapshot; ..."
    rồi commit `data/static/snapshot.json` lên GitHub.
    """
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / 'data' / 'static' / 'snapshot.json'
    if not p.exists():
        return pd.DataFrame(columns=_EMPTY_COLS)
    try:
        with p.open('r', encoding='utf-8') as f:
            d = json.load(f)
        rows = [r for r in d.get('tickers', []) if r.get('ticker') in symbols]
        df = pd.DataFrame(rows)
        # Đảm bảo có đủ cột schema để caller không vỡ
        for col in _EMPTY_COLS:
            if col not in df.columns:
                df[col] = 0.0
        return df[_EMPTY_COLS]
    except Exception:
        return pd.DataFrame(columns=_EMPTY_COLS)


def _try_source_with_timeout(source: str, symbols: tuple, timeout_s: float = 3.0):
    """v58 — Gọi vn_trading(source).price_board với HARD TIMEOUT.
    Tránh stuck 30s khi network slow. Trả None nếu timeout/fail.
    """
    import contextlib, io
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from data._clients import vn_trading, throttle
    def _call():
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            throttle()
            return vn_trading(source).price_board(symbols_list=list(symbols))
    ex = ThreadPoolExecutor(max_workers=1)
    try:
        return ex.submit(_call).result(timeout=timeout_s)
    except (TimeoutError, Exception):
        return None
    finally:
        ex.shutdown(wait=False)


@st.cache_data(ttl=300, show_spinner=False)
def market_snapshot(symbols: tuple) -> pd.DataFrame:
    """Snapshot toàn bộ symbols → DataFrame:
    ['ticker', 'sector', 'ref_price', 'last_price', 'change', 'change_pct',
     'volume', 'value_M', 'market_cap_B', 'listed_share'].

    Giá ở đơn vị đồng (raw từ price_board). value_M = triệu đ; market_cap_B =
    tỷ đ.

    v58 — 5-LEVEL fallback chain:
      L1: VCI Trading.price_board (3s timeout)
      L2: MSN Trading.price_board (3s timeout)
      L3: TCBS Trading.price_board (3s timeout)
      L4: per-ticker history (cache disk 24h sau lần đầu)
      L5: STATIC snapshot từ data/static/snapshot.json (instant, offline)

    Worst case all live source fail: instant load từ JSON commit trong repo.
    """
    pb = None
    for source in ['VCI', 'MSN', 'TCBS']:
        pb = _try_source_with_timeout(source, symbols, timeout_s=3.0)
        if pb is not None and len(pb) > 0:
            break
    # L4: per-ticker history fallback (~30-90s lần đầu, instant sau khi cache)
    if pb is None or len(pb) == 0:
        df = _snapshot_fallback_from_history(symbols)
        # L5: nếu L4 cũng empty (tất cả ticker fetch fail) → load static JSON
        if df.empty:
            return _snapshot_from_static_json(symbols)
        return df
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

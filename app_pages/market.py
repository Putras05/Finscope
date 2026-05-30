"""Trang 'Tổng quan Thị trường' — heatmap + sector + top movers + bảng đầy đủ.

Snapshot 53 mã HOSE qua 1 lệnh vnstock Trading.price_board (cache 5'):
giá hiện tại · % thay đổi · vốn hóa · giá trị giao dịch. Đây là bức tranh
TỔNG mà một nhà đầu tư chứng khoán cần thấy đầu mỗi phiên.
"""
import streamlit as st
import pandas as pd
import numpy as np

from core.constants import TICKERS
from data.market import market_snapshot, market_kpis, sector_overview, top_movers


@st.cache_data(ttl=300, show_spinner=False)
def _last5_close_map(symbols: tuple) -> dict:
    """Map {ticker: [5 close gần nhất]} dùng cho sparkline trong heatmap card.

    Cache 5 phút. Mỗi ticker dùng fetch_data đã cache → lần 2 instant. Parallel
    10 thread để fetch lần đầu nhanh (~5s cho 53 mã). Fail-safe per-ticker.
    """
    from concurrent.futures import ThreadPoolExecutor
    from data.fetcher import fetch_data
    def _one(tk):
        try:
            df = fetch_data(tk)
            return tk, [float(v) for v in df['Close'].tail(5).values]
        except Exception:
            return tk, []
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(_one, symbols))
    return {tk: arr for tk, arr in results if arr}


def _spark_svg(prices: list, col: str, w: int = 70, h: int = 18) -> str:
    """SVG polyline mini cho 5-7 điểm — chèn trong card heatmap."""
    if not prices or len(prices) < 2:
        return ''
    pmin = min(prices); pmax = max(prices); rng = max(pmax - pmin, 1e-9)
    n = len(prices)
    pts = ' '.join(f'{i*w/(n-1):.1f},{(h-2) - (p-pmin)/rng*(h-4):.1f}'
                   for i, p in enumerate(prices))
    return (f'<svg width="{w}" height="{h}" style="display:block">'
            f'<polyline points="{pts}" fill="none" stroke="{col}" '
            f'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def _pct_color(p: float, _T) -> str:
    """Màu theo % thay đổi — gradient đỏ/xám/xanh."""
    if p > 1:    return '#16A34A'
    if p > 0.05: return '#22C55E'
    if p > -0.05: return _T['text_muted']
    if p > -1:   return '#F87171'
    return '#DC2626'


def _pct_bg(p: float) -> str:
    if p > 0.05:  return 'rgba(22,163,74,0.10)'
    if p < -0.05: return 'rgba(220,38,38,0.10)'
    return 'rgba(148,163,184,0.07)'


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Tổng quan Thị trường" if not is_en else "Market Overview"} — 53 mã HOSE</h1>'
        f'<p>{"Snapshot toàn cảnh: giá hiện tại · % thay đổi · vốn hóa · giá trị giao dịch · sector breakdown · top movers — cập nhật mỗi 5 phút." if not is_en else "Full market snapshot: live prices · % change · market cap · turnover · sector breakdown · top movers — refreshes every 5 minutes."}</p>'
        f'</div>', unsafe_allow_html=True)

    with st.spinner('Đang lấy snapshot thị trường 53 mã...' if not is_en else 'Fetching 53-ticker snapshot...'):
        try:
            mdf = market_snapshot(tuple(TICKERS))
        except Exception as e:
            st.error(f'Không lấy được snapshot: {str(e)[:120]}')
            return
    # v58 — Snapshot rỗng: hiện banner + nút Refresh thay vì im lặng
    if mdf.empty:
        _c1, _c2 = st.columns([4, 1])
        with _c1:
            st.warning(
                ('Snapshot tạm thời rỗng — nguồn dữ liệu thị trường đang '
                 'bảo trì. Vẫn truy cập được từng mã ở trang Dashboard.')
                if not is_en else
                ('Market snapshot temporarily empty — data source under '
                 'maintenance. Per-ticker data still available on Dashboard.'))
        with _c2:
            if st.button(('Làm mới' if not is_en else 'Refresh'),
                          key='_market_refresh_btn',
                          use_container_width=True):
                # Clear cache key để fetch lại ngay
                st.cache_data.clear()
                st.rerun()
        return

    kpi = market_kpis(mdf)

    # ── KPI strip ───────────────────────────────────────────────────────
    cols = st.columns(6)
    _br_col = _T['success'] if kpi['n_up'] > kpi['n_down'] else _T['danger'] if kpi['n_down'] > kpi['n_up'] else _T['text_muted']
    _avg_col = _T['success'] if kpi['avg_pct'] > 0 else _T['danger']
    _kpis = [
        (('Mã tăng' if not is_en else 'Advancers'),     f'{kpi["n_up"]}',   _T['success']),
        (('Mã giảm' if not is_en else 'Decliners'),     f'{kpi["n_down"]}', _T['danger']),
        (('Mã đứng' if not is_en else 'Unchanged'),     f'{kpi["n_flat"]}', _T['text_muted']),
        (('Δ trung bình' if not is_en else 'Avg Δ%'),
         f'{kpi["avg_pct"]:+.2f}%', _avg_col),
        (('Vốn hóa tổng' if not is_en else 'Total mcap'),
         f'{kpi["total_mcap_T"]:,.0f} ' + ('nghìn tỷ' if not is_en else 'k bil'),
         _T['accent']),
        (('GTGD hôm nay' if not is_en else "Today's turnover"),
         f'{kpi["total_value_B"]:,.0f} ' + ('tỷ đ' if not is_en else 'B đ'),
         '#0F766E'),
    ]
    for col, (lbl, val, c) in zip(cols, _kpis):
        col.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-top:3px solid {c};border-radius:10px;padding:12px 14px">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_muted"]};'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">{lbl}</div>'
            f'<div style="font-size:18px;font-weight:800;color:{c};line-height:1.1">{val}</div>'
            f'</div>', unsafe_allow_html=True)

    # ── TOP MOVERS (gainers + losers) ──────────────────────────────────
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    cg, cl = st.columns(2)
    g_df, l_df = top_movers(mdf, n=5)
    def _movers_html(rows_df, color):
        if rows_df.empty:
            return f'<div style="color:{_T["text_muted"]};font-size:12px;padding:14px">—</div>'
        _items = ''
        for _, r in rows_df.iterrows():
            _arr = '▲' if r['change_pct'] >= 0 else '▼'
            _items += (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 14px;border-top:1px solid {_T["divider"]}">'
                f'<div><span style="font-weight:800;color:{_T["accent"]};font-size:14px">{r["ticker"]}</span>'
                f'<span style="color:{_T["text_muted"]};font-size:11px;margin-left:8px">{r["sector"]}</span></div>'
                f'<div style="text-align:right">'
                f'<span style="font-size:13px;color:{_T["text_primary"]}">{r["last_price"]:,.0f} đ</span> '
                f'<span style="font-size:14px;font-weight:800;color:{color}">{_arr} {r["change_pct"]:+.2f}%</span>'
                f'</div></div>')
        return _items
    with cg:
        st.markdown(
            f'<div style="border:1px solid {_T["border"]};border-radius:12px;overflow:hidden;background:{_T["bg_card"]}">'
            f'<div style="padding:10px 14px;background:rgba(22,163,74,0.10);font-size:12px;font-weight:800;'
            f'color:{_T["success"]};letter-spacing:.5px;text-transform:uppercase">▲ {"Top tăng giá" if not is_en else "Top gainers"}</div>'
            f'{_movers_html(g_df, _T["success"])}'
            f'</div>', unsafe_allow_html=True)
    with cl:
        st.markdown(
            f'<div style="border:1px solid {_T["border"]};border-radius:12px;overflow:hidden;background:{_T["bg_card"]}">'
            f'<div style="padding:10px 14px;background:rgba(220,38,38,0.10);font-size:12px;font-weight:800;'
            f'color:{_T["danger"]};letter-spacing:.5px;text-transform:uppercase">▼ {"Top giảm giá" if not is_en else "Top losers"}</div>'
            f'{_movers_html(l_df, _T["danger"])}'
            f'</div>', unsafe_allow_html=True)

    # ── SECTOR OVERVIEW ────────────────────────────────────────────────
    st.markdown("<div style='margin:20px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Tổng quan theo ngành" if not is_en else "Sector overview"}</div>',
                unsafe_allow_html=True)
    sec_df = sector_overview(mdf)
    _rows = ''
    for _, r in sec_df.iterrows():
        _c = _pct_color(r['avg_pct'], _T)
        _arr = '▲' if r['avg_pct'] >= 0 else '▼'
        _rows += (
            f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
            f'<td style="padding:8px 12px;font-weight:700">{r["sector"]}</td>'
            f'<td style="padding:8px 12px;text-align:center">{r["n"]}</td>'
            f'<td style="padding:8px 12px;color:{_c};font-weight:800">{_arr} {r["avg_pct"]:+.2f}%</td>'
            f'<td style="padding:8px 12px;color:{_T["success"]};text-align:center">{int(r["n_up"])}</td>'
            f'<td style="padding:8px 12px;color:{_T["danger"]};text-align:center">{int(r["n_down"])}</td>'
            f'<td style="padding:8px 12px;text-align:right">{r["mcap_B"]/1000:,.0f} ' + ('nghìn tỷ' if not is_en else 'k bil') + '</td>'
            f'<td style="padding:8px 12px;text-align:right">{r["value_M"]/1000:,.1f} ' + ('tỷ' if not is_en else 'B đ') + '</td>'
            f'</tr>')
    _hdr_sec = (['Ngành', 'Số mã', 'Δ trung bình', 'Tăng', 'Giảm', 'Vốn hóa', 'GTGD']
                if not is_en else
                ['Sector', '# Tickers', 'Avg Δ%', 'Up', 'Down', 'Mcap', 'Turnover'])
    _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr_sec)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
        f'<tbody>{_rows}</tbody></table></div>',
        unsafe_allow_html=True)

    # ── HEATMAP grid: 53 mã, color theo % change ────────────────────────
    st.markdown("<div style='margin:20px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Heatmap 53 mã HOSE" if not is_en else "53 HOSE tickers heatmap"} '
                f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
                f'{"sắp theo vốn hóa giảm dần · màu theo % thay đổi" if not is_en else "sorted by mcap desc · colored by %change"}</span></div>',
                unsafe_allow_html=True)
    sorted_df = mdf.sort_values('market_cap_B', ascending=False)
    # Pre-load 5-close cho toàn bộ ticker — cached 5'/per session, fail-safe
    try:
        _spark_map = _last5_close_map(tuple(sorted_df['ticker'].tolist()))
    except Exception:
        _spark_map = {}
    _cards = ''
    for _, r in sorted_df.iterrows():
        _c = _pct_color(r['change_pct'], _T)
        _bg = _pct_bg(r['change_pct'])
        _arr = '▲' if r['change_pct'] >= 0 else '▼' if r['change_pct'] < -0.05 else '─'
        _spark_html = _spark_svg(_spark_map.get(r['ticker'], []), _c, w=92, h=20)
        _cards += (
            f'<div style="flex:1 1 130px;min-width:120px;background:{_bg};'
            f'border:1px solid {_T["border"]};border-radius:8px;padding:9px 11px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span style="font-weight:800;color:{_T["text_primary"]};font-size:13px">{r["ticker"]}</span>'
            f'<span style="font-size:9.5px;color:{_T["text_muted"]}">{r["market_cap_B"]/1000:,.0f}k tỷ</span>'
            f'</div>'
            f'<div style="font-size:13px;color:{_c};font-weight:800;margin-top:2px">{_arr} {r["change_pct"]:+.2f}%</div>'
            f'<div style="font-size:10.5px;color:{_T["text_secondary"]};margin-top:1px">'
            f'{r["last_price"]:,.0f} đ</div>'
            f'<div style="margin-top:4px">{_spark_html}</div>'
            f'</div>')
    st.markdown(
        f'<div style="display:flex;gap:6px;flex-wrap:wrap">{_cards}</div>',
        unsafe_allow_html=True)

    # ── Bảng đầy đủ (sortable feel) — tải xuống CSV ─────────────────────
    st.markdown("<div style='margin:20px 0 6px'></div>", unsafe_allow_html=True)
    with st.expander('Bảng dữ liệu đầy đủ + Tải CSV' if not is_en else 'Full data table + CSV download',
                     expanded=False):
        _disp = sorted_df.copy()
        _disp['last_price'] = _disp['last_price'].map(lambda v: f'{v:,.0f}')
        _disp['change'] = _disp['change'].map(lambda v: f'{v:+,.0f}')
        _disp['change_pct'] = _disp['change_pct'].map(lambda v: f'{v:+.2f}%')
        _disp['volume'] = _disp['volume'].map(lambda v: f'{v:,.0f}')
        _disp['value_M'] = (_disp['value_M'] / 1000).map(lambda v: f'{v:,.1f}')
        _disp['market_cap_B'] = (_disp['market_cap_B'] / 1000).map(lambda v: f'{v:,.0f}')
        _disp = _disp.drop(columns=['ref_price', 'listed_share'])
        _disp.columns = (['Mã', 'Ngành', 'Giá (đ)', 'Δ (đ)', 'Δ %', 'KL', 'GTGD (tỷ)', 'Vốn hóa (nghìn tỷ)']
                         if not is_en else
                         ['Ticker', 'Sector', 'Price (đ)', 'Δ (đ)', 'Δ %', 'Volume', 'Turnover (B)', 'Mcap (kB)'])
        st.dataframe(_disp, use_container_width=True, hide_index=True)
        import io
        csv_buf = io.StringIO(); mdf.to_csv(csv_buf, index=False)
        st.download_button(
            'Tải CSV' if not is_en else 'Download CSV',
            data=csv_buf.getvalue(), mime='text/csv',
            file_name=f'finscope_market_snapshot.csv',
            use_container_width=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:12px;line-height:1.6">'
        f'{"Nguồn: vnstock Trading.price_board · cache 5 phút. Vốn hóa = giá hiện tại × số CP lưu hành. GTGD = giá trị khớp lệnh lũy kế từ đầu phiên. Số liệu thực, không lưu lại sau khi cache hết hạn." if not is_en else "Source: vnstock Trading.price_board · 5-min cache. Market cap = current price × outstanding shares. Turnover = matched-order accumulated value from session open. Live data, not persisted."}'
        f'</div>', unsafe_allow_html=True)

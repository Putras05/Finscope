"""Trang 'Phân tích Cơ bản' — báo cáo tài chính + tỷ số tài chính.

Sử dụng income statement + balance sheet (vnstock 4.x, 4 quý gần nhất) + giá
thị trường + số CP lưu hành (từ Trading.price_board) → tính P/E, P/B, EPS,
ROE, ROA, biên LN, D/E… TỰ DERIVED (không dùng endpoint ratio() bị paywalled).
"""
import streamlit as st
import pandas as pd
import numpy as np

from core.constants import TICKERS, ticker_sector
from data.fundamental import fetch_financials, extract_series, compute_kpis
from data.market import market_snapshot


def _fmt_money(v: float, unit: str = 'tỷ') -> str:
    """Format đồng → tỷ/nghìn tỷ. v ở đơn vị đồng."""
    if v != v: return '—'
    if unit == 'nghìn_tỷ':
        return f'{v / 1e12:,.2f} nghìn tỷ'
    return f'{v / 1e9:,.0f} tỷ'


def _fmt_pct(v: float) -> str:
    return f'{v:+.1f}%' if v == v else '—'


def _kpi_card(label, value, color, _T, hint=''):
    return (
        f'<div style="flex:1 1 180px;min-width:160px;background:{_T["bg_card"]};'
        f'border:1px solid {_T["border"]};border-top:3px solid {color};border-radius:10px;'
        f'padding:12px 14px">'
        f'<div style="font-size:10px;font-weight:700;color:{_T["text_muted"]};'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">{label}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{color};line-height:1.1">{value}</div>'
        f'<div style="font-size:11px;color:{_T["text_secondary"]};margin-top:4px">{hint}</div>'
        f'</div>')


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Phân tích Cơ bản" if not is_en else "Fundamental Analysis"} — {ticker}</h1>'
        f'<p>{ticker_sector(ticker)} &nbsp;·&nbsp; '
        f'{"Báo cáo tài chính + tỷ số TỰ TÍNH (P/E, P/B, ROE, ROA, biên LN…) từ income + balance + giá thị trường — 4 quý gần nhất" if not is_en else "Financial statements + SELF-COMPUTED ratios (P/E, P/B, ROE, ROA, margins…) from income + balance + market price — last 4 quarters"}'
        f'</p></div>', unsafe_allow_html=True)

    # ── Lấy financial + market info ────────────────────────────────────
    with st.spinner('Đang lấy báo cáo tài chính 4 quý...' if not is_en else 'Fetching 4-quarter statements...'):
        fin = fetch_financials(ticker)
    if not fin['ok']:
        st.error(fin['note'])
        return

    # Lấy giá hiện tại + số CP lưu hành từ price_board (đã cache 5')
    last_price_vnd = 0.0; listed_share = 0.0
    try:
        msnap = market_snapshot(tuple(TICKERS))
        row = msnap[msnap['ticker'] == ticker]
        if len(row):
            last_price_vnd = float(row['last_price'].iloc[0])
            listed_share   = float(row['listed_share'].iloc[0])
    except Exception:
        pass

    ext = extract_series(fin)
    kpi = compute_kpis(ext, last_price_vnd=last_price_vnd, listed_share=listed_share)
    if not kpi.get('ok'):
        st.warning('Không trích được dữ liệu từ BCTC.')
        return

    # ── KPI strip — NGƯỠNG khác cho NGÂN HÀNG (D/E cao + ROA thấp là CHUẨN) ──
    _is_bank = 'Ngân hàng' in ticker_sector(ticker)
    _roe_col = _T['success'] if kpi['roe'] > 15 else _T['warning'] if kpi['roe'] > 10 else _T['danger']
    if _is_bank:
        # Bank: ROA 0.8-2.5% là bình thường (do leverage cao); D/E 5-12x chuẩn
        # ngành (tiền gửi khách hàng tính là nợ). Áp ngưỡng riêng để không
        # đánh đỏ sai mọi mã ngân hàng.
        _roa_col = _T['success'] if kpi['roa'] > 1.5 else _T['warning'] if kpi['roa'] > 1.0 else _T['danger']
        _de_col  = _T['success'] if kpi['debt_equity'] < 8 else _T['warning'] if kpi['debt_equity'] < 12 else _T['danger']
        _roa_hint = '>1.5% tốt (ngân hàng)' if not is_en else '>1.5% good (bank)'
        _de_hint  = ('Nợ/VCSH · bank thường 5-12x' if not is_en else 'D/E · banks typically 5-12x')
    else:
        _roa_col = _T['success'] if kpi['roa'] > 8 else _T['warning'] if kpi['roa'] > 4 else _T['danger']
        _de_col  = _T['success'] if kpi['debt_equity'] < 1 else _T['warning'] if kpi['debt_equity'] < 2 else _T['danger']
        _roa_hint = '>8% tốt' if not is_en else '>8% good'
        _de_hint  = ('Nợ/VCSH; <1 an toàn' if not is_en else 'D/E; <1 safe')
    _pe_col = _T['accent'] if kpi['pe'] == kpi['pe'] else _T['text_muted']

    _cards1 = ''.join([
        _kpi_card('P/E', f'{kpi["pe"]:.2f}x' if kpi["pe"]==kpi["pe"] else '—',
                  _pe_col, _T,
                  ('Tự tính: Giá / TTM EPS' if not is_en else 'Computed: Price / TTM EPS')),
        _kpi_card('P/B', f'{kpi["pb"]:.2f}x' if kpi["pb"]==kpi["pb"] else '—',
                  _T['accent'], _T,
                  f'BVPS = {kpi["bvps"]:,.0f} đ' if kpi['bvps']==kpi['bvps'] else ''),
        _kpi_card('EPS (TTM)', f'{kpi["eps_ttm"]:,.0f} đ' if kpi['eps_ttm']==kpi['eps_ttm'] else '—',
                  _T['text_primary'], _T,
                  (('4 quý gần nhất' if not is_en else 'Last 4 quarters')
                   if kpi.get('eps_source') == 'reported' else
                   ('tự tính: TTM NI / số CP' if not is_en else 'computed: TTM NI / shares'))),
        _kpi_card('ROE',
                  f'{kpi["roe"]:.1f}%' if kpi['roe']==kpi['roe'] else '—',
                  _roe_col, _T, '>15% tốt'),
        _kpi_card('ROA',
                  f'{kpi["roa"]:.1f}%' if kpi['roa']==kpi['roa'] else '—',
                  _roa_col, _T, _roa_hint),
        _kpi_card(('Vốn hóa' if not is_en else 'Market cap'),
                  _fmt_money(kpi['market_cap'], 'nghìn_tỷ'),
                  '#0F766E', _T,
                  f'= {kpi["last_price"]:,.0f} đ × {kpi["listed_share"]/1e6:,.0f}M cp' if listed_share else ''),
        _kpi_card('D/E',
                  f'{kpi["debt_equity"]:.2f}' if kpi['debt_equity']==kpi['debt_equity'] else '—',
                  _de_col, _T, _de_hint),
    ])
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cards1}</div>',
        unsafe_allow_html=True)

    # ── SO SÁNH PEER cùng ngành — bảng + pill đánh giá vs trung bình ──────
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    try:
        from data.fundamental import peer_kpis as _peer_fn
        _peer = _peer_fn(ticker)
    except Exception:
        _peer = {'ok': False}
    if _peer.get('ok') and _peer['n'] >= 2:
        _sec = _peer['sector']
        _is_fb = _peer.get('fallback_bluechip', False)
        _hdr_title = (("So sánh ngành" if not is_en else "Peer comparison") + f' — {_sec}'
                      if not _is_fb else
                      ("So sánh nhóm dẫn dắt" if not is_en else "Peers — bluechips"))
        _hdr_note = (f'{_peer["n"]} {"mã cùng ngành — trung vị làm chuẩn so sánh" if not is_en else "peers — median benchmark"}'
                     if not _is_fb else
                     f'{"Ngành quá hẹp — đối chiếu" if not is_en else "Sector too narrow — compared against"} '
                     f'{_peer["n"]} {"mã top vốn hóa" if not is_en else "top-mcap tickers"}')
        st.markdown(
            f'<div class="sec-hdr">{_hdr_title}'
            f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
            f'{_hdr_note}</span></div>', unsafe_allow_html=True)
        _avg = _peer['avg']
        def _cmp_cell(val, avg, prefer='low'):
            """Pill so sánh val vs avg. prefer='low' (PE/DE) hay 'high' (ROE)."""
            if not (val == val and avg == avg):
                return '<span style="color:#94A3B8">—</span>'
            diff_pct = (val - avg) / abs(avg) * 100 if avg else 0
            is_better = (val < avg) if prefer == 'low' else (val > avg)
            _c = '#16A34A' if is_better else '#DC2626'
            _arr = '▼' if val < avg else '▲'
            return (f'<span style="color:{_c};font-weight:700">{val:.2f}</span> '
                    f'<span style="font-size:10px;color:{_T["text_muted"]}">{_arr}{abs(diff_pct):.0f}%</span>')
        _rows = ''
        for p in _peer['peers']:
            _is_cur = (p['ticker'] == ticker)
            _bg = _T['warning_bg'] if _is_cur else 'transparent'
            _bold = 'font-weight:800' if _is_cur else 'font-weight:600'
            _badge = (' <span style="background:#F9A825;color:#1A2A4A;font-size:10px;'
                      'font-weight:800;padding:2px 8px;border-radius:8px;margin-left:6px">'
                      f'{"Mã đang xem" if not is_en else "Selected"}</span>') if _is_cur else ''
            _mcap_s = (f'{p["mcap"]/1e12:,.1f} ' + ("nghìn tỷ" if not is_en else "T VND")
                       if p['mcap']==p['mcap'] and p['mcap']>0 else '—')
            _rows += (
                f'<tr style="background:{_bg};border-top:1px solid {_T["divider"]}">'
                f'<td style="padding:8px 12px;{_bold};color:{_T["text_primary"]}">'
                f'{p["ticker"]}{_badge}</td>'
                f'<td style="padding:8px 12px">{_cmp_cell(p["pe"], _avg["pe"], "low")}</td>'
                f'<td style="padding:8px 12px">{_cmp_cell(p["pb"], _avg["pb"], "low")}</td>'
                f'<td style="padding:8px 12px">{_cmp_cell(p["roe"], _avg["roe"], "high")}</td>'
                f'<td style="padding:8px 12px">{_cmp_cell(p["de"], _avg["de"], "low")}</td>'
                f'<td style="padding:8px 12px;color:{_T["text_secondary"]};font-size:12px">{_mcap_s}</td>'
                f'</tr>')
        # Hàng trung vị ngành
        _rows += (
            f'<tr style="background:{_T["bg_elevated"]};border-top:2px solid {_T["accent"]}">'
            f'<td style="padding:8px 12px;font-weight:800;color:{_T["accent"]}">'
            f'{"Trung vị ngành" if not is_en else "Industry median"}</td>'
            f'<td style="padding:8px 12px;font-weight:700">{_avg["pe"]:.2f}' if _avg["pe"]==_avg["pe"] else '<td style="padding:8px 12px">—</td>')
        _rows += (f'</td><td style="padding:8px 12px;font-weight:700">{_avg["pb"]:.2f}</td>'
                  if _avg["pb"]==_avg["pb"] else '<td style="padding:8px 12px">—</td>')
        _rows += (f'<td style="padding:8px 12px;font-weight:700">{_avg["roe"]:.1f}%</td>'
                  if _avg["roe"]==_avg["roe"] else '<td style="padding:8px 12px">—</td>')
        _rows += (f'<td style="padding:8px 12px;font-weight:700">{_avg["de"]:.2f}</td>'
                  if _avg["de"]==_avg["de"] else '<td style="padding:8px 12px">—</td>')
        _rows += '<td style="padding:8px 12px"></td></tr>'
        _hdr_pc = (['Mã', 'P/E', 'P/B', 'ROE', 'D/E', 'Vốn hóa'] if not is_en
                   else ['Ticker', 'P/E', 'P/B', 'ROE', 'D/E', 'Mcap'])
        st.markdown(
            f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
            f'<thead><tr style="background:{_T["accent"]};color:#fff">'
            + ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr_pc)
            + f'</tr></thead><tbody>{_rows}</tbody></table></div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:6px;line-height:1.55">'
            f'{"▼ thấp hơn / ▲ cao hơn trung vị ngành; XANH = tốt hơn (P/E·D/E thấp · ROE cao), ĐỎ = kém hơn." if not is_en else "▼ below / ▲ above industry median; GREEN = better (low P/E·D/E · high ROE), RED = worse."}'
            f'</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)

    # ── KQKD 4 QUÝ — bảng + chart Revenue/Net income ───────────────────
    st.markdown(f'<div class="sec-hdr">{"Kết quả kinh doanh 4 quý gần nhất" if not is_en else "Income statement — last 4 quarters"}'
                f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
                f'Doanh thu · LN gộp · LN sau thuế · EPS</span></div>',
                unsafe_allow_html=True)
    periods = ext['periods']
    inc = ext['income']
    # Bảng (đơn vị tỷ đồng)
    _hdr = ['Chỉ tiêu (tỷ đ)' if not is_en else 'Item (B đ)'] + periods
    def _row_html(name, vals, is_eps=False):
        cells = ''.join(
            f'<td style="padding:8px 12px;text-align:right">'
            f'{(v if is_eps else v/1e9):,.0f}{(" đ" if is_eps else "")}</td>'
            if v == v else '<td style="padding:8px 12px;text-align:right;color:#94A3B8">—</td>'
            for v in vals)
        return (f'<tr style="border-top:1px solid {_T["divider"]}">'
                f'<td style="padding:8px 12px;font-weight:600;color:{_T["text_primary"]}">{name}</td>'
                f'{cells}</tr>')
    _income_rows = (
        _row_html('Doanh thu thuần' if not is_en else 'Net revenue', inc['revenue']) +
        _row_html('Lợi nhuận gộp' if not is_en else 'Gross profit', inc['gross_profit']) +
        _row_html('LN trước thuế' if not is_en else 'Pre-tax profit', inc['pretax']) +
        _row_html('LN sau thuế (cổ đông Cty mẹ)' if not is_en else 'Net income (parent)', inc['net_income']) +
        _row_html('EPS cơ bản (đ/cp)' if not is_en else 'Basic EPS (đ/share)', inc['eps'], is_eps=True)
    )
    _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
        f'<tbody>{_income_rows}</tbody></table></div>',
        unsafe_allow_html=True)

    # Chart: Doanh thu (bar) + LN sau thuế (bar)
    try:
        import plotly.graph_objects as go
        from charts.base import _PLOTLY_CONFIG, _plotly_axes_style
        _x = list(reversed(periods))     # cũ → mới (trái → phải)
        _rev = list(reversed([v / 1e9 if v == v else 0 for v in inc['revenue']]))
        _ni = list(reversed([v / 1e9 if v == v else 0 for v in inc['net_income']]))
        _fig = go.Figure()
        _fig.add_trace(go.Bar(x=_x, y=_rev,
                              name='Doanh thu (tỷ đ)' if not is_en else 'Revenue (B đ)',
                              marker=dict(color='#0891B2')))
        _fig.add_trace(go.Bar(x=_x, y=_ni,
                              name='LN sau thuế (tỷ đ)' if not is_en else 'Net income (B đ)',
                              marker=dict(color='#16A34A')))
        _fig.update_layout(height=320, margin=dict(l=46, r=20, t=20, b=40),
                           barmode='group',
                           paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
                           font=dict(family='Inter', size=11, color=_T['text_primary']),
                           hovermode='x unified',
                           legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center'))
        _plotly_axes_style(_fig, _T)
        st.plotly_chart(_fig, use_container_width=True, config=_PLOTLY_CONFIG)
    except Exception as _e:
        st.caption(f'⚠ {_e}')

    # ── CÂN ĐỐI KẾ TOÁN ─────────────────────────────────────────────────
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Cân đối kế toán 4 quý" if not is_en else "Balance sheet — last 4 quarters"}'
                f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
                f'Tài sản · Vốn CSH · Nợ · Tiền</span></div>', unsafe_allow_html=True)
    bal = ext['balance']
    _bal_rows = (
        _row_html(('TỔNG TÀI SẢN' if not is_en else 'TOTAL ASSETS'), bal['total_assets']) +
        _row_html(('Vốn chủ sở hữu' if not is_en else 'Equity'), bal['equity']) +
        _row_html(('Tổng nợ phải trả' if not is_en else 'Total liabilities'), bal['total_debt']) +
        _row_html(('Nợ ngắn hạn' if not is_en else 'Short-term debt'), bal['short_debt']) +
        _row_html(('Nợ dài hạn' if not is_en else 'Long-term debt'), bal['long_debt']) +
        _row_html(('Tiền & tương đương' if not is_en else 'Cash & equivalents'), bal['cash'])
    )
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
        f'<tbody>{_bal_rows}</tbody></table></div>',
        unsafe_allow_html=True)

    # ── BÁO CÁO LƯU CHUYỂN TIỀN TỆ (Big-3: income + balance + CASH FLOW) ──
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Báo cáo Lưu chuyển Tiền tệ 4 quý" if not is_en else "Cash Flow Statement — last 4 quarters"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"HĐ kinh doanh · HĐ đầu tư · HĐ tài chính · LCTT thuần · Free Cash Flow (FCF)" if not is_en else "Operating · Investing · Financing · Net · Free Cash Flow"}'
        f'</span></div>', unsafe_allow_html=True)
    cf = ext.get('cashflow', {})
    _cf_rows = (
        _row_html(('LCTT HĐ kinh doanh (CFO)' if not is_en else 'Operating CF'), cf.get('oper_cf', [float('nan')]*len(periods))) +
        _row_html(('LCTT HĐ đầu tư (CFI)'    if not is_en else 'Investing CF'), cf.get('inv_cf', [float('nan')]*len(periods))) +
        _row_html(('LCTT HĐ tài chính (CFF)' if not is_en else 'Financing CF'), cf.get('fin_cf', [float('nan')]*len(periods))) +
        _row_html(('LCTT thuần trong kỳ'     if not is_en else 'Net change in cash'), cf.get('net_cf', [float('nan')]*len(periods)))
    )
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
        f'<tbody>{_cf_rows}</tbody></table></div>',
        unsafe_allow_html=True)

    # 3 KPI Cash Flow + FCF + P/FCF
    st.markdown("<div style='margin:10px 0 6px'></div>", unsafe_allow_html=True)
    _cf_col_o = _T['success'] if (kpi['oper_cf_ttm'] == kpi['oper_cf_ttm'] and kpi['oper_cf_ttm'] > 0) else _T['danger']
    _cf_col_f = _T['success'] if (kpi['fcf_ttm']     == kpi['fcf_ttm']     and kpi['fcf_ttm']     > 0) else _T['danger']
    _cf_cards = ''.join([
        _kpi_card(('CFO (TTM)' if not is_en else 'TTM CFO'),
                  _fmt_money(kpi['oper_cf_ttm']), _cf_col_o, _T,
                  ('Tiền HĐ KD tạo ra' if not is_en else 'Cash from operations')),
        _kpi_card(('CFI (TTM)' if not is_en else 'TTM CFI'),
                  _fmt_money(kpi['inv_cf_ttm']),
                  '#0891B2' if kpi['inv_cf_ttm']==kpi['inv_cf_ttm'] else _T['text_muted'], _T,
                  ('Tiền HĐ đầu tư (thường âm)' if not is_en else 'Cash from investing (usually negative)')),
        _kpi_card(('CFF (TTM)' if not is_en else 'TTM CFF'),
                  _fmt_money(kpi['fin_cf_ttm']),
                  _T['warning'] if kpi['fin_cf_ttm']==kpi['fin_cf_ttm'] else _T['text_muted'], _T,
                  ('Tiền HĐ tài chính (vay/trả/CT)' if not is_en else 'Cash from financing')),
        _kpi_card('FCF (TTM)',
                  _fmt_money(kpi['fcf_ttm']), _cf_col_f, _T,
                  ('CFO + CFI · dòng tiền tự do' if not is_en else 'CFO + CFI · free cash flow')),
        _kpi_card('P/FCF',
                  f'{kpi["p_fcf"]:.2f}x' if kpi['p_fcf']==kpi['p_fcf'] else '—',
                  _T['accent'], _T,
                  ('Vốn hóa / FCF · thấp = rẻ' if not is_en else 'Mcap / FCF · lower = cheaper')),
    ])
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cf_cards}</div>',
        unsafe_allow_html=True)

    # ── BIÊN LỢI NHUẬN + GROWTH ─────────────────────────────────────────
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Biên lợi nhuận & Tăng trưởng" if not is_en else "Margins & Growth"}</div>',
                unsafe_allow_html=True)
    # Nhãn margin theo loại doanh nghiệp (bank dùng "biên LN trước trích lập")
    _gross_lbl = ('Biên LN trước trích lập' if _is_bank and not is_en else
                  'Pre-provision margin' if _is_bank else
                  'Biên LN gộp' if not is_en else 'Gross margin')
    _gross_hint = ('LN HĐ trước dự phòng / Tổng TN HĐ (TTM)' if _is_bank and not is_en else
                   'Pre-prov. profit / Total op. income (TTM)' if _is_bank else
                   'LN gộp / Doanh thu TTM' if not is_en else
                   'Gross profit / Revenue (TTM)')
    _cards2 = ''.join([
        _kpi_card(_gross_lbl,
                  f'{kpi["gross_margin"]:.1f}%' if kpi['gross_margin']==kpi['gross_margin'] else '—',
                  _T['accent'], _T, _gross_hint),
        _kpi_card(('Biên LN ròng' if not is_en else 'Net margin'),
                  f'{kpi["net_margin"]:.1f}%' if kpi['net_margin']==kpi['net_margin'] else '—',
                  _T['success'] if kpi['net_margin']>10 else _T['warning'], _T,
                  'LN sau thuế / Doanh thu TTM'),
        _kpi_card(('Δ Doanh thu (QoQ)' if not is_en else 'Revenue QoQ Δ'),
                  _fmt_pct(kpi['rev_qoq']),
                  _T['success'] if kpi['rev_qoq']>0 else _T['danger'],
                  _T, 'Quý gần nhất vs quý trước'),
        _kpi_card(('Δ LN sau thuế (QoQ)' if not is_en else 'Net income QoQ Δ'),
                  _fmt_pct(kpi['ni_qoq']),
                  _T['success'] if kpi['ni_qoq']>0 else _T['danger'],
                  _T, 'Quý gần nhất vs quý trước'),
        _kpi_card(('TTM Doanh thu' if not is_en else 'TTM Revenue'),
                  _fmt_money(kpi['rev_ttm']),
                  _T['text_primary'], _T, 'Tổng 4 quý'),
        _kpi_card(('TTM LN sau thuế' if not is_en else 'TTM Net income'),
                  _fmt_money(kpi['ni_ttm']),
                  _T['success'], _T, 'Tổng 4 quý'),
    ])
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cards2}</div>',
        unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:14px;line-height:1.6">'
        f'{"Số liệu: vnstock 4.x VCI · 4 quý gần nhất (bản cộng đồng). TỰ TÍNH P/E, P/B, ROE, ROA, biên LN, D/E từ income + balance + giá thị trường (vốn hóa = giá × số CP lưu hành). KHÔNG dùng endpoint ratio() vì bản miễn phí chỉ trả demo 2018." if not is_en else "Source: vnstock 4.x VCI · last 4 quarters (community edition). P/E, P/B, ROE, ROA, margins, D/E are SELF-COMPUTED from income + balance + market price (mcap = price × outstanding shares). The ratio() endpoint is NOT used because the free tier returns only 2018 demo data."}'
        f'</div>', unsafe_allow_html=True)

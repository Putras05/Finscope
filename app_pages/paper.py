"""Trang 'Giao dịch Demo' (paper trading) — sổ lệnh ảo + thống kê P&L.

Cho phép người dùng đặt lệnh MUA/BÁN ảo trên 53 mã HOSE, theo dõi vị thế,
lịch sử lệnh, lãi/lỗ thực hiện + chưa thực hiện, và thống kê hành vi giao
dịch (số lệnh, win rate, P&L trung bình…). Lưu sổ ra file để giữ qua mỗi
phiên — sổ riêng cho từng máy.
"""
import streamlit as st
import datetime as _dt

from core.constants import TICKERS, ticker_sector
from data import paper as PP
from data.fetcher import fetch_data


def _kpi_card(label, value, color, _T, sub=None):
    sub_html = (f'<div style="font-size:10px;color:{_T["text_muted"]};margin-top:3px">'
                f'{sub}</div>' if sub else '')
    return (
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-top:3px solid {color};border-radius:10px;padding:12px 14px">'
        f'<div style="font-size:10px;font-weight:700;color:{_T["text_muted"]};'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">{label}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{color};line-height:1.1">{value}</div>'
        f'{sub_html}</div>'
    )


def _get_last_close(tk: str) -> float | None:
    """Giá đóng cửa mới nhất (đ) cho mã. None nếu fetch lỗi."""
    try:
        d = fetch_data(tk)
        return float(d['Close'].iloc[-1]) * 1000.0
    except Exception:
        return None


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Giao dịch Demo" if not is_en else "Paper Trading"} — {"Sổ lệnh ảo" if not is_en else "Virtual Order Book"}</h1>'
        f'<p>{"Đặt lệnh MUA/BÁN ảo, theo dõi lãi/lỗ & thống kê — sổ lưu cục bộ, dữ liệu giá thực." if not is_en else "Place virtual BUY/SELL orders, track P&L & stats — local book, real prices."}</p>'
        f'</div>', unsafe_allow_html=True)

    state = PP.load_state()

    # Lấy giá hiện tại cho các mã đang nắm giữ (để tính unrealized + equity)
    cur_prices = {}
    for tk in list(state['positions'].keys()):
        p = _get_last_close(tk)
        if p is not None:
            cur_prices[tk] = p
    # Giá hiện tại của mã đang chọn (cho form đặt lệnh)
    last_close_sel = _get_last_close(ticker) or 0.0

    stats = PP.compute_stats(state, cur_prices)

    # ── KPI strip ───────────────────────────────────────────────────────
    _ret_col = _T['success'] if stats['total_pnl'] >= 0 else _T['danger']
    _ret_sign = '▲' if stats['total_pnl'] >= 0 else '▼'
    cols = st.columns(5)
    cols[0].markdown(_kpi_card(
        'Tiền mặt' if not is_en else 'Cash',
        f'{stats["cash"]:,.0f} đ', _T['text_primary'], _T,
        f'{"Vốn ban đầu" if not is_en else "Initial"}: {stats["initial_capital"]:,.0f}'
    ), unsafe_allow_html=True)
    cols[1].markdown(_kpi_card(
        'Giá trị nắm giữ' if not is_en else 'Holdings',
        f'{stats["holdings_value"]:,.0f} đ', _T['accent'], _T,
        f'{len(stats["positions_rows"])} {"vị thế" if not is_en else "positions"}'
    ), unsafe_allow_html=True)
    cols[2].markdown(_kpi_card(
        'Tổng tài sản' if not is_en else 'Total Equity',
        f'{stats["equity"]:,.0f} đ', '#0F766E', _T
    ), unsafe_allow_html=True)
    cols[3].markdown(_kpi_card(
        'P&L tổng' if not is_en else 'Total P&L',
        f'{_ret_sign} {stats["total_pnl"]:+,.0f} đ', _ret_col, _T,
        f'{stats["total_return_pct"]:+.2f}%'
    ), unsafe_allow_html=True)
    cols[4].markdown(_kpi_card(
        'Tỉ lệ thắng' if not is_en else 'Win Rate',
        f'{stats["win_rate"]:.0f}%', _T['warning'], _T,
        f'{stats["n_wins"]}W / {stats["n_losses"]}L · {stats["n_sells"]} {"bán" if not is_en else "sells"}'
    ), unsafe_allow_html=True)

    st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)

    # ── 4 tab: Đặt lệnh · Vị thế · Lịch sử · Thống kê ──────────────────
    tab_order, tab_pos, tab_hist, tab_stat = st.tabs([
        '  ' + ('Đặt lệnh' if not is_en else 'Place Order') + '  ',
        '  ' + ('Vị thế hiện tại' if not is_en else 'Current Positions') + '  ',
        '  ' + ('Lịch sử lệnh' if not is_en else 'Order History') + '  ',
        '  ' + ('Thống kê & Reset' if not is_en else 'Stats & Reset') + '  ',
    ])

    # ── TAB 1: ĐẶT LỆNH ────────────────────────────────────────────────
    with tab_order:
        st.markdown(
            f'<div class="info-box" style="margin-bottom:10px">'
            f'{"Mã đang xem" if not is_en else "Selected ticker"}: '
            f'<b style="color:{_T["accent"]}">{ticker}</b> · '
            f'{ticker_sector(ticker)}<br>'
            f'{"Giá tham chiếu (close gần nhất)" if not is_en else "Reference price (last close)"}: '
            f'<b>{last_close_sel:,.0f} đ</b></div>',
            unsafe_allow_html=True)
        col_form, col_info = st.columns([3, 2])
        with col_form:
            with st.form('order_form', clear_on_submit=False):
                _side = st.radio(
                    'Loại lệnh' if not is_en else 'Side',
                    options=['BUY', 'SELL'], horizontal=True,
                    key='po_side',
                )
                _qty = st.number_input(
                    'Khối lượng (cổ phiếu)' if not is_en else 'Quantity (shares)',
                    min_value=1, max_value=1_000_000, value=100, step=10,
                    key='po_qty',
                )
                _px = st.number_input(
                    'Giá (đ/cp)' if not is_en else 'Price (đ/share)',
                    min_value=1.0, max_value=10_000_000.0,
                    value=float(last_close_sel) if last_close_sel else 10000.0,
                    step=100.0, format='%.0f', key='po_px',
                )
                _est = int(_qty) * float(_px)
                st.markdown(
                    f'<div style="font-size:12px;color:{_T["text_muted"]};margin-top:-4px">'
                    f'{"Tổng giá trị" if not is_en else "Total value"}: '
                    f'<b style="color:{_T["text_primary"]}">{_est:,.0f} đ</b></div>',
                    unsafe_allow_html=True)
                submitted = st.form_submit_button(
                    ('Đặt lệnh' if not is_en else 'Submit order'),
                    use_container_width=True, type='primary')
            if submitted:
                if _side == 'BUY':
                    state, ok, msg = PP.buy(state, ticker, int(_qty), float(_px))
                else:
                    state, ok, msg = PP.sell(state, ticker, int(_qty), float(_px))
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        with col_info:
            pos = state['positions'].get(ticker)
            if pos:
                _gap = (last_close_sel - pos['avg_price']) if last_close_sel else 0
                _gpct = (_gap / pos['avg_price'] * 100) if pos['avg_price'] else 0
                _gc = _T['success'] if _gap >= 0 else _T['danger']
                st.markdown(
                    f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
                    f'border-left:4px solid {_T["accent"]};border-radius:10px;padding:14px 18px">'
                    f'<div style="font-size:11px;font-weight:700;color:{_T["text_muted"]};'
                    f'text-transform:uppercase;letter-spacing:.5px">'
                    f'{"Vị thế hiện tại" if not is_en else "Current position"}</div>'
                    f'<div style="font-size:18px;font-weight:800;color:{_T["text_primary"]};margin-top:4px">'
                    f'{pos["qty"]:,} {ticker}</div>'
                    f'<div style="font-size:12px;color:{_T["text_secondary"]};margin-top:2px">'
                    f'{"Giá vốn TB" if not is_en else "Avg cost"}: '
                    f'<b>{pos["avg_price"]:,.0f} đ</b></div>'
                    f'<div style="font-size:12px;color:{_gc};margin-top:6px">'
                    f'{"Lãi/lỗ tạm tính" if not is_en else "Unrealized"}: '
                    f'<b>{_gap:+,.0f} đ ({_gpct:+.2f}%)</b></div>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:{_T["bg_card"]};border:1px dashed {_T["border"]};'
                    f'border-radius:10px;padding:14px 18px;color:{_T["text_muted"]};font-size:12px">'
                    f'{"Chưa có vị thế cho" if not is_en else "No position in"} '
                    f'<b style="color:{_T["text_primary"]}">{ticker}</b>.</div>',
                    unsafe_allow_html=True)

    # ── TAB 2: VỊ THẾ HIỆN TẠI ─────────────────────────────────────────
    with tab_pos:
        if not stats['positions_rows']:
            st.info('Chưa có vị thế nào.' if not is_en else 'No open positions.')
        else:
            _hdr = (['Mã', 'KL', 'Giá vốn TB', 'Giá hiện tại', 'Giá trị', 'Lãi/lỗ tạm tính']
                    if not is_en else
                    ['Ticker', 'Qty', 'Avg cost', 'Current price', 'Value', 'Unrealized P&L'])
            _rows = ''
            for r in sorted(stats['positions_rows'], key=lambda x: -x['value']):
                _c = _T['success'] if r['unrealized'] >= 0 else _T['danger']
                _arr = '▲' if r['unrealized'] >= 0 else '▼'
                _rows += (
                    f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
                    f'<td style="padding:9px 12px;font-weight:700;color:{_T["accent"]}">{r["ticker"]}</td>'
                    f'<td style="padding:9px 12px">{r["qty"]:,}</td>'
                    f'<td style="padding:9px 12px">{r["avg_price"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px">{r["cur_price"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px;font-weight:700">{r["value"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px;color:{_c};font-weight:700">'
                    f'{_arr} {r["unrealized"]:+,.0f} đ ({r["unrealized_pct"]:+.2f}%)</td>'
                    f'</tr>')
            _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
            st.markdown(
                f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
                f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
                f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
                f'<tbody>{_rows}</tbody></table></div>',
                unsafe_allow_html=True)

    # ── TAB 3: LỊCH SỬ ──────────────────────────────────────────────────
    with tab_hist:
        hist = list(reversed(state.get('history', [])))
        if not hist:
            st.info('Chưa có lệnh nào.' if not is_en else 'No orders yet.')
        else:
            _hdr = (['Thời điểm', 'Mã', 'Loại', 'KL', 'Giá', 'Giá trị', 'Lãi/lỗ thực hiện']
                    if not is_en else
                    ['Time', 'Ticker', 'Side', 'Qty', 'Price', 'Value', 'Realized P&L'])
            _rows = ''
            for h in hist[:200]:        # tối đa 200 dòng gần nhất
                _sc = _T['success'] if h['side'] == 'BUY' else _T['danger']
                _rl = h.get('realized')
                if _rl is None:
                    _rl_txt, _rc = '—', _T['text_muted']
                else:
                    _rc = _T['success'] if _rl >= 0 else _T['danger']
                    _rl_txt = f'{_rl:+,.0f} đ'
                _rows += (
                    f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
                    f'<td style="padding:8px 10px;color:{_T["text_muted"]};font-family:monospace;font-size:11px">'
                    f'{h["ts"][:16].replace("T"," ")}</td>'
                    f'<td style="padding:8px 10px;font-weight:700;color:{_T["accent"]}">{h["ticker"]}</td>'
                    f'<td style="padding:8px 10px;color:{_sc};font-weight:800">{h["side"]}</td>'
                    f'<td style="padding:8px 10px">{h["qty"]:,}</td>'
                    f'<td style="padding:8px 10px">{h["price"]:,.0f}</td>'
                    f'<td style="padding:8px 10px">{h["value"]:,.0f}</td>'
                    f'<td style="padding:8px 10px;color:{_rc};font-weight:700">{_rl_txt}</td>'
                    f'</tr>')
            _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
            st.markdown(
                f'<div style="border-radius:12px;overflow:hidden;max-height:480px;'
                f'overflow-y:auto;border:1px solid {_T["border"]}">'
                f'<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
                f'<thead style="position:sticky;top:0">'
                f'<tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
                f'<tbody>{_rows}</tbody></table></div>',
                unsafe_allow_html=True)

    # ── TAB 4: THỐNG KÊ & RESET ────────────────────────────────────────
    with tab_stat:
        # ── Equity curve — đường tài sản theo thời gian ─────────────────
        curve = PP.equity_curve(state)
        if len(curve) >= 2:
            st.markdown(f'<div class="sec-hdr">{"Đường tài sản (Equity Curve)" if not is_en else "Equity Curve"}'
                        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
                        f'{"Cash + giá trị nắm giữ theo thời gian — neo vào Close hằng ngày" if not is_en else "Cash + holdings value over time — anchored to daily Close"}'
                        f'</span></div>', unsafe_allow_html=True)
            try:
                import plotly.graph_objects as _go
                from charts.base import _plotly_axes_style, _PLOTLY_CONFIG
                _dates = [c['date'] for c in curve]
                _eq    = [c['equity']   for c in curve]
                _cash  = [c['cash']     for c in curve]
                _hold  = [c['holdings'] for c in curve]
                _init  = float(state.get('initial_capital', 100_000_000))
                _fig = _go.Figure()
                _fig.add_trace(_go.Scatter(
                    x=_dates, y=_eq, mode='lines+markers',
                    line=dict(color='#0F766E', width=2.4),
                    marker=dict(size=6, color='#0F766E', line=dict(color='#fff', width=1)),
                    name=('Tổng tài sản' if not is_en else 'Total Equity'),
                    fill='tozeroy', fillcolor='rgba(15,118,110,0.08)',
                    hovertemplate='<b>%{x}</b><br>%{y:,.0f} đ<extra></extra>'))
                _fig.add_trace(_go.Scatter(
                    x=_dates, y=_cash, mode='lines',
                    line=dict(color='#94A3B8', width=1.4, dash='dot'),
                    name=('Tiền mặt' if not is_en else 'Cash'),
                    hovertemplate='Cash: %{y:,.0f} đ<extra></extra>'))
                _fig.add_hline(y=_init, line=dict(color=_T['text_muted'], width=1, dash='dash'),
                               annotation_text=('Vốn ban đầu' if not is_en else 'Initial capital'),
                               annotation_position='right',
                               annotation_font=dict(size=10, color=_T['text_muted']))
                _fig.update_layout(
                    height=340, margin=dict(l=50, r=30, t=10, b=40),
                    paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
                    font=dict(family='Inter', size=11, color=_T['text_primary']),
                    hovermode='x unified',
                    legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center',
                                bgcolor='rgba(0,0,0,0)'))
                _plotly_axes_style(_fig, _T)
                _fig.update_yaxes(title=dict(text='đồng', font=dict(size=10, color=_T['text_muted'])))
                st.plotly_chart(_fig, use_container_width=True, config=_PLOTLY_CONFIG)
            except Exception as _e:
                st.caption(f'⚠ {_e}')
            st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)
        _detail = [
            (('Số lệnh tổng' if not is_en else 'Total trades'),       f'{stats["n_trades"]}', _T['text_primary']),
            (('Lệnh mua' if not is_en else 'Buy orders'),             f'{stats["n_buys"]}', _T['success']),
            (('Lệnh bán' if not is_en else 'Sell orders'),            f'{stats["n_sells"]}', _T['danger']),
            (('P&L thực hiện' if not is_en else 'Realized P&L'),
             f'{stats["realized_pnl"]:+,.0f} đ',
             _T['success'] if stats['realized_pnl'] >= 0 else _T['danger']),
            (('P&L chưa thực hiện' if not is_en else 'Unrealized P&L'),
             f'{stats["unrealized_pnl"]:+,.0f} đ',
             _T['success'] if stats['unrealized_pnl'] >= 0 else _T['danger']),
            (('Lãi TB / lệnh thắng' if not is_en else 'Avg win'),    f'{stats["avg_win"]:+,.0f} đ', _T['success']),
            (('Lỗ TB / lệnh thua' if not is_en else 'Avg loss'),     f'{stats["avg_loss"]:+,.0f} đ', _T['danger']),
            (('Lệnh thắng lớn nhất' if not is_en else 'Max win'),    f'{stats["max_win"]:+,.0f} đ', _T['success']),
            (('Lệnh thua nặng nhất' if not is_en else 'Max loss'),   f'{stats["max_loss"]:+,.0f} đ', _T['danger']),
            (('Max Drawdown' if not is_en else 'Max Drawdown'),
             f'{stats["max_drawdown_pct"]:.2f}%',
             _T['success'] if stats['max_drawdown_pct'] > -5 else
             (_T['warning'] if stats['max_drawdown_pct'] > -15 else _T['danger'])),
            (('Sharpe (annualized)' if not is_en else 'Sharpe (ann.)'),
             f'{stats["sharpe_ratio"]:.2f}' if stats['sharpe_ratio'] == stats['sharpe_ratio'] else 'N/A',
             _T['success'] if (stats['sharpe_ratio'] == stats['sharpe_ratio'] and stats['sharpe_ratio'] > 1)
             else (_T['warning'] if (stats['sharpe_ratio'] == stats['sharpe_ratio'] and stats['sharpe_ratio'] > 0)
                   else _T['danger'])),
            (('Phí giao dịch (cộng dồn)' if not is_en else 'Total fees'),
             f'{stats["total_fees"]:,.0f} đ', _T['text_secondary']),
            (('Thuế bán (cộng dồn)' if not is_en else 'Sell tax'),
             f'{stats["total_tax"]:,.0f} đ', _T['text_secondary']),
        ]
        _cells = ''.join(
            f'<div style="flex:1 1 180px;min-width:170px;background:{_T["bg_card"]};'
            f'border:1px solid {_T["border"]};border-top:3px solid {col};border-radius:10px;'
            f'padding:10px 12px"><div style="font-size:10px;color:{_T["text_muted"]};'
            f'text-transform:uppercase;letter-spacing:.4px">{lbl}</div>'
            f'<div style="font-size:15px;font-weight:800;color:{col};margin-top:3px">{val}</div></div>'
            for lbl, val, col in _detail)
        st.markdown(
            f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cells}</div>',
            unsafe_allow_html=True)

        st.markdown("<div style='margin:18px 0 8px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="sec-hdr">{"Đặt lại sổ giao dịch" if not is_en else "Reset trading book"}</div>',
                    unsafe_allow_html=True)
        col_a, col_b = st.columns([2, 1])
        with col_a:
            new_cap = st.number_input(
                'Vốn ban đầu (đ)' if not is_en else 'Initial capital (đ)',
                min_value=1_000_000.0, max_value=10_000_000_000.0,
                value=100_000_000.0, step=10_000_000.0, format='%.0f',
                key='paper_reset_cap')
        with col_b:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button(('Reset sổ' if not is_en else 'Reset book'),
                         key='paper_reset_btn', use_container_width=True):
                PP.reset_state(float(new_cap))
                st.success(('Đã đặt lại sổ.' if not is_en else 'Book reset.'))
                st.rerun()

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:14px;line-height:1.6">'
        f'{"Sổ giao dịch ảo lưu cục bộ tại paper_state.json (mỗi máy 1 sổ). KHÔNG phải tài khoản chứng khoán thật — chỉ dùng để luyện tập kỷ luật giao dịch & theo dõi P&L với giá thị trường thật." if not is_en else "Virtual book stored locally in paper_state.json (one book per machine). NOT a real brokerage — for practicing trading discipline & tracking P&L against real market prices."}'
        f'</div>', unsafe_allow_html=True)

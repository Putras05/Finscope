import streamlit as st
import datetime as _dt
import numpy as np
import pandas as pd

from core.i18n import t
from core.constants import TICKERS, CLR, get_clr, ticker_sector
from data.fetcher import fetch_data
from data.metrics import calc_metrics
from models.ar    import run_ar
from models.mlr   import run_mlr
from models.arima import run_arima
from ui.components import sparkline_svg
from charts.portfolio import chart_portfolio_compare_plotly
from charts.base import _PLOTLY_CONFIG


def _build_ticker_bundle(tk, train_ratio, p):
    d      = fetch_data(tk)
    ar_r   = run_ar   (tk, train_ratio, p=p)
    mlr_r  = run_mlr  (tk, train_ratio, p=p)
    cart_r = run_arima(tk, train_ratio, p=p)   # model-3 slot = ARIMA (key giữ 'cart')
    _k3 = sum(cart_r.get('order', (p, 0, 0))) + 1
    m_ar   = calc_metrics(ar_r['yte'],   ar_r['pte'],   k=p)
    m_mlr  = calc_metrics(mlr_r['yte'],  mlr_r['pte'],  k=3 * p)
    m_cart = calc_metrics(cart_r['yte'], cart_r['pte'], k=_k3)
    # FinScope Ensemble — gộp 3 mô hình lõi (trọng số ∝ 1/MAPE); DERIVED,
    # không train thêm nên gần như miễn phí. Giữ mô hình kết hợp xuất hiện
    # nhất quán trên toàn app (kể cả so sánh đa mã).
    from models.ensemble import build_ensemble
    ens_r = build_ensemble([
        {'name': 'AR',    'res': ar_r,   'mape': m_ar['MAPE']},
        {'name': 'MLR',   'res': mlr_r,  'mape': m_mlr['MAPE']},
        {'name': 'ARIMA', 'res': cart_r, 'mape': m_cart['MAPE']},
    ], d)
    m_ens = (calc_metrics(ens_r['yte'], ens_r['pte'], k=2)
             if ens_r is not None else None)
    return tk, {
        'data':   d,
        'ar':     ar_r,
        'mlr':    mlr_r,
        'cart':   cart_r,
        'ens':    ens_r,
        'm_ar':   m_ar,
        'm_mlr':  m_mlr,
        'm_cart': m_cart,
        'm_ens':  m_ens,
    }


@st.cache_data(show_spinner=False, ttl=1800)
def _load_portfolio_models(tks, train_ratio, p):
    """Cache N tickers × 3 models — train song song qua ThreadPoolExecutor.
    `run_*` đã `@st.cache_data` nên thread-safe. `tks` là tuple để hashable."""
    from concurrent.futures import ThreadPoolExecutor
    result = {}
    with ThreadPoolExecutor(max_workers=min(4, len(tks))) as ex:
        futures = [ex.submit(_build_ticker_bundle, tk, train_ratio, p)
                   for tk in tks]
        for fut in futures:
            tk, bundle = fut.result()
            result[tk] = bundle
    return result


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{t("portfolio.title")}</h1>'
        f'<p>{t("portfolio.subtitle")}</p>'
        f'</div>', unsafe_allow_html=True)

    # ── Chọn rổ mã để so sánh (mặc định = mã đang xem + 2 mã đại diện) ──
    _is_en_p = st.session_state.get('lang', 'VI') == 'EN'
    _default = list(dict.fromkeys([ticker] + [t_ for t_ in ('FPT', 'HPG', 'VNM')
                                              if t_ != ticker]))[:3]
    sel = st.multiselect(
        'So sánh các mã' if not _is_en_p else 'Compare tickers',
        options=TICKERS, default=_default, max_selections=6,
        help=('Chọn 2–6 mã để so sánh (giới hạn 6 để app chạy nhanh)'
              if not _is_en_p else 'Pick 2–6 tickers to compare (capped at 6 for speed)'),
    )
    if len(sel) < 2:
        st.info('Chọn ít nhất 2 mã để so sánh.' if not _is_en_p
                else 'Select at least 2 tickers to compare.')
        return

    # Cache hit thường trong <100ms; cache miss ~1-3s/mã → spinner phản ánh đúng.
    with st.spinner(t('load.portfolio')):
        _bundle = _load_portfolio_models(tuple(sel), train_ratio, ar_order)

    all_data   = {tk: _bundle[tk]['data']   for tk in sel}
    all_ar1    = {tk: _bundle[tk]['ar']     for tk in sel}
    all_mlr    = {tk: _bundle[tk]['mlr']    for tk in sel}
    all_cart   = {tk: _bundle[tk]['cart']   for tk in sel}
    all_ens    = {tk: _bundle[tk]['ens']    for tk in sel}
    all_m_ar1  = {tk: _bundle[tk]['m_ar']   for tk in sel}
    all_m_mlr  = {tk: _bundle[tk]['m_mlr']  for tk in sel}
    all_m_cart = {tk: _bundle[tk]['m_cart'] for tk in sel}
    all_m_ens  = {tk: _bundle[tk]['m_ens']  for tk in sel}

    _kpi_cols = st.columns(4)
    _ret_ytd = {}
    _year_start = _dt.date(_dt.date.today().year, 1, 1)
    for _tk in sel:
        _d = all_data[_tk]
        _d_year = _d[_d['Ngay'] >= _year_start]
        # YTD = (Close hiện tại / Close cuối năm trước) − 1.
        # Base = phiên CUỐI CÙNG TRƯỚC năm hiện tại (close năm trước), KHÔNG
        # phải phiên đầu năm hiện tại — tránh underestimate khi đầu năm có gap.
        _d_prev = _d[_d['Ngay'] < _year_start]
        if len(_d_year) >= 1 and len(_d_prev) >= 1:
            _base = float(_d_prev['Close'].iloc[-1])
            _now  = float(_d_year['Close'].iloc[-1])
            _ret_ytd[_tk] = (_now / _base - 1) * 100 if _base > 0 else 0.0
        elif len(_d_year) >= 2:
            _ret_ytd[_tk] = (_d_year['Close'].iloc[-1] /
                             _d_year['Close'].iloc[0] - 1) * 100
        else:
            # Fallback: COMPOUND daily returns, KHÔNG sum (sum % ≠ tích lũy).
            _r = _d['Return'].dropna() / 100.0   # df['Return'] đang ở scale %
            _ret_ytd[_tk] = float(((1 + _r).prod() - 1) * 100) if len(_r) else 0.0
    _best_tk  = max(_ret_ytd, key=_ret_ytd.get)
    _worst_tk = min(_ret_ytd, key=_ret_ytd.get)
    _sharpe = {}
    for _tk in sel:
        _r = all_data[_tk]['Return'].dropna()
        _sharpe[_tk] = (_r.mean() / _r.std() * (252**0.5)) if _r.std() > 0 else 0
    _best_sharpe = max(_sharpe, key=_sharpe.get)
    _kpi_data = [
        (t('portfolio.kpi_best_ytd'),  f'{_best_tk}  {_ret_ytd[_best_tk]:+.2f}%',       _T['success']),
        (t('portfolio.kpi_worst_ytd'), f'{_worst_tk}  {_ret_ytd[_worst_tk]:+.2f}%',     _T['danger']),
        (t('portfolio.kpi_sharpe'),    f'{_best_sharpe}  {_sharpe[_best_sharpe]:.2f}',  _T['accent']),
        (t('portfolio.kpi_rec'),
         t('portfolio.rec_accumulate', tk=_best_tk) if _ret_ytd[_best_tk] > 5
         else t('portfolio.rec_caution', tk=_worst_tk),
         _T['warning']),
    ]
    for _kc, (_lbl, _val, _col) in zip(_kpi_cols, _kpi_data):
        _kc.markdown(
            f'<div style="background:{_T["bg_card"]};border-radius:12px;padding:14px 16px;'
            f'box-shadow:{_T["shadow_sm"]};border:1px solid {_T["border"]};'
            f'border-top:3px solid {_col}">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_muted"]};'
            f'letter-spacing:.7px;text-transform:uppercase;margin-bottom:6px">{_lbl}</div>'
            f'<div style="font-size:15px;font-weight:800;color:{_col}">{_val}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:14px"></div>', unsafe_allow_html=True)

    # Xác định ngày phiên giao dịch kế tiếp (dùng mã đầu tiên làm mốc — cùng sàn HOSE)
    _ref_tk = sel[0]
    _last_date_p = all_data[_ref_tk]['Ngay'].iloc[-1]
    if isinstance(_last_date_p, str):
        _last_date_p = _dt.datetime.strptime(_last_date_p, '%Y-%m-%d').date()
    _next_date_p = _last_date_p + _dt.timedelta(days=1)
    while _next_date_p.weekday() >= 5:  # Sat=5, Sun=6
        _next_date_p += _dt.timedelta(days=1)

    if ar_order == 1:
        _src_desc_p = f'{t("dash.based_on_close")} {_last_date_p}'
    else:
        _first_date_p = all_data[_ref_tk]['Ngay'].iloc[-ar_order]
        if isinstance(_first_date_p, str):
            _first_date_p = _dt.datetime.strptime(_first_date_p, '%Y-%m-%d').date()
        _src_desc_p = t('dash.based_on_close_range',
                        p=ar_order, d0=_first_date_p, d1=_last_date_p)
    st.markdown(
        f'<div class="sec-hdr">{t("portfolio.price_hdr")} '
        f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};'
        f'margin-left:8px">'
        f'{t("dash.forecast_for")} <b style="color:{_T["accent"]}">{_next_date_p.strftime("%Y-%m-%d")}</b> '
        f'({_src_desc_p})</span></div>',
        unsafe_allow_html=True)
    _fcols = st.columns(len(sel))
    for col_w, tk in zip(_fcols, sel):
        T_tk    = all_data[tk].iloc[-1]
        np_ar1  = all_ar1[tk]['next_pred']
        np_mlr  = all_mlr[tk]['next_pred']
        np_cart = all_cart[tk]['next_pred']
        _ens_tk = all_ens[tk]
        np_ens  = _ens_tk['next_pred'] if _ens_tk is not None else float('nan')
        _r_tk   = float(T_tk['Return'])
        _rc_tk  = '#1B6B2F' if _r_tk >= 0 else '#C62828'
        _ra_tk  = '▲' if _r_tk >= 0 else '▼'
        _base_tk = T_tk['Close']
        def _pct_col(v): return '#1B6B2F' if v >= 0 else '#C62828'
        def _pct_bg(v):  return '#E8F5E9' if v >= 0 else '#FFEBEE'
        p1 = (np_ar1  - _base_tk) / _base_tk * 100
        p2 = (np_mlr  - _base_tk) / _base_tk * 100
        p3 = (np_cart - _base_tk) / _base_tk * 100
        # Dải Ensemble (mô hình kết hợp) — nổi bật bên dưới 3 mô hình lõi
        if np_ens == np_ens:   # not NaN
            _pe = (np_ens - _base_tk) / _base_tk * 100
            _ens_strip = (
                f'<div style="margin-top:8px;background:linear-gradient(135deg,#0F766E,#0891B2);'
                f'border-radius:8px;padding:7px 10px;display:flex;justify-content:space-between;'
                f'align-items:center;color:#fff">'
                f'<span style="font-size:10px;font-weight:800;letter-spacing:.3px">FinScope Ensemble</span>'
                f'<span style="font-size:13px;font-weight:800">{np_ens*1000:,.0f} '
                f'<span style="font-size:11px;opacity:.9">({_pe:+.2f}%)</span></span></div>')
        else:
            _ens_strip = ''
        col_w.markdown(
            f'<div style="background:{_T["bg_card"]};border-radius:14px;padding:16px 18px;'
            f'box-shadow:{_T["shadow_md"]};border:1px solid {_T["border"]};border-top:5px solid {CLR[tk]}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<b style="color:{CLR[tk]};font-size:18px">{tk}</b>'
            f'<span style="font-size:10px;color:{_T["text_muted"]}">{ticker_sector(tk)}</span>'
            f'</div>'
            f'<div style="font-size:9px;color:#10B981;font-weight:700;margin-top:4px">'
            f'● {t("common.settled")} · {str(T_tk["Ngay"])}</div>'
            f'<div style="font-size:26px;font-weight:800;color:{_T["text_primary"]};margin:6px 0 2px">'
            f'{T_tk["Close"]*1000:,.0f} đ</div>'
            f'<div style="display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;'
            f'border-radius:12px;color:{_rc_tk};background:{_T["success_bg"] if _r_tk>=0 else _T["danger_bg"]};margin-bottom:10px">'
            f'{_ra_tk} {abs(_r_tk):.2f}%</div>'
            f'<div style="margin:8px 0 0;padding:8px;background:{_T["bg_elevated"]};border-radius:8px">'
            f'{sparkline_svg(all_data[tk]["Close"].values[-30:]*1000, CLR[tk], 260, 48)}'
            f'</div>'
            f'<div style="font-size:9px;color:{_T["text_muted"]};margin:4px 0 8px">{t("portfolio.last_30")}</div>'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_secondary"]};letter-spacing:.5px;'
            f'text-transform:uppercase;margin-bottom:6px">{t("portfolio.next_session")}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">'
            f'<div style="background:{_T["grad_ar"]};border-radius:8px;padding:6px;text-align:center">'
            f'<div style="font-size:9px;color:{_T["text_secondary"]};font-weight:700">AR({ar_order})</div>'
            f'<div style="font-size:13px;font-weight:700;color:{_T["text_primary"]}">{np_ar1*1000:,.0f}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{_pct_col(p1)}">{p1:+.2f}%</div></div>'
            f'<div style="background:{_T["grad_mlr"]};border-radius:8px;padding:6px;text-align:center">'
            f'<div style="font-size:9px;color:{_T["text_secondary"]};font-weight:700">MLR</div>'
            f'<div style="font-size:13px;font-weight:700;color:{_T["text_primary"]}">{np_mlr*1000:,.0f}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{_pct_col(p2)}">{p2:+.2f}%</div></div>'
            f'<div style="background:{_T["grad_arima"]};border-radius:8px;padding:6px;text-align:center">'
            f'<div style="font-size:9px;color:{_T["text_secondary"]};font-weight:700">ARIMA</div>'
            f'<div style="font-size:13px;font-weight:700;color:{_T["text_primary"]}">{np_cart*1000:,.0f}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{_pct_col(p3)}">{p3:+.2f}%</div></div>'
            f'</div>{_ens_strip}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Normalized performance chart — luôn hiện toàn bộ lịch sử để so sánh dài hạn
    # (không dùng toggle filter vì gây nhầm lẫn với date range ở History page)
    st.markdown(f'<div class="sec-hdr">{t("portfolio.normalized_hdr")}</div>',
                unsafe_allow_html=True)
    fig_port = chart_portfolio_compare_plotly(all_data, train_ratio, T=_T)
    st.plotly_chart(fig_port, use_container_width=True, config=_PLOTLY_CONFIG)

    st.markdown(f'<div class="sec-hdr">{t("portfolio.perf_table_hdr")}</div>', unsafe_allow_html=True)
    _BG   = _T['bg_card'];      _BGH = _T['bg_elevated']
    _FG   = _T['text_primary']; _FGS = _T['text_secondary']
    _BRD  = _T['border'];       _ACC = _T['accent']
    _MUTED = _T['text_muted']
    _TK_COLORS = get_clr(_T)

    def _models_of(tk):
        lst = [(f'AR({ar_order})', all_m_ar1[tk]),
               ('MLR', all_m_mlr[tk]),
               ('ARIMA', all_m_cart[tk])]
        if all_m_ens[tk] is not None:
            lst.append(('FinScope Ensemble', all_m_ens[tk]))
        return lst

    _best_idx = {}
    for tk in sel:
        mapes = [md['MAPE'] for _, md in _models_of(tk)]
        _best_idx[tk] = int(np.argmin(mapes))

    _th = (f'background:{_BGH};color:{_FGS};font-size:11px;font-weight:700;'
           f'text-transform:uppercase;letter-spacing:.6px;padding:9px 12px;'
           f'border-bottom:2px solid {_BRD};text-align:left;white-space:nowrap')
    _td_base = f'font-size:13px;padding:8px 12px;border-bottom:1px solid {_BRD};color:{_FG}'
    _td_num  = f'{_td_base};text-align:right;font-variant-numeric:tabular-nums'

    # SVG star tự build (best model marker) — không dùng ★ emoji
    _svg_star = (
        f'<svg width="12" height="12" viewBox="0 0 24 24" fill="{_ACC}" '
        f'stroke="{_ACC}" stroke-width="1" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:-1px;margin-left:4px">'
        f'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 '
        f'5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    )

    _rows_html = ''
    for tk in sel:
        _mods = _models_of(tk)
        for i, (mn, md) in enumerate(_mods):
            is_best = (i == _best_idx[tk])
            row_bg  = f'background:{_ACC}18' if is_best else f'background:{_BG}'
            bold    = 'font-weight:700' if is_best else ''
            tick_cell = ''
            if i == 0:
                tick_cell = (f'<td rowspan="{len(_mods)}" style="{_td_base};background:{_BGH};vertical-align:middle;'
                             f'font-weight:800;font-size:14px;color:{_TK_COLORS[tk]};'
                             f'border-right:2px solid {_BRD};text-align:center">{tk}</td>')
            _best_marker = _svg_star if is_best else ''
            _rows_html += (
                f'<tr style="{row_bg}">'
                f'{tick_cell}'
                f'<td style="{_td_base};{bold}">{mn}{_best_marker}</td>'
                f'<td style="{_td_num};{bold}">{md["MAPE"]:.2f}%</td>'
                f'<td style="{_td_num}">{md["RMSE"]:.4f}</td>'
                f'<td style="{_td_num}">{md["MAE"]:.4f}</td>'
                f'<td style="{_td_num}">{md["R2adj"]:.4f}</td>'
                f'</tr>'
            )

    st.markdown(f"""
<div style="overflow-x:auto;border:1px solid {_BRD};border-radius:10px;overflow:hidden">
<table style="width:100%;border-collapse:collapse;background:{_BG}">
<thead><tr>
  <th style="{_th};width:60px">{t('col.ticker')}</th>
  <th style="{_th}">{t('col.model')}</th>
  <th style="{_th};text-align:right">MAPE</th>
  <th style="{_th};text-align:right">RMSE</th>
  <th style="{_th};text-align:right">MAE</th>
  <th style="{_th};text-align:right">R²adj</th>
</tr></thead>
<tbody>{_rows_html}</tbody>
</table></div>
""", unsafe_allow_html=True)
    st.caption(t('note.mape_quality'))

    st.markdown(f'<div class="sec-hdr" style="margin-top:16px">{t("portfolio.return_stats_hdr")}</div>',
                unsafe_allow_html=True)
    _ret_rows = ''
    for i, tk in enumerate(sel):
        ret_v   = all_data[tk]['Return'].dropna()
        row_bg  = f'background:{_BGH}' if i % 2 == 1 else f'background:{_BG}'
        _ret_rows += (
            f'<tr style="{row_bg}">'
            f'<td style="{_td_base};font-weight:800;color:{_TK_COLORS[tk]};text-align:center">{tk}</td>'
            f'<td style="{_td_num}">{ret_v.mean():+.3f}</td>'
            f'<td style="{_td_num}">{ret_v.std():.3f}</td>'
            f'<td style="{_td_num};color:#4ADE80">{ret_v.max():+.2f}</td>'
            f'<td style="{_td_num};color:#F87171">{ret_v.min():+.2f}</td>'
            f'<td style="{_td_num}">{(ret_v > 0).mean()*100:.1f}%</td>'
            f'</tr>'
        )
    st.markdown(f"""
<div style="overflow-x:auto;border:1px solid {_BRD};border-radius:10px;overflow:hidden;margin-top:4px">
<table style="width:100%;border-collapse:collapse;background:{_BG}">
<thead><tr>
  <th style="{_th};width:60px;text-align:center">{t('col.ticker')}</th>
  <th style="{_th};text-align:right">{t('col.return_avg')}</th>
  <th style="{_th};text-align:right">Std Dev (%)</th>
  <th style="{_th};text-align:right">Max (%)</th>
  <th style="{_th};text-align:right">Min (%)</th>
  <th style="{_th};text-align:right">{t('col.up_days')}</th>
</tr></thead>
<tbody>{_ret_rows}</tbody>
</table></div>
""", unsafe_allow_html=True)

    # Đã bỏ 2 chart "Ma trận tương quan return" và "Độ lệch chuẩn return hàng ngày"
    # theo yêu cầu user — bảng số liệu phía trên đã đủ thông tin tổng quan.

    # ── Markowitz Mean-Variance Optimizer ──────────────────────────────
    _render_optimizer_section(sel, all_data, _T, _is_en_p)


def _render_optimizer_section(sel, all_data, _T, is_en):
    """Section Optimizer Markowitz + biên hiệu quả (efficient frontier).

    Dùng daily Return của các mã đã chọn để tính trọng số portfolio tối ưu
    theo 3 chiến lược: Equal Weight, Min Variance, Max Sharpe (tangency).
    """
    import plotly.graph_objects as _go
    from services.optimizer import optimize, efficient_frontier
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    st.markdown(
        f'<div class="sec-hdr" style="margin-top:20px">'
        f'{"Tối ưu danh mục — Markowitz Mean-Variance (1952)" if not is_en else "Portfolio Optimization — Markowitz Mean-Variance (1952)"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"Annualized 252 phiên · Long-only · Sum(w)=1" if not is_en else "Annualized 252 bars · Long-only · Sum(w)=1"}'
        f'</span></div>',
        unsafe_allow_html=True)

    # Ghép returns DataFrame
    rets = pd.DataFrame({tk: all_data[tk]['Return'] for tk in sel}).dropna()
    if len(rets) < 60:
        st.warning('Cần ≥ 60 phiên có đủ dữ liệu cho mọi mã.' if not is_en
                    else 'Need ≥ 60 bars of overlapping data.')
        return

    try:
        opt = optimize(rets)
    except Exception as e:
        st.error(f'Lỗi optimizer: {e}')
        return

    # 3 card chiến lược
    cards_html = ''
    palette = {'equal_weight': '#94A3B8',
                'min_variance': '#0F766E',
                'max_sharpe':   '#A855F7'}
    for key in ('equal_weight', 'min_variance', 'max_sharpe'):
        p = opt[key]
        col = palette[key]
        weights_html = ''
        for tk, w in zip(opt['tickers'], p['weights']):
            if w > 0.005:
                pct = w * 100
                bar_w = max(2.0, pct)
                weights_html += (
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;margin-top:6px;font-size:11.5px">'
                    f'<span style="font-weight:700;color:{_T["accent"]}">{tk}</span>'
                    f'<span style="color:{_T["text_secondary"]}">{pct:.1f}%</span>'
                    f'</div>'
                    f'<div style="height:5px;background:{_T["bg_elevated"]};'
                    f'border-radius:999px;overflow:hidden">'
                    f'<div style="height:100%;width:{bar_w}%;background:{col};'
                    f'border-radius:999px"></div></div>')
        # Sharpe có thể NaN → tính trước rồi nhúng (tránh ternary trong f-string concat)
        _shp_txt = (f'{p["sharpe"]:+.2f}' if p["sharpe"] == p["sharpe"] else 'N/A')
        cards_html += (
            f'<div style="flex:1;min-width:240px;background:{_T["bg_card"]};'
            f'border:1px solid {_T["border"]};border-top:4px solid {col};'
            f'border-radius:12px;padding:14px 16px">'
            f'<div style="font-size:11px;color:{_T["text_muted"]};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.7px">'
            f'{p["name"]}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;'
            f'margin:8px 0 6px">'
            f'<div><div style="font-size:10px;color:{_T["text_muted"]}">'
            f'{"Lợi suất" if not is_en else "Return"} (ann.)</div>'
            f'<div style="font-size:15px;font-weight:800;color:{col}">'
            f'{p["expected_return"]*100:+.2f}%</div></div>'
            f'<div><div style="font-size:10px;color:{_T["text_muted"]}">'
            f'{"Biến động" if not is_en else "Volatility"} (ann.)</div>'
            f'<div style="font-size:15px;font-weight:800;color:{col}">'
            f'{p["volatility"]*100:.2f}%</div></div>'
            f'<div><div style="font-size:10px;color:{_T["text_muted"]}">Sharpe</div>'
            f'<div style="font-size:15px;font-weight:800;color:{col}">'
            f'{_shp_txt}</div></div>'
            f'</div>'
            f'<div style="border-top:1px solid {_T["divider"]};margin-top:6px;'
            f'padding-top:4px">{weights_html}</div></div>')

    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px">{cards_html}</div>',
        unsafe_allow_html=True)

    # ── Biên hiệu quả (efficient frontier) ─────────────────────────────
    st.markdown(
        f'<div class="sec-hdr" style="margin-top:16px">'
        f'{"Biên hiệu quả (Efficient Frontier)" if not is_en else "Efficient Frontier"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"Mỗi điểm = trọng số tối ưu giảm thiểu σ với mức lợi suất kỳ vọng cho trước" if not is_en else "Each point = optimal weights minimizing σ given target return"}'
        f'</span></div>',
        unsafe_allow_html=True)

    try:
        ef = efficient_frontier(rets, n_points=30)
    except Exception as e:
        st.caption(f'Lỗi frontier: {e}')
        return
    if not ef['points']:
        st.caption('Không tính được biên hiệu quả.' if not is_en
                    else 'Frontier could not be computed.')
        return

    # Chart
    fig = _go.Figure()
    fr_vol = [p['volatility'] * 100 for p in ef['points']]
    fr_ret = [p['expected_return'] * 100 for p in ef['points']]
    fig.add_trace(_go.Scatter(
        x=fr_vol, y=fr_ret, mode='lines+markers',
        line=dict(color='#0F766E', width=2.4),
        marker=dict(size=6, color='#0F766E', line=dict(color='#fff', width=1)),
        name=('Biên hiệu quả' if not is_en else 'Efficient Frontier'),
        hovertemplate='σ %{x:.2f}%<br>R %{y:+.2f}%<extra></extra>'))

    # Plot 3 portfolio đặc biệt + từng mã riêng
    for key, color, label_vi, label_en, sym in [
        ('equal_weight', '#94A3B8', 'Cân bằng', 'Equal', 'square'),
        ('min_variance', '#0F766E', 'Min Var', 'Min Var', 'diamond'),
        ('max_sharpe',   '#A855F7', 'Max Sharpe', 'Max Sharpe', 'star'),
    ]:
        p = opt[key]
        fig.add_trace(_go.Scatter(
            x=[p['volatility'] * 100], y=[p['expected_return'] * 100],
            mode='markers+text',
            marker=dict(size=14, color=color, symbol=sym,
                         line=dict(color='#fff', width=2)),
            text=[label_en if is_en else label_vi],
            textposition='top center',
            textfont=dict(size=10, color=color),
            name=label_en if is_en else label_vi,
            hovertemplate=f'<b>{p["name"]}</b><br>σ %{{x:.2f}}%<br>R %{{y:+.2f}}%<extra></extra>'))

    # Plot từng mã
    mu_arr = opt['mu_annual']
    cov_arr = np.array(opt['cov_annual'])
    for i, tk in enumerate(opt['tickers']):
        fig.add_trace(_go.Scatter(
            x=[float(np.sqrt(max(cov_arr[i, i], 0.0))) * 100],
            y=[mu_arr[i] * 100],
            mode='markers+text',
            marker=dict(size=10, color='#F59E0B', symbol='circle-open',
                         line=dict(color='#F59E0B', width=2)),
            text=[tk], textposition='bottom right',
            textfont=dict(size=10, color=_T['text_muted']),
            showlegend=False,
            hovertemplate=f'<b>{tk}</b><br>σ %{{x:.2f}}%<br>R %{{y:+.2f}}%<extra></extra>'))

    fig.update_layout(
        height=400, margin=dict(l=60, r=30, t=10, b=50),
        paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
        font=dict(family='Inter', size=11, color=_T['text_primary']),
        xaxis_title=('Biến động hoá năm σ (%)' if not is_en else 'Annualized volatility σ (%)'),
        yaxis_title=('Lợi suất hoá năm μ (%)' if not is_en else 'Annualized return μ (%)'),
        legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center',
                     bgcolor='rgba(0,0,0,0)'),
        hovermode='closest')
    _plotly_axes_style(fig, _T)
    st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    st.caption(
        ('Markowitz (1952) chứng minh: với cùng mức rủi ro σ, portfolio nằm trên biên hiệu quả cho lợi suất kỳ vọng cao nhất; với cùng lợi suất, biên hiệu quả cho rủi ro thấp nhất. Điểm Max Sharpe = portfolio tangency tiếp xúc với đường thị trường vốn (Capital Market Line) — cân bằng tốt nhất giữa lợi suất và rủi ro.'
         if not is_en else
         'Markowitz (1952) shows: for the same risk σ, portfolios on the efficient frontier yield the highest expected return; for the same return, the frontier has the lowest risk. Max Sharpe = the tangency portfolio touching the Capital Market Line — optimal risk-adjusted return.'))



    # ── CAPM + PCA + Cointegration (Sprint B math additions) ───────────
    # Bug fix v51: _is_en_p chỉ tồn tại trong render(); ở đây là
    # _render_optimizer_section nên dùng param `is_en` của hàm này.
    _render_capm_section(sel, all_data, _T, is_en)
    _render_pca_section(sel, all_data, _T, is_en)
    _render_cointegration_section(sel, all_data, _T, is_en)


def _render_capm_section(sel, all_data, _T, is_en):
    """CAPM Beta + Alpha vs VN-Index (Sharpe 1964, Lintner 1965)."""
    import plotly.graph_objects as _go
    from services.capm import fetch_vnindex, capm_table
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    st.markdown(
        f'<div class="sec-hdr" style="margin-top:20px">'
        f'CAPM — Beta & Alpha vs VN-Index'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"Sharpe 1964, Lintner 1965 · OLS hồi quy excess returns" if not is_en else "Sharpe 1964, Lintner 1965 · OLS on excess returns"}'
        f'</span></div>', unsafe_allow_html=True)

    # rf input (annual %)
    rf_pct = st.slider(
        ('Lãi suất phi rủi ro (%/năm) — mặc định 4.7% lãi gửi 12 tháng SBV'
         if not is_en else
         'Risk-free rate (%/year) — default 4.7% SBV 12m deposit'),
        min_value=0.0, max_value=10.0, value=4.7, step=0.1, key='_capm_rf')

    with st.spinner('Đang tải VN-Index...' if not is_en else 'Loading VN-Index...'):
        try:
            vn = fetch_vnindex()
        except Exception as e:
            st.warning(
                f'{"Không tải được VN-Index" if not is_en else "Could not load VN-Index"}: {e}')
            return

    rows = capm_table(all_data, vn, rf_annual_pct=float(rf_pct))
    if not rows:
        st.info('Không có dữ liệu CAPM.' if not is_en else 'No CAPM data.')
        return

    # Bảng beta/alpha
    hdr = (['Mã', 'β (Beta)', 'α/năm (%)', 'R²', 't-stat β', 'p-value', 'n']
            if not is_en else
            ['Ticker', 'β (Beta)', 'α/year (%)', 'R²', 't-stat β', 'p-value', 'n'])
    rows_html = ''
    for r in rows:
        b = r.get('beta')
        a = r.get('alpha_annual_pct')
        # NaN/None check — error rows ("thiếu dữ liệu") render colspan muted,
        # KHÔNG render +nan% bằng đỏ (looks like real underperformer).
        bad = (b is None or b != b or a is None or a != a)
        if bad:
            _err_msg = (r.get('error') or ('thiếu dữ liệu' if not is_en else 'missing data'))
            rows_html += (
                f'<tr style="border-top:1px solid {_T["divider"]};'
                f'color:{_T["text_muted"]}">'
                f'<td style="padding:8px 12px;font-weight:700;color:{_T["accent"]}">{r["ticker"]}</td>'
                f'<td colspan="6" style="padding:8px 12px;font-style:italic">{_err_msg}</td>'
                f'</tr>')
            continue
        b_col = ('#0F766E' if b < 1 else ('#A855F7' if b < 1.5 else '#DC2626'))
        a_col = '#0F766E' if a > 0 else '#DC2626'
        rows_html += (
            f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
            f'<td style="padding:8px 12px;font-weight:700;color:{_T["accent"]}">{r["ticker"]}</td>'
            f'<td style="padding:8px 12px;color:{b_col};font-weight:700">{b:.3f}</td>'
            f'<td style="padding:8px 12px;color:{a_col};font-weight:700">{a:+.2f}%</td>'
            f'<td style="padding:8px 12px">{r["r_squared"]:.3f}</td>'
            f'<td style="padding:8px 12px">{r["t_beta"]:.2f}</td>'
            f'<td style="padding:8px 12px">{r["p_beta"]:.4f}</td>'
            f'<td style="padding:8px 12px">{r["n_obs"]}</td>'
            f'</tr>')
    th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in hdr)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    # SML chart: β trục X, lợi suất kỳ vọng trục Y
    # Lọc NaN beta trước — `max(...) * 1.2` trên all-NaN → NaN axis crash.
    _good = [r for r in rows
             if r.get('beta') is not None and r.get('beta') == r.get('beta')]
    if len(_good) < 2:
        st.caption(
            ('Không đủ mã có β hợp lệ để vẽ SML (cần ≥ 2 mã đủ data overlap).'
             if not is_en else
             'Not enough tickers with valid β to draw SML (need ≥ 2 with sufficient overlap).'))
    elif len(_good) >= 2:
        fig = _go.Figure()
        rm_excess_daily = (vn['Return'].dropna().mean() - rf_pct/100/252)
        rm_excess_annual = rm_excess_daily * 252 * 100
        beta_range = [0, max(r['beta'] for r in _good) * 1.2]
        sml_x = beta_range
        sml_y = [rf_pct + b * rm_excess_annual for b in beta_range]
        fig.add_trace(_go.Scatter(
            x=sml_x, y=sml_y, mode='lines',
            line=dict(color=_T['text_muted'], width=2, dash='dash'),
            name=('Security Market Line' if is_en else 'Đường thị trường (SML)'),
            hovertemplate='SML: β=%{x:.2f}, E[R]=%{y:.2f}%<extra></extra>'))
        for r in _good:
            er_annual = (r['alpha'] + r['beta'] * rm_excess_daily) * 252 * 100 + rf_pct
            fig.add_trace(_go.Scatter(
                x=[r['beta']], y=[er_annual],
                mode='markers+text',
                marker=dict(size=14, color='#0F766E' if r['alpha_annual_pct'] > 0 else '#DC2626',
                             line=dict(color='#fff', width=2)),
                text=[r['ticker']], textposition='top center',
                textfont=dict(size=11, color=_T['text_primary']),
                showlegend=False,
                hovertemplate=f'<b>{r["ticker"]}</b><br>β=%{{x:.3f}}<br>E[R]/{ "y" if is_en else "năm"}=%{{y:.2f}}%<extra></extra>'))
        fig.update_layout(
            height=360, margin=dict(l=60, r=30, t=10, b=50),
            paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
            font=dict(family='Inter', size=11, color=_T['text_primary']),
            xaxis_title='β (Beta)',
            yaxis_title=('Lợi suất kỳ vọng năm (%)' if not is_en else 'Expected annual return (%)'),
            hovermode='closest')
        _plotly_axes_style(fig, _T)
        st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    st.caption(
        ('<b>β > 1</b>: cổ phiếu nhạy hơn thị trường (volatile). <b>β < 1</b>: defensive. '
         '<b>α > 0</b>: vượt CAPM expectation (outperform thị trường sau khi điều chỉnh rủi ro). '
         'Mã NẰM TRÊN đường SML = outperform; NẰM DƯỚI = underperform.'
         if not is_en else
         '<b>β > 1</b>: more volatile than market. <b>β < 1</b>: defensive. '
         '<b>α > 0</b>: outperforms CAPM (risk-adjusted alpha). '
         'Tickers ABOVE SML = outperform; BELOW = underperform.'),
        unsafe_allow_html=True)


def _render_pca_section(sel, all_data, _T, is_en):
    """PCA decomposition + biplot (Hotelling 1933, Jolliffe 2002)."""
    import plotly.graph_objects as _go
    from services.pca import pca_decompose
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    st.markdown(
        f'<div class="sec-hdr" style="margin-top:24px">'
        f'{"Phân tích Thành phần Chính (PCA)" if not is_en else "Principal Component Analysis (PCA)"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"Hotelling 1933 · eigendecomp ma trận tương quan" if not is_en else "Hotelling 1933 · correlation matrix eigendecomposition"}'
        f'</span></div>', unsafe_allow_html=True)

    rets = pd.DataFrame({tk: all_data[tk]['Return'] for tk in sel}).dropna()
    if len(rets) < 30 or rets.shape[1] < 2:
        st.info('Cần ≥ 30 phiên và ≥ 2 mã.' if not is_en
                else 'Need ≥ 30 sessions and ≥ 2 tickers.')
        return

    try:
        pca = pca_decompose(rets)
    except Exception as e:
        st.warning(f'{"PCA lỗi" if not is_en else "PCA error"}: {e}'); return

    col_a, col_b = st.columns(2)
    with col_a:
        ev = pca['var_explained']
        cv = pca['cum_var_explained']
        x = [f'PC{i+1}' for i in range(len(ev))]
        fig_scree = _go.Figure()
        fig_scree.add_trace(_go.Bar(
            x=x, y=[e*100 for e in ev],
            marker=dict(color='#0F766E'),
            name=('Var explained (%)' if is_en else 'Phương sai (%)'),
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'))
        fig_scree.add_trace(_go.Scatter(
            x=x, y=[c*100 for c in cv], mode='lines+markers',
            line=dict(color='#A855F7', width=2.5),
            marker=dict(size=8, color='#A855F7'),
            name=('Cumulative (%)' if is_en else 'Tích lũy (%)'),
            yaxis='y2',
            hovertemplate='Cum: %{y:.1f}%<extra></extra>'))
        fig_scree.update_layout(
            height=300, margin=dict(l=50, r=50, t=30, b=40),
            paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
            font=dict(family='Inter', size=11, color=_T['text_primary']),
            title=dict(text=('Scree plot' if is_en else 'Biểu đồ Scree'),
                        font=dict(size=12, color=_T['text_primary'])),
            yaxis=dict(title='%'),
            yaxis2=dict(title='Cum %', overlaying='y', side='right'),
            legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center',
                         bgcolor='rgba(0,0,0,0)'))
        _plotly_axes_style(fig_scree, _T)
        st.plotly_chart(fig_scree, use_container_width=True, config=_PLOTLY_CONFIG)

    with col_b:
        loadings = pca['pc1_pc2_loadings']
        fig_bp = _go.Figure()
        for ld in loadings:
            fig_bp.add_trace(_go.Scatter(
                x=[0, ld['loading_pc1']], y=[0, ld['loading_pc2']],
                mode='lines', line=dict(color='#94A3B8', width=1.5),
                showlegend=False, hoverinfo='skip'))
            fig_bp.add_trace(_go.Scatter(
                x=[ld['loading_pc1']], y=[ld['loading_pc2']],
                mode='markers+text',
                marker=dict(size=12, color='#0F766E',
                             line=dict(color='#fff', width=2)),
                text=[ld['ticker']], textposition='top right',
                textfont=dict(size=11, color=_T['text_primary']),
                showlegend=False,
                hovertemplate=f'<b>{ld["ticker"]}</b><br>PC1=%{{x:.3f}}<br>PC2=%{{y:.3f}}<extra></extra>'))
        fig_bp.update_layout(
            height=300, margin=dict(l=50, r=30, t=30, b=40),
            paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
            font=dict(family='Inter', size=11, color=_T['text_primary']),
            title=dict(text=('PC1 vs PC2 biplot' if is_en else 'Biplot PC1 vs PC2'),
                        font=dict(size=12, color=_T['text_primary'])),
            xaxis_title=f'PC1 ({ev[0]*100:.1f}%)' if len(ev) >= 1 else 'PC1',
            yaxis_title=f'PC2 ({ev[1]*100:.1f}%)' if len(ev) >= 2 else 'PC2',
            hovermode='closest')
        _plotly_axes_style(fig_bp, _T)
        st.plotly_chart(fig_bp, use_container_width=True, config=_PLOTLY_CONFIG)

    pc1_var = pca['var_explained'][0] * 100 if pca['var_explained'] else 0
    st.caption(
        (f'<b>PC1</b> giải thích <b>{pc1_var:.1f}%</b> phương sai — thường là "market factor" '
         '(yếu tố thị trường chung mà toàn bộ rổ mã chia sẻ). PC2/PC3 có thể là sector / size / momentum factor.'
         if not is_en else
         f'<b>PC1</b> explains <b>{pc1_var:.1f}%</b> of variance — typically the "market factor".'),
        unsafe_allow_html=True)


def _render_cointegration_section(sel, all_data, _T, is_en):
    """Engle-Granger cointegration test (Engle-Granger 1987 — Nobel 2003)."""
    import plotly.graph_objects as _go
    from services.cointegration import pair_matrix, spread_zscore
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    st.markdown(
        f'<div class="sec-hdr" style="margin-top:24px">'
        f'{"Đồng tích hợp (Cointegration) — Engle-Granger" if not is_en else "Cointegration — Engle-Granger"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'Engle-Granger 1987 (Nobel 2003) · pairs-trading framework'
        f'</span></div>', unsafe_allow_html=True)

    prices = pd.DataFrame({tk: all_data[tk]['Close'] for tk in sel}).dropna()
    if prices.shape[1] < 2 or len(prices) < 60:
        st.info('Cần ≥ 2 mã và ≥ 60 phiên overlap.' if not is_en
                else 'Need ≥ 2 tickers and ≥ 60 overlapping sessions.')
        return

    with st.spinner('Đang test cointegration...' if not is_en else 'Testing cointegration...'):
        try:
            pm = pair_matrix(prices)
        except Exception as e:
            st.warning(f'{"Lỗi test cointegration" if not is_en else "Cointegration test error"}: {e}')
            return

    pairs = pm['pairs_significant']
    n_coint = sum(1 for p in pairs if p['is_cointegrated'])
    st.markdown(
        f'<div style="font-size:13px;color:{_T["text_secondary"]};margin-bottom:8px">'
        f'{"Tìm được" if not is_en else "Found"} <b style="color:{_T["accent"]}">{n_coint}</b> '
        f'{"cặp đồng tích hợp (p < 0.05) trong tổng" if not is_en else "cointegrated pairs (p < 0.05) out of"} '
        f'<b>{len(pairs)}</b> {"cặp." if not is_en else "pairs."}</div>',
        unsafe_allow_html=True)

    hdr = (['Cặp', 'p-value', 'β (hedge)', 'z hiện tại', 'Đồng tích hợp?']
           if not is_en else
           ['Pair', 'p-value', 'β (hedge)', 'Current z', 'Cointegrated?'])
    rows_html = ''
    for p in pairs[:12]:
        z = p.get('current_z', 0) or 0
        z_col = '#DC2626' if abs(z) > 2 else ('#F59E0B' if abs(z) > 1 else _T['text_secondary'])
        ci_html = ('<span style="color:#0F766E;font-weight:800">✓</span>' if p['is_cointegrated']
                    else '<span style="color:#94A3B8">—</span>')
        rows_html += (
            f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
            f'<td style="padding:8px 12px;font-weight:700;color:{_T["accent"]}">{p["a"]} ↔ {p["b"]}</td>'
            f'<td style="padding:8px 12px">{p["p_value"]:.4f}</td>'
            f'<td style="padding:8px 12px">{p["beta"]:.3f}</td>'
            f'<td style="padding:8px 12px;color:{z_col};font-weight:700">{z:+.2f}σ</td>'
            f'<td style="padding:8px 12px;text-align:center">{ci_html}</td>'
            f'</tr>')
    th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in hdr)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    if pairs and pairs[0]['is_cointegrated']:
        best = pairs[0]
        sp = spread_zscore(prices[best['a']].values, prices[best['b']].values,
                            beta=best['beta'])
        z = sp['z']
        if len(z) > 0:
            fig = _go.Figure()
            fig.add_trace(_go.Scatter(
                x=list(range(len(z))), y=z, mode='lines',
                line=dict(color='#A855F7', width=1.6),
                name=f'z-score spread {best["a"]} − {best["beta"]:.2f}×{best["b"]}',
                hovertemplate='z=%{y:+.2f}σ<extra></extra>'))
            for level, lbl, color in [(2, '+2σ', '#DC2626'), (-2, '−2σ', '#DC2626'),
                                        (0, 'mean', _T['text_muted'])]:
                fig.add_hline(y=level, line=dict(color=color, width=1, dash='dash'))
            fig.update_layout(
                height=280, margin=dict(l=50, r=30, t=10, b=40),
                paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
                font=dict(family='Inter', size=11, color=_T['text_primary']),
                xaxis_title='phiên', yaxis_title='z-score (σ)',
                showlegend=True,
                legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center',
                             bgcolor='rgba(0,0,0,0)'))
            _plotly_axes_style(fig, _T)
            st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    st.caption(
        ('<b>p-value < 0.05</b>: hai chuỗi giá đồng tích hợp — spread A − β·B '
         'mean-reverting. <b>Lưu ý</b>: HOSE không cho phép bán khống, cặp này '
         'chỉ dùng để hiểu mối tương quan dài hạn.'
         if not is_en else
         '<b>p-value < 0.05</b>: the two price series are cointegrated — '
         'spread A − β·B is mean-reverting. <b>Note</b>: HOSE prohibits '
         'short-selling; this pair is for long-term correlation insight only.'),
        unsafe_allow_html=True)

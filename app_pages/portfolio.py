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
            _ret_ytd[_tk] = float(_d['Return'].sum())
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

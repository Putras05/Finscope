import streamlit as st
import numpy as np

import plotly.graph_objects as go

from core.i18n import t
from core.constants import ticker_sector, ticker_desc
from data.metrics import calc_metrics
from charts.price import chart_price_history_plotly
from charts.comparison import chart_test_result_plotly
from charts.arima_diag import chart_fan_ci, chart_acf_pacf, chart_residual_qq
from charts.base import _PLOTLY_CONFIG


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{t("analysis.title")} — {ticker}</h1>'
        f'<p>{ticker_sector(ticker)} &nbsp;·&nbsp; {ticker_desc(ticker)}</p>'
        f'</div>', unsafe_allow_html=True)

    import datetime as _dt
    _last_date_a = df['Ngay'].iloc[-1]
    if isinstance(_last_date_a, str):
        _last_date_a = _dt.datetime.strptime(_last_date_a, '%Y-%m-%d').date()
    _next_date_a = _last_date_a
    while True:
        _next_date_a += _dt.timedelta(days=1)
        if _next_date_a.weekday() < 5:
            break
    if ar_order == 1:
        _src_desc = f'{t("dash.based_on_close")} {_last_date_a}'
    else:
        _first_date_a = df['Ngay'].iloc[-ar_order]
        if isinstance(_first_date_a, str):
            _first_date_a = _dt.datetime.strptime(_first_date_a, '%Y-%m-%d').date()
        _src_desc = t('dash.based_on_close_range',
                      p=ar_order, d0=_first_date_a, d1=_last_date_a)
    _next_lbl = (
        f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};'
        f'margin-left:6px">'
        f'· {t("dash.forecast_for")} <b style="color:{_T["accent"]}">{_next_date_a.strftime("%Y-%m-%d")}</b> '
        f'({_src_desc})</span>'
    )

    # 8 mô hình — các mô hình nâng cao tính từ cache (đã warm ở topbar/app)
    from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
    from models.ml import run_gbr
    _adv_specs = [
        ('SARIMA', run_sarima), ('Holt-Winters', run_ets),
        ('GARCH', run_garch), ('SARIMAX', run_sarimax),
        ('Gradient Boosting', run_gbr),
    ]
    _adv_res = {}
    for _nm, _fn in _adv_specs:
        try:
            _adv_res[_nm] = _fn(ticker, train_ratio, p=ar_order,
                                date_from=date_from, date_to=date_to)
        except Exception as _e:
            _adv_res[_nm] = None

    # ── Dựng FinScope Ensemble từ 8 mô hình đã tính (trọng số ∝ 1/MAPE) ──
    def _mape_of(_res):
        if _res is None:
            return float('nan')
        _y = np.asarray(_res.get('yte', []), float); _p = np.asarray(_res.get('pte', []), float)
        _f = np.isfinite(_y) & np.isfinite(_p)
        if _f.sum() < 3:
            return float('nan')
        return calc_metrics(_y[_f], _p[_f], k=2)['MAPE']

    _ens_members = [
        {'name': f'AR({ar_order})', 'res': r1, 'mape': m1['MAPE']},
        {'name': 'MLR', 'res': r2, 'mape': m2['MAPE']},
        {'name': 'ARIMA', 'res': r3, 'mape': m3['MAPE']},
    ]
    for _nm in ('SARIMA', 'Holt-Winters', 'GARCH', 'SARIMAX', 'Gradient Boosting'):
        _rr = _adv_res.get(_nm)
        if _rr is not None:
            _ens_members.append({'name': _nm, 'res': _rr, 'mape': _mape_of(_rr)})
    try:
        from models.ensemble import build_ensemble
        _ens_res = build_ensemble(_ens_members, df)
    except Exception:
        _ens_res = None

    (tab_ar1, tab_mlr, tab_cart,
     tab_sar, tab_ets, tab_garch, tab_sarx, tab_gbr,
     tab_ens) = st.tabs([
        f'  AR({ar_order})  ', '  MLR  ', '  ARIMA  ',
        '  SARIMA  ', '  Holt-Winters  ', '  GARCH  ', '  SARIMAX  ',
        '  Gradient Boosting  ', '  FinScope Ensemble  '])

    with tab_ar1:
        m_tr1 = calc_metrics(r1['ytr'], r1['ptr'])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t('metric.mape_train'), f"{m_tr1['MAPE']:.2f}%")
        c2.metric(t('metric.mape_test'),  f"{m1['MAPE']:.2f}%")
        c3.metric("RMSE",                 f"{m1['RMSE']:.4f}")
        c4.metric("MAE",                  f"{m1['MAE']:.4f}")
        c5.metric("R²adj",                f"{m1['R2adj']:.4f}")
        st.markdown(
            f'<div class="info-box">'
            + t('analysis.train_range_info',
                d0=str(r1['dates_tr'][0]), d1=str(r1['dates_tr'][-1]), n=r1['nt'],
                t0=str(r1['dates_te'][0]), t1=str(r1['dates_te'][-1]), m=len(r1['yte']))
            + _next_lbl
            + f'</div>', unsafe_allow_html=True)
        with st.expander(t('analysis.equation_ar1')):
            _p_a = r1.get('p', 1)
            _h_a = r1.get('h', 1)
            _coefs_a = r1.get('coefs', [r1.get('rho', 0)])
            _c_a = r1.get('c', r1.get('intercept', 0))

            _ar_terms = []
            for _k, _rho_k in enumerate(_coefs_a):
                _sub = 't' if _k == 0 else f't-{_k}'
                if _k == 0:
                    _ar_terms.append(f'{float(_rho_k):.6f} \\cdot Y_{{{_sub}}}')
                else:
                    _sign = '+' if _rho_k >= 0 else '-'
                    _ar_terms.append(f'{_sign} {abs(float(_rho_k)):.6f} \\cdot Y_{{{_sub}}}')
            _ar_eq_body = ' '.join(_ar_terms)
            _c_sign = '+' if _c_a >= 0 else '-'
            _ar_eq = f'$$\\hat{{Y}}_{{t+{_h_a}}} = {_ar_eq_body} {_c_sign} {abs(float(_c_a)):.6f}$$'

            _rows = [f'| $\\hat{{c}}$ | {float(_c_a):.6f} | {t("ar1.intercept")} |']
            _is_en_tbl = st.session_state.get('lang', 'VI') == 'EN'
            _coef_meaning = 'Order' if _is_en_tbl else 'Hệ số bậc'
            for _k, _rho_k in enumerate(_coefs_a):
                _lag_label = 't' if _k == 0 else f't-{_k}'
                _rows.append(f'| $\\hat{{\\rho}}_{{{_k+1}}}$ ($Y_{{{_lag_label}}}$) | {float(_rho_k):.6f} | {_coef_meaning} {_k+1} |')
            _coef_table = '\n'.join(_rows)

            st.markdown(f"""
{t('ar1.model_header')} — AR({_p_a}, h={_h_a})

{_ar_eq}

| {t('ar1.param')} | {t('ar1.value')} | {t('ar1.meaning')} |
|---------|---------|---------|
{_coef_table}

- $\\hat{{\\rho}}_1 \\approx 1$ → **{t('ar1.unit_root')}**
- {t('ar1.tomorrow')}
            """)
        try:
            _cfg = {**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_AR1_history'}}
            fig_h1 = chart_price_history_plotly(r1, ticker, date_from, date_to, T=_T)
            st.plotly_chart(fig_h1, use_container_width=True, config=_cfg)
            fig_t1 = chart_test_result_plotly(r1, ticker, f'AR({ar_order})', m1, T=_T)
            st.plotly_chart(fig_t1, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_AR1_forecast'}})
        except Exception as _e:
            st.error(t('error.ar1_chart', e=_e))

    with tab_mlr:
        _p_m = r2.get('p', 1)
        m_tr2 = calc_metrics(r2['ytr'], r2['ptr'], k=3 * _p_m)
        b0 = r2['intercept']
        _mlr_coef = r2['coef']
        b1 = float(_mlr_coef[0])
        b2 = float(_mlr_coef[_p_m])
        b3 = float(_mlr_coef[2 * _p_m])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t('metric.mape_train'), f"{m_tr2['MAPE']:.2f}%")
        c2.metric(t('metric.mape_test'),  f"{m2['MAPE']:.2f}%")
        c3.metric("RMSE",                 f"{m2['RMSE']:.4f}")
        c4.metric("MAE",                  f"{m2['MAE']:.4f}")
        c5.metric("R²adj",                f"{m2['R2adj']:.4f}")
        st.markdown(
            f'<div class="info-box">'
            + t('analysis.train_range_info',
                d0=str(r2['dates_tr'][0]), d1=str(r2['dates_tr'][-1]), n=r2['nt'],
                t0=str(r2['dates_te'][0]), t1=str(r2['dates_te'][-1]), m=len(r2['yte']))
            + _next_lbl
            + f'</div>', unsafe_allow_html=True)
        with st.expander(t('analysis.equation_mlr')):
            _h_m = r2.get('h', 1)
            if _p_m == 1:
                _b2_exp   = int(f'{b2:.2e}'.split('e')[1]) if b2 != 0 else 0
                _b2_mant  = b2 / (10 ** _b2_exp) if b2 != 0 else 0
                _b2_latex = (f'{_b2_mant:.3f} \\times 10^{{{_b2_exp}}}'
                             if abs(b2) < 1e-3 or abs(b2) > 1e4 else f'{b2:.6f}')
                _mlr_eq = (
                    f'$$\\hat{{Y}}_{{t+{_h_m}}} = {b0:.4f}'
                    f' + {b1:.6f}\\cdot Y_{{t}}'
                    f' + {_b2_latex}\\cdot V_{{t}}'
                    f' + {b3:.4f}\\cdot (H_{{t}}-L_{{t}})$$'
                )
                _mlr_rows = [
                    f'| $\\hat{{\\beta}}_0$ | {b0:.4f} | {t("mlr.intercept")} |',
                    f'| $\\hat{{\\beta}}_{{Y,1}}$ ($Y_{{t}}$) | {b1:.6f} | {t("mlr.prev_price")} |',
                    f'| $\\hat{{\\beta}}_{{V,1}}$ ($V_{{t}}$) | ${_b2_latex}$ | {t("mlr.vol_pressure")} |',
                    f'| $\\hat{{\\beta}}_{{R,1}}$ ($(H-L)_{{t}}$) | {b3:.4f} | {t("mlr.range_vol")} |',
                ]
            else:
                _mlr_eq = (
                    f'$$\\hat{{Y}}_{{t+{_h_m}}} = \\hat{{\\beta}}_0'
                    f' + \\sum_{{j=1}}^{{{_p_m}}} \\hat{{\\beta}}_{{Y,j}}\\cdot Y_{{t-j+1}}'
                    f' + \\sum_{{j=1}}^{{{_p_m}}} \\hat{{\\beta}}_{{V,j}}\\cdot V_{{t-j+1}}'
                    f' + \\sum_{{j=1}}^{{{_p_m}}} \\hat{{\\beta}}_{{R,j}}\\cdot (H-L)_{{t-j+1}}$$'
                )
                _mlr_rows = [f'| $\\hat{{\\beta}}_0$ | {b0:.4f} | {t("mlr.intercept")} |']
                for _j in range(_p_m):
                    _lag_lbl = 't' if _j == 0 else f't-{_j}'
                    _cy = float(_mlr_coef[_j])
                    _cv = float(_mlr_coef[_p_m + _j])
                    _cr = float(_mlr_coef[2 * _p_m + _j])
                    _mlr_rows += [
                        f'| $\\hat{{\\beta}}_{{Y,{_j+1}}}$ ($Y_{{{_lag_lbl}}}$) | {_cy:.6f} | {t("mlr.prev_price")} lag {_j+1} |',
                        f'| $\\hat{{\\beta}}_{{V,{_j+1}}}$ ($V_{{{_lag_lbl}}}$) | {_cv:.4e} | {t("mlr.vol_pressure")} lag {_j+1} |',
                        f'| $\\hat{{\\beta}}_{{R,{_j+1}}}$ ($(H-L)_{{{_lag_lbl}}}$) | {_cr:.6f} | {t("mlr.range_vol")} lag {_j+1} |',
                    ]
            _mlr_table = '\n'.join(_mlr_rows)
            st.markdown(f"""
{t('mlr.model_header')} — MLR({_p_m}, h={_h_m})

{_mlr_eq}

| {t('mlr.coef')} | {t('ar1.value')} | {t('ar1.meaning')} |
|-------|---------|---------|
{_mlr_table}
            """)
        try:
            fig_h2 = chart_price_history_plotly(r2, ticker, date_from, date_to, T=_T)
            st.plotly_chart(fig_h2, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_MLR_history'}})
            fig_t2 = chart_test_result_plotly(r2, ticker, 'MLR', m2, T=_T)
            st.plotly_chart(fig_t2, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_MLR_forecast'}})
        except Exception as _e:
            st.error(t('error.mlr_chart', e=_e))

    with tab_cart:
        _is_en_ar = st.session_state.get('lang', 'VI') == 'EN'
        _order = r3.get('order', (0, 1, 0))
        _p3, _d3, _q3 = (list(_order) + [0, 0, 0])[:3]
        m_tr3 = calc_metrics(r3['ytr'], r3['ptr'])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t('metric.mape_train'), f"{m_tr3['MAPE']:.2f}%")
        c2.metric(t('metric.mape_test'),  f"{m3['MAPE']:.2f}%")
        c3.metric("RMSE",                 f"{m3['RMSE']:.4f}")
        c4.metric("MAE",                  f"{m3['MAE']:.4f}")
        c5.metric("R²adj",                f"{m3['R2adj']:.4f}")

        _np3 = r3['next_pred']
        _nlo = r3.get('next_lower', float('nan'))
        _nhi = r3.get('next_upper', float('nan'))
        st.markdown(
            f'<div class="info-box">'
            + t('arima.order_info', p=_p3, d=_d3, q=_q3)
            + f' &nbsp;·&nbsp; AIC=<b>{r3.get("aic", float("nan")):.1f}</b>'
            + f' &nbsp;·&nbsp; BIC=<b>{r3.get("bic", float("nan")):.1f}</b>'
            + f' &nbsp;·&nbsp; {t("arima.next_pred")}: <b>{_np3*1000:,.0f} đ</b>'
            + (f' &nbsp;·&nbsp; {t("arima.ci95")}: '
               f'<b>[{_nlo*1000:,.0f} – {_nhi*1000:,.0f}] đ</b>'
               if _nlo == _nlo else '')
            + _next_lbl
            + f'</div>', unsafe_allow_html=True)

        with st.expander(t('arima.config'), expanded=True):
            _cx = _T['bg_card']; _cxe = _T['bg_elevated']
            _cf = _T['text_primary']; _cfs = _T['text_secondary']
            _cb = _T['border'];  _ca = _T['accent']
            _lb = r3.get('ljungbox_p', float('nan'))
            if _lb == _lb:
                _lb_col = _T['success'] if _lb > 0.05 else _T['warning']
                _lb_note = (t('arima.ljungbox_ok') if _lb > 0.05
                            else t('arima.ljungbox_bad'))
                _lb_val = f'{_lb:.3f}'
            else:
                _lb_col = _cfs; _lb_note = ''; _lb_val = 'N/A'
            _obj_lbl = ('Mục tiêu dự báo:' if not _is_en_ar else 'Forecast objective:')
            _method_lbl = ('Phương pháp:' if not _is_en_ar else 'Method:')
            _method_txt = ('Ước lượng hợp lý cực đại (MLE); bậc (p,d,q) tự chọn '
                           'theo AIC, d xác định bằng kiểm định ADF.'
                           if not _is_en_ar else
                           'Maximum-likelihood estimation; (p,d,q) auto-selected '
                           'by AIC, d set via the ADF stationarity test.')
            _eng = r3.get('engine', 'statsmodels ARIMA')
            st.markdown(f"""
<div style="background:{_cx};color:{_cf};padding:4px 2px;font-size:13px;line-height:1.7">
<div style="font-weight:800;font-size:14px;color:{_ca};margin-bottom:8px">
  ARIMA(p, d, q) — Box &amp; Jenkins · {_eng}
</div>
<div style="margin-bottom:6px">
  <span style="color:{_cfs};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px">{_obj_lbl}</span><br>
  <div style="color:{_cf};padding:3px 0 3px 8px;font-size:13px;font-style:italic">
    &phi;(B)(1&minus;B)<sup>d</sup> Y<sub>t</sub> = &theta;(B) &epsilon;<sub>t</sub>
  </div>
</div>
<div style="margin-bottom:8px;color:{_cfs};font-size:12px">
  {_method_lbl} <b style="color:{_cf}">{_method_txt}</b>
</div>
<table style="width:100%;border-collapse:collapse;margin-bottom:8px;font-size:12px">
<thead><tr>
  <th style="background:{_cxe};color:{_cfs};padding:5px 10px;border:1px solid {_cb};text-align:left">{('Thành phần' if not _is_en_ar else 'Component')}</th>
  <th style="background:{_cxe};color:{_cfs};padding:5px 10px;border:1px solid {_cb};text-align:center">{t('ar1.value')}</th>
</tr></thead>
<tbody>
  <tr><td style="background:{_cx};color:{_cf};padding:5px 10px;border:1px solid {_cb}">p — {('bậc tự hồi quy (AR)' if not _is_en_ar else 'autoregressive order (AR)')}</td>
      <td style="background:{_cx};color:{_ca};padding:5px 10px;border:1px solid {_cb};text-align:center;font-weight:700">{_p3}</td></tr>
  <tr><td style="background:{_cxe};color:{_cf};padding:5px 10px;border:1px solid {_cb}">d — {('bậc sai phân (I)' if not _is_en_ar else 'differencing order (I)')}</td>
      <td style="background:{_cxe};color:{_ca};padding:5px 10px;border:1px solid {_cb};text-align:center;font-weight:700">{_d3}</td></tr>
  <tr><td style="background:{_cx};color:{_cf};padding:5px 10px;border:1px solid {_cb}">q — {('bậc trung bình trượt (MA)' if not _is_en_ar else 'moving-average order (MA)')}</td>
      <td style="background:{_cx};color:{_ca};padding:5px 10px;border:1px solid {_cb};text-align:center;font-weight:700">{_q3}</td></tr>
  <tr><td style="background:{_cxe};color:{_cf};padding:5px 10px;border:1px solid {_cb}">{t('arima.ljungbox')}</td>
      <td style="background:{_cxe};color:{_lb_col};padding:5px 10px;border:1px solid {_cb};text-align:center;font-weight:700">{_lb_val}</td></tr>
</tbody></table>
<div style="color:{_lb_col};font-size:11.5px">{_lb_note}</div>
</div>
""", unsafe_allow_html=True)

        try:
            fig_h3 = chart_price_history_plotly(r3, ticker, date_from, date_to, T=_T)
            st.plotly_chart(fig_h3, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_ARIMA_history'}})
            fig_t3 = chart_test_result_plotly(r3, ticker, 'ARIMA', m3, T=_T, show_scatter=False)
            st.plotly_chart(fig_t3, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_ARIMA_forecast'}})

            # ── Fan chart khoảng tin cậy ─────────────────────────────────
            st.markdown(
                f'<div class="sec-hdr" style="margin-top:18px">'
                + t('arima.fan_hdr', ticker=ticker) + '</div>',
                unsafe_allow_html=True)
            st.markdown(
                f'<div class="info-box" style="margin-bottom:12px">'
                + t('arima.fan_desc') + '</div>', unsafe_allow_html=True)
            fig_fan = chart_fan_ci(r3, ticker, T=_T,
                                   method_label=f'ARIMA({_p3},{_d3},{_q3})',
                                   is_en=_is_en_ar)
            st.plotly_chart(fig_fan, use_container_width=True, config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': f'{ticker}_ARIMA_fan_ci'}})

            # ── Chẩn đoán phần dư: ACF/PACF + residual/Q-Q ───────────────
            st.markdown(
                f'<div class="sec-hdr" style="margin-top:20px">'
                + t('arima.diag_hdr', ticker=ticker) + '</div>',
                unsafe_allow_html=True)
            st.markdown(
                f'<div class="info-box" style="margin-bottom:12px">'
                + t('arima.diag_desc') + '</div>', unsafe_allow_html=True)
            _resid = r3.get('resid')
            if _resid is not None and len(np.asarray(_resid)) > 10:
                try:
                    fig_ap = chart_acf_pacf(_resid, T=_T, is_en=_is_en_ar)
                    st.plotly_chart(fig_ap, use_container_width=True, config=_PLOTLY_CONFIG)
                    fig_rq = chart_residual_qq(_resid, T=_T, is_en=_is_en_ar)
                    st.plotly_chart(fig_rq, use_container_width=True, config=_PLOTLY_CONFIG)
                except Exception as _ed:
                    st.caption(f'⚠ {_ed}')
        except Exception as _e:
            st.error(t('error.arima_chart', e=_e))

    # ── 4 TAB MÔ HÌNH NÂNG CAO (SARIMA · Holt-Winters · GARCH · SARIMAX) ──
    with tab_sar:
        _render_adv_tab(_adv_res.get('SARIMA'), 'SARIMA', ticker, date_from, date_to, _T, _next_lbl)
    with tab_ets:
        _render_adv_tab(_adv_res.get('Holt-Winters'), 'Holt-Winters', ticker, date_from, date_to, _T, _next_lbl)
    with tab_garch:
        _render_adv_tab(_adv_res.get('GARCH'), 'GARCH', ticker, date_from, date_to, _T, _next_lbl)
    with tab_sarx:
        _render_adv_tab(_adv_res.get('SARIMAX'), 'SARIMAX', ticker, date_from, date_to, _T, _next_lbl)
    with tab_gbr:
        _render_adv_tab(_adv_res.get('Gradient Boosting'), 'Gradient Boosting', ticker, date_from, date_to, _T, _next_lbl)

    # ── TAB MÔ HÌNH KẾT HỢP (FinScope Ensemble) ─────────────────────────
    with tab_ens:
        _is_en_e = st.session_state.get('lang', 'VI') == 'EN'
        if _ens_res is None:
            st.warning('Cần ≥2 mô hình hợp lệ để dựng Ensemble.'
                       if not _is_en_e else 'Need ≥2 valid models to build the ensemble.')
        else:
            _render_adv_tab(_ens_res, 'FinScope Ensemble', ticker,
                            date_from, date_to, _T, _next_lbl)


def _render_adv_tab(res, label, ticker, date_from, date_to, _T, _next_lbl):
    """Render 1 tab mô hình nâng cao: metrics + tóm tắt + lịch sử giá + fan chart CI."""
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    if res is None or not res.get('ok', True):
        st.warning((res.get('summary') if res else None)
                   or ('Mô hình hiện không khả dụng.' if not is_en else 'Model unavailable.'))
        return
    yte = np.asarray(res['yte'], float); pte = np.asarray(res['pte'], float)
    fin = np.isfinite(pte) & np.isfinite(yte)
    if fin.sum() < 3:
        st.warning('Không đủ dữ liệu hợp lệ.' if not is_en else 'Not enough valid data.')
        return
    m = calc_metrics(yte[fin], pte[fin], k=2)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t('metric.mape_test'), f"{m['MAPE']:.2f}%")
    c2.metric("RMSE", f"{m['RMSE']:.4f}")
    c3.metric("MAE", f"{m['MAE']:.4f}")
    c4.metric("R²adj", f"{m['R2adj']:.4f}")
    _np = res.get('next_pred', float('nan'))
    c5.metric('Dự báo phiên tới' if not is_en else 'Next forecast',
              f"{_np*1000:,.0f} đ" if np.isfinite(_np) else 'N/A')
    _nlo = res.get('next_lower'); _nhi = res.get('next_upper')
    _ci_txt = (f' &nbsp;·&nbsp; {t("arima.ci95")}: '
               f'<b>[{_nlo*1000:,.0f} – {_nhi*1000:,.0f}] đ</b>'
               if (_nlo is not None and np.isfinite(_nlo)) else '')
    st.markdown(
        f'<div class="info-box"><b>{label}</b> · {res.get("summary", "")}'
        f' &nbsp;·&nbsp; engine: {res.get("engine", "")}{_ci_txt}{_next_lbl}</div>',
        unsafe_allow_html=True)
    _adv_equation(label, res, is_en)
    try:
        figh = chart_price_history_plotly(res, ticker, date_from, date_to, T=_T)
        st.plotly_chart(figh, use_container_width=True, config={
            **_PLOTLY_CONFIG, 'toImageButtonOptions': {
                **_PLOTLY_CONFIG['toImageButtonOptions'],
                'filename': f'{ticker}_{label}_history'}})
        figf = chart_fan_ci(res, ticker, T=_T, method_label=label, is_en=is_en)
        st.plotly_chart(figf, use_container_width=True, config={
            **_PLOTLY_CONFIG, 'toImageButtonOptions': {
                **_PLOTLY_CONFIG['toImageButtonOptions'],
                'filename': f'{ticker}_{label}_CI'}})
    except Exception as _e:
        st.error(f'Chart error: {_e}')


def _adv_equation(label, res, is_en):
    """Expander hiển thị công thức toán + bảng tham số ước lượng của mô hình nâng cao."""
    coef = res.get('coef', {}) or {}

    def _g(*keys, default=0.0):
        for k in keys:
            if k in coef:
                return coef[k]
        return default

    _title = 'Phương trình & tham số ước lượng' if not is_en else 'Equation & estimated parameters'
    with st.expander(_title, expanded=True):
        if label == 'SARIMA':
            _o = res.get('order', (0, 0, 0)); _so = res.get('seasonal_order', (0, 0, 0, 5))
            st.markdown(f"**SARIMA{_o}×{_so}** — "
                        + ('ARIMA có thành phần mùa vụ (chu kỳ s=5 phiên/tuần)'
                           if not is_en else 'seasonal ARIMA (period s=5 trading days)'))
            st.latex(r"\phi_p(B)\,\Phi_P(B^s)\,(1-B)^d(1-B^s)^D\,Y_t"
                     r"=\theta_q(B)\,\Theta_Q(B^s)\,\varepsilon_t")
        elif label.startswith('Holt'):
            st.markdown("**Holt-Winters — ETS(A, Ad, N)** — "
                        + ('san mũ có xu thế giảm dần (damped)'
                           if not is_en else 'exponential smoothing with damped trend'))
            st.latex(r"\ell_t=\alpha\,y_t+(1-\alpha)\,(\ell_{t-1}+\phi\,b_{t-1})")
            st.latex(r"b_t=\beta\,(\ell_t-\ell_{t-1})+(1-\beta)\,\phi\,b_{t-1}")
            st.latex(r"\hat{y}_{t+h}=\ell_t+\Big(\sum_{i=1}^{h}\phi^{\,i}\Big)\,b_t")
            _a = _g('smoothing_level'); _b = _g('smoothing_trend'); _ph = _g('damping_trend')
            st.caption(f"α (level) = {_a:.4f} · β (trend) = {_b:.4f} · φ (damping) = {_ph:.4f}")
        elif label == 'GARCH':
            st.markdown("**AR(1) mean + GARCH(1,1) variance** — "
                        + ('mô hình biến động có điều kiện'
                           if not is_en else 'conditional-volatility model'))
            st.latex(r"r_t=\mu+\varphi\,r_{t-1}+\varepsilon_t,\qquad \varepsilon_t=\sigma_t z_t")
            st.latex(r"\sigma_t^{2}=\omega+\alpha\,\varepsilon_{t-1}^{2}+\beta\,\sigma_{t-1}^{2}")
            _al = _g('alpha[1]'); _be = _g('beta[1]')
            st.caption(('Độ dai dẳng biến động α+β = ' if not is_en
                        else 'Volatility persistence α+β = ') + f"{_al + _be:.4f}"
                       + (' (gần 1 → biến động kéo dài)' if not is_en
                          else ' (near 1 → long-lasting volatility)'))
        elif label == 'SARIMAX':
            _o = res.get('order', (0, 0, 0))
            st.markdown(f"**SARIMAX{_o} + biến ngoại sinh** — "
                        + ('ARIMA kèm log(Volume) & Range (biên độ)'
                           if not is_en else 'ARIMA with log(Volume) & Range regressors'))
            st.latex(r"Y_t=\beta_1\log V_t+\beta_2\,(H_t-L_t)+\eta_t,\qquad"
                     r"\phi_p(B)(1-B)^d\,\eta_t=\theta_q(B)\,\varepsilon_t")
            _b1 = _g('x1'); _b2 = _g('x2')
            st.caption(f"β₁ (log Volume) = {_b1:.4f} · β₂ (Range) = {_b2:.4f}")
        elif label.startswith('Gradient'):
            st.markdown("**Gradient Boosting Regressor** — "
                        + ('học máy phi tuyến: cộng dồn nhiều cây quyết định nhỏ để '
                           'dự báo LỢI SUẤT phiên kế tiếp rồi quy về giá'
                           if not is_en else
                           'nonlinear ML: an additive ensemble of shallow trees '
                           'predicts next-bar RETURN, then maps to price'))
            st.latex(r"\hat{r}_{t+1}=\sum_{m=1}^{M}\nu\,h_m(\mathbf{x}_t),\qquad"
                     r"\hat{P}_{t+1}=P_t\,(1+\hat{r}_{t+1})")
            st.caption(res.get('params', '')
                       + (' · đặc trưng: Return, Volume_ratio, Range_ratio, '
                          'MA5/MA20 ratio, RSI14 (× p lag)' if not is_en else
                          ' · features: Return, Volume_ratio, Range_ratio, '
                          'MA5/MA20 ratio, RSI14 (× p lags)'))
        elif 'Ensemble' in label:
            st.markdown("**Forecast combination (Bates–Granger)** — "
                        + ('trung bình có trọng số NGHỊCH-MAPE: mô hình càng chính '
                           'xác → trọng số càng lớn → dự báo ổn định hơn'
                           if not is_en else
                           'inverse-MAPE weighted average: more accurate models get '
                           'larger weights → more robust forecast'))
            # v58.3 — fix: 2 raw-string nối → "\qquadw_i" (LaTeX không nhận lệnh
            # \qquadw_i) → render thô. Thêm space + dùng widehat cho rộng rãi.
            st.latex(r"\widehat{Y}_{t} \;=\; \sum_{i} w_{i}\,\widehat{Y}_{i,t},"
                     r"\qquad\qquad w_{i} \;=\; \frac{1 / (\mathrm{MAPE}_{i} + 0.1)}"
                     r"{\sum_{j} 1 / (\mathrm{MAPE}_{j} + 0.1)}")
            _w = res.get('weights', {}) or {}
            if _w:
                _wh = ('| Mô hình thành phần | Trọng số |\n|---|---|\n' if not is_en
                       else '| Member model | Weight |\n|---|---|\n')
                _wr = '\n'.join(f"| {k} | {v*100:.1f}% |"
                                for k, v in sorted(_w.items(), key=lambda kv: -kv[1]))
                st.markdown(_wh + _wr)
            st.caption((f"Gộp {res.get('n_members', '?')} mô hình." if not is_en
                        else f"Combines {res.get('n_members', '?')} models."))

        # Bảng tham số: ARIMA-họ dùng `coef`; GBR dùng `importances`.
        if coef:
            _hdr = ('| Tham số | Giá trị |\n|---|---|\n' if not is_en
                    else '| Parameter | Value |\n|---|---|\n')
            _rows = '\n'.join(f"| `{k}` | {float(v):.6f} |" for k, v in coef.items())
            st.markdown(_hdr + _rows)
        _imp = res.get('importances', {}) or {}
        if _imp and not coef:
            _ih = ('| Đặc trưng | Độ quan trọng |\n|---|---|\n' if not is_en
                   else '| Feature | Importance |\n|---|---|\n')
            _ir = '\n'.join(f"| `{k}` | {float(v)*100:.1f}% |"
                            for k, v in sorted(_imp.items(), key=lambda kv: -kv[1]))
            st.markdown(_ih + _ir)

        _aic = res.get('aic'); _bic = res.get('bic')
        if _aic is not None and np.isfinite(_aic):
            _bic_s = f"  ·  BIC = {_bic:.1f}" if (_bic is not None and np.isfinite(_bic)) else ''
            st.caption(f"AIC = {_aic:.1f}{_bic_s}")

"""Trang 'Mô hình Nâng cao' — bộ mô hình thống kê + chức năng Khoảng tin cậy.

Tập hợp 7 mô hình dự báo (AR, MLR, ARIMA + SARIMA, Holt-Winters/ETS, GARCH,
SARIMAX), so sánh dự báo phiên kế tiếp kèm khoảng tin cậy 80%/95%, vẽ fan chart
cho từng mô hình thống kê và biểu đồ biến động (volatility) của GARCH.
"""
import numpy as np
import streamlit as st

from core.i18n import t
from data.metrics import calc_metrics, _ci95
from charts.base import _PLOTLY_CONFIG
from charts.arima_diag import chart_fan_ci
from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
from models.deep import run_lstm


def _safe_metrics(res, k=2):
    yte = np.asarray(res['yte'], dtype=float)
    pte = np.asarray(res['pte'], dtype=float)
    fin = np.isfinite(pte) & np.isfinite(yte)
    if fin.sum() < 3:
        return dict(MAPE=float('nan'), RMSE=float('nan'),
                    MAE=float('nan'), R2adj=float('nan'))
    return calc_metrics(yte[fin], pte[fin], k=k)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'

    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Mô hình Thống kê Nâng cao" if not is_en else "Advanced Statistical Models"} — {ticker}</h1>'
        f'<p>{"Bộ 8 mô hình dự báo (gồm học sâu LSTM) & khoảng tin cậy 80%/95% cho phiên kế tiếp" if not is_en else "Eight forecasting models (incl. deep-learning LSTM) & 80%/95% confidence intervals"}</p>'
        f'</div>', unsafe_allow_html=True)

    _spin = ('Đang ước lượng SARIMA · Holt-Winters · GARCH · SARIMAX...'
             if not is_en else
             'Estimating SARIMA · Holt-Winters · GARCH · SARIMAX · Deep Learning...')
    with st.spinner(_spin):
        rs = run_sarima(ticker, train_ratio, p=ar_order,
                        date_from=date_from, date_to=date_to)
        re_ = run_ets(ticker, train_ratio, p=ar_order,
                      date_from=date_from, date_to=date_to)
        rg = run_garch(ticker, train_ratio, p=ar_order,
                       date_from=date_from, date_to=date_to)
        rx = run_sarimax(ticker, train_ratio, p=ar_order,
                         date_from=date_from, date_to=date_to)
    _spin2 = ('Đang huấn luyện mô hình học sâu (LSTM)...' if not is_en
              else 'Training deep-learning model (LSTM)...')
    with st.spinner(_spin2):
        rl = run_lstm(ticker, train_ratio, p=ar_order,
                      date_from=date_from, date_to=date_to)
    _lstm_name = rl.get('name', 'Deep Learning (LSTM)')

    last_close = float(df['Close'].iloc[-1])

    # ── Chuẩn hoá CI cho AR & MLR (không có khoảng giải tích) bằng ±1.96·σ_resid
    def _wrap_linear(res, name):
        ci = _ci95(res['yte'], res['pte'])
        npd = float(res['next_pred'])
        return dict(name=name, res=res, native_ci=False,
                    next_pred=npd, lo95=npd - ci, hi95=npd + ci,
                    lo80=npd - ci * (1.281551566 / 1.959963985),
                    hi80=npd + ci * (1.281551566 / 1.959963985))

    def _wrap_stat(res, name):
        return dict(name=name, res=res, native_ci=True,
                    next_pred=float(res['next_pred']),
                    lo95=float(res.get('next_lower', np.nan)),
                    hi95=float(res.get('next_upper', np.nan)),
                    lo80=float(res.get('next_lower80', np.nan)),
                    hi80=float(res.get('next_upper80', np.nan)))

    rows = [
        _wrap_linear(r1, f'AR({ar_order})'),
        _wrap_linear(r2, 'MLR'),
        _wrap_stat(r3, 'ARIMA'),
        _wrap_stat(rs, 'SARIMA'),
        _wrap_stat(re_, 'Holt-Winters'),
        _wrap_stat(rg, 'GARCH'),
        _wrap_stat(rx, 'SARIMAX'),
        _wrap_stat(rl, _lstm_name),
    ]
    metr = {
        f'AR({ar_order})': m1, 'MLR': m2, 'ARIMA': m3,
        'SARIMA': _safe_metrics(rs), 'Holt-Winters': _safe_metrics(re_),
        'GARCH': _safe_metrics(rg), 'SARIMAX': _safe_metrics(rx),
        _lstm_name: _safe_metrics(rl),
    }

    # ════════════════════════════════════════════════════════════════════
    #  1) BẢNG KHOẢNG TIN CẬY — DỰ BÁO PHIÊN KẾ TIẾP
    # ════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Khoảng tin cậy — Dự báo phiên kế tiếp" if not is_en else "Confidence Interval — Next-session Forecast"}'
        f'</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="info-box" style="margin-bottom:10px">'
        f'{"Giá hiện tại" if not is_en else "Current price"}: '
        f'<b>{last_close*1000:,.0f} đ</b> &nbsp;·&nbsp; '
        f'{"dải tô đậm = CI 80%, dải nhạt = CI 95%. Mô hình thống kê dùng khoảng dự báo giải tích; AR/MLR dùng ±1,96·σ phần dư." if not is_en else "darker band = 80% CI, lighter = 95% CI. Statistical models use analytic prediction intervals; AR/MLR use ±1.96·σ of residuals."}'
        f'</div>', unsafe_allow_html=True)

    _hdr = (['Mô hình', 'Cấu hình', 'Dự báo (đ)', 'Thay đổi', 'CI 80% (đ)', 'CI 95% (đ)', 'Độ rộng 95%']
            if not is_en else
            ['Model', 'Config', 'Forecast (đ)', 'Change', 'CI 80% (đ)', 'CI 95% (đ)', '95% width'])
    _rows_html = ''
    for r in rows:
        npd = r['next_pred']
        if not np.isfinite(npd):
            continue
        chg = (npd - last_close) / last_close * 100 if last_close else 0
        arr = '▲' if chg >= 0 else '▼'
        chg_col = _T['success'] if chg >= 0 else _T['danger']
        cfg = r['res'].get('summary', r['res'].get('params', '—')) \
            if r['native_ci'] else ('±1,96σ' if not is_en else '±1.96σ')
        width95 = (r['hi95'] - r['lo95']) * 1000
        _rows_html += (
            f'<tr style="color:{_T["text_primary"]};border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:9px 12px;font-weight:700">{r["name"]}</td>'
            f'<td style="padding:9px 12px;font-size:11px;color:{_T["text_muted"]}">{cfg}</td>'
            f'<td style="padding:9px 12px;font-weight:700">{npd*1000:,.0f}</td>'
            f'<td style="padding:9px 12px;color:{chg_col};font-weight:700">{arr} {abs(chg):.2f}%</td>'
            f'<td style="padding:9px 12px">[{r["lo80"]*1000:,.0f} – {r["hi80"]*1000:,.0f}]</td>'
            f'<td style="padding:9px 12px">[{r["lo95"]*1000:,.0f} – {r["hi95"]*1000:,.0f}]</td>'
            f'<td style="padding:9px 12px;color:{_T["text_secondary"]}">{width95:,.0f} đ</td>'
            f'</tr>')
    _th = ''.join(
        f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;-webkit-overflow-scrolling:touch;'
        f'border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
        f'<tbody>{_rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    #  2) FAN CHART KHOẢNG TIN CẬY — TỪNG MÔ HÌNH THỐNG KÊ
    # ════════════════════════════════════════════════════════════════════
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Fan chart khoảng tin cậy theo mô hình" if not is_en else "Per-model confidence fan charts"}'
        f'</div>', unsafe_allow_html=True)

    _fan_models = [
        ('ARIMA', r3), ('SARIMA', rs), ('Holt-Winters', re_),
        ('GARCH', rg), ('SARIMAX', rx), (_lstm_name, rl),
    ]
    _tabs = st.tabs([f'  {nm}  ' for nm, _ in _fan_models])
    for _tab, (nm, res) in zip(_tabs, _fan_models):
        with _tab:
            if not res.get('ok', True):
                st.warning(res.get('summary', 'N/A'))
                continue
            _mm = metr.get(nm, {})
            _eng = res.get('engine', '')
            _sm = res.get('summary', res.get('params', ''))
            st.markdown(
                f'<div class="info-box" style="margin-bottom:8px">'
                f'<b>{nm}</b> · {_sm} '
                f'&nbsp;·&nbsp; MAPE test = <b>{_mm.get("MAPE", float("nan")):.2f}%</b>'
                f' &nbsp;·&nbsp; RMSE = <b>{_mm.get("RMSE", float("nan")):.4f}</b>'
                f'</div>', unsafe_allow_html=True)
            try:
                fig = chart_fan_ci(res, ticker, T=_T, method_label=nm, is_en=is_en)
                st.plotly_chart(fig, use_container_width=True, config={
                    **_PLOTLY_CONFIG, 'toImageButtonOptions': {
                        **_PLOTLY_CONFIG['toImageButtonOptions'],
                        'filename': f'{ticker}_{nm}_CI'}})
            except Exception as _e:
                st.error(f'Chart error: {_e}')

    # ════════════════════════════════════════════════════════════════════
    #  3) BIẾN ĐỘNG GARCH (CONDITIONAL VOLATILITY)
    # ════════════════════════════════════════════════════════════════════
    if rg.get('ok', False) and rg.get('vol_test') is not None:
        st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="sec-hdr">'
            f'{"Biến động có điều kiện — GARCH" if not is_en else "Conditional volatility — GARCH"}'
            f'</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="info-box" style="margin-bottom:10px">'
            f'{"Độ lệch chuẩn lợi suất dự báo (%/phiên). Vùng biến động cao → khoảng tin cậy rộng hơn. σ phiên tới ≈" if not is_en else "Forecast return volatility (%/session). High-volatility regimes widen the CI. Next-session σ ≈"} '
            f'<b>{rg.get("vol_next", float("nan")):.2f}%</b>'
            f'</div>', unsafe_allow_html=True)
        try:
            import pandas as pd
            import plotly.graph_objects as go
            from charts.base import _plotly_axes_style
            _vt = np.asarray(rg['vol_test'], dtype=float)
            _dt = list(pd.to_datetime(rg['dates_te']).to_pydatetime())
            _c = '#22D3EE' if _T.get('is_dark') else '#0891B2'
            figv = go.Figure()
            figv.add_trace(go.Scatter(
                x=_dt, y=_vt, mode='lines', line=dict(color=_c, width=1.4),
                fill='tozeroy', fillcolor='rgba(8,145,178,0.12)',
                name='σ (%)',
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>σ = %{y:.2f}%<extra></extra>'))
            figv.update_layout(
                height=320, margin=dict(l=44, r=16, t=20, b=46),
                paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
                font=dict(family='Inter', size=11, color=_T['text_primary']),
                hovermode='x unified', showlegend=False)
            _plotly_axes_style(figv, _T)
            figv.update_xaxes(tickformat='%m/%Y')
            figv.update_yaxes(title=dict(
                text=('Độ biến động σ (%)' if not is_en else 'Volatility σ (%)'),
                font=dict(size=11, color=_T['text_secondary'])))
            st.plotly_chart(figv, use_container_width=True, config=_PLOTLY_CONFIG)
        except Exception as _e:
            st.caption(f'⚠ {_e}')

    # ════════════════════════════════════════════════════════════════════
    #  4) XẾP HẠNG ĐỘ CHÍNH XÁC (TEST)
    # ════════════════════════════════════════════════════════════════════
    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Xếp hạng độ chính xác trên tập kiểm tra" if not is_en else "Accuracy ranking on the test set"}'
        f'</div>', unsafe_allow_html=True)
    _names = list(metr.keys())
    _mapes = [metr[n].get('MAPE', float('nan')) for n in _names]
    _order = list(np.argsort([m if np.isfinite(m) else 1e9 for m in _mapes]))
    _max_mape = max([m for m in _mapes if np.isfinite(m)] + [1e-9])
    _medal = ['🥇', '🥈', '🥉']
    _rows2 = ''
    for _rank, _i in enumerate(_order):
        n = _names[_i]; mm = metr[n]
        mp = mm.get('MAPE', float('nan'))
        if not np.isfinite(mp):
            badge = '—'; bar = 0
        else:
            badge = _medal[_rank] if _rank < 3 else f'{_rank+1}'
            bar = 100 - (mp / _max_mape * 75)
        _mc = _T['success'] if mp < 1.5 else (_T['warning'] if mp < 2 else _T['danger'])
        _bg = f'background:{_T["warning_bg"]}' if _rank == 0 else (
            f'background:{_T["bg_elevated"]}' if _rank == 1 else f'background:{_T["bg_card"]}')
        _rows2 += (
            f'<tr style="{_bg};color:{_T["text_primary"]};border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:9px 12px;font-size:16px">{badge}</td>'
            f'<td style="padding:9px 12px;font-weight:700">{n}</td>'
            f'<td style="padding:9px 12px;color:{_mc};font-weight:700">{mp:.2f}%</td>'
            f'<td style="padding:9px 14px;min-width:120px">'
            f'<div style="background:{_T["border"]};border-radius:4px;height:6px;overflow:hidden">'
            f'<div style="background:{_mc};width:{bar:.0f}%;height:100%"></div></div></td>'
            f'<td style="padding:9px 12px">{mm.get("RMSE", float("nan")):.4f}</td>'
            f'<td style="padding:9px 12px">{mm.get("MAE", float("nan")):.4f}</td>'
            f'</tr>')
    _h2 = (['Hạng', 'Mô hình', 'MAPE', 'Hiệu năng', 'RMSE', 'MAE'] if not is_en
           else ['Rank', 'Model', 'MAPE', 'Performance', 'RMSE', 'MAE'])
    _th2 = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _h2)
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th2}</tr></thead>'
        f'<tbody>{_rows2}</tbody></table></div>',
        unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:10px">'
        f'{"Ghi chú: ARIMA/SARIMA/SARIMAX & Holt-Winters cho khoảng dự báo giải tích từ phân phối hậu nghiệm; GARCH dựng khoảng theo biến động có điều kiện; AR/MLR dùng xấp xỉ ±1,96·σ phần dư." if not is_en else "Note: ARIMA/SARIMA/SARIMAX & Holt-Winters give analytic prediction intervals; GARCH builds intervals from conditional volatility; AR/MLR use a ±1.96·σ residual approximation."}'
        f'</div>', unsafe_allow_html=True)

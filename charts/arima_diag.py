"""Biểu đồ chẩn đoán ARIMA & fan chart khoảng tin cậy.

- chart_fan_ci      : fan chart dải tin cậy 80%/95% (dùng chung mọi mô hình)
- chart_acf_pacf    : ACF & PACF của phần dư
- chart_residual_qq : phần dư theo thời gian + biểu đồ Q-Q (kiểm tra chuẩn)
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.themes import theme
from charts.base import _plotly_axes_style


def _next_business_day(last_date):
    import datetime as _dt
    if isinstance(last_date, str):
        last_date = _dt.datetime.strptime(last_date, '%Y-%m-%d').date()
    d = last_date
    while True:
        d += _dt.timedelta(days=1)
        if d.weekday() < 5:
            return d


def chart_fan_ci(res: dict, ticker: str, T: dict = None,
                 method_label: str = '', is_en: bool = False,
                 tail: int = 140, show_next: bool = True) -> go.Figure:
    """Fan chart: giá thực vs dự báo + dải tin cậy 80% & 95% trên tập test,
    kèm điểm dự báo phiên kế tiếp (out-of-sample) với thanh CI."""
    if T is None:
        T = theme()
    is_dark = T.get('is_dark', False)

    yte = np.asarray(res['yte'], dtype=float)
    pte = np.asarray(res['pte'], dtype=float)
    lo95 = np.asarray(res['pte_lower'], dtype=float)
    hi95 = np.asarray(res['pte_upper'], dtype=float)
    lo80 = np.asarray(res.get('pte_lower80', lo95), dtype=float)
    hi80 = np.asarray(res.get('pte_upper80', hi95), dtype=float)
    dts = list(pd.to_datetime(res['dates_te']).to_pydatetime())

    n = len(pte)
    if tail and n > tail:
        s = n - tail
        yte, pte = yte[s:], pte[s:]
        lo95, hi95, lo80, hi80 = lo95[s:], hi95[s:], lo80[s:], hi80[s:]
        dts = dts[s:]

    actual_c = '#F1F5F9' if is_dark else '#0F172A'
    fc_c = '#22D3EE' if is_dark else '#0891B2'
    band95 = 'rgba(8,145,178,0.12)'
    band80 = 'rgba(8,145,178,0.24)'

    fig = go.Figure()
    # 95% band
    fig.add_trace(go.Scatter(x=dts, y=hi95, mode='lines', line=dict(width=0),
                             hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=dts, y=lo95, mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor=band95,
                             name='95% CI', hoverinfo='skip'))
    # 80% band
    fig.add_trace(go.Scatter(x=dts, y=hi80, mode='lines', line=dict(width=0),
                             hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=dts, y=lo80, mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor=band80,
                             name='80% CI', hoverinfo='skip'))
    # actual + forecast
    fig.add_trace(go.Scatter(
        x=dts, y=yte, mode='lines', name='Thực tế' if not is_en else 'Actual',
        line=dict(color=actual_c, width=1.8),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(
        x=dts, y=pte, mode='lines', name='Dự báo' if not is_en else 'Forecast',
        line=dict(color=fc_c, width=1.5, dash='dot'),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:,.2f}<extra></extra>'))

    # Điểm dự báo phiên kế tiếp + thanh CI 95%
    if show_next and np.isfinite(res.get('next_pred', np.nan)):
        nd = _next_business_day(res['dates_te'][-1])
        np_ = float(res['next_pred'])
        nlo, nhi = float(res['next_lower']), float(res['next_upper'])
        fig.add_trace(go.Scatter(
            x=[nd], y=[np_], mode='markers',
            marker=dict(color=fc_c, size=9, symbol='diamond',
                        line=dict(color='#FFFFFF', width=1)),
            error_y=dict(type='data', symmetric=False,
                         array=[nhi - np_], arrayminus=[np_ - nlo],
                         color=fc_c, thickness=1.6, width=6),
            name='Phiên tới' if not is_en else 'Next',
            hovertemplate=(f'<b>{nd}</b><br>'
                           f'{np_:,.2f} [{nlo:,.2f}, {nhi:,.2f}]<extra></extra>')))

    _title = (f'{method_label} · {ticker} — '
              + ('Khoảng tin cậy dự báo' if not is_en else 'Forecast confidence interval'))
    fig.update_layout(
        title=dict(text=f'<b>{_title}</b>', x=0.5, xanchor='center',
                   font=dict(size=13, color=T['text_primary'])),
        height=420, margin=dict(l=46, r=16, t=52, b=58),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=11, color=T['text_primary']),
        hovermode='x',
        hoverlabel=dict(bgcolor=T['bg_elevated'], bordercolor=T['border'],
                        font_size=12, font_color=T['text_primary']),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2,
                    xanchor='center', x=0.5, bgcolor='rgba(0,0,0,0)',
                    font=dict(size=10.5, color=T['text_primary'])),
    )
    _plotly_axes_style(fig, T)
    fig.update_xaxes(tickformat='%m/%Y')
    fig.update_yaxes(title=dict(
        text=('Giá đóng cửa (nghìn đ)' if not is_en else 'Close (k VND)'),
        font=dict(size=11, color=T['text_secondary']), standoff=10))
    return fig


def chart_future_fan(fr: dict, ticker: str, T: dict = None,
                     is_en: bool = False) -> go.Figure:
    """Fan chart dự báo H phiên TỚI: lịch sử gần đây + dự báo + dải 80%/95% loe rộng."""
    if T is None:
        T = theme()
    is_dark = T.get('is_dark', False)
    rdt = list(pd.to_datetime(fr['recent_dates']).to_pydatetime())
    rcl = np.asarray(fr['recent_close'], float) * 1000.0
    fdt = list(pd.to_datetime(fr['future_dates']).to_pydatetime())
    mean = np.asarray(fr['mean'], float) * 1000.0
    lo95 = np.asarray(fr['lo95'], float) * 1000.0
    hi95 = np.asarray(fr['hi95'], float) * 1000.0
    lo80 = np.asarray(fr['lo80'], float) * 1000.0
    hi80 = np.asarray(fr['hi80'], float) * 1000.0

    # Nối liền điểm cuối lịch sử với dự báo
    bx = [rdt[-1]] + fdt
    b_mean = np.concatenate([[rcl[-1]], mean])
    b_lo95 = np.concatenate([[rcl[-1]], lo95]); b_hi95 = np.concatenate([[rcl[-1]], hi95])
    b_lo80 = np.concatenate([[rcl[-1]], lo80]); b_hi80 = np.concatenate([[rcl[-1]], hi80])

    actual_c = '#F1F5F9' if is_dark else '#0F172A'
    fc_c = '#22D3EE' if is_dark else '#0891B2'
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bx, y=b_hi95, mode='lines', line=dict(width=0),
                             hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=bx, y=b_lo95, mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor='rgba(8,145,178,0.12)',
                             name='95% CI', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=bx, y=b_hi80, mode='lines', line=dict(width=0),
                             hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=bx, y=b_lo80, mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor='rgba(8,145,178,0.24)',
                             name='80% CI', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=rdt, y=rcl, mode='lines',
                             line=dict(color=actual_c, width=1.8),
                             name='Thực tế' if not is_en else 'Actual',
                             hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:,.0f} đ<extra></extra>'))
    fig.add_trace(go.Scatter(x=bx, y=b_mean, mode='lines+markers',
                             line=dict(color=fc_c, width=2, dash='dot'),
                             marker=dict(size=5, color=fc_c),
                             name='Dự báo' if not is_en else 'Forecast',
                             hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:,.0f} đ<extra></extra>'))
    fig.add_vline(x=rdt[-1], line=dict(color=T['text_muted'], width=1, dash='dash'))
    fig.update_layout(
        height=400, margin=dict(l=46, r=16, t=20, b=44),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=11, color=T['text_primary']),
        hovermode='x',
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10.5, color=T['text_primary'])))
    _plotly_axes_style(fig, T)
    fig.update_xaxes(tickformat='%d/%m')
    fig.update_yaxes(title=dict(text=('Giá (nghìn đ)' if not is_en else 'Price (k VND)'),
                                font=dict(size=11, color=T['text_secondary'])))
    return fig


def chart_acf_pacf(resid: np.ndarray, T: dict = None, nlags: int = 20,
                   is_en: bool = False) -> go.Figure:
    """ACF & PACF của phần dư với dải tin cậy ±1.96/√n."""
    if T is None:
        T = theme()
    from statsmodels.tsa.stattools import acf, pacf
    resid = np.asarray(resid, dtype=float)
    resid = resid[np.isfinite(resid)]
    n = len(resid)
    nlags = min(nlags, max(1, n // 3))
    a = acf(resid, nlags=nlags, fft=True)
    try:
        p = pacf(resid, nlags=nlags, method='ywm')
    except Exception:
        p = pacf(resid, nlags=nlags)
    conf = 1.959963985 / np.sqrt(n)
    lags = np.arange(1, nlags + 1)

    bar_c = '#22D3EE' if T.get('is_dark') else '#0891B2'
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('ACF — phần dư' if not is_en else 'ACF — residuals',
                                        'PACF — phần dư' if not is_en else 'PACF — residuals'),
                        horizontal_spacing=0.10)
    for col, vals in [(1, a[1:nlags + 1]), (2, p[1:nlags + 1])]:
        fig.add_trace(go.Bar(x=lags, y=vals, marker_color=bar_c,
                             width=0.35, showlegend=False,
                             hovertemplate='lag %{x}<br>%{y:.3f}<extra></extra>'),
                      row=1, col=col)
        for yb in (conf, -conf):
            fig.add_hline(y=yb, line=dict(color='#EF4444', width=1, dash='dash'),
                          row=1, col=col)
        fig.add_hline(y=0, line=dict(color=T['text_muted'], width=1), row=1, col=col)
    fig.update_layout(
        height=300, margin=dict(l=40, r=16, t=44, b=36),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=10, color=T['text_primary']),
        bargap=0.5,
    )
    _plotly_axes_style(fig, T)
    return fig


def chart_residual_qq(resid: np.ndarray, dates=None, T: dict = None,
                      is_en: bool = False) -> go.Figure:
    """Phần dư theo thời gian + biểu đồ Q-Q chuẩn."""
    if T is None:
        T = theme()
    from scipy import stats as sp
    resid = np.asarray(resid, dtype=float)
    resid = resid[np.isfinite(resid)]
    line_c = '#22D3EE' if T.get('is_dark') else '#0891B2'
    ref_c = '#EF4444'

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('Phần dư theo thời gian' if not is_en else 'Residuals over time',
                                        'Q-Q chuẩn' if not is_en else 'Normal Q-Q'),
                        horizontal_spacing=0.12)
    x_idx = list(range(len(resid)))
    fig.add_trace(go.Scatter(x=x_idx, y=resid, mode='lines',
                             line=dict(color=line_c, width=1),
                             showlegend=False,
                             hovertemplate='%{y:.3f}<extra></extra>'), row=1, col=1)
    fig.add_hline(y=0, line=dict(color=ref_c, width=1, dash='dash'), row=1, col=1)

    (osm, osr), (slope, intercept, _r) = sp.probplot(resid, dist='norm')
    fig.add_trace(go.Scatter(x=osm, y=osr, mode='markers',
                             marker=dict(color=line_c, size=4, opacity=0.6),
                             showlegend=False,
                             hovertemplate='%{x:.2f}, %{y:.2f}<extra></extra>'),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=osm, y=slope * osm + intercept, mode='lines',
                             line=dict(color=ref_c, width=1.4),
                             showlegend=False, hoverinfo='skip'), row=1, col=2)
    fig.update_layout(
        height=300, margin=dict(l=40, r=16, t=44, b=36),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=10, color=T['text_primary']),
    )
    _plotly_axes_style(fig, T)
    return fig

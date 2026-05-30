import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm as sp_norm

from core.themes import theme
from core.constants import TICKERS, get_clr
from core.i18n import t
from charts.base import _plotly_layout_base

# v58 — Bỏ matplotlib + chart_portfolio_compare() dead. Active code dùng
# chart_portfolio_compare_plotly() bên trên.


def chart_portfolio_compare_plotly(all_data: dict, train_ratio: float, T=None):
    """Hiệu suất chuẩn hóa 3 cổ phiếu — Plotly interactive."""
    if T is None:
        T = theme()

    is_dark = T.get('is_dark', False)
    colors = get_clr(T)

    fig = go.Figure()

    _tks = list(all_data.keys())
    for tk in _tks:
        df_tk   = all_data[tk]
        dt_tk   = pd.to_datetime(df_tk['Ngay'])
        cl_tk   = df_tk['Close'].values
        norm_tk = cl_tk / cl_tk[0] * 100
        fig.add_trace(go.Scatter(
            x=dt_tk, y=norm_tk, mode='lines',
            name=f'{tk} ({cl_tk[-1]*1000:,.0f} đ → {norm_tk[-1]:.1f})',
            line=dict(color=colors[tk], width=2),
            hovertemplate=f'<b>{tk}</b><br>%{{x|%Y-%m-%d}}<br>Norm: %{{y:.1f}}<extra></extra>',
        ))

    _ref = _tks[0]
    nt_ref    = int(len(all_data[_ref]) * train_ratio)
    split_dt  = pd.to_datetime(all_data[_ref]['Ngay'].values[nt_ref])
    split_str = pd.Timestamp(split_dt).strftime('%Y-%m-%d')
    fig.add_vline(x=split_str, line=dict(color=T['text_muted'], width=1.5, dash='dash'))
    fig.add_annotation(
        x=split_str, y=1.04, yref='paper',
        text=t('chart.train_test_label'), showarrow=False,
        font=dict(size=10, color=T['text_secondary']),
        bgcolor=T['bg_card'], borderpad=3,
    )

    fig.add_hline(y=100, line=dict(color=T['text_muted'], width=0.8, dash='dot'))

    fig.update_layout(
        title=dict(
            text=t('chart.portfolio_title'),
            x=0.5, xanchor='center',
            font=dict(size=13, color=T['text_primary']),
        ),
        height=520,
        margin=dict(l=42, r=15, t=55, b=55),  # v37: mobile-friendly
        paper_bgcolor=T['bg_card'],
        plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=11, color=T['text_primary']),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=T['bg_elevated'], bordercolor=T['border'],
                        font_size=12, font_color=T['text_primary']),
        legend=dict(
            orientation='h', yanchor='top', y=-0.13,
            xanchor='center', x=0.5,
            bgcolor=T['bg_elevated'], bordercolor=T['border'], borderwidth=1,
            font=dict(size=11, color=T['text_primary']),
            itemsizing='constant',
        ),
        xaxis=dict(
            showgrid=False, showline=True, linecolor=T['border'],
            tickfont=dict(size=10, color=T['text_muted']),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=T['grid'],
            tickformat=',.0f',
            tickfont=dict(size=10, color=T['text_muted']),
            title=dict(text=t('chart.normalized_base'),
                       font=dict(size=11, color=T['text_secondary'])),
        ),
    )

    return fig


def chart_correlation_plotly(corr, T=None):
    """Correlation heatmap — Plotly, high-contrast per-cell text via annotations."""
    if T is None:
        T = theme()

    is_dark = T.get('is_dark', False)
    z = corr.values

    colorscale = (
        [
            [0.0,  '#1E293B'], [0.3,  '#1E40AF'],
            [0.55, '#2563EB'], [0.75, '#3B82F6'],
            [0.9,  '#60A5FA'], [1.0,  '#93C5FD'],
        ]
        if is_dark else
        [
            [0.0,  '#EFF6FF'], [0.3,  '#BFDBFE'],
            [0.5,  '#60A5FA'], [0.7,  '#2563EB'],
            [0.85, '#1D4ED8'], [1.0,  '#1E3A8A'],
        ]
    )

    fig = go.Figure(data=go.Heatmap(
        z=z, x=list(corr.columns), y=list(corr.index),
        colorscale=colorscale, zmin=0.0, zmax=1.0,
        hovertemplate='<b>%{y} ↔ %{x}</b><br>r = %{z:.4f}<extra></extra>',
        xgap=3, ygap=3,
        colorbar=dict(
            title=dict(text='r', font=dict(color=T['text_secondary'], size=12)),
            tickfont=dict(color=T['text_muted'], size=10),
            outlinecolor=T['border'], outlinewidth=1,
            thickness=18, len=0.75,
            tickvals=[0, 0.25, 0.5, 0.75, 1.0],
        ),
    ))

    # v58.9 — batch annotations 1 lần (cũ: 9 add_annotation calls cho 3×3
    # matrix = 9 figure rebuild → 300-600ms). Single update_layout.
    _annots = []
    for i, row_name in enumerate(corr.index):
        for j, col_name in enumerate(corr.columns):
            v = float(z[i, j])
            txt_color = '#FFFFFF' if v > 0.55 else '#0F172A'
            _annots.append(dict(
                x=col_name, y=row_name,
                text=f'<b>{v:.3f}</b>',
                showarrow=False,
                font=dict(size=18, family='Inter', color=txt_color),
            ))
    fig.update_layout(annotations=_annots)

    fig.update_layout(
        title=dict(
            text=t('chart.return_corr'),
            x=0.5, xanchor='center',
            font=dict(size=14, color=T['text_primary']),
        ),
        height=480,
        margin=dict(l=45, r=15, t=50, b=50),  # v37: mobile-friendly
        paper_bgcolor=T['bg_card'],
        plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', color=T['text_primary']),
        xaxis=dict(side='bottom', tickfont=dict(size=14, color=T['text_primary'])),
        yaxis=dict(autorange='reversed', tickfont=dict(size=14, color=T['text_primary'])),
    )

    return fig


def chart_returns_hist(df: pd.DataFrame, ticker: str, T: dict = None) -> go.Figure:
    """Histogram phân phối Return — Plotly, có toolbar đầy đủ."""
    if T is None: T = theme()
    CLR_NOW  = get_clr(T)
    col      = CLR_NOW[ticker]
    ret      = df['Return'].dropna()
    mu, sigma = float(ret.mean()), float(ret.std())
    x_norm   = np.linspace(float(ret.min()), float(ret.max()), 300)
    y_norm   = sp_norm.pdf(x_norm, mu, sigma)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ret, nbinsx=80, histnorm='probability density',
        marker=dict(color=col, opacity=0.65, line=dict(width=0)),
        hovertemplate='Return: %{x:.2f}%<br>Density: %{y:.4f}<extra></extra>',
        showlegend=True,
        name=f'{t("chart.daily_return_label")} (μ={mu:.3f}, σ={sigma:.3f})',
    ))
    fig.add_trace(go.Scatter(
        x=x_norm, y=y_norm, mode='lines',
        line=dict(color='#EF4444', width=2.2),
        name=t('chart.normal_label', mu=f'{mu:.3f}', sigma=f'{sigma:.3f}'),
        hovertemplate='x=%{x:.2f}<br>pdf=%{y:.4f}<extra></extra>',
    ))
    fig.add_vline(x=0,       line=dict(color=T['text_muted'], width=1.1, dash='dash'))
    fig.add_vline(x=float(mu), line=dict(color=col, width=1.2, dash='dot'))

    lay = _plotly_layout_base(T, height=400)
    lay.update(dict(
        title=dict(
            text=f'<b>{ticker}</b>  —  {t("chart.ret_hist_title")}',
            x=0.5, xanchor='center',
            font=dict(size=13, color=T['text_primary']),
        ),
        bargap=0.02,
        xaxis=dict(
            title=dict(text=t('chart.ret_axis'), font=dict(size=11, color=T['text_secondary'])),
            showgrid=False, showline=True, linecolor=T['border'],
            tickfont=dict(size=10, color=T['text_muted']), zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=t('chart.density_axis'), font=dict(size=11, color=T['text_secondary'])),
            showgrid=True, gridcolor=T['grid'],
            tickfont=dict(size=10, color=T['text_muted']), zeroline=False,
        ),
        legend=dict(
            orientation='h', yanchor='top', y=-0.25,
            xanchor='center', x=0.5,
            bgcolor=T['bg_elevated'], bordercolor=T['border'], borderwidth=1,
            font=dict(size=10, color=T['text_primary']),
            itemsizing='constant',
        ),
        margin=dict(l=42, r=15, t=50, b=80),  # v37: mobile-friendly
        hovermode='x',
    ))
    fig.update_layout(lay)
    return fig

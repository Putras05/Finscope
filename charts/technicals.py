"""Biểu đồ PHÂN TÍCH KỸ THUẬT tổng hợp cho FinScope.

Một nến (candlestick) trên cửa sổ gần đây, phủ các lớp kỹ thuật bật/tắt được:
  • Hỗ trợ / Kháng cự (đường ngang theo vùng swing, nhãn độ mạnh).
  • Fibonacci thoái lui (các mức 23.6/38.2/50/61.8/78.6%).
  • Kênh xu hướng hồi quy (đường giữa + biên trên/dưới).
  • ZigZag sóng (nối các điểm đảo chiều, đánh số swing — nền tảng đếm sóng).

Giá hiển thị quy về ĐỒNG (×1000) để đồng bộ với phần Chiến lược.
Tất cả chỉ báo tính trên CÙNG cửa sổ hiển thị → mốc thời gian khớp.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from charts.base import _PLOTLY_CONFIG, _plotly_axes_style
from data import technicals as TA


_INC = '#10B981'
_DEC = '#EF4444'
_FIB_CLR = '#7C3AED'
_SUP_CLR = '#16A34A'
_RES_CLR = '#DC2626'
_CH_CLR = '#0891B2'
_ZZ_CLR = '#F59E0B'


def chart_technical(df: pd.DataFrame, ticker: str, T: dict, *,
                    window: int = 180, show_sr: bool = True,
                    show_fib: bool = True, show_channel: bool = True,
                    show_zigzag: bool = True, zigzag_pct: float = 0.06,
                    is_en: bool = False) -> go.Figure:
    """Vẽ nến + các lớp kỹ thuật trên `window` phiên gần nhất."""
    d = df.tail(window).reset_index(drop=True)
    dates = pd.to_datetime(d['Ngay'])
    K = 1000.0                                    # nghìn đồng → đồng

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dates, open=d['Open'] * K, high=d['High'] * K,
        low=d['Low'] * K, close=d['Close'] * K,
        increasing=dict(line=dict(color=_INC, width=1), fillcolor=_INC),
        decreasing=dict(line=dict(color=_DEC, width=1), fillcolor=_DEC),
        name=ticker, showlegend=False,
    ))

    x0, x1 = dates.iloc[0], dates.iloc[-1]

    # ── Kênh xu hướng hồi quy ───────────────────────────────────────────
    if show_channel:
        ch = TA.trend_channel(d, lookback=window)
        if len(ch['mid']):
            cx = dates.iloc[ch['idx']]
            for key, dash, nm, op in [('upper', 'dot', None, 0.5),
                                      ('mid', 'dash', 'Kênh xu hướng', 0.9),
                                      ('lower', 'dot', None, 0.5)]:
                fig.add_trace(go.Scatter(
                    x=cx, y=np.asarray(ch[key]) * K, mode='lines',
                    line=dict(color=_CH_CLR, width=1.5 if key == 'mid' else 1,
                              dash=dash),
                    opacity=op, name=(nm or ''), showlegend=bool(nm),
                    hoverinfo='skip',
                ))

    # ── Fibonacci thoái lui ─────────────────────────────────────────────
    if show_fib:
        fib = TA.fibonacci_levels(d, lookback=window)
        for r, px in fib.get('levels', []):
            if r in (0.0, 1.0):
                continue
            fig.add_hline(
                y=px * K, line=dict(color=_FIB_CLR, width=1, dash='dot'),
                opacity=0.55,
                annotation_text=f'Fib {r*100:.1f}% · {px*K:,.0f}',
                annotation_position='left',
                annotation_font=dict(size=9, color=_FIB_CLR),
            )

    # ── Hỗ trợ / Kháng cự ───────────────────────────────────────────────
    if show_sr:
        sr = TA.support_resistance(d, lookback=window, max_levels=3)
        for px, strg in sr['resistance'][:3]:
            fig.add_hline(
                y=px * K, line=dict(color=_RES_CLR, width=1.4, dash='solid'),
                opacity=0.6,
                annotation_text=f'{"R" if is_en else "Kháng cự"} {px*K:,.0f} ·{strg}',
                annotation_position='right',
                annotation_font=dict(size=9, color=_RES_CLR))
        for px, strg in sr['support'][:3]:
            fig.add_hline(
                y=px * K, line=dict(color=_SUP_CLR, width=1.4, dash='solid'),
                opacity=0.6,
                annotation_text=f'{"S" if is_en else "Hỗ trợ"} {px*K:,.0f} ·{strg}',
                annotation_position='right',
                annotation_font=dict(size=9, color=_SUP_CLR))

    # ── ZigZag sóng (đánh số swing) ─────────────────────────────────────
    if show_zigzag:
        zz = TA.zigzag(d, pct=zigzag_pct)
        if len(zz['idx']) >= 2:
            zx = dates.iloc[zz['idx']]
            zy = np.asarray(zz['px']) * K
            fig.add_trace(go.Scatter(
                x=zx, y=zy, mode='lines+markers+text',
                line=dict(color=_ZZ_CLR, width=1.6),
                marker=dict(color=_ZZ_CLR, size=6,
                            line=dict(color='#fff', width=1)),
                text=[str(i) for i in range(len(zz['idx']))],
                textposition='top center',
                textfont=dict(size=9, color=_ZZ_CLR),
                name=('Waves (ZigZag)' if is_en else 'Sóng (ZigZag)'),
                hovertemplate='%{x|%Y-%m-%d}<br>%{y:,.0f} đ<extra></extra>',
            ))

    fig.update_layout(
        height=480, margin=dict(l=46, r=70, t=24, b=40),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=11, color=T['text_primary']),
        hovermode='x unified', dragmode='pan',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', yanchor='bottom', y=-0.18,
                    xanchor='center', x=0.5, bgcolor='rgba(0,0,0,0)',
                    font=dict(size=10)),
        uirevision=f'tech_{ticker}',
    )
    _plotly_axes_style(fig, T)
    fig.update_xaxes(tickformat='%m/%Y',
                     rangebreaks=[dict(bounds=['sat', 'mon'])])
    fig.update_yaxes(title=dict(text=('Giá (đ)' if not is_en else 'Price (đ)'),
                                font=dict(size=11, color=T['text_secondary'])))
    return fig

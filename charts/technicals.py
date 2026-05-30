"""Biểu đồ PHÂN TÍCH KỸ THUẬT tổng hợp cho FinScope.

Một nến (candlestick) trên cửa sổ gần đây, phủ các lớp kỹ thuật bật/tắt được:
  • Hỗ trợ / Kháng cự (đường ngang theo vùng swing, nhãn độ mạnh).
  • Fibonacci thoái lui (các mức 23.6/38.2/50/61.8/78.6%).
  • Kênh xu hướng hồi quy (đường giữa + biên trên/dưới).
  • ZigZag sóng (nối các điểm đảo chiều — nền tảng đếm sóng).
  • Mẫu hình nến (chỉ đánh dấu nến gần đây để chart không bị dày).
  • VWAP (giá trung bình theo khối lượng) — đường tham chiếu giao dịch.
  • Parabolic SAR — chấm dừng lỗ / điểm đảo chiều (Wilder).

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
_VWAP_CLR = '#8B5CF6'
_PSAR_CLR = '#94A3B8'


def chart_technical(df: pd.DataFrame, ticker: str, T: dict, *,
                    window: int = 180, show_sr: bool = True,
                    show_fib: bool = True, show_channel: bool = True,
                    show_zigzag: bool = True, show_patterns: bool = True,
                    show_vwap: bool = False, show_psar: bool = False,
                    zigzag_pct: float = 0.06, is_en: bool = False) -> go.Figure:
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

    # ── Kênh xu hướng hồi quy ───────────────────────────────────────────
    if show_channel:
        ch = TA.trend_channel(d, lookback=window)
        if len(ch['mid']):
            cx = dates.iloc[ch['idx']]
            for key, dash, nm, op, w in [('upper', 'dot', None, 0.35, 0.8),
                                          ('mid', 'dash',
                                           ('Channel' if is_en else 'Kênh xu hướng'),
                                           0.85, 1.4),
                                          ('lower', 'dot', None, 0.35, 0.8)]:
                fig.add_trace(go.Scatter(
                    x=cx, y=np.asarray(ch[key]) * K, mode='lines',
                    line=dict(color=_CH_CLR, width=w, dash=dash),
                    opacity=op, name=(nm or ''), showlegend=bool(nm),
                    hoverinfo='skip',
                ))

    # ── VWAP (giá trung bình theo khối lượng) ───────────────────────────
    if show_vwap:
        try:
            v = TA.vwap(d, window=20)
            fig.add_trace(go.Scatter(
                x=dates, y=v * K, mode='lines',
                line=dict(color=_VWAP_CLR, width=1.6),
                name=('VWAP (20)' if is_en else 'VWAP 20 phiên'),
                hovertemplate='VWAP: %{y:,.0f} đ<extra></extra>',
            ))
        except Exception:
            pass

    # ── Parabolic SAR (chấm dừng lỗ / điểm đảo chiều) ───────────────────
    if show_psar:
        try:
            s = TA.parabolic_sar(d)
            fig.add_trace(go.Scatter(
                x=dates, y=s * K, mode='markers',
                marker=dict(symbol='circle', size=4, color=_PSAR_CLR,
                            line=dict(width=0)),
                name='Parabolic SAR',
                hovertemplate='SAR: %{y:,.0f} đ<extra></extra>',
            ))
        except Exception:
            pass

    # v58.9 — BATCH shapes + annotations 1 lần thay vì 9 lần add_hline.
    # Mỗi add_hline rebuild figure internal → 9 calls = 800-1200ms.
    # Gom hết vào _shapes/_annots, update_layout(shapes=..., annotations=...)
    # 1 phát → cut 60%+ thời gian render chart kỹ thuật.
    _shapes = list(fig.layout.shapes) if fig.layout.shapes else []
    _annots = list(fig.layout.annotations) if fig.layout.annotations else []

    # ── Fibonacci thoái lui — nhãn dồn về PHẢI, font nhỏ, nền nhạt ───────
    if show_fib:
        fib = TA.fibonacci_levels(d, lookback=window)
        for r, px in fib.get('levels', []):
            if r in (0.0, 1.0):
                continue
            _shapes.append(dict(
                type='line', xref='paper', yref='y', x0=0, x1=1,
                y0=px * K, y1=px * K,
                line=dict(color=_FIB_CLR, width=0.9, dash='dot'),
                opacity=0.45))
            _annots.append(dict(
                xref='paper', yref='y', x=1, y=px * K,
                text=f'Fib {r*100:.1f}%', xanchor='left', xshift=-2,
                showarrow=False, font=dict(size=8, color=_FIB_CLR),
                bgcolor='rgba(124,58,237,0.08)', borderpad=1))

    # ── Hỗ trợ / Kháng cự — chỉ giữ TOP 2 mỗi bên cho gọn ──────────────
    if show_sr:
        sr = TA.support_resistance(d, lookback=window, max_levels=2)
        for px, strg in sr['resistance'][:2]:
            _shapes.append(dict(
                type='line', xref='paper', yref='y', x0=0, x1=1,
                y0=px * K, y1=px * K,
                line=dict(color=_RES_CLR, width=1.2, dash='solid'),
                opacity=0.55))
            _annots.append(dict(
                xref='paper', yref='y', x=1, y=px * K, xanchor='left',
                text=f'{"R" if is_en else "Kháng cự"} {px*K:,.0f} ·{strg}',
                showarrow=False, font=dict(size=9, color=_RES_CLR)))
        for px, strg in sr['support'][:2]:
            _shapes.append(dict(
                type='line', xref='paper', yref='y', x0=0, x1=1,
                y0=px * K, y1=px * K,
                line=dict(color=_SUP_CLR, width=1.2, dash='solid'),
                opacity=0.55))
            _annots.append(dict(
                xref='paper', yref='y', x=1, y=px * K, xanchor='left',
                text=f'{"S" if is_en else "Hỗ trợ"} {px*K:,.0f} ·{strg}',
                showarrow=False, font=dict(size=9, color=_SUP_CLR)))

    fig.update_layout(shapes=_shapes, annotations=_annots)

    # ── ZigZag — line + marker, BỎ số (gọn hơn) ─────────────────────────
    if show_zigzag:
        zz = TA.zigzag(d, pct=zigzag_pct)
        if len(zz['idx']) >= 2:
            zx = dates.iloc[zz['idx']]
            zy = np.asarray(zz['px']) * K
            fig.add_trace(go.Scatter(
                x=zx, y=zy, mode='lines+markers',
                line=dict(color=_ZZ_CLR, width=1.3),
                marker=dict(color=_ZZ_CLR, size=5,
                            line=dict(color='#fff', width=1)),
                name=('Waves (ZigZag)' if is_en else 'Sóng (ZigZag)'),
                hovertemplate='%{x|%Y-%m-%d}<br>%{y:,.0f} đ<extra></extra>',
            ))

    # ── Mẫu hình nến — CHỈ đánh dấu N nến gần nhất, không phủ cả cửa sổ ─
    if show_patterns:
        _PATS_RECENT = 30                # chỉ marker trong ~30 nến gần nhất
        _all_pats = TA.candlestick_patterns(d, lookback=window)
        _cut = len(d) - _PATS_RECENT
        pats = [p for p in _all_pats if p['idx'] >= _cut]
        bx, by, bt = [], [], []
        rx, ry, rt = [], [], []
        nx, ny, nt = [], [], []
        for p in pats:
            i = p['idx']
            _pn = p['name_en'] if is_en else p['name']
            if p['dir'] > 0:
                bx.append(dates.iloc[i]); by.append(d['Low'].iloc[i] * K * 0.985); bt.append(_pn)
            elif p['dir'] < 0:
                rx.append(dates.iloc[i]); ry.append(d['High'].iloc[i] * K * 1.015); rt.append(_pn)
            else:
                nx.append(dates.iloc[i]); ny.append(d['High'].iloc[i] * K * 1.012); nt.append(_pn)
        if bx:
            fig.add_trace(go.Scatter(
                x=bx, y=by, mode='markers', name=('Bullish pattern' if is_en else 'Mẫu hình tăng'),
                marker=dict(symbol='triangle-up', size=9, color=_SUP_CLR,
                            line=dict(color='#fff', width=1)),
                text=bt, hovertemplate='%{text}<br>%{x|%Y-%m-%d}<extra></extra>'))
        if rx:
            fig.add_trace(go.Scatter(
                x=rx, y=ry, mode='markers', name=('Bearish pattern' if is_en else 'Mẫu hình giảm'),
                marker=dict(symbol='triangle-down', size=9, color=_RES_CLR,
                            line=dict(color='#fff', width=1)),
                text=rt, hovertemplate='%{text}<br>%{x|%Y-%m-%d}<extra></extra>'))
        if nx:
            fig.add_trace(go.Scatter(
                x=nx, y=ny, mode='markers', name='Doji',
                marker=dict(symbol='diamond', size=6, color=T['text_muted'],
                            line=dict(color='#fff', width=1)),
                text=nt, hovertemplate='%{text}<br>%{x|%Y-%m-%d}<extra></extra>'))

    fig.update_layout(
        height=480, margin=dict(l=46, r=90, t=24, b=40),
        paper_bgcolor=T['bg_card'], plot_bgcolor=T['bg_card'],
        font=dict(family='Inter', size=11, color=T['text_primary']),
        hovermode='x', dragmode='pan',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', yanchor='bottom', y=-0.18,
                    xanchor='center', x=0.5, bgcolor='rgba(0,0,0,0)',
                    font=dict(size=10)),
        uirevision=f'tech_{ticker}',
    )
    _plotly_axes_style(fig, T)
    fig.update_xaxes(tickformat='%m/%Y',
                     rangebreaks=[dict(bounds=['sat', 'mon'])])
    fig.update_yaxes(title=dict(text=('Price (đ)' if is_en else 'Giá (đ)'),
                                font=dict(size=11, color=T['text_secondary'])))
    return fig

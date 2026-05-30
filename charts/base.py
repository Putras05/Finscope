import base64
import numpy as np
import plotly.graph_objects as go

from core.themes import theme, lighten_color
from core.constants import get_clr

# v58 — Bỏ matplotlib (-80MB Streamlit Cloud build). sparkline_b64 đã chuyển
# sang pure SVG (xem hàm bên dưới). set_mpl_theme cũng bỏ import (unused).


_PLOTLY_CONFIG = {
    # v57 — Tắt MODEBAR hoàn toàn (nút chụp ảnh / zoom / pan / reset / download
    # PNG / etc.). User chỉ cần kéo (pan) qua chart để xem lịch sử — modebar
    # chiếm DOM, hover-fade-in animation gây lag rõ khi scroll qua nhiều chart.
    'displayModeBar': False,
    'displaylogo': False,
    # v57 — Tắt mọi animation/transition của Plotly. Default Plotly là 500ms
    # transition khi zoom/pan; với 10 trace x 1000+ points, tween animation
    # nuốt CPU. responsive=False để tắt resize observer (lag khi scroll do
    # sidebar reflow).
    'responsive': False,
    'doubleClick': 'reset',
    'scrollZoom': False,
    # showTips=False để tắt tooltip "double click to autoscale" của Plotly
    'showTips': False,
    'staticPlot': False,  # giữ tương tác (hover + drag = pan)
    # v58 — GIỮ LẠI toImageButtonOptions key dù displayModeBar=False, vì 18+
    # chỗ trong app_pages dùng pattern `{**_PLOTLY_CONFIG, 'toImageButtonOptions':
    # {**_PLOTLY_CONFIG['toImageButtonOptions'], 'filename': '...'}}` để custom
    # filename khi user export PNG. Bỏ key này gây KeyError vỡ chart.
    'toImageButtonOptions': {'format': 'png', 'scale': 3, 'filename': 'finscope_chart'},
}


# v57 — Layout patch áp dụng MỌI figure: tắt animation/transition figure-level.
_PLOTLY_LAYOUT_NO_ANIM = {
    'transition': {'duration': 0},
    'uirevision': 'static',  # giữ trạng thái zoom/pan giữa các rerun → không relayout
}


# v57 — Monkey-patch go.Figure.update_layout để MỌI chart trong app tự động
# thêm transition.duration=0 + uirevision='static'. Tránh phải sửa 11 file
# charts/*.py. setdefault → không ghi đè caller nếu họ pass explicit value.
_ORIG_UPDATE_LAYOUT = go.Figure.update_layout


def _patched_update_layout(self, *args, **kwargs):
    if 'transition' not in kwargs:
        kwargs['transition'] = {'duration': 0}
    if 'uirevision' not in kwargs:
        kwargs['uirevision'] = 'static'
    # v57 — dragmode='pan' default → user kéo chart sẽ pan (di chuyển ngang)
    # thay vì zoom hộp. Đúng UX mong muốn.
    if 'dragmode' not in kwargs:
        kwargs['dragmode'] = 'pan'
    return _ORIG_UPDATE_LAYOUT(self, *args, **kwargs)


go.Figure.update_layout = _patched_update_layout


def calc_r2(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def _plotly_axes_style(fig: go.Figure, T: dict) -> None:
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        showline=True, linecolor=T['border'], linewidth=1,
        ticks='outside', tickcolor=T['border'], ticklen=4,
        tickfont=dict(size=10, color=T['text_muted']),
        showspikes=True, spikecolor=T['accent'], spikemode='across',
        spikesnap='cursor', spikedash='dot', spikethickness=1,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=T['grid'], gridwidth=1,
        zeroline=False, showline=False, ticks='',
        tickformat=',.2f',
        tickfont=dict(size=10, color=T['text_muted']),
        showspikes=True, spikecolor=T['accent'], spikemode='across',
        spikesnap='cursor', spikedash='dot', spikethickness=1,
    )


def _plotly_layout_base(T: dict, height: int = 360) -> dict:
    return dict(
        height=height,
        paper_bgcolor=T['bg_card'],
        plot_bgcolor=T['bg_card'],
        font=dict(family='Inter, system-ui, sans-serif', size=11, color=T['text_primary']),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor=T['bg_elevated'], bordercolor=T['border'],
            font_size=12, font_color=T['text_primary'], font_family='Inter',
        ),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.04,
            xanchor='right', x=1.0,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11, color=T['text_primary']),
            itemsizing='constant',
        ),
        margin=dict(l=42, r=12, t=50, b=35),  # v37: giảm margins (mobile-friendly + desktop vẫn đẹp)
    )


def sparkline_b64(prices, next_price, col, T: dict = None):
    """v58 — Pure SVG sparkline (không cần matplotlib).

    Render thành inline SVG (text), encode base64 → trông giống PNG cũ
    nhưng nhẹ hơn, không boot matplotlib (-80MB Streamlit Cloud + -3s khởi
    động). Trả base64-encoded SVG; caller dùng `data:image/svg+xml;base64,...`
    sẽ work giống `data:image/png;base64`.
    """
    if T is None:
        T = theme()
    is_dark = T.get('is_dark', False)
    bg = T['bg_card']
    line_col = lighten_color(col, 0.20) if is_dark else col

    prices = [float(p) for p in prices]
    next_price = float(next_price)
    n = len(prices)
    if n < 2:
        # Trả empty SVG để caller không crash
        empty = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="80"/>'
        return base64.b64encode(empty.encode()).decode()

    # Toạ độ chart: 240 × 80 px, padding 4
    W, H, PAD = 240, 80, 4
    inner_w = W - 2 * PAD
    inner_h = H - 2 * PAD
    all_vals = prices + [next_price]
    vmin, vmax = min(all_vals), max(all_vals)
    span = max(vmax - vmin, 1e-9)

    def _xy(i, v, total_pts):
        x = PAD + (i / max(total_pts - 1, 1)) * inner_w
        y = PAD + (1 - (v - vmin) / span) * inner_h
        return x, y

    # Path historical prices
    pts = []
    for i, p in enumerate(prices):
        x, y = _xy(i, p, n + 1)
        pts.append(f'{x:.1f},{y:.1f}')
    path_hist = 'M ' + ' L '.join(pts)

    # Segment dotted: last hist → next predicted
    lx, ly = _xy(n - 1, prices[-1], n + 1)
    nx, ny = _xy(n,     next_price, n + 1)
    chg     = next_price - prices[-1]
    seg_col = '#10B981' if chg >= 0 else '#EF4444'

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" preserveAspectRatio="none">'
        f'<rect width="{W}" height="{H}" fill="{bg}"/>'
        f'<path d="{path_hist}" stroke="{line_col}" stroke-width="2" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="{seg_col}" stroke-width="1.8" stroke-dasharray="4,3" opacity="0.75"/>'
        f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="4" fill="{seg_col}"/>'
        f'</svg>'
    )
    return base64.b64encode(svg.encode()).decode()

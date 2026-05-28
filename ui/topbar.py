"""Thanh điều hướng + tham số ở TRÊN CÙNG trang chính (không dùng sidebar).

Lý do: navigation đặt trong sidebar quá mong manh (splash che, trạng thái
collapse, custom-toggle JS). Đưa lên main area → LUÔN hiển thị, ổn định trên
mọi trình duyệt/thiết bị — cách nhiều app Streamlit production dùng.
"""
import streamlit as st
import datetime as _dt
from streamlit_option_menu import option_menu

from core.constants import TICKERS, TICKER_INFO
from core.i18n import t
from ui.logo import mark_mono


def _sector_short(tk: str) -> str:
    """Ngành ngắn gọn của mã (bỏ đuôi '· HOSE'); fallback 'Khác' nếu thiếu."""
    s = TICKER_INFO.get(tk, '')
    return s.split('·')[0].strip() if s else 'Khác'


# Sắp mã theo NHÓM NGÀNH để dropdown dễ chọn — 3 mã mặc định ở đầu.
_DEFAULT_TOP = ['FPT', 'HPG', 'VNM']
_TICKER_ORDER = _DEFAULT_TOP + sorted(
    [tk for tk in TICKERS if tk not in _DEFAULT_TOP],
    key=lambda tk: (_sector_short(tk), tk))

# Sectors sorted by số mã giảm dần (nhóm phổ biến lên đầu — Ngân hàng > BĐS > …)
def _sector_counts() -> dict:
    c = {}
    for tk in TICKERS:
        s = _sector_short(tk); c[s] = c.get(s, 0) + 1
    return c
_SECTOR_COUNTS = _sector_counts()
_ALL_SECTORS = sorted(_SECTOR_COUNTS.keys(),
                      key=lambda s: (-_SECTOR_COUNTS[s], s))
_ALL_LABEL = 'Tất cả ngành'

_PAGE_KEYS = [
    'Dashboard Tổng quan', 'Tổng quan Thị trường', 'Phân tích Cơ bản',
    'Phân tích Chi tiết', 'Mô hình Nâng cao', 'Chiến lược Giao dịch',
    'Tin tức Thị trường', 'Tín hiệu & Cảnh báo', 'Lịch sử & Dữ liệu',
    'Danh mục Đầu tư', 'Giao dịch Demo', 'Hướng dẫn Sử dụng',
]
_ICONS = [
    'speedometer2', 'globe', 'bank',
    'graph-up-arrow', 'bezier2', 'bullseye',
    'newspaper', 'activity', 'clock-history',
    'briefcase', 'cash-stack', 'book-half',
]

# Logo FinScope — kính soi tài chính (ui/logo.py), không dùng emoji.
_LOGO_SVG = mark_mono(24, '#1E40AF')


def render_topbar() -> tuple:
    """Render header + nav + controls ở main area. Trả về:
    (page_key, ticker, train_ratio, date_from, date_to, ar_order)
    """
    _is_en = st.session_state.get('lang', 'VI') == 'EN'

    # ── Header thương hiệu — wordmark gradient + huy hiệu logo ───────────
    # WORDMARK: "Fin" đậm-tối + "Scope" gradient blue→teal (background-clip).
    # Font-feature: liga + numeric tabular cho cảm giác chuyên nghiệp.
    _wm_html = (
        f"<span style='display:inline-flex;align-items:center;gap:10px;"
        f"font-family:Inter,system-ui,sans-serif;font-size:24px;"
        f"font-weight:800;letter-spacing:-.8px;line-height:1'>"
        f"{_LOGO_SVG}"
        f"<span style='display:inline-block'>"
        f"<span style='color:#0F172A'>Fin</span>"
        f"<span style='background:linear-gradient(90deg,#1E40AF 0%,#0891B2 60%,#0F766E 100%);"
        f"-webkit-background-clip:text;background-clip:text;color:transparent;"
        f"-webkit-text-fill-color:transparent'>Scope</span>"
        f"</span></span>")

    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"flex-wrap:wrap;gap:8px;padding:6px 4px 10px'>"
        f"<div style='display:flex;align-items:center;gap:12px;flex-wrap:wrap'>"
        f"{_wm_html}"
        # Đường gạch dọc tinh tế chia wordmark khỏi tagline
        f"<span style='width:1px;height:22px;background:#CBD5E1'></span>"
        f"<span style='font-size:12.5px;color:#475569;font-weight:500;"
        f"letter-spacing:.2px'>{t('app.tagline')}</span>"
        f"<span style='font-size:10.5px;font-weight:700;color:#0F766E;"
        f"background:linear-gradient(90deg,#ECFEFF 0%,#F0FDFA 100%);"
        f"border:1px solid #99F6E4;padding:3px 10px;border-radius:999px;"
        f"letter-spacing:.4px'>"
        f"{'Multi-model · 2026' if _is_en else 'Đa mô hình · 2026'}</span>"
        f"</div>"
        f"<span style='font-size:11px;color:#94A3B8;font-style:italic'>"
        f"Nguyễn Thành Danh · Trần Huỳnh Nhã Trúc</span>"
        f"</div>", unsafe_allow_html=True)

    # ── Navigation ngang ────────────────────────────────────────────────
    _labels = [
        t('nav.dashboard'),   t('nav.market'),    t('nav.fundamental'),
        t('nav.analysis'),    t('nav.advanced'),  t('nav.strategy'),
        t('nav.news'),        t('nav.signals'),   t('nav.history'),
        t('nav.portfolio'),   t('nav.paper'),     t('nav.guide'),
    ]
    if '_page_key' not in st.session_state:
        st.session_state['_page_key'] = 'Dashboard Tổng quan'
    _cur = (_PAGE_KEYS.index(st.session_state['_page_key'])
            if st.session_state['_page_key'] in _PAGE_KEYS else 0)

    _is_dark = st.session_state.get('theme_mode', 'light') == 'dark'
    _bg      = '#0F1B33' if _is_dark else '#FFFFFF'
    _txt     = '#CBD5E1' if _is_dark else '#475569'
    _sel_bg  = '#1E40AF'
    _sel_tx  = '#FFFFFF'
    _sel = option_menu(
        menu_title=None,
        options=_labels,
        icons=_ICONS,
        orientation='horizontal',
        default_index=_cur,
        key='_topnav',
        styles={
            'container': {'padding': '4px', 'background-color': _bg,
                          'border-radius': '12px', 'border': '1px solid #E2E8F0',
                          'margin-bottom': '6px'},
            'nav-link': {'font-size': '12.5px', 'font-weight': '600',
                         'color': _txt, 'padding': '8px 12px',
                         'border-radius': '8px', 'margin': '0 2px',
                         '--hover-color': '#EFF6FF'},
            'nav-link-selected': {'background-color': _sel_bg, 'color': _sel_tx,
                                  'font-weight': '700'},
            'icon': {'font-size': '14px'},
        },
    )
    if _sel not in _labels:
        _sel = _labels[_cur]
    page = _PAGE_KEYS[_labels.index(_sel)]
    st.session_state['_page_key'] = page

    # ── Hàng điều khiển: NGÀNH → MÃ → train · p · từ · đến · nút ────────
    # Two-step lựa chọn (kiểu pro app): chọn NGÀNH trước, MÃ trong ngành đó
    # sau. Sector "Tất cả ngành" giữ luồng cũ. 9 cột.
    c = st.columns([1.3, 1.1, 1.2, 0.8, 1.3, 1.3, 0.6, 0.6, 0.7])

    # NGÀNH selectbox — option "Tất cả ngành" + 31 ngành sort theo độ phổ biến.
    _all_lbl_disp = _ALL_LABEL if not _is_en else 'All sectors'
    _ticker_unit  = 'mã' if not _is_en else 'tickers'
    _SECTOR_OPTS = [_ALL_LABEL] + _ALL_SECTORS
    if 'tb_sector' not in st.session_state:
        st.session_state['tb_sector'] = _ALL_LABEL
    sector = c[0].selectbox(
        'Ngành' if not _is_en else 'Sector',
        _SECTOR_OPTS, key='tb_sector',
        format_func=lambda s: (_all_lbl_disp if s == _ALL_LABEL
                               else f'{s} ({_SECTOR_COUNTS.get(s,0)} {_ticker_unit})'),
    )

    # MÃ filtered theo ngành — ưu tiên 3 mã default ở đầu nếu chọn "Tất cả".
    if sector == _ALL_LABEL:
        ticker_opts = _TICKER_ORDER
    else:
        ticker_opts = [tk for tk in _TICKER_ORDER if _sector_short(tk) == sector]
        if not ticker_opts:
            ticker_opts = _TICKER_ORDER
    # Reset tb_ticker nếu không nằm trong options sau khi đổi ngành (tránh
    # Streamlit warning "default not in options").
    if st.session_state.get('tb_ticker') not in ticker_opts:
        st.session_state['tb_ticker'] = ticker_opts[0]
    if sector == _ALL_LABEL:
        _fmt_tk = lambda tk: f'{tk} · {_sector_short(tk)}'
    else:
        _fmt_tk = lambda tk: tk    # ngành đã hiện ở dropdown trên → khỏi lặp
    ticker = c[1].selectbox(
        'Mã' if not _is_en else 'Ticker', ticker_opts, key='tb_ticker',
        format_func=_fmt_tk,
    )
    train_ratio = c[2].slider(t('sidebar.train_ratio'), 70, 90, 80, step=5,
                              format='%d%%', key='tb_ratio') / 100
    if 'sb_ar_order' not in st.session_state:
        st.session_state['sb_ar_order'] = 1
    ar_order = c[3].number_input(
        'p', min_value=1, max_value=100, value=st.session_state['sb_ar_order'],
        step=1, key='sb_ar_order', help=t('sidebar.ar_order_help'))
    _today = _dt.date.today()
    if 'sb_date_from' not in st.session_state:
        st.session_state['sb_date_from'] = _dt.date(2016, 1, 1)
    if 'sb_date_to' not in st.session_state:
        st.session_state['sb_date_to'] = _today
    date_from = c[4].date_input(t('sidebar.from'), key='sb_date_from',
                                format='YYYY/MM/DD')
    date_to = c[5].date_input(t('sidebar.to'), key='sb_date_to',
                              format='YYYY/MM/DD')

    # Nút Dark / Lang / Refresh — căn xuống cho thẳng hàng input
    c[6].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    c[7].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    c[8].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if c[6].button('Sáng' if _is_dark else 'Tối', key='tb_dark',
                   use_container_width=True, help='Dark / Light'):
        st.session_state.theme_mode = 'light' if _is_dark else 'dark'
        st.rerun()
    if c[7].button('VI' if _is_en else 'EN', key='tb_lang',
                   use_container_width=True, help='Ngôn ngữ / Language'):
        st.session_state.lang = 'VI' if _is_en else 'EN'
        st.rerun()
    if c[8].button('↻', key='tb_refresh', use_container_width=True,
                   help=t('common.refresh')):
        for _k in ['_data_cache_key', '_df', '_r1', '_r2', '_r3',
                   '_m1', '_m2', '_m3']:
            st.session_state.pop(_k, None)
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.rerun()

    st.markdown(f"<hr style='border:none;border-top:1px solid #E2E8F0;margin:4px 0 10px'/>",
                unsafe_allow_html=True)
    return page, ticker, train_ratio, date_from, date_to, int(ar_order)

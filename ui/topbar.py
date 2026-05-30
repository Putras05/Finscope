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
    'Danh mục Đầu tư', 'Giao dịch Demo', 'Cơ sở Toán học',
    'Hồ sơ', 'Hướng dẫn Sử dụng',
]
_ICONS = [
    'speedometer2', 'globe', 'bank',
    'graph-up-arrow', 'bezier2', 'bullseye',
    'newspaper', 'activity', 'clock-history',
    'briefcase', 'cash-stack', 'calculator',
    'person-circle', 'book-half',
]

# Logo FinScope — kính soi tài chính (ui/logo.py), không dùng emoji.
_LOGO_SVG = mark_mono(24, '#1E40AF')


def _theme_tokens() -> dict:
    """Lấy 5 token màu dark-aware cho topbar — tránh hardcoded light colors
    làm header trắng tinh trên dark theme.
    """
    _is_dark = st.session_state.get('theme_mode', 'light') == 'dark'
    return {
        'hdr_tx':   '#F1F5F9' if _is_dark else '#0F172A',
        'sub_tx':   '#94A3B8' if _is_dark else '#475569',   # tagline secondary
        'chip_bg':  '#1E293B' if _is_dark else '#F8FAFC',
        'chip_brd': '#334155' if _is_dark else '#E2E8F0',
        'divider':  '#475569' if _is_dark else '#CBD5E1',
    }


def render_topbar() -> tuple:
    """Render header + nav + controls ở main area. Trả về:
    (page_key, ticker, train_ratio, date_from, date_to, ar_order)
    """
    _is_en = st.session_state.get('lang', 'VI') == 'EN'
    _tok = _theme_tokens()
    _HDR_TX  = _tok['hdr_tx']
    _SUB_TX  = _tok['sub_tx']
    _CHIP_BG = _tok['chip_bg']
    _CHIP_BRD = _tok['chip_brd']
    _DIVIDER = _tok['divider']

    # ── Header thương hiệu — wordmark gradient + huy hiệu logo ───────────
    # WORDMARK: "Fin" đậm-tối + "Scope" gradient blue→teal (background-clip).
    # Font-feature: liga + numeric tabular cho cảm giác chuyên nghiệp.
    _wm_html = (
        f"<span style='display:inline-flex;align-items:center;gap:10px;"
        f"font-family:Inter,system-ui,sans-serif;font-size:24px;"
        f"font-weight:800;letter-spacing:-.8px;line-height:1'>"
        f"{_LOGO_SVG}"
        f"<span style='display:inline-block'>"
        f"<span style='color:{_HDR_TX}'>Fin</span>"
        f"<span style='background:linear-gradient(90deg,#1E40AF 0%,#0891B2 60%,#0F766E 100%);"
        f"-webkit-background-clip:text;background-clip:text;color:transparent;"
        f"-webkit-text-fill-color:transparent'>Scope</span>"
        f"</span></span>")

    # ── User chip (góc phải): avatar + tên + nút Đăng xuất + chuông cảnh báo
    from auth.session import current_user, is_guest, logout_user
    from services.alerts import counts as _alert_counts
    _u = current_user() or {}
    _u_name  = _u.get('display_name') or _u.get('username') or 'Khách'
    _u_role  = ('Khách' if is_guest() else 'Tài khoản') if not _is_en else \
               ('Guest' if is_guest() else 'Account')
    _u_initial = (_u_name[:1] or '?').upper()
    _u_color = '#F59E0B' if is_guest() else '#1E40AF'
    # 1 lần đọc file alerts thay vì 2 (count_active + count_unread_triggered)
    _n_active, _n_trig = _alert_counts()

    _bell_badge = (
        f'<span style="position:absolute;top:-4px;right:-4px;background:#DC2626;'
        f'color:#fff;border-radius:999px;font-size:9px;font-weight:800;'
        f'padding:1px 5px;border:2px solid #fff;min-width:14px;text-align:center">'
        f'{_n_trig}</span>' if _n_trig > 0 else '')
    _bell_color = '#DC2626' if _n_trig > 0 else ('#F59E0B' if _n_active > 0 else '#94A3B8')
    # Tooltip text trong HTML `title=` không render đẹp; thay bằng aria-label
    # cho accessibility — user click vào trang Tín hiệu để quản lý cảnh báo.
    _bell_aria = (f'{_n_active} cảnh báo đang chờ, {_n_trig} đã kích hoạt'
                   if not _is_en else
                   f'{_n_active} alerts pending, {_n_trig} triggered')
    from ui.icons import icon as _icon_fn
    _bell_html = (
        f'<span role="status" aria-label="{_bell_aria}" '
        f'style="position:relative;display:inline-flex;align-items:center;'
        f'justify-content:center;width:30px;height:30px;border-radius:50%;'
        f'background:{_CHIP_BG};border:1px solid {_CHIP_BRD}">'
        f'{_icon_fn("bell", 14, _bell_color)}{_bell_badge}</span>')

    _user_chip_html = (
        f"<div style='display:inline-flex;align-items:center;gap:8px;"
        f"background:{_CHIP_BG};border:1px solid {_CHIP_BRD};border-radius:999px;"
        f"padding:3px 4px 3px 4px'>"
        f"<span style='width:26px;height:26px;border-radius:50%;"
        f"background:{_u_color};color:#fff;display:inline-flex;"
        f"align-items:center;justify-content:center;font-weight:800;"
        f"font-size:12px;letter-spacing:0'>{_u_initial}</span>"
        f"<span style='display:inline-flex;flex-direction:column;line-height:1.1;"
        f"padding-right:4px'>"
        f"<span style='font-size:11.5px;font-weight:700;color:{_HDR_TX}'>{_u_name}</span>"
        f"<span style='font-size:9.5px;color:#94A3B8;text-transform:uppercase;"
        f"letter-spacing:.6px'>{_u_role}</span></span></div>")

    # Header: wordmark trái — bell + chip + logout sub-cột phải, tất cả INLINE
    # v58 — Tăng tỷ trọng cột trái (5.5/1.2/0.6 thay vì 4.2/1.5/0.7) để
    # FinScope + tagline + badge có chỗ thở. Giảm font subtitle 12.5 → 11.5
    # + thêm white-space:nowrap cho badge để không xuống dòng giữa chừng.
    _hdr_l, _hdr_r1, _hdr_r2 = st.columns([5.5, 1.2, 0.6])
    with _hdr_l:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;"
            f"flex-wrap:nowrap;padding:6px 4px 4px;overflow:hidden'>"
            f"{_wm_html}"
            f"<span style='width:1px;height:22px;background:{_DIVIDER};"
            f"flex-shrink:0'></span>"
            f"<span style='font-size:11.5px;color:{_SUB_TX};font-weight:500;"
            f"letter-spacing:.2px;white-space:nowrap;overflow:hidden;"
            f"text-overflow:ellipsis;min-width:0'>{t('app.tagline')}</span>"
            f"<span style='font-size:10.5px;font-weight:700;color:#0F766E;"
            f"background:linear-gradient(90deg,#ECFEFF 0%,#F0FDFA 100%);"
            f"border:1px solid #99F6E4;padding:3px 10px;border-radius:999px;"
            f"letter-spacing:.4px;white-space:nowrap;flex-shrink:0'>"
            f"{'Multi-model · 2026' if _is_en else 'Đa mô hình · 2026'}</span>"
            f"</div>", unsafe_allow_html=True)
    with _hdr_r1:
        st.markdown(
            f"<div style='display:flex;justify-content:flex-end;align-items:center;"
            f"gap:8px;padding:8px 4px 0;height:42px'>{_bell_html}{_user_chip_html}</div>",
            unsafe_allow_html=True)
    with _hdr_r2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button(('Đăng xuất' if not _is_en else 'Sign out'),
                      key='_topbar_logout', use_container_width=True,
                      help='Quay về màn hình đăng nhập'):
            logout_user()
            st.rerun()

    # ── Navigation ngang ────────────────────────────────────────────────
    # v58 — Labels NGẮN GỌN (1-2 từ) để 14 items fit 1 hàng, không wrap 3 dòng.
    # Vẫn giữ icon riêng + tooltip mô tả đầy đủ qua title attr (option_menu
    # hỗ trợ qua menu_icon_help).
    if _is_en:
        _labels = [
            'Dashboard', 'Market', 'Fundamental',
            'Analysis', 'Advanced', 'Strategy',
            'News', 'Signals', 'History',
            'Portfolio', 'Paper',
            'Math', 'Profile', 'Guide',
        ]
    else:
        _labels = [
            'Dashboard', 'Thị trường', 'Cơ bản',
            'Chi tiết', 'Nâng cao', 'Chiến lược',
            'Tin tức', 'Tín hiệu', 'Lịch sử',
            'Danh mục', 'Paper',
            'Cơ sở Toán', 'Hồ sơ', 'Hướng dẫn',
        ]
    if '_page_key' not in st.session_state:
        st.session_state['_page_key'] = 'Dashboard Tổng quan'
    _cur = (_PAGE_KEYS.index(st.session_state['_page_key'])
            if st.session_state['_page_key'] in _PAGE_KEYS else 0)

    _is_dark = st.session_state.get('theme_mode', 'light') == 'dark'
    _bg      = '#0F1B33' if _is_dark else '#FFFFFF'
    _txt     = '#CBD5E1' if _is_dark else '#475569'
    _brd     = '#1E293B' if _is_dark else '#E2E8F0'      # v58: dark border
    _hover   = '#1E3A8A' if _is_dark else '#EFF6FF'      # v58: dark hover
    _sel_bg  = '#1E40AF'
    _sel_tx  = '#FFFFFF'
    # v58 — option_menu iframe có wrapper trắng từ Streamlit framework
    # + component có thể cache stale styles. Fix: (1) global CSS override
    # cho iframe wrapper, (2) BUMP KEY theo theme để force re-init khi đổi.
    st.markdown(f"""
    <style>
    /* Tô đậm wrapper của streamlit_option_menu — kill rect trắng */
    iframe[title*="option_menu"], iframe[title*="streamlit_option_menu"] {{
        background: {_bg} !important;
        border-radius: 12px !important;
    }}
    /* Element container quanh iframe — đồng màu page */
    div[data-testid="stIFrame"] > div,
    .element-container > iframe[title*="option_menu"] {{
        background: transparent !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    _sel = option_menu(
        menu_title=None,
        options=_labels,
        icons=_ICONS,
        orientation='horizontal',
        default_index=_cur,
        # Key static: tránh re-mount component khi toggle theme (80ms jank).
        # CSS override iframe[title*="option_menu"] (xem dưới) survives stale frames.
        key='_topnav',
        styles={
            'container': {'padding': '4px', 'background-color': _bg,
                          'border-radius': '12px', 'border': f'1px solid {_brd}',
                          'margin-bottom': '6px'},
            'nav-link': {'font-size': '12px', 'font-weight': '600',
                         'color': _txt, 'padding': '7px 9px',
                         'border-radius': '7px', 'margin': '0 1px',
                         'white-space': 'nowrap',
                         '--hover-color': _hover},
            'nav-link-selected': {'background-color': _sel_bg, 'color': _sel_tx,
                                  'font-weight': '700'},
            'icon': {'font-size': '14px'},
        },
    )
    if _sel not in _labels:
        _sel = _labels[_cur]
    page = _PAGE_KEYS[_labels.index(_sel)]
    st.session_state['_page_key'] = page

    # ── Hàng điều khiển: NGÀNH → MÃ → ★ → train · p · từ · đến · nút ────
    # Two-step lựa chọn (kiểu pro app): chọn NGÀNH trước, MÃ trong ngành đó
    # sau. Sector "Tất cả ngành" giữ luồng cũ. Thêm cột ★ cho watchlist.
    c = st.columns([1.15, 1.25, 0.75, 1.05, 0.65, 1.15, 1.15, 0.55, 0.55, 0.6])

    # NGÀNH selectbox — "Tất cả ngành" + "Yêu thích" + 31 ngành.
    _all_lbl_disp = _ALL_LABEL if not _is_en else 'All sectors'
    _wl_label = 'Yêu thích' if not _is_en else 'Watchlist'
    _ticker_unit  = 'mã' if not _is_en else 'tickers'
    _SECTOR_OPTS = [_ALL_LABEL, _wl_label] + _ALL_SECTORS
    if 'tb_sector' not in st.session_state:
        st.session_state['tb_sector'] = _ALL_LABEL
    # 1 lần đọc file watchlist — sau đó cả sector dropdown + star button
    # dùng chung biến _wl_now (kiểm tra is_watching = check thuần Python).
    from services.watchlist import get_watchlist as _get_wl
    _wl_now = _get_wl()
    sector = c[0].selectbox(
        'Ngành' if not _is_en else 'Sector',
        _SECTOR_OPTS, key='tb_sector',
        format_func=lambda s: (_all_lbl_disp if s == _ALL_LABEL
                               else (f'{_wl_label} ({len(_wl_now)} {_ticker_unit})'
                                     if s == _wl_label
                                     else f'{s} ({_SECTOR_COUNTS.get(s,0)} {_ticker_unit})')),
    )

    # MÃ filtered theo ngành — ưu tiên 3 mã default ở đầu nếu chọn "Tất cả".
    if sector == _ALL_LABEL:
        ticker_opts = _TICKER_ORDER
    elif sector == _wl_label:
        ticker_opts = [tk for tk in _wl_now if tk in TICKERS] or _TICKER_ORDER[:3]
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

    # v56 — Chen mã user vừa chọn LÊN ĐẦU queue warmer (priority 0).
    # Nếu mã đã warm → call no-op. Nếu chưa → bắt đầu warm song song với
    # rerun foreground → tab switch sẽ instant ngay lần thứ hai.
    try:
        from services.warmup import prioritize as _prioritize_warm
        _prioritize_warm(ticker)
    except Exception:
        pass

    # Watchlist toggle (per-user) — bật/tắt mã đang chọn vào watchlist.
    # Label = text Vietnamese ngắn gọn (Streamlit standard button không nhận HTML).
    # `_wl_now` đã tính 1 lần ở phía trên (cho sector dropdown count) — giờ
    # chỉ check thuần Python set, KHÔNG đọc lại file.
    from services.watchlist import toggle as _wl_toggle
    _is_wl = (ticker or '').upper() in set(_wl_now)
    c[2].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if _is_wl:
        _wl_btn_label = 'Đã lưu' if not _is_en else 'Saved'
        _star_help    = 'Bỏ khỏi danh mục yêu thích' if not _is_en else 'Remove from watchlist'
    else:
        _wl_btn_label = 'Lưu mã' if not _is_en else 'Save'
        _star_help    = 'Thêm vào danh mục yêu thích' if not _is_en else 'Add to watchlist'
    if c[2].button(_wl_btn_label, key='_wl_toggle',
                    use_container_width=True, help=_star_help,
                    type='primary' if _is_wl else 'secondary'):
        _wl_toggle(ticker)
        st.rerun()

    train_ratio = c[3].slider(t('sidebar.train_ratio'), 70, 90, 80, step=5,
                              format='%d%%', key='tb_ratio') / 100
    if 'sb_ar_order' not in st.session_state:
        st.session_state['sb_ar_order'] = 1
    ar_order = c[4].number_input(
        'p', min_value=1, max_value=100, value=st.session_state['sb_ar_order'],
        step=1, key='sb_ar_order', help=t('sidebar.ar_order_help'))
    _today = _dt.date.today()
    if 'sb_date_from' not in st.session_state:
        st.session_state['sb_date_from'] = _dt.date(2016, 1, 1)
    if 'sb_date_to' not in st.session_state:
        st.session_state['sb_date_to'] = _today
    date_from = c[5].date_input(t('sidebar.from'), key='sb_date_from',
                                format='YYYY/MM/DD')
    date_to = c[6].date_input(t('sidebar.to'), key='sb_date_to',
                              format='YYYY/MM/DD')

    # Nút Dark / Lang / Refresh — căn xuống cho thẳng hàng input
    c[7].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    c[8].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    c[9].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if c[7].button('Sáng' if _is_dark else 'Tối', key='tb_dark',
                   use_container_width=True, help='Dark / Light'):
        st.session_state.theme_mode = 'light' if _is_dark else 'dark'
        st.rerun()
    if c[8].button('VI' if _is_en else 'EN', key='tb_lang',
                   use_container_width=True, help='Ngôn ngữ / Language'):
        st.session_state.lang = 'VI' if _is_en else 'EN'
        st.rerun()
    if c[9].button('↻', key='tb_refresh', use_container_width=True,
                   help=t('common.refresh')):
        for _k in ['_data_cache_key', '_df', '_r1', '_r2', '_r3',
                   '_m1', '_m2', '_m3']:
            st.session_state.pop(_k, None)
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.rerun()

    st.markdown(f"<hr style='border:none;border-top:1px solid {_CHIP_BRD};margin:4px 0 10px'/>",
                unsafe_allow_html=True)
    return page, ticker, train_ratio, date_from, date_to, int(ar_order)

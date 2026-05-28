import sys, os
# Windows console mặc định cp1252 → vnstock in tiếng Việt ra stdout sẽ bốc
# UnicodeEncodeError ('charmap codec can't encode'). Ép utf-8 sớm + errors=replace
# để không bao giờ vỡ luồng fetch.
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import streamlit as st
import warnings
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

from core.config import PAGE_TITLE, PAGE_ICON, LAYOUT, SIDEBAR_STATE
from core.themes import theme
from core.i18n import t
from data.fetcher import fetch_data
from data.metrics import calc_metrics
from models.ar    import run_ar
from models.mlr   import run_mlr
from models.arima import run_arima
from core.validate import validate_params
from ui.css import inject_global_css, inject_theme_css
from ui.js import inject_theme_js, hide_streamlit_badges_js
from ui.topbar import render_topbar

# v40 PERF: Lazy page imports — chỉ load module khi user navigate đến.
# Trước: 6 imports eager × ~50ms = ~300ms cold start. Giờ chỉ 1 page.

# Favicon = logo FinScope (PNG đồng bộ thương hiệu); fallback emoji nếu thiếu file.
from pathlib import Path as _Path
_fav = _Path(__file__).resolve().parent / 'static' / 'finscope_favicon.png'
_page_icon = str(_fav) if _fav.exists() else PAGE_ICON

st.set_page_config(
    page_title=PAGE_TITLE,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
    page_icon=_page_icon,
)

if 'theme_mode' not in st.session_state:
    st.session_state['theme_mode'] = 'light'
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'VI'

_T = theme()

# CSS/JS phải inject MỖI rerun — Streamlit garbage-collect các st.markdown
# element không re-render → gating bằng session_state làm sidebar dark blue
# biến mất sau rerun đầu. Trade-off: chấp nhận chi phí websocket.
inject_global_css()
inject_theme_css(_T)
inject_theme_js(_T)
hide_streamlit_badges_js()

# ẨN UI CHUẨN: dùng config.toml với toolbarMode="minimal" (đã set ở .streamlit/config.toml)
# → Manage app button, hamburger menu, header bị ẩn CHÍNH THỨC (không cần CSS hack)
# Badge "Hosted with Streamlit" — branding bắt buộc của Streamlit free tier,
# không có cách technical nào ẩn 100% (các hack CSS/JS hoạt động không ổn định).
st.markdown("""
<style>
    [class*="viewerBadge"], [class*="ViewerBadge"],
    [class*="_profileContainer_"], [class*="profileContainer"],
    [data-testid="stDecoration"],
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    [data-testid*="manage-app"],
    .stDeployButton, .stAppDeployButton,
    a[href*="share.streamlit.io"]:not([href*="docs"]),
    #MainMenu,
    /* Sidebar không còn dùng (điều hướng + tham số đã chuyển lên topbar) */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Topbar cần khoảng đệm trên nhỏ hơn để gọn */
    .main .block-container, [data-testid="stMain"] .block-container {
        padding-top: 1.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Splash/cover page: chỉ hiện 1 lần khi user vào app, click "Vào Ngay" để đến main app
if not st.session_state.get('_splash_done'):
    from app_pages import splash as _pg_splash
    _pg_splash.render()
    st.stop()

# Preload mã mặc định 1 lần duy nhất mỗi session → UX mượt hơn
from core.preload import preload_all_tickers, trigger_bg_arima
preload_all_tickers()

# Điều hướng + tham số ở TOP main area (luôn hiển thị, không phụ thuộc sidebar)
page, ticker, train_ratio, date_from, date_to, ar_order = render_topbar()

# ── Tải dữ liệu (bọc try/except: mã lỗi hoặc vnstock rate-limit 20 req/phút
#    KHÔNG làm sập app — hiện thông báo thân thiện) ──────────────────────────
try:
    _df_for_validate = fetch_data(ticker, date_from, date_to)
except Exception as _fe:
    _is_en_err = st.session_state.get('lang', 'VI') == 'EN'
    _msg = str(_fe)
    _rate = ('rate' in _msg.lower() or 'limit' in _msg.lower()
             or '20' in _msg or 'request' in _msg.lower())
    if _rate:
        _body = ('Nguồn dữ liệu (vnstock) đang giới hạn ~20 lượt/phút. '
                 'Vui lòng chờ ~60 giây rồi thử lại, hoặc chọn lại mã đã xem.'
                 if not _is_en_err else
                 'The data source (vnstock) is rate-limited (~20 req/min). '
                 'Please wait ~60s and retry, or reselect a previously viewed ticker.')
    else:
        _body = (f'Không tải được dữ liệu cho mã <b>{ticker}</b>. '
                 f'Hãy chọn mã khác. (Chi tiết: {_msg[:120]})'
                 if not _is_en_err else
                 f'Could not load data for <b>{ticker}</b>. '
                 f'Please pick another ticker. (Detail: {_msg[:120]})')
    st.markdown(
        f'<div style="background:#FEF3C7;border:2px solid #D97706;border-radius:12px;'
        f'padding:22px 26px;margin:20px 0">'
        f'<div style="font-size:14px;font-weight:800;color:#92400E;'
        f'text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">'
        f'{"Tạm thời chưa tải được dữ liệu" if not _is_en_err else "Data temporarily unavailable"}</div>'
        f'<div style="font-size:13px;color:#78350F;line-height:1.6">{_body}</div>'
        f'</div>', unsafe_allow_html=True)
    st.stop()

# ── Validate tham số AR order trước khi train ─────
_n_total = len(_df_for_validate)
_valid   = validate_params(ar_order, _n_total, train_ratio)

if _valid['overall'] == 'err':
    _err_html = (
        f'<div style="background:#FEE2E2;border:2px solid #DC2626;'
        f'border-radius:12px;padding:24px 28px;margin:20px 0">'
        f'<div style="font-size:14px;font-weight:800;color:#991B1B;'
        f'letter-spacing:1px;text-transform:uppercase;margin-bottom:10px">'
        f'{t("validate.blocked")}</div>'
        f'<div style="font-size:13px;color:#7F1D1D;'
        f'margin-bottom:6px;font-family:monospace">'
        f'{_valid["p_msg"]}</div>'
        f'</div>'
    )
    st.markdown(_err_html, unsafe_allow_html=True)
    st.stop()
elif _valid['overall'] == 'warn':
    st.warning(_valid['p_msg'])

_cache_key = f"{ticker}_{train_ratio:.3f}_{date_from}_{date_to}_p{ar_order}"
_need_reload = (
    '_data_cache_key' not in st.session_state or
    st.session_state._data_cache_key != _cache_key
)

if _need_reload:
    # Invalidate PDF cache khi data đổi → user sẽ thấy button "Xuất PDF" lại
    st.session_state.pop('_pdf_bytes', None)

    from ui.components import render_training_overlay
    import time as _time

    _prog_ph  = st.empty()
    _title    = 'Đang huấn luyện mô hình' if st.session_state.get('lang', 'VI') == 'VI' \
                else 'Training models'
    _subtitle = f'{ticker} · Train ratio {int(train_ratio*100)}% · p={ar_order}'

    def _show(step, total, task):
        _prog_ph.markdown(
            render_training_overlay(_title, _subtitle, step, total, task, _T),
            unsafe_allow_html=True)

    _show(0, 3, t('load.market'))
    df = fetch_data(ticker, date_from, date_to)

    # ── HUẤN LUYỆN SONG SONG cả 7 mô hình (1 lần) → warm cache ──────────
    # Mỗi run_* đã @st.cache_data → các trang sau chỉ đọc cache (tức thì).
    # Chạy đồng thời → tổng thời gian ≈ mô hình lâu nhất (ARIMA ~3s) thay vì
    # cộng dồn tuần tự ~13s.
    _show(1, 3, ('Huấn luyện song song các mô hình...'
                 if st.session_state.get('lang', 'VI') == 'VI'
                 else 'Training models in parallel...'))
    from concurrent.futures import ThreadPoolExecutor as _TPE
    from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
    from models.ml import run_gbr
    _mkw = dict(p=ar_order, date_from=date_from, date_to=date_to)
    with _TPE(max_workers=8) as _ex:
        _futs = {
            'ar':      _ex.submit(run_ar,      ticker, train_ratio, **_mkw),
            'mlr':     _ex.submit(run_mlr,     ticker, train_ratio, **_mkw),
            'arima':   _ex.submit(run_arima,   ticker, train_ratio, **_mkw),
            'sarima':  _ex.submit(run_sarima,  ticker, train_ratio, **_mkw),
            'ets':     _ex.submit(run_ets,     ticker, train_ratio, **_mkw),
            'garch':   _ex.submit(run_garch,   ticker, train_ratio, **_mkw),
            'sarimax': _ex.submit(run_sarimax, ticker, train_ratio, **_mkw),
            'gbr':     _ex.submit(run_gbr,     ticker, train_ratio, **_mkw),
        }
        r1 = _futs['ar'].result()
        r2 = _futs['mlr'].result()
        r3 = _futs['arima'].result()
        # mô hình nâng cao + GBR — chỉ cần .result() để warm cache (bỏ qua lỗi lẻ)
        for _k in ('sarima', 'ets', 'garch', 'sarimax', 'gbr'):
            try:
                _futs[_k].result()
            except Exception:
                pass

    _show(2, 3, t('load.metrics'))
    m1 = calc_metrics(r1['yte'], r1['pte'], k=ar_order)
    m2 = calc_metrics(r2['yte'], r2['pte'], k=3 * ar_order)
    # ARIMA: số tham số ≈ p + q + 1 (hằng số) — dùng cho R²adj
    _k3 = sum(r3.get('order', (ar_order, 0, 0))) + 1
    m3 = calc_metrics(r3['yte'], r3['pte'], k=_k3)

    _show(5, 5, 'Done.')
    _time.sleep(0.3)
    _prog_ph.empty()
    st.session_state._data_cache_key = _cache_key
    st.session_state._df = df
    st.session_state._r1 = r1
    st.session_state._r2 = r2
    st.session_state._r3 = r3
    st.session_state._m1 = m1
    st.session_state._m2 = m2
    st.session_state._m3 = m3

    # Lần đầu load xong → rerun 1 lần duy nhất để sidebar tái render với
    # session_state đầy đủ → nút "Xuất PDF" hiện ngay không phải đợi
    # user click đi tab khác.
    if not st.session_state.get('_first_load_done'):
        st.session_state['_first_load_done'] = True
        trigger_bg_arima(ticker, ar_order, date_from, date_to)
        st.rerun()

    trigger_bg_arima(ticker, ar_order, date_from, date_to)
else:
    df = st.session_state._df
    r1 = st.session_state._r1
    r2 = st.session_state._r2
    r3 = st.session_state._r3
    m1 = st.session_state._m1
    m2 = st.session_state._m2
    m3 = st.session_state._m3

_args = (ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
         ar_order)

if page == 'Dashboard Tổng quan':
    from app_pages import dashboard as _pg_dash
    _pg_dash.render(*_args)
elif page == 'Tổng quan Thị trường':
    from app_pages import market as _pg_market
    _pg_market.render(*_args)
elif page == 'Phân tích Cơ bản':
    from app_pages import fundamental as _pg_fund
    _pg_fund.render(*_args)
elif page == 'Phân tích Chi tiết':
    from app_pages import analysis as _pg_ana
    _pg_ana.render(*_args)
elif page == 'Mô hình Nâng cao':
    from app_pages import advanced as _pg_adv
    _pg_adv.render(*_args)
elif page == 'Chiến lược Giao dịch':
    from app_pages import strategy as _pg_strat
    _pg_strat.render(*_args)
elif page == 'Tin tức Thị trường':
    from app_pages import news as _pg_news
    _pg_news.render(*_args)
elif page == 'Tín hiệu & Cảnh báo':
    from app_pages import signals as _pg_sig
    _pg_sig.render(*_args)
elif page == 'Lịch sử & Dữ liệu':
    from app_pages import history as _pg_hist
    _pg_hist.render(*_args)
elif page == 'Danh mục Đầu tư':
    from app_pages import portfolio as _pg_port
    _pg_port.render(*_args)
elif page == 'Giao dịch Demo':
    from app_pages import paper as _pg_paper
    _pg_paper.render(*_args)
elif page == 'Hướng dẫn Sử dụng':
    from app_pages import guide as _pg_guide
    _pg_guide.render(*_args)

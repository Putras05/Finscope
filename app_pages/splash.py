import streamlit as st
import base64
from pathlib import Path

from ui.logo import mark_gradient


def _img_b64(filename: str) -> str:
    """Đọc ảnh từ static/ và encode base64."""
    p = Path(__file__).resolve().parent.parent / 'static' / filename
    if not p.exists():
        return ''
    return base64.b64encode(p.read_bytes()).decode()


def render():
    """Splash page — light theme. Avoids Streamlit's 4-space-indent
    code-block trap by joining HTML parts WITHOUT leading whitespace."""

    tdt_b64 = _img_b64('TDT_logo.png')
    khoa_b64 = _img_b64('khoa_logo.png')

    # ── PRELOAD pro-style: warm sẵn 7 mô hình của mã mặc định NGAY khi hiện
    #    trang bìa (tận dụng vài giây user đọc cover) → bấm VÀO NGAY là
    #    Dashboard hiện gần như tức thì. Chạy 1 lần / session, daemon thread. ──
    if not st.session_state.get('_splash_warm_started'):
        st.session_state['_splash_warm_started'] = True
        import threading as _th

        def _warm_default():
            try:
                from core.constants import TICKERS
                from data.fetcher import fetch_data
                from models.ar import run_ar
                from models.mlr import run_mlr
                from models.arima import run_arima
                from models.advanced import (run_sarima, run_ets,
                                             run_garch, run_sarimax)
                from models.ml import run_gbr
                tk = TICKERS[0]
                fetch_data(tk)  # warm raw data (1 network call) trước
                for _fn in (run_ar, run_mlr, run_arima, run_sarima,
                            run_ets, run_garch, run_sarimax, run_gbr):
                    try:
                        _fn(tk, 0.80, p=1)
                    except Exception:
                        pass
                # Warm PhoBERT pipeline (đọc hiểu AI cho tin) — nếu transformers
                # có sẵn → nạp ngầm để khi user tới trang News/Strategy không phải
                # đợi load. Thiếu thư viện → bỏ qua (deploy-safe, fallback lexicon).
                try:
                    from data.news_ai import dl_available, _load_dl_pipeline
                    if dl_available():
                        _load_dl_pipeline()
                except Exception:
                    pass
                # Warm tin tức RSS + sentiment (cache 30') để thẻ "Tâm lý
                # tin tức" trên Dashboard hiện tức thì, không chờ mạng.
                try:
                    from data.news import news_sentiment
                    news_sentiment(tk)
                except Exception:
                    pass
                # Warm Phân tích Cơ bản (income + balance, cache 1h) — fetch
                # song song income+balance đã giảm còn ~3s; pre-warm ở đây để
                # khi user click vào trang là tức thì.
                try:
                    from data.fundamental import fetch_financials
                    fetch_financials(tk)
                except Exception:
                    pass
                # Warm Tổng quan Thị trường (price_board 53 mã, cache 5')
                try:
                    from data.market import market_snapshot
                    from core.constants import TICKERS as _TICKERS
                    market_snapshot(tuple(_TICKERS))
                except Exception:
                    pass
                # ── v52 PRE-WARM AGGRESSIVE — warm thêm cho tab switching mượt ──
                # Warm VN-Index để CAPM section (Portfolio) tức thì
                try:
                    from services.capm import fetch_vnindex
                    fetch_vnindex()
                except Exception:
                    pass
                # Warm signal engine 8 trụ + ichimoku + technicals cho top 3 mã
                # → các tab Tín hiệu, Paper Pro Suggest, Strategy mở tức thì
                try:
                    from services.signal_engine import build_signal_report
                    from data.fetcher import fetch_data as _fd
                    from data.ichimoku import add_ichimoku
                    from data import technicals as _TA
                    for _tk_warm in TICKERS[:3]:                # FPT, MWG, MSN
                        try:
                            _df = _fd(_tk_warm)
                            add_ichimoku(_df)                  # cache ichimoku
                            _TA.support_resistance(_df)       # cache S/R
                            _TA.trend_channel(_df, lookback=90)
                            _TA.adx(_df); _TA.obv(_df)
                            _TA.parabolic_sar(_df)
                            _TA.candlestick_patterns(_df, lookback=12)
                            build_signal_report(_df, _tk_warm,
                                                  include_fundamentals=False)
                        except Exception:
                            pass
                except Exception:
                    pass
                # Warm peer_kpis cho mã đầu tiên (Phân tích Cơ bản tab Peer)
                try:
                    from data.fundamental import peer_kpis
                    peer_kpis(TICKERS[0], max_peers=6)
                except Exception:
                    pass
            except Exception:
                pass
        _th.Thread(target=_warm_default, daemon=True).start()

    # Ẩn sidebar TRONG splash bằng style ở parent <head> có id riêng →
    # app chính gỡ chính xác theo id (không để CSS sót lại che sidebar).
    import streamlit.components.v1 as _components
    _components.html("""
<script>
(function(){
  try{ var doc = window.parent.document; }catch(e){ return; }
  if(!doc || doc.getElementById('__splash_css__')) return;
  var s = doc.createElement('style'); s.id='__splash_css__';
  s.textContent='[data-testid=\\"stSidebar\\"],[data-testid=\\"collapsedControl\\"],[data-testid=\\"stSidebarCollapsedControl\\"]{display:none !important;}';
  (doc.head||doc.documentElement).appendChild(s);
})();
</script>
""", height=0)

    # ── CSS — raw triple-string, no f-string, no indent traps ──
    css = """<style>
html body .stApp, html body [data-testid="stAppViewContainer"], html body [data-testid="stMain"], html body section.main {
background: radial-gradient(ellipse at 20% 0%, rgba(59,130,246,0.08) 0, transparent 55%), radial-gradient(ellipse at 80% 100%, rgba(30,64,175,0.06) 0, transparent 60%), linear-gradient(165deg, #FFFFFF 0%, #F8FAFC 50%, #F1F5F9 100%) !important;
background-attachment: fixed !important;
min-height: 100vh !important;
}
[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
.main .block-container { padding-top: 1.5rem !important; max-width: 920px !important; background: transparent !important; }
[data-testid="stAppViewContainer"]::before, .stApp::before {
content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
background-image: linear-gradient(rgba(30,64,175,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(30,64,175,0.04) 1px, transparent 1px);
background-size: 48px 48px;
mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
-webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
}
.splash-wrap { position: relative; z-index: 10; max-width: 880px; margin: 0 auto; padding: 24px 32px 16px; text-align: center; animation: splash-fade-in 0.8s ease-out; }
@keyframes splash-fade-in { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.splash-logos { display: flex; justify-content: center; align-items: center; gap: 56px; margin-bottom: 24px; flex-wrap: wrap; }
.splash-logos img { height: 92px; width: auto; filter: drop-shadow(0 6px 16px rgba(30,64,175,0.15)); }
.splash-univ { text-align: center; flex: 0 1 320px; min-width: 240px; }
.splash-univ .name { display: block; font-weight: 800; color: #1E40AF !important; font-size: 17px; line-height: 1.4; letter-spacing: 0.6px; }
.splash-univ .faculty { display: inline-block; margin-top: 8px; padding: 6px 18px; font-size: 12px; font-weight: 700; color: #1E40AF !important; letter-spacing: 2px; background: rgba(59,130,246,0.10); border: 1px solid rgba(59,130,246,0.30); border-radius: 999px; }
.splash-badge { display: inline-block; margin: 18px 0 14px; padding: 7px 20px; font-size: 11px; font-weight: 700; color: #475569 !important; letter-spacing: 2.2px; text-transform: uppercase; background: rgba(241,245,249,0.7); border-top: 1px solid rgba(148,163,184,0.30); border-bottom: 1px solid rgba(148,163,184,0.30); }
.splash-title { font-family: 'Cambria','Times New Roman', Georgia, serif; font-weight: 700; color: #0F172A !important; font-size: 30px; line-height: 1.35; margin: 14px 0 6px; letter-spacing: 0.4px; }
.splash-title-accent { color: #1E40AF !important; font-style: italic; }
.splash-sep { display: block; width: 80px; height: 3px; margin: 18px auto 24px; background: linear-gradient(90deg, transparent, #1E40AF, transparent); border-radius: 2px; }
.splash-card { background: #FFFFFF !important; border: 1px solid rgba(148,163,184,0.25); border-left: 4px solid #1E40AF; border-radius: 12px; padding: 20px 28px; margin: 14px auto; max-width: 600px; box-shadow: 0 4px 14px rgba(15,23,42,0.06), 0 1px 3px rgba(15,23,42,0.04); text-align: left; position: relative; z-index: 5; }
.splash-card .label { display: block; font-size: 10.5px; font-weight: 800; color: #1E40AF !important; text-transform: uppercase; letter-spacing: 2.2px; margin-bottom: 10px; }
.splash-card .value { font-size: 15px; color: #0F172A !important; font-weight: 600; line-height: 1.85; }
.splash-card .value .author-id { color: #64748B !important; font-weight: 500; font-size: 13.5px; margin-left: 6px; }
.splash-card .value .author-role { color: #1E40AF !important; font-weight: 700; font-size: 11.5px; margin-left: 8px; letter-spacing: 0.4px; text-transform: uppercase; }
.splash-card .value .author-email { display: block; margin-top: 6px; font-size: 12px; color: #475569 !important; font-weight: 500; }
.splash-card .value .author-email a { color: #1E40AF !important; text-decoration: none; }
div[data-testid="stButton"] { display: flex; justify-content: center; margin: 32px auto 12px; position: relative; z-index: 5; }
div[data-testid="stButton"] > button { background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%) !important; color: #FFFFFF !important; font-weight: 800 !important; font-size: 15px !important; padding: 14px 44px !important; border-radius: 999px !important; border: none !important; letter-spacing: 2.5px !important; box-shadow: 0 6px 20px rgba(30,64,175,0.35), inset 0 1px 0 rgba(255,255,255,0.20) !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; min-width: 220px; }
div[data-testid="stButton"] > button:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 28px rgba(30,64,175,0.50) !important; }
.splash-footer { margin-top: 18px; font-size: 11px; color: #94A3B8 !important; letter-spacing: 1.6px; text-transform: uppercase; position: relative; z-index: 5; text-align: center; }
.splash-footer .dot { color: #CBD5E1; margin: 0 10px; }
</style>"""

    st.markdown(css, unsafe_allow_html=True)

    # ── HTML — list-join trick: ghép thành 1 string KHÔNG có \n đầu / indent
    # → Streamlit's CommonMark KHÔNG nhầm thành <pre><code>.
    html_parts = [
        '<div class="splash-wrap">',
        '<div class="splash-logos">',
        f'<img src="data:image/png;base64,{tdt_b64}" alt="TDTU"/>',
        '<div class="splash-univ">',
        '<span class="name">TRƯỜNG ĐẠI HỌC TÔN ĐỨC THẮNG</span>',
        '<br/>',
        '<span class="faculty">KHOA TOÁN — THỐNG KÊ</span>',
        '</div>',
        f'<img src="data:image/png;base64,{khoa_b64}" alt="Faculty"/>',
        '</div>',
        '<div class="splash-badge">Phân tích Chứng khoán Đa mô hình · 2026</div>',
        '<div class="splash-title">',
        # Wordmark style: "Fin" solid dark + "Scope" gradient blue→cyan→teal
        # (giống topbar — đã verified user duyệt). Letter-spacing âm chặt
        # hơn cho cảm giác hiện đại; font-feature liga + tnum cho fintech.
        ('<span style="display:inline-flex;align-items:center;gap:16px;'
         'justify-content:center;font-family:Inter,system-ui,sans-serif;'
         'font-size:58px;font-weight:900;letter-spacing:-2.2px;line-height:1;'
         'font-feature-settings:\'liga\' 1,\'tnum\' 1">'
         + mark_gradient(56) +
         '<span style="display:inline-block">'
         '<span style="color:#0F172A">Fin</span>'
         '<span style="background:linear-gradient(90deg,#1E40AF 0%,#0891B2 50%,#0F766E 100%);'
         '-webkit-background-clip:text;background-clip:text;color:transparent;'
         '-webkit-text-fill-color:transparent">Scope</span>'
         '</span></span><br/>'),
        '<span style="font-size:18px;color:#334155;font-weight:600;display:inline-block;margin-top:6px;letter-spacing:.3px">PHÂN TÍCH &amp; DỰ BÁO CHỨNG KHOÁN</span><br/>',
        '<span style="font-size:14px;color:#64748B;font-weight:500;font-style:italic">Dựa trên Mô hình Thống kê &amp; Học máy · Khoảng tin cậy · Chiến lược Giao dịch</span>',
        '</div>',
        '<span class="splash-sep"></span>',
        '<div class="splash-card">',
        '<span class="label">Nhóm tác giả</span>',
        '<div class="value">',
        'Nguyễn Thành Danh<span class="author-id">— C2300014</span>'
        '<span class="author-role">· Nhóm trưởng</span><br/>',
        'Trần Huỳnh Nhã Trúc<span class="author-id">— C2300189</span>'
        '<span class="author-role">· Thành viên</span>',
        '<span class="author-email">Liên hệ nhóm trưởng: '
        '<a href="mailto:thanhdanhgvt@gmail.com">thanhdanhgvt@gmail.com</a> · '
        '<a href="tel:+84931740509">0931 740 509</a></span>',
        '</div>',
        '</div>',
        '</div>',
    ]
    logo_html = ''.join(html_parts)
    st.markdown(logo_html, unsafe_allow_html=True)

    # ── KHỐI XÁC THỰC NGƯỜI DÙNG ──────────────────────────────────────
    _render_auth_panel()

    footer_html = (
        '<div class="splash-footer">'
        'HOSE Stock Forecasting '
        '<span class="dot">·</span> Statistical &amp; Machine Learning Models '
        '<span class="dot">·</span> 2026'
        '</div>'
    )
    st.markdown(footer_html, unsafe_allow_html=True)


def _render_auth_panel() -> None:
    """3 tab: Đăng nhập · Đăng ký · Khách. Khi xác thực thành công → vào app."""
    import streamlit as _st
    from auth.store import create_user, verify_credentials, update_last_seen
    from auth.session import login_user, login_as_guest

    # v58 — Bỏ wrapper div unclosed (gây Streamlit tabs render OUTSIDE card
    # → user thấy ô trống). Chỉ giữ HEADER label centered, tabs render
    # bình thường dưới với styling từ stTabs CSS.
    _st.markdown(
        '<div style="max-width:560px;margin:18px auto 6px;'
        'text-align:center;font-size:12px;font-weight:800;'
        'color:#1E40AF;text-transform:uppercase;letter-spacing:2.2px;'
        'padding:10px 0 8px">Tài khoản · Account</div>',
        unsafe_allow_html=True)

    tab_login, tab_reg, tab_guest = _st.tabs([
        '  Đăng nhập  ', '  Đăng ký  ', '  Dùng thử (Khách)  ',
    ])

    with tab_login:
        with _st.form('_login_form', clear_on_submit=False):
            u = _st.text_input('Tên đăng nhập', key='_lg_u',
                                placeholder='ví dụ: thanhdanh')
            p = _st.text_input('Mật khẩu', type='password', key='_lg_p',
                                placeholder='Tối thiểu 6 ký tự')
            ok = _st.form_submit_button('ĐĂNG NHẬP', use_container_width=True,
                                          type='primary')
        if ok:
            ok2, msg, rec = verify_credentials(u or '', p or '')
            if ok2 and rec:
                login_user(rec)
                update_last_seen(rec['id'])
                _st.session_state['_splash_done'] = True
                _st.rerun()
            else:
                _st.error(msg)

    with tab_reg:
        with _st.form('_reg_form', clear_on_submit=False):
            u = _st.text_input('Tên đăng nhập', key='_rg_u',
                                placeholder='3–32, chỉ chữ thường + số + . _ -')
            d = _st.text_input('Tên hiển thị', key='_rg_d',
                                placeholder='Ví dụ: Nguyễn Thành Danh')
            e = _st.text_input('Email (tuỳ chọn)', key='_rg_e')
            p1 = _st.text_input('Mật khẩu', type='password', key='_rg_p1',
                                  placeholder='Tối thiểu 6 ký tự')
            p2 = _st.text_input('Nhập lại mật khẩu', type='password', key='_rg_p2')
            ok = _st.form_submit_button('TẠO TÀI KHOẢN', use_container_width=True,
                                          type='primary')
        if ok:
            if (p1 or '') != (p2 or ''):
                _st.error('Hai lần nhập mật khẩu không khớp.')
            else:
                ok2, msg, rec = create_user(u or '', p1 or '', d or '', e or None)
                if ok2 and rec:
                    login_user(rec)
                    _st.session_state['_splash_done'] = True
                    _st.success(msg)
                    _st.rerun()
                else:
                    _st.error(msg)

    with tab_guest:
        if _st.button('VÀO NHANH VỚI TƯ CÁCH KHÁCH', key='_guest_enter',
                       use_container_width=True, type='primary'):
            login_as_guest()
            _st.session_state['_splash_done'] = True
            _st.rerun()

    # v58 — bỏ stray </div> (đã không còn wrapper div mở ở trên)

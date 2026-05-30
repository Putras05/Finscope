import streamlit as st


def _theme_css(T: dict) -> str:
    return f"""<style>
/* ══ APP BACKGROUND ══════════════════════════════════════════════════════════ */
.stApp {{ background: {T['bg_app']} !important; color: {T['text_primary']} !important; }}
[data-testid="stMain"] .block-container {{ background: transparent !important; color: {T['text_primary']} !important; }}

/* v58 — Inline code (text trong backticks) → màu đen + bg xám nhẹ, KHÔNG
   xanh lá mặc định Streamlit. Áp dụng cho table feature names (MA5_ratio,
   RSI14, ...) trong trang Chi tiết / Cơ sở Toán / Hướng dẫn. */
[data-testid="stMain"] code {{
    color: {T['text_primary']} !important;
    background: {T['bg_elevated']} !important;
    padding: 1px 5px !important;
    border-radius: 3px !important;
    font-size: 0.92em !important;
    font-family: 'Consolas', 'Menlo', monospace !important;
}}

/* v58 — GLOBAL: card/badge containers (div có border-radius + padding) hay
   bị clipped phía dưới do height inherent từ flex container. Force overflow
   visible + min content. Áp dụng cho card pattern phổ biến (P/E, ROE, KPI,
   pattern badges, sec-hdr, ...). */
[data-testid="stMain"] div[style*="border-radius:"][style*="border:"] {{
    overflow: visible !important;
}}
/* Card có border-top (KPI strip, ratios cards) — đảm bảo content không
   chạm mép dưới. Padding-bottom + min-height đủ cho 3-4 dòng text. */
[data-testid="stMain"] div[style*="border-top:3px"],
[data-testid="stMain"] div[style*="border-top: 3px"] {{
    padding-bottom: 14px !important;
    overflow: visible !important;
}}
/* Banner header (Dashboard/Cơ bản/Chiến lược/Lịch sử) — gradient dark blue
   thường bị cut at top. */
[data-testid="stMain"] div[style*="linear-gradient"][style*="border-radius:"] {{
    padding-top: 18px !important;
    padding-bottom: 18px !important;
}}

/* sidebar handled by _SIDEBAR_CSS — injected separately */

/* ══ MAIN CONTENT BUTTONS ════════════════════════════════════════════════════ */
[data-testid="stMain"] .stButton > button {{
    background: {T['bg_elevated']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important; font-weight: 600 !important;
    transition: background-color .14s, color .14s, border-color .14s !important;
}}
[data-testid="stMain"] .stButton > button:hover {{
    background: {T['accent']} !important;
    color: #ffffff !important;
    border-color: {T['accent']} !important;
}}

/* ══ METRIC CARDS ════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {{
    background: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    box-shadow: {T['shadow_sm']} !important;
}}
[data-testid="stMetricLabel"] p {{ color: {T['text_secondary']} !important; }}
[data-testid="stMetricValue"] {{ color: {T['text_primary']} !important; }}
[data-testid="stMetricDelta"] {{ color: {T['text_secondary']} !important; }}

/* ══ PAGE HEADER BANNER ══════════════════════════════════════════════════════ */
.page-header {{
    background: {T['banner_bg']} !important;
    border-radius: 14px !important;
    box-shadow: {T['shadow_md']} !important;
    border: none !important;
}}
.page-header h1 {{ color: {T['banner_text']} !important; }}
.page-header p  {{ color: {T['banner_subtext']} !important; }}

/* ══ SECTION HEADER ═════════════════════════════════════════════════════════ */
.sec-hdr {{
    color: {T['text_secondary']} !important;
    background: {T['bg_elevated']} !important;
    border-left: 4px solid {T['accent']} !important;
    padding: 7px 14px !important;
    border-radius: 0 6px 6px 0 !important;
    font-size: 10.5px !important; font-weight: 800 !important;
    letter-spacing: 1.2px !important; text-transform: uppercase !important;
    /* v58 — margin-bottom 18px (thay vì 12px) để header không dính chart Plotly
       phía dưới. Margin-top giữ 22px cho khoảng cách section. */
    margin: 22px 0 18px !important;
    display: block !important;
    line-height: 1.4 !important;
}}

/* ══ TABS ════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
    background: {T['bg_elevated']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important; padding: 4px !important; gap: 6px !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {T['text_secondary']} !important; background: transparent !important;
    border-radius: 8px !important; padding: 10px 28px !important;
}}
.stTabs [aria-selected="true"] {{
    background: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    box-shadow: {T['shadow_sm']} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    background: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 0 0 10px 10px !important; padding: 18px !important;
}}

/* ══ ALERT CARDS — dark mode override ═══════════════════════════════════════ */
{('''
.alert-buy  { background: #0D2B15 !important; border-color: #34D399 !important; color: #86EFAC !important; }
.alert-sell { background: #2B0D0D !important; border-color: #F87171 !important; color: #FCA5A5 !important; }
.alert-warn { background: #2B200D !important; border-color: #FCD34D !important; color: #FDE68A !important; }
.alert-neut { background: #1A2233 !important; border-color: #64748B !important; color: #CBD5E1 !important; }
/* FIX A2: Forecast card colors (up/down/flat) — dark mode override */
.up   { background: rgba(52,211,153,0.15) !important; color: #86EFAC !important; }
.down { background: rgba(248,113,113,0.15) !important; color: #FCA5A5 !important; }
.flat { background: rgba(148,163,184,0.15) !important; color: #CBD5E1 !important; }
''' if T.get('is_dark') else '')}

/* ══ DATAFRAMES — full theme-aware fix ══════════════════════════════════════ */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrameResizable"],
[data-testid="stDataFrameResizable"] > div {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
}}
[data-testid="stDataFrame"] {{
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"] iframe {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
}}
[data-testid="stDataFrame"] thead tr th,
[data-testid="stDataFrame"] [role="columnheader"] {{
    background: {T['bg_elevated']} !important;
    background-color: {T['bg_elevated']} !important;
    color: {T['text_secondary']} !important;
    border-bottom: 2px solid {T['border']} !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    padding: 10px 12px !important;
}}
[data-testid="stDataFrame"] tbody tr td,
[data-testid="stDataFrame"] [role="cell"],
[data-testid="stDataFrame"] [role="gridcell"] {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border-bottom: 1px solid {T['divider']} !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
}}
[data-testid="stDataFrame"] [role="rowheader"] {{
    background: {T['bg_elevated']} !important;
    color: {T['text_secondary']} !important;
    font-weight: 600 !important;
}}
[data-testid="stDataFrame"] *:not([style*="color"]) {{
    color: {T['text_primary']} !important;
}}
[data-testid="stElementToolbar"],
[data-testid="stElementToolbar"] button {{
    background: {T['bg_card']} !important;
    color: {T['text_secondary']} !important;
    border-color: {T['border']} !important;
}}

/* ══ EXPANDERS ═══════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important; border-radius: 10px !important;
}}
[data-testid="stExpander"] summary {{
    color: {T['text_primary']} !important; font-weight: 600 !important;
    background: {T['bg_elevated']} !important;
}}
[data-testid="stExpander"] > div,
[data-testid="stExpander"] .streamlit-expanderContent,
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
}}
[data-testid="stExpander"] p,
[data-testid="stExpander"] li,
[data-testid="stExpander"] span:not(.katex *),
[data-testid="stExpander"] strong {{
    color: {T['text_primary']} !important;
}}
[data-testid="stExpander"] table {{
    background: {T['bg_card']} !important;
    border-collapse: collapse !important;
    width: 100% !important;
}}
[data-testid="stExpander"] th {{
    background: {T['bg_elevated']} !important;
    color: {T['text_secondary']} !important;
    padding: 6px 12px !important;
    border: 1px solid {T['border']} !important;
    font-size: 12px !important;
}}
[data-testid="stExpander"] td {{
    background: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    padding: 6px 12px !important;
    border: 1px solid {T['border']} !important;
    font-size: 13px !important;
}}
.katex, .katex * {{ color: {T['text_primary']} !important; }}

/* ══ INFO BOXES ══════════════════════════════════════════════════════════════ */
.info-box {{
    background: {T['bg_elevated']} !important;
    border-color: {T['border']} !important;
    color: {T['text_primary']} !important;
}}

/* ══ DOWNLOAD BUTTON ═════════════════════════════════════════════════════════ */
[data-testid="stMain"] [data-testid="stDownloadButton"] > button,
[data-testid="stMain"] .stDownloadButton > button {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border: 1.5px solid {T['border']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: background-color .14s, color .14s, border-color .14s !important;
}}
[data-testid="stMain"] [data-testid="stDownloadButton"] > button *,
[data-testid="stMain"] .stDownloadButton > button * {{
    color: {T['text_primary']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] [data-testid="stDownloadButton"] > button:hover,
[data-testid="stMain"] .stDownloadButton > button:hover {{
    background: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
}}
[data-testid="stMain"] [data-testid="stDownloadButton"] > button:hover *,
[data-testid="stMain"] .stDownloadButton > button:hover * {{
    color: #FFFFFF !important;
}}

/* ══ PRESET CHIPS + ALL MAIN-AREA COLUMN BUTTONS ════════════════════════════ */
/* FIX 2026-04-23: chip/button trong column → pill oval viền xanh nhạt
   (nhất quán với chatbot page suggestion chips) */
[data-testid="stMain"] [data-testid="stColumn"] .stButton > button,
[data-testid="stMain"] [data-testid="column"] .stButton > button,
[data-testid="stMain"] [data-testid="stHorizontalBlock"] .stButton > button {{
    background: {'rgba(96,165,250,0.15)' if T.get('is_dark') else 'rgba(21,101,192,0.08)'} !important;
    background-color: {'rgba(96,165,250,0.15)' if T.get('is_dark') else 'rgba(21,101,192,0.08)'} !important;
    color: {T['accent']} !important;
    border: 1px solid {T['accent']} !important;
    border-radius: 20px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    min-height: 38px !important;
    transition: background-color .14s, color .14s, border-color .14s !important;
}}
[data-testid="stMain"] [data-testid="stColumn"] .stButton > button *,
[data-testid="stMain"] [data-testid="column"] .stButton > button *,
[data-testid="stMain"] [data-testid="stHorizontalBlock"] .stButton > button * {{
    color: {T['accent']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] [data-testid="stColumn"] .stButton > button:hover,
[data-testid="stMain"] [data-testid="column"] .stButton > button:hover,
[data-testid="stMain"] [data-testid="stHorizontalBlock"] .stButton > button:hover {{
    background: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
    box-shadow: 0 4px 12px {T['accent']}40 !important;
}}
[data-testid="stMain"] [data-testid="stColumn"] .stButton > button:hover *,
[data-testid="stMain"] [data-testid="column"] .stButton > button:hover *,
[data-testid="stMain"] [data-testid="stHorizontalBlock"] .stButton > button:hover * {{
    color: #FFFFFF !important;
}}

/* ══ DATE INPUT (main area) ══════════════════════════════════════════════════ */
[data-testid="stMain"] [data-baseweb="input"] {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 20px !important;
    min-height: 40px !important;
    padding: 0 14px !important;
    transition: border-color .14s !important;
}}
[data-testid="stMain"] [data-baseweb="input"]:focus-within {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 2px {T['accent']}33 !important;
}}
[data-testid="stMain"] [data-baseweb="input"] input,
[data-testid="stMain"] [data-baseweb="input"] * {{
    background: transparent !important;
    background-color: transparent !important;
    color: {T['text_primary']} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
[data-testid="stMain"] .stDateInput > div > div {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 20px !important;
    min-height: 40px !important;
}}
[data-testid="stMain"] .stDateInput input,
[data-testid="stMain"] .stDateInput [data-baseweb="input"] * {{
    color: {T['text_primary']} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    background: transparent !important;
}}
/* ══ SELECTBOX & NUMBER INPUT (main area) ════════════════════════════════════ */
[data-testid="stMain"] .stSelectbox > div > div,
[data-testid="stMain"] [data-testid="stSelectbox"] > div > div,
[data-testid="stMain"] [data-baseweb="select"] > div {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 20px !important;
    color: {T['text_primary']} !important;
}}
[data-testid="stMain"] .stSelectbox > div > div *,
[data-testid="stMain"] [data-baseweb="select"] * {{
    background: transparent !important;
    color: {T['text_primary']} !important;
}}
[data-testid="stMain"] .stNumberInput > div > div,
[data-testid="stMain"] [data-testid="stNumberInput"] > div > div {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 20px !important;
}}
[data-testid="stMain"] .stNumberInput input,
[data-testid="stMain"] [data-testid="stNumberInput"] input {{
    background: transparent !important;
    color: {T['text_primary']} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] label p, [data-testid="stMain"] label {{
    color: {T['text_secondary']} !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}}

/* ══ METRIC CARDS — aggressive child selectors ═══════════════════════════════ */
[data-testid="stMain"] [data-testid="metric-container"],
[data-testid="stMain"] [data-testid="stMetric"] {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    box-shadow: {T['shadow_sm']} !important;
    padding: 14px 16px !important;
}}
[data-testid="stMain"] [data-testid="stMetricLabel"] *,
[data-testid="stMain"] [data-testid="stMetricLabel"] p {{
    color: {T['text_secondary']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] [data-testid="stMetricValue"],
[data-testid="stMain"] [data-testid="stMetricValue"] * {{
    color: {T['text_primary']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] [data-testid="stMetricDelta"] * {{
    background: transparent !important;
}}

/* ══ REFRESH HEADER BUTTON ═══════════════════════════════════════════════════ */
.refresh-header-btn .stButton > button,
.refresh-header-btn .stButton > button:focus,
.refresh-header-btn .stButton > button:active,
.refresh-header-btn .stButton > button:focus:not(:active) {{
    background: linear-gradient(135deg,#0D1F4A 0%,#1B3D8C 60%,#2756C0 100%) !important;
    background-image: linear-gradient(135deg,#0D1F4A 0%,#1B3D8C 60%,#2756C0 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 22px !important;
    min-height: 60px !important;
    padding: 0 !important;
    transition: filter 0.2s ease, transform 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(27,61,140,0.4) !important;
}}
.refresh-header-btn .stButton > button:hover {{
    filter: brightness(1.2) !important;
    transform: rotate(180deg) !important;
}}
.refresh-header-btn .stButton > button p,
.refresh-header-btn .stButton > button span {{
    color: #FFFFFF !important;
    background: transparent !important;
}}

/* ══ DATE PICKER CALENDAR POPUP ══════════════════════════════════════════════ */
[data-baseweb="calendar"],
[data-baseweb="calendar"] > div,
[data-baseweb="popover"] [data-baseweb="calendar"] {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border']} !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
    border-radius: 10px !important;
}}
[data-baseweb="calendar"] * {{
    color: {T['text_primary']} !important;
    background: transparent !important;
    background-color: transparent !important;
}}
[data-baseweb="calendar"] [role="button"]:hover {{
    background: {T['accent']}33 !important;
    background-color: {T['accent']}33 !important;
}}
[data-baseweb="calendar"] [aria-selected="true"] {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
}}
[data-baseweb="calendar"] [aria-current="date"] {{
    border: 1px solid {T['accent']} !important;
}}
[data-baseweb="calendar"] [role="columnheader"] {{
    color: {T['text_muted']} !important;
    font-weight: 700 !important;
}}

/* ══ BEST MODEL GLOW ANIMATION ═══════════════════════════════════════════════ */
@keyframes best-glow {{
    0%, 100% {{ box-shadow: 0 0 5px #F9A825, 0 0 10px rgba(249,168,37,0.3); }}
    50%       {{ box-shadow: 0 0 18px #F9A825, 0 0 35px rgba(249,168,37,0.5); }}
}}
.best-model-card {{ animation: best-glow 2.5s ease-in-out infinite; }}

/* ══ LIVE DOT ANIMATION ══════════════════════════════════════════════════════ */
@keyframes live-pulse {{
    0%, 100% {{ opacity:1; transform:scale(1); box-shadow:0 0 6px {('#34D399' if T.get('is_dark') else '#10B981')}; }}
    50%       {{ opacity:.65; transform:scale(1.35); box-shadow:0 0 14px {('#34D399' if T.get('is_dark') else '#10B981')}; }}
}}
.live-dot {{
    /* v58 — green sáng hơn (#34D399) trên dark mode để contrast ≥ 4.5:1.
       Light mode giữ #10B981 (đậm hơn) cho contrast trên nền trắng.       */
    display:inline-block; width:8px; height:8px; border-radius:50%;
    background:{('#34D399' if T.get('is_dark') else '#10B981')}; margin-right:5px; vertical-align:middle;
    animation: live-pulse 2s infinite;
}}

/* ══ SLIDER (main area) ══════════════════════════════════════════════════════ */
[data-testid="stMain"] [data-testid="stSlider"] {{
    /* v58 — Tăng padding-bottom 10px để tick label (70%/90%) tách khỏi
       value bubble (80%) phía trên slider thumb. */
    padding: 4px 0 12px !important;
}}
/* v58 — ẨN tick label min/max (70% / 90%) — gây dính vị trí giữa value
   bubble + đôi khi lệch ra ngoài container. Value 80% đã hiển thị rõ. */
[data-testid="stMain"] [data-testid="stSlider"] [data-testid="stTickBar"],
[data-testid="stMain"] [data-testid="stSlider"] [data-testid="stTickBar"] * {{
    display: none !important;
}}
[data-testid="stMain"] [data-testid="stSlider"] [data-testid="stThumbValue"] p,
[data-testid="stMain"] [data-testid="stSlider"] [data-testid="stThumbValue"],
[data-testid="stMain"] [data-testid="stSlider"] output {{
    color: {T['accent']} !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    background: transparent !important;
    /* v58 — bubble value lên cao hơn (translateY -4px) để không đè tick */
    transform: translateY(-2px) !important;
}}
[data-testid="stMain"] [data-testid="stSlider"] [role="slider"] {{
    background: {T['accent']} !important;
    border: 2px solid {T['bg_card']} !important;
    box-shadow: 0 2px 8px {T['accent']}66 !important;
    width: 18px !important;
    height: 18px !important;
}}
[data-testid="stMain"] [data-testid="stSlider"] > div > div > div {{
    background: {T['border']} !important;
    height: 4px !important;
    border-radius: 2px !important;
}}
[data-testid="stMain"] [data-testid="stSlider"] > div > div > div > div {{
    background: {T['accent']} !important;
    height: 4px !important;
    border-radius: 2px !important;
}}

/* ══ HR ══════════════════════════════════════════════════════════════════════ */
hr {{ border-color: {T['border']} !important; }}

/* ══ FOCUS OUTLINES — Accessibility (Tab navigation) ═════════════════════════
   User dùng Tab/Shift-Tab điều hướng bàn phím sẽ thấy ring accent 2px.
   Chỉ hiện khi :focus-visible (click chuột không trigger, tránh ring thừa). */
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
[data-testid="stTextInput"] input:focus-visible,
[data-testid="stNumberInput"] input:focus-visible,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
[data-testid="stDateInput"] input:focus-visible,
[data-testid="stSlider"] [role="slider"]:focus-visible,
[data-testid="stChatInput"] textarea:focus-visible,
[data-baseweb="tab"]:focus-visible {{
    outline: 2px solid {T['accent']} !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 0 4px {('rgba(96,165,250,0.22)' if T.get('is_dark') else 'rgba(21,101,192,0.18)')} !important;
}}
/* Loại bỏ outline cũ xấu của Streamlit default */
.stButton > button:focus:not(:focus-visible) {{ outline: none !important; }}

/* ══ SCROLLBAR ═══════════════════════════════════════════════════════════════
   Style custom để nhìn rõ ở cả dark/light mode, rộng hơn default cho 4K.
   Dark mode: accent-blue tint trên bg tối (contrast cao).
   Light mode: gray với hover accent. */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{
    background: {T['bg_elevated']};
    border-radius: 10px;
}}
::-webkit-scrollbar-thumb {{
    background: {('rgba(96,165,250,0.35)' if T.get('is_dark') else 'rgba(148,163,184,0.55)')};
    border-radius: 10px;
    border: 2px solid {T['bg_elevated']};
}}
::-webkit-scrollbar-thumb:hover {{
    background: {('rgba(96,165,250,0.65)' if T.get('is_dark') else 'rgba(96,165,250,0.70)')};
}}
::-webkit-scrollbar-corner {{ background: transparent; }}
* {{ scrollbar-width: thin; scrollbar-color: {('rgba(96,165,250,0.35) transparent' if T.get('is_dark') else 'rgba(148,163,184,0.55) transparent')}; }}

/* ══ OVERRIDE: HIGH-SPECIFICITY CHIP + DOWNLOAD BUTTON FIX ══════════════════ */
[data-testid="stMain"] div[data-testid="stHorizontalBlock"] .stButton > button {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 20px !important;
    padding: 8px 16px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    min-height: 40px !important;
    transition: background-color 0.2s, color 0.2s, border-color 0.2s !important;
}}
[data-testid="stMain"] div[data-testid="stHorizontalBlock"] .stButton > button p {{
    color: {T['text_primary']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] div[data-testid="stHorizontalBlock"] .stButton > button:hover {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px {T['accent']}40 !important;
}}
[data-testid="stMain"] div[data-testid="stHorizontalBlock"] .stButton > button:hover p {{
    color: #FFFFFF !important;
    background: transparent !important;
}}
[data-testid="stMain"] div[data-testid="stDownloadButton"] > button,
[data-testid="stMain"] div .stDownloadButton > button {{
    background: {T['bg_card']} !important;
    background-color: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    padding: 12px 20px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 44px !important;
    transition: background-color 0.2s, color 0.2s, border-color 0.2s !important;
}}
[data-testid="stMain"] div[data-testid="stDownloadButton"] > button p,
[data-testid="stMain"] div .stDownloadButton > button p {{
    color: {T['text_primary']} !important;
    background: transparent !important;
}}
[data-testid="stMain"] div[data-testid="stDownloadButton"] > button:hover,
[data-testid="stMain"] div .stDownloadButton > button:hover {{
    background: {T['success']} !important;
    background-color: {T['success']} !important;
    color: #FFFFFF !important;
    border-color: {T['success']} !important;
}}
[data-testid="stMain"] div[data-testid="stDownloadButton"] > button:hover p,
[data-testid="stMain"] div .stDownloadButton > button:hover p {{
    color: #FFFFFF !important;
    background: transparent !important;
}}

/* ══ CHAT INPUT — theme-aware ════════════════════════════════════════════════ */
div[data-testid="stChatInput"] > div {{
    background: {T['bg_elevated']} !important;
    background-color: {T['bg_elevated']} !important;
    border: 2px solid {T['accent']} !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 12px {T['accent']}20 !important;
}}
div[data-testid="stChatInput"] > div:focus-within {{
    border-color: {T.get('accent_hover', T['accent'])} !important;
    box-shadow: 0 4px 16px {T['accent']}40 !important;
}}
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] [contenteditable],
div[data-testid="stChatInput"] input {{
    color: {T['text_primary']} !important;
    background: transparent !important;
    caret-color: {T['accent']} !important;
}}
div[data-testid="stChatInput"] * {{
    color: {T['text_primary']} !important;
}}
div[data-testid="stChatInput"] button,
div[data-testid="stChatInput"] button svg {{
    color: {T['accent']} !important;
    fill: {T['accent']} !important;
}}

/* v58 — Chat CSS đã xoá vì chatbot page bị remove khỏi app (~50 dòng dead) */

/* ══ ALL MAIN BUTTONS — legacy selectors + baseButton direct targeting ══════ */
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] .stButton > button p,
[data-testid="stMain"] .stButton > button span,
[data-testid="stMain"] .stButton > button div {{
    color: {T['text_primary']} !important;
}}
[data-testid="stMain"] .stButton > button[kind="primary"],
[data-testid="stMain"] .stButton > button[kind="primary"] p,
[data-testid="stMain"] .stButton > button[kind="primary"] span {{
    color: #FFFFFF !important;
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    border-color: {T['accent']} !important;
}}

/* ══ baseButton — direct element targeting (Streamlit 1.3x+) ════════════════ */
[data-testid="stMain"] [data-testid*="baseButton"] {{
    background: {T['bg_elevated']} !important;
    background-color: {T['bg_elevated']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border_strong']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background-color .14s, color .14s, border-color .14s !important;
}}
[data-testid="stMain"] [data-testid*="baseButton"] p,
[data-testid="stMain"] [data-testid*="baseButton"] span,
[data-testid="stMain"] [data-testid*="baseButton"] div {{
    color: {T['text_primary']} !important;
    background: transparent !important;
    background-color: transparent !important;
}}
[data-testid="stMain"] [data-testid*="baseButton"]:hover {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
}}
[data-testid="stMain"] [data-testid*="baseButton"]:hover p,
[data-testid="stMain"] [data-testid*="baseButton"]:hover span {{
    color: #FFFFFF !important;
}}
[data-testid="stMain"] [data-testid="baseButton-primary"] {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
}}
[data-testid="stMain"] [data-testid="baseButton-primary"] p,
[data-testid="stMain"] [data-testid="baseButton-primary"] span {{
    color: #FFFFFF !important;
    background: transparent !important;
}}

/* ══ NUCLEAR OVERRIDE — html body scope beats emotion CSS (highest !important spec) */
html body [data-testid="stMain"] button[kind="secondary"] {{
    background: {T['bg_elevated']} !important;
    background-color: {T['bg_elevated']} !important;
    color: {T['text_primary']} !important;
    border: 1px solid {T['border_strong']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
html body [data-testid="stMain"] button[kind="secondary"] p,
html body [data-testid="stMain"] button[kind="secondary"] span,
html body [data-testid="stMain"] button[kind="secondary"] div {{
    color: {T['text_primary']} !important;
    background: transparent !important;
    background-color: transparent !important;
}}
html body [data-testid="stMain"] button[kind="secondary"]:hover {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
}}
html body [data-testid="stMain"] button[kind="secondary"]:hover p,
html body [data-testid="stMain"] button[kind="secondary"]:hover span {{
    color: #FFFFFF !important;
}}
html body [data-testid="stMain"] button[kind="primary"] {{
    background: {T['accent']} !important;
    background-color: {T['accent']} !important;
    color: #FFFFFF !important;
    border-color: {T['accent']} !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}}
html body [data-testid="stMain"] button[kind="primary"] p,
html body [data-testid="stMain"] button[kind="primary"] span,
html body [data-testid="stMain"] button[kind="primary"] div {{
    color: #FFFFFF !important;
    background: transparent !important;
    background-color: transparent !important;
}}
html body [data-testid="stMain"] button[kind="primary"]:hover {{
    filter: brightness(1.1) !important;
}}

/* ══ ELEMENT CONTAINERS — transparent to show parent background ══════════════ */
[data-testid="stMain"] .element-container,
[data-testid="stMain"] [data-testid="element-container"],
[data-testid="stMain"] .stElementContainer {{
    background: transparent !important;
    background-color: transparent !important;
}}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"],
[data-testid="stMain"] [data-testid="stHorizontalBlock"] [data-testid="column"] {{
    background: transparent !important;
    background-color: transparent !important;
}}

/* ══ VERTICAL BLOCK — transparent (Streamlit default is white) ═══════════════ */
[data-testid="stMain"] [data-testid="stVerticalBlock"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {{
    background: transparent !important;
    background-color: transparent !important;
}}
/* ══ SCROLLABLE CONTAINER (height=N) — use app bg so it looks contained ══════ */
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:has(> [data-testid="stVerticalBlock"]) {{
    background: {T['bg_app']} !important;
    border-radius: 10px !important;
}}

/* ══ STAPP / STMAIN — root level bg ══════════════════════════════════════════ */
.stApp > header {{ background: transparent !important; }}
[data-testid="stAppViewContainer"] {{
    background: {T['bg_app']} !important;
    background-color: {T['bg_app']} !important;
}}
[data-testid="stMain"] {{
    background: {T['bg_app']} !important;
    background-color: {T['bg_app']} !important;
}}

/* ══ TOAST / NOTIFICATION ════════════════════════════════════════════════════ */
[data-testid="stNotification"],
[data-testid="stAlert"] {{
    background: {T['bg_card']} !important;
    color: {T['text_primary']} !important;
    border-color: {T['border']} !important;
}}

/* ══ SPINNER ═════════════════════════════════════════════════════════════════ */
[data-testid="stSpinner"] > div {{
    background: {T['bg_elevated']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['text_primary']} !important;
}}

/* Spinner trong SIDEBAR — phải dùng dark blue theme như sidebar (không phải light) */
[data-testid="stSidebar"] [data-testid="stSpinner"] > div,
[data-testid="stSidebar"] [data-testid="stSpinner"] {{
    background: rgba(13,71,161,0.35) !important;
    border: 1px solid rgba(191,219,254,0.25) !important;
    border-radius: 8px !important;
    color: #DBEAFE !important;
    font-size: 12px !important;
    padding: 8px 12px !important;
}}
[data-testid="stSidebar"] [data-testid="stSpinner"] div,
[data-testid="stSidebar"] [data-testid="stSpinner"] span,
[data-testid="stSidebar"] [data-testid="stSpinner"] p {{
    color: #DBEAFE !important;
    background: transparent !important;
}}
/* Spinner circle SVG */
[data-testid="stSidebar"] [data-testid="stSpinner"] svg circle {{
    stroke: #7AA4D4 !important;
}}

/* Disabled button trong sidebar — giữ dark blue, không chuyển white */
[data-testid="stSidebar"] button:disabled,
[data-testid="stSidebar"] button[disabled] {{
    background: rgba(13,71,161,0.35) !important;
    background-color: rgba(13,71,161,0.35) !important;
    color: rgba(219,234,254,0.6) !important;
    border: 1px solid rgba(191,219,254,0.20) !important;
    opacity: 1 !important;
    cursor: wait !important;
}}

/* v58 — Bot-msg + chat-row CSS đã xoá (chatbot page removed) */
</style>"""



_SIDEBAR_CSS = """<style>
/* ═══════════════════════════════════════════════════════════
   SIDEBAR BACKGROUND
   ═══════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"],
div[data-testid="stSidebar"],
aside[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1F4A 0%, #152E70 55%, #0A1838 100%) !important;
    background-color: #0D1F4A !important;
    border-right: none !important;
    box-shadow: 3px 0 16px rgba(0,0,0,0.25) !important;
}

/* ═══════════════════════════════════════════════════════════
   UNIVERSAL OVERRIDE
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] *::before,
[data-testid="stSidebar"] *::after {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
}

[data-testid="stSidebar"] * {
    color: #D0E0F5 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b {
    color: #FFFFFF !important;
    font-weight: 800 !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label *,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {
    color: #7AA4D4 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ═══════════════════════════════════════════════════════════
   NAV — option_menu
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] iframe {
    background: transparent !important;
    background-color: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stCustomComponentV1"],
[data-testid="stSidebar"] .stComponentContainer,
[data-testid="stSidebar"] .element-container:has(iframe) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] .nav-pills,
[data-testid="stSidebar"] ul[class*="nav"] {
    background: transparent !important;
    background-color: transparent !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] ul[class*="nav"] li a,
[data-testid="stSidebar"] .nav-link {
    border-radius: 8px !important;
    transition: background .15s ease, border-color .15s ease !important;
}

/* ═══════════════════════════════════════════════════════════
   SELECTBOX
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.08) !important;
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child *,
[data-testid="stSidebar"] .stSelectbox > div > div * {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #B8CFEE !important;
    fill: #B8CFEE !important;
}

/* ═══════════════════════════════════════════════════════════
   DROPDOWN POPUP
   ═══════════════════════════════════════════════════════════ */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] > div > div,
div[data-baseweb="popover"] > div > div > div,
div[data-baseweb="menu"],
div[data-baseweb="menu"] > ul,
div[data-baseweb="menu"] > div,
ul[role="listbox"],
div[role="listbox"],
[data-baseweb="list"],
[data-baseweb="list"] > div {
    background: #0D1F4A !important;
    background-color: #0D1F4A !important;
    border: 1px solid rgba(66,165,245,0.35) !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.6) !important;
}
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
ul[role="listbox"] *,
[data-baseweb="list"] * {
    background: transparent !important;
    background-color: transparent !important;
}
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] [role="option"],
ul[role="listbox"] li,
ul[role="listbox"] [role="option"],
[data-baseweb="list"] [role="option"] {
    color: #C8DEFF !important;
    font-weight: 500 !important;
    padding: 9px 14px !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] [role="option"]:hover,
ul[role="listbox"] li:hover,
ul[role="listbox"] [role="option"]:hover,
[data-baseweb="list"] [role="option"]:hover {
    background: rgba(66,165,245,0.25) !important;
    background-color: rgba(66,165,245,0.25) !important;
    color: #FFFFFF !important;
}
div[data-baseweb="popover"] [aria-selected="true"],
ul[role="listbox"] [aria-selected="true"],
[data-baseweb="list"] [aria-selected="true"] {
    background: rgba(66,165,245,0.40) !important;
    background-color: rgba(66,165,245,0.40) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════
   DATE INPUT
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] [data-testid="stDateInput"] label,
[data-testid="stSidebar"] .stDateInput label {
    color: rgba(191,219,254,0.75) !important;
    font-size: 9px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
[data-testid="stSidebar"] .stDateInput > div > div,
[data-testid="stSidebar"] [data-testid="stDateInput"] > div > div,
[data-testid="stSidebar"] [data-baseweb="input"] {
    background: rgba(255,255,255,0.08) !important;
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stDateInput input,
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="date"] {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border: none !important;
    text-align: center !important;
}
[data-baseweb="calendar"] {
    background: #152E70 !important;
    background-color: #152E70 !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
}
[data-baseweb="calendar"] * { color: #D0E0F5 !important; }
[data-baseweb="calendar"] button:hover { background: rgba(66,165,245,0.3) !important; background-color: rgba(66,165,245,0.3) !important; }
[data-baseweb="calendar"] [aria-selected="true"] { background: #42A5F5 !important; background-color: #42A5F5 !important; color: #FFFFFF !important; }

/* ═══════════════════════════════════════════════════════════
   SLIDER
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] [data-testid="stSlider"] > div > div > div > div {
    background: #42A5F5 !important;
    background-color: #42A5F5 !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] > div > div > div {
    background: rgba(255,255,255,0.15) !important;
    background-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 2px solid #42A5F5 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stTickBar"],
[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stTickBar"] * {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] .btn-refresh .stButton > button,
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #1565C0 !important;
    background-color: #1565C0 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(21,101,192,0.4) !important;
}
[data-testid="stSidebar"] .btn-refresh .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #1976D2 !important;
    background-color: #1976D2 !important;
}
[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,0.08) !important;
    background-color: rgba(255,255,255,0.08) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
    background: rgba(255,255,255,0.15) !important;
    background-color: rgba(255,255,255,0.15) !important;
}

/* ═══════════════════════════════════════════════════════════
   DIVIDERS & SCROLLBAR
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 12px 0 !important;
}
[data-testid="stSidebar"]::-webkit-scrollbar { width: 6px; }
[data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.30); }

/* ═══════════════════════════════════════════════════════════
   SIDEBAR COLLAPSE / EXPAND BUTTON
   ═══════════════════════════════════════════════════════════ */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    background: #1A3A6A !important;
    background-color: #1A3A6A !important;
    border-radius: 0 12px 12px 0 !important;
    border: 1px solid rgba(112,160,220,0.4) !important;
    border-left: 3px solid #7AA4D4 !important;
    box-shadow: 4px 0 16px rgba(0,0,0,0.45) !important;
    min-width: 32px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 100 !important;
    position: fixed !important;
    top: 12px !important;
    left: 0 !important;
    cursor: pointer !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: #2557A7 !important;
    background-color: #2557A7 !important;
    border-color: #D0E0F5 !important;
}
[data-testid="collapsedControl"] *,
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] *,
[data-testid="stSidebarCollapsedControl"] svg {
    color: #D0E0F5 !important;
    fill: #D0E0F5 !important;
    stroke: #D0E0F5 !important;
    background: transparent !important;
}
[data-testid="stSidebarHeader"] button,
[data-testid="stSidebarHeader"] [data-testid="baseButton-headerNoPadding"] {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #D0E0F5 !important;
}
[data-testid="stSidebarHeader"] button:hover {
    background: rgba(255,255,255,0.18) !important;
}
[data-testid="stSidebarHeader"] button svg,
[data-testid="stSidebarHeader"] button * {
    color: #D0E0F5 !important;
    fill: #D0E0F5 !important;
    background: transparent !important;
}

/* ═══════════════════════════════════════════════════════════
   MOBILE RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media screen and (max-width: 992px) {
    .main .block-container { padding: 0.6rem 0.8rem 2rem !important; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
}

@media screen and (max-width: 768px) {
    /* v36: padding cực nhỏ (0.2rem ≈ 3px) → chart rộng gần hết viewport.
     * User feedback "làm rộng ra xíu" — gain 14px each side so chart có
     * thêm ~28px width effective. */
    .main .block-container {
        padding: 0.2rem 0.2rem 1rem !important;
        max-width: 100vw !important;
        overflow-x: clip !important;
    }
    /* v36: 1 plot 1 row + rộng hơn.
     * 100% column stack giữ nguyên. Giảm gap (1rem → 0.5rem) và margin-bottom
     * (0.4rem → 0.2rem) để chart kế nhau gần hơn, tiết kiệm vertical space. */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
        margin-bottom: 0.4rem !important;
    }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
        box-sizing: border-box !important;
        margin-bottom: 0.2rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    /* Sidebar columns giữ nguyên 2-col (cho Light/Dark + VI/EN buttons) */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }

    .main * { word-break: break-word !important; overflow-wrap: break-word !important; }
    .stDataFrame, .stTable, .hist-tbl-wrap {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    /* v38: Markdown tables (vd: equation tables ở Phân tích Chi tiết) cũng cần
     * overflow-x:auto vì có cell với LaTeX dài + Vietnamese description dài. */
    [data-testid="stMarkdownContainer"] table,
    .stMarkdown table {
        display: block !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        white-space: nowrap !important;
    }
    [data-testid="stMarkdownContainer"] table td,
    [data-testid="stMarkdownContainer"] table th,
    .stMarkdown table td,
    .stMarkdown table th {
        white-space: normal !important;
        word-break: break-word !important;
    }
    /* v34 ROOT FIX: BỎ max-height cap.
     * v33 cap 360px → CART tree (cao 620-1100px) bị truncate thành cột bar đơn.
     * User screenshot xác nhận tree bị broken. Cap height KHÔNG khiến Plotly
     * re-render nhỏ hơn — chỉ cắt visible area → broken UX.
     * Giờ để chart render natural height, user scroll dọc (cách messaging apps
     * + social feeds đều làm). */
    .stPlotlyChart,
    [data-testid="stPlotlyChart"] {
        width: 100% !important;
        overflow-x: auto !important;
        overflow-y: visible !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: manipulation !important;
    }
    /* v37: Modebar hide vẫn giữ làm safety net (config displayModeBar=False
     * trong base.py đã tắt, nhưng phòng các chart custom chưa apply config) */
    .modebar-container,
    .modebar,
    [class*="modebar"] {
        display: none !important;
    }
    /* v34 FIX: Rangeselector buttons (1N/3N/5N/Tất cả) nhỏ gọn hơn trên mobile */
    .rangeselector text {
        font-size: 10px !important;
    }
    .rangeselector .button rect {
        rx: 3px !important;
    }
    /* v36 cleanup: bỏ diagnostic marker v35 (đã không cần) */
    /* v33 FIX #3: Release min-height:160px on KPI cards stacked vertically.
     * 4 cards × 160px = 640px dead air trên phone. */
    .main div[style*="min-height:160px"],
    .main div[style*="min-height: 160px"] {
        min-height: 0 !important;
    }
    [data-testid="stMetricValue"] { font-size: clamp(16px, 4vw, 22px) !important; }
    [data-testid="stMetricLabel"] { font-size: clamp(9px, 2vw, 11px) !important; }
    .stTabs [data-baseweb="tab"] { padding: 12px 16px !important; min-height: 44px !important; }
    .main .stButton > button,
    .main .stDownloadButton > button { min-height: 44px !important; padding: 10px 16px !important; }
    .page-header h1 { font-size: 16px !important; }
    .page-header p  { font-size: 10.5px !important; }
    .sec-hdr { font-size: 10px !important; padding: 5px 10px !important; letter-spacing: 0.8px !important; }
    .alert-card { padding: 12px 14px !important; font-size: 12px !important; }
    /* v33 FIX #7 (corrected): Long badges với white-space:nowrap có thể overflow.
     * NHƯNG nowrap + text-overflow:ellipsis là pattern cố ý truncate (chatbot
     * conv titles, history badges). WHITELIST: chỉ wrap nếu element KHÔNG có
     * text-overflow:ellipsis. */
    [data-testid="stMain"] div[style*="white-space:nowrap"]:not([style*="text-overflow"]):not([style*="overflow:hidden"]),
    [data-testid="stMain"] span[style*="white-space:nowrap"]:not([style*="text-overflow"]):not([style*="overflow:hidden"]) {
        white-space: normal !important;
    }
}

@media screen and (max-width: 480px) {
    /* v33 FIX #14: Auto-shrink hardcoded font-sizes — BOTH no-space + space variants.
     * Trước chỉ catch "font-size:36px" (no space). Giờ catch cả "font-size: 36px". */
    .main div[style*="font-size:36px"],
    .main div[style*="font-size: 36px"],
    .main div[style*="font-size:34px"],
    .main div[style*="font-size: 34px"],
    .main div[style*="font-size:32px"],
    .main div[style*="font-size: 32px"] {
        font-size: clamp(20px, 6vw, 28px) !important;
    }
    .main div[style*="font-size:30px"],
    .main div[style*="font-size: 30px"],
    .main div[style*="font-size:28px"],
    .main div[style*="font-size: 28px"],
    .main div[style*="font-size:26px"],
    .main div[style*="font-size: 26px"] {
        font-size: clamp(18px, 5vw, 22px) !important;
    }
    .main .block-container { padding: 0.35rem 0.35rem 1rem !important; }
    /* Redundant với 768px scope (đã có ở trên), giữ phòng trường hợp cascade */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
        margin-bottom: 0.4rem !important;
    }
    .main { font-size: 12px !important; }
    .sec-hdr { font-size: 9.5px !important; padding: 4px 8px !important; letter-spacing: 0.5px !important; }
    .page-header { padding: 10px 14px !important; }
    .page-header h1 { font-size: 15px !important; }
    .page-header p  { font-size: 10px !important; }
    [data-testid="stMetricValue"] { font-size: 16px !important; }
    .stTabs [data-baseweb="tab"] { padding: 10px 12px !important; font-size: 12px !important; min-height: 44px !important; }
    .hist-tbl th, .hist-tbl td { padding: 5px 7px !important; font-size: 11px !important; }
    /* v33 FIX #1: 44px touch target (Apple HIG) — was 40px. */
    .main [data-testid="stHorizontalBlock"] .stButton > button {
        padding: 8px 10px !important; font-size: 11px !important; min-height: 44px !important;
    }
}

@media screen and (max-width: 360px) {
    .main .block-container { padding: 0.25rem 0.25rem 0.8rem !important; }
    .main { font-size: 11px !important; }
    .page-header h1 { font-size: 14px !important; }
    [data-testid="stMetricValue"] { font-size: 14px !important; }
}

@media (hover: none) and (pointer: coarse) {
    button, [role="button"], .stButton > button, .stDownloadButton > button,
    .stTabs [data-baseweb="tab"] { min-height: 44px !important; }
    .fc-card:hover { transform: none !important; }
}

/* v58 — Chatbot mobile + landscape CSS đã xoá (~100 dòng dead) */

/* ═══════════════════════════════════════════════════════════
   SIDEBAR — DESKTOP DEFAULT OPEN, COLLAPSIBLE VIA TOGGLE
   ═══════════════════════════════════════════════════════════ */
/* v27 ROOT-CAUSE FIX: Trước em khoá `width: 280px !important` trên desktop
 * → Streamlit's collapse mechanism (width:0) BỊ ĐÈ → click không thấy gì đổi.
 * v27: Bỏ width lock, để Streamlit native control width. Khi user click toggle,
 * Streamlit's React setState collapsed → CSS class apply width:0 → SIDEBAR
 * thực sự collapse.
 *
 * Force-show collapseButton/header bằng selector NHẸ (no !important on display)
 * — Streamlit có thể override khi collapsed để ẩn nút X. CollapsedControl
 * (hamburger) thì để Streamlit's React tự handle visibility — không force. */
@media screen and (min-width: 769px) {
    [data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"]:not([aria-expanded]) {
        /* Chỉ apply khi sidebar đang EXPANDED. Khi collapsed, Streamlit set
         * aria-expanded="false" → rule này không match → width tự collapse. */
        min-width: 280px;
        width: 280px;
    }
    /* Show toggle X button khi sidebar expanded (Streamlit có thể hide
     * — mình force show để user thấy nút collapse) */
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"],
    button[data-testid="baseButton-headerNoPadding"] {
        display: flex !important;
        visibility: visible !important;
    }
    /* collapsedControl (hamburger): KHÔNG force display. Để Streamlit's
     * React tự show khi collapsed, ẩn khi expanded. */
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR TOGGLE BUTTON THEMING — high specificity override
   Áp dụng cho CẢ desktop và mobile để theme navy khớp với sidebar.
   Container (stSidebarHeader) trong suốt, nút (stSidebarCollapseButton)
   có background semi-transparent + border xanh nhạt.
   ═══════════════════════════════════════════════════════════ */

/* CONTAINER — phải TRONG SUỐT, không phải button */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    background: transparent !important;
    background-color: transparent !important;
    padding: 8px 14px 4px !important;
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
    min-height: 36px !important;
    border: none !important;
    box-shadow: none !important;
}

/* BUTTON X — nền semi-translucent, viền xanh nhạt, kích thước 30x30 */
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] > button,
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] [data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] button[kind="headerNoPadding"] {
    background: rgba(255, 255, 255, 0.10) !important;
    background-color: rgba(255, 255, 255, 0.10) !important;
    background-image: none !important;
    border: 1px solid rgba(122, 164, 212, 0.40) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    color: #D0E0F5 !important;
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    min-height: 30px !important;
    padding: 4px !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: background-color 0.15s ease, border-color 0.15s ease !important;
}

/* HOVER state */
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover,
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] > button:hover,
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] [data-testid="baseButton-headerNoPadding"]:hover,
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"]:hover,
section[data-testid="stSidebar"] button[kind="headerNoPadding"]:hover {
    background: rgba(122, 164, 212, 0.30) !important;
    background-color: rgba(122, 164, 212, 0.30) !important;
    border-color: rgba(208, 224, 245, 0.70) !important;
}

/* SVG icon bên trong button — màu xanh sáng giống collapsedControl */
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] *,
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button svg,
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button *,
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] svg,
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] *,
section[data-testid="stSidebar"] button[kind="headerNoPadding"] svg,
section[data-testid="stSidebar"] button[kind="headerNoPadding"] * {
    color: #D0E0F5 !important;
    fill: #D0E0F5 !important;
    stroke: #D0E0F5 !important;
    background: transparent !important;
    background-color: transparent !important;
    width: 16px !important;
    height: 16px !important;
}

/* Mobile (<=768px): sidebar dạng slide-in panel, Streamlit native handle transform.
 * Lý do KHÔNG dùng [aria-expanded]: Streamlit drive collapse bằng inline
 * transform: translateX(-Xpx) — set TRỰC TIẾP lên section. Mình chỉ cần
 * cho sidebar `position: fixed` + z-index cao, Streamlit's native CSS animation
 * sẽ tự handle slide-in/out. KHÔNG override `transform` của Streamlit. */
@media screen and (max-width: 768px) {
    [data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        /* iOS Safari: 100vh tính cả URL bar → sidebar bị che cuối. 100dvh = dynamic viewport */
        height: 100vh !important;       /* fallback browser cũ */
        height: 100dvh !important;      /* iOS Safari + modern */
        width: min(280px, 85vw) !important;
        min-width: min(280px, 85vw) !important;
        max-width: 85vw !important;
        z-index: 999 !important;
        box-shadow: 4px 0 24px rgba(0,0,0,0.45) !important;
        overflow-y: auto !important;
        /* transform CHƯA set ở đây — Streamlit's native collapse driver
           sẽ set inline transform: translateX(-Xpx) khi collapse, và xoá khi mở.
           Mình giữ smooth transition để slide đẹp. */
        transition: transform 0.25s ease, visibility 0.25s !important;
    }
    /* Phòng ngừa: Streamlit 1.39 dùng grid layout với reserved sidebar track.
     * Khi sidebar position:fixed (out of flow), grid track 280px có thể vẫn để
     * trống gutter trên main content. Force 1-column grid trên mobile. */
    [data-testid="stAppViewContainer"] {
        grid-template-columns: 1fr !important;
    }
    /* Mobile: HIỆN nút toggle close (X) bên trong sidebar khi mở */
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"],
    button[data-testid="baseButton-headerNoPadding"] {
        display: flex !important;
        visibility: visible !important;
        background: rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        color: #D0E0F5 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarHeader"] svg {
        color: #D0E0F5 !important;
        fill: #D0E0F5 !important;
    }
    /* Mobile: HIỆN nút open (hamburger) khi sidebar collapsed.
     * z-index 1001 > sidebar 999 → tap được kể cả khi DOM stacking conflict.
     * Khi sidebar mở, Streamlit sẽ tự ẩn nút này (display:none).
     * left:10px positioning ổn vì khi sidebar mở, collapsedControl đã hidden. */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 1001 !important;
    }
    /* Mobile: main content full-width, không bị sidebar đẩy */
    .main .block-container,
    [data-testid="stMain"] .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        margin-left: 0 !important;
        max-width: 100vw !important;
    }
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR NUMBER INPUT — SCOPE HẸP, không đụng select/date
   ═══════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] > div {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 10px !important;
    padding: 0 !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] > div:focus-within {
    border-color: #7AA4D4 !important;
    background: rgba(122, 164, 212, 0.10) !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input[type="number"] {
    background: transparent !important;
    border: none !important;
    color: #FFFFFF !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 12px 8px !important;
    cursor: text !important;
    caret-color: #7AA4D4 !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input[type="number"]::-webkit-inner-spin-button,
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none !important;
    margin: 0 !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button {
    background: rgba(255, 255, 255, 0.04) !important;
    border: none !important;
    border-left: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: rgba(191, 219, 254, 0.8) !important;
    width: 36px !important;
    min-width: 36px !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button:hover {
    background: rgba(122, 164, 212, 0.25) !important;
    color: #FFFFFF !important;
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR SELECTBOX — FORCE màu rõ ràng, không cho CSS khác đè
   ═══════════════════════════════════════════════════════════ */

/* Container selectbox */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div:hover {
    border-color: rgba(122, 164, 212, 0.5) !important;
    background: rgba(255, 255, 255, 0.12) !important;
}

/* Text hiển thị giá trị đã chọn (ví dụ "FPT") */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: transparent !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}

/* Input bên trong */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] input {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Single value container */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [class*="singleValue"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [class*="SingleValue"] {
    color: #FFFFFF !important;
}

/* Icon dropdown (mũi tên xuống) */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg {
    fill: rgba(191, 219, 254, 0.8) !important;
}

/* Dropdown menu popup */
div[data-baseweb="popover"] [role="listbox"] {
    background: #0F1729 !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}

div[data-baseweb="popover"] [role="option"] {
    background: transparent !important;
    color: #FFFFFF !important;
}

div[data-baseweb="popover"] [role="option"]:hover {
    background: rgba(122, 164, 212, 0.25) !important;
}

/* Placeholder khi chưa chọn */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [class*="placeholder"] {
    color: rgba(191, 219, 254, 0.5) !important;
}
</style>
<script></script>"""


_GLOBAL_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="st-"] { font-family: 'Inter','Segoe UI',system-ui,sans-serif !important; }

/* ══ HIDE STREAMLIT CLOUD BADGES / BRANDING (cho demo NCKH sạch sẽ) ══════════ */
/* Pattern matching mạnh — không phụ thuộc hash suffix của Streamlit CSS-in-JS */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stHeader"],
[data-testid="stAppViewBlockContainer"] + div,
[data-testid="stMainMenu"],
#MainMenu,
header[data-testid="stHeader"],
div[class*="viewerBadge"],
div[class*="ViewerBadge"],
a[class*="viewerBadge"],
span[class*="viewerBadge"],
div[class*="_profileContainer"],
div[class*="_profile_container"],
div[class*="profileContainer"],
span[class*="_profileContainer"],
a[href*="share.streamlit.io"],
a[href*="streamlit.io/cloud"],
a[href*="streamlit.io"]:not([href*="docs.streamlit.io"]),
button[kind="header"],
button[data-testid="baseButton-header"],
button[data-testid="manage-app-button"],
.stDeployButton,
.stAppDeployButton,
footer,
[data-testid="stBottom"] [data-testid*="viewer"],
div[data-testid="manage-app-button"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    left: -9999px !important;
}

/* Block mọi element có chữ "Hosted with Streamlit" hoặc "Created by" */
div:has(> a[href*="streamlit.io"]),
div:has(> span:only-child[class*="viewerBadge"]) {
    display: none !important;
}

/* Desktop: constrain max-width để không bị stretch xấu trên 4K/ultrawide.
   Auto center với margin:auto. Mobile media-query bên dưới override khi cần.
   v58 — top padding 2.5rem (thay 1rem) để FinScope logo SVG (icon kính lúp)
   không bị clip ở mép trên page. */
.main .block-container {
    padding: 2.5rem 2rem 3rem;
    max-width: 1600px;
    margin: 0 auto;
}
[data-testid="stSidebar"] > div { padding-top: 0.4rem; }

[data-testid="stMetric"] {
  border-radius: 12px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] p {
  font-size: 10px !important; font-weight: 700 !important;
  letter-spacing: .6px !important; text-transform: uppercase !important;
}
[data-testid="stMetricValue"] { font-size: 18px !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"] { font-size: 11.5px !important; font-weight: 600 !important; }

.page-header {
  border-radius: 14px; padding: 14px 24px 12px; margin-bottom: 16px;
  position: relative; overflow: hidden;
}
.page-header h1 { font-size: 18px; margin: 0 0 3px; font-weight: 800; letter-spacing: -.3px; }
.page-header p  { margin: 0; font-size: 11.5px; font-weight: 500; }

.alert-card {
  border-radius: 12px; padding: 14px 18px; margin: 8px 0;
  border-left: 5px solid; font-size: 13px; line-height: 1.6;
}
.alert-buy  { background: #E8F5E9; border-color: #2E7D32; color: #1B4D20; }
.alert-sell { background: #FFEBEE; border-color: #C62828; color: #7A1515; }
.alert-warn { background: #FFF8E1; border-color: #F9A825; color: #6D4C00; }
.alert-neut { background: #F3F6FA; border-color: #8090B0; color: #3A4A6A; }

.info-box {
  border-radius: 10px; padding: 10px 16px;
  font-size: 13px; margin: 8px 0; line-height: 1.7;
}

.fc-card {
  border-radius: 14px; padding: 20px 16px 15px;
  text-align: center; transition: transform .18s, box-shadow .18s;
  position: relative; overflow: hidden;
}
.fc-card:hover { transform: translateY(-3px); }
.fc-method { font-size: 9px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
.up   { color: #166534; background: #DCFCE7; }
.down { color: #991B1B; background: #FEE2E2; }
.flat { color: #475569; background: #F1F5F9; }

[data-testid="stIconMaterial"] { display: none !important; }
.material-symbols-outlined, .material-symbols-rounded,
[class*="material-symbols"] { font-size: 0 !important; }
button span[translate="no"],
[data-testid="stDownloadButton"] span[translate="no"],
[data-testid="stButton"] span[translate="no"] {
    font-size: inherit !important;
    line-height: inherit !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; font-size: 13px !important; }
details > summary { font-size: 13px !important; font-weight: 600 !important; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }

/* ═══════════════════════════════════════════════════════════════
   CHATBOT — Premium redesigned UI
   ═══════════════════════════════════════════════════════════════ */

/* v58 — Chat rows / avatars / bubbles / typing-dots CSS đã xoá (~155 dòng dead) */

/* ═══════════════════════════════════════════════════════════════
   CHATBOT — Chat input
   ═══════════════════════════════════════════════════════════════ */

div[data-testid="stChatInput"] { margin-top: 10px !important; }
div[data-testid="stChatInput"] > div {
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(21,101,192,.10) !important;
    transition: box-shadow .2s !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    box-shadow: 0 4px 20px rgba(21,101,192,.22) !important;
}

/* ── Conversation history scrollable container ── */
/* Icon buttons (✏ ✕) inside the fixed-height scroll box */
div[data-testid="stVerticalBlockBorderWrapper"]
    .main [data-testid="stColumn"] .stButton > button {
    padding: 5px 8px !important;
    min-height: 32px !important;
    font-size: 12px !important;
    border-radius: 8px !important;
}
/* Title button (conversation name) — left-ish feel */
div[data-testid="stVerticalBlockBorderWrapper"]
    .main [data-testid="stColumn"]:first-child .stButton > button {
    padding: 6px 10px !important;
    min-height: 34px !important;
    font-size: 12.5px !important;
    border-radius: 8px !important;
    text-overflow: ellipsis !important;
    overflow: hidden !important;
    white-space: nowrap !important;
}

/* Smooth scroll */
/* scroll-behavior: auto thay vì smooth — smooth ép browser repaint mỗi wheel
   event, gây lag rõ rệt khi scroll qua nhiều Plotly chart (DOM nặng). */
html { scroll-behavior: auto; }

/* ══ VERTICAL BLOCK — base transparent (overridden by theme CSS) ════════════ */
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* ══ POPOVER MENU from main area ════════════════════════════════════════════ */
[data-testid="stPopover"] [data-testid="stVerticalBlock"] {
    background: var(--bg-card, #FFFFFF) !important;
}

</style>"""


def inject_global_css() -> None:
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(_RADIO_SEGMENTED_CSS, unsafe_allow_html=True)
    st.markdown(_NAV_TRANSITION_CSS, unsafe_allow_html=True)


# Streamlit MẶC ĐỊNH fade-out + grayscale toàn page khi đang rerun (`data-stale`
# = true) → user click chuyển trang thấy nội dung CŨ MỜ ĐI hồi lâu rồi mới về
# trang mới. Fix:
#  1) Tắt opacity-fade + filter trên data-stale → giữ rõ nét đến khi render xong.
#  2) Thay vào: thanh progress bar mỏng 3px ở ĐỈNH page (gradient teal) chạy
#     ngang khi đang rerun → feedback rõ ràng mà KHÔNG che/mờ nội dung cũ.
#  3) Cursor wait nhẹ trên toàn body khi stale (cho mọi action).
_NAV_TRANSITION_CSS = """<style>
/* ══ TẮT FADE-OUT khi đang rerun — giữ nội dung sắc nét ════════════════════
   Streamlit 1.40+ thêm nhiều selector data-stale; phải override hết.       */
[data-stale],
[data-stale="true"],
[data-stale="true"] *,
[data-testid="stAppViewContainer"] [data-stale],
[data-testid="stAppViewContainer"] [data-stale="true"],
[data-testid="stApp"] [data-stale],
[data-testid="stApp"] [data-stale="true"],
[data-testid="stMain"] [data-stale="true"],
section.main [data-stale="true"],
.element-container[data-stale="true"],
.stMarkdown[data-stale="true"],
[data-testid="stPlotlyChart"][data-stale="true"],
[data-testid="stMetric"][data-stale="true"],
[data-testid="stTabs"] [data-stale="true"],
[data-testid="stVerticalBlock"] [data-stale="true"] {
    opacity: 1 !important;
    filter: none !important;
    pointer-events: auto !important;
    transition: none !important;
    animation: none !important;
}

/* ══ Disable Streamlit element fade-in animation cũng ═════════════════════ */
[data-testid="stAppViewContainer"] *,
[data-testid="stMain"] * {
    animation-duration: 0.01ms !important;
    animation-delay: 0ms !important;
}
/* Trừ các keyframes tôi định nghĩa thủ công.
   .live-dot PHẢI giữ animation (dashboard.py:557 — LIVE pulse green indicator).
   .live-bubble-meta + .streaming-cursor là dead selectors — đã xoá. */
.best-model-card,
.splash-wrap,
.live-dot {
    animation-duration: revert !important;
    animation-delay: revert !important;
}

/* ══ Disable Plotly transitions trong chart (nhúng SVG-level) ═════════════
   Pan/zoom Plotly emit 100+ DOM mutations; mỗi child element repaint với
   transition delay = visible stutter. Tắt hoàn toàn.                       */
.js-plotly-plot .plotly .main-svg,
.js-plotly-plot * {
    transition: none !important;
    transition-duration: 0s !important;
    animation: none !important;
}

/* ══ v58: HIDE PLOTLY MODEBAR HOÀN TOÀN, MỌI VIEWPORT ════════════════════
   User chỉ kéo (pan) chart — không cần camera/zoom/reset/download/lasso.
   Modebar hover-fade-in animation gây lag rõ khi scroll qua nhiều chart.
   Trước đây CSS hide chỉ trong @media (max-width:768px); giờ global.   */
.modebar-container,
.modebar,
.modebar-group,
.modebar-btn,
[class*="modebar"],
.js-plotly-plot .modebar,
.js-plotly-plot .modebar-container {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}

/* ══ v58: CSS containment — browser optimize paint khi scroll qua cards ══
   `contain: layout style paint` đánh dấu element là isolated layout/paint
   boundary → khi card thay đổi nội dung KHÔNG trigger reflow toàn page.
   Đặc biệt hiệu quả với Streamlit metric/card layout (~20-40 cards/page).
   `content-visibility: auto` cho phép browser skip render off-screen
   sections (huge win cho page dài).                                      */
[data-testid="stMetric"],
[data-testid="stPlotlyChart"],
.element-container > [data-testid="stMarkdownContainer"],
.stTabs [data-baseweb="tab-panel"] {
    contain: layout style;
}
[data-testid="stPlotlyChart"] {
    /* paint containment thêm cho chart — Plotly có SVG nặng */
    contain: layout style paint;
    content-visibility: auto;
    contain-intrinsic-size: auto 480px;
}

/* ══ v58: content-visibility cho block container (page-level sections)
   ═══════════════════════════════════════════════════════════════════════
   Streamlit chia page thành nhiều `.stVerticalBlock` containers. Khi
   container off-screen, browser SKIP layout/paint/style hoàn toàn → scroll
   page dài (Portfolio 800+ dòng, Paper 1200+ dòng) mượt hẳn.
   contain-intrinsic-size = browser dùng placeholder size khi chưa render. */
.stVerticalBlock > .element-container,
.stHorizontalBlock {
    content-visibility: auto;
    contain-intrinsic-size: auto 300px;
}

/* ══ v58: Disable hover transform (gây compositor layer thrash khi scroll)
   ═══════════════════════════════════════════════════════════════════════
   .fc-card và các card có translateY(-3px) trên hover; khi mouse cross
   trong lúc scroll → compositor work liên tục. Tắt khi đang scroll. */
body.scrolling .fc-card:hover,
body.scrolling [data-testid="stMetric"]:hover,
body.scrolling .stButton > button:hover {
    transform: none !important;
    box-shadow: none !important;
}

/* ══ v58: AGGRESSIVE — tắt mọi animation cho element off-screen.
   `content-visibility: hidden` browser hoàn toàn skip render. Chỉ áp dụng
   cho element thực sự off-screen (viewport scroll xa). content-visibility:
   auto đã tự handle, nhưng force animation paused thêm để chắc.            */
body.scrolling * {
    animation-play-state: paused !important;
}

/* ══ v58: HINT browser dùng GPU compositor cho main scroll container
   ═══════════════════════════════════════════════════════════════════════
   `will-change: scroll-position` để browser pre-allocate compositor layer
   cho main area. Lifetime ngắn — chỉ apply khi đang scroll.                */
body.scrolling [data-testid="stMain"] {
    will-change: scroll-position;
}

/* ══ v58: Pause infinite animation khi user đang scroll ═══════════════════
   `.best-model-card best-glow 2.5s infinite` và các pulse animation đốt CPU
   ngay cả khi off-screen. JS scroll handler thêm class `.scrolling` vào
   body trong khi scroll, gỡ ra sau 200ms idle. CSS pause animation khi
   class active. Combine với content-visibility: auto ở trên = scroll smooth. */
body.scrolling .best-model-card,
body.scrolling .live-dot,
body.scrolling .nav-loading {
    animation-play-state: paused !important;
}

/* ══ THANH PROGRESS TRÊN ĐỈNH khi rerun (thay cho fade toàn page) ═══════════ */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 0;
    background: linear-gradient(90deg, transparent 0%, #0F766E 40%, #0891B2 60%, transparent 100%);
    z-index: 999999;
    transition: height 0.18s ease, opacity 0.18s ease;
    opacity: 0;
    pointer-events: none;
}
[data-stale="true"] [data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]:has([data-stale="true"])::before {
    height: 3px;
    opacity: 1;
    animation: nav-loading 1.2s ease-in-out infinite;
}
@keyframes nav-loading {
    0%   { transform: translateX(-30%); }
    100% { transform: translateX(30%); }
}

/* ══ CURSOR FEEDBACK nhẹ khi đang rerun ════════════════════════════════════ */
[data-stale="true"] [data-testid="stMain"] {
    cursor: progress;
}

/* ══ ĐỊNH VỊ NAV TOP — scroll lên đầu mỗi lần đổi page (smooth) ════════════
   Streamlit không tự scroll-to-top khi đổi page → trang dài + đổi sang trang
   ngắn = user vẫn ở giữa, lúng túng. CSS-only scroll-margin để khi anchor đổi. */
section.main > div.block-container { scroll-margin-top: 0 !important; }
</style>"""


# Style st.radio(horizontal=True) so it looks like a segmented control
# (used in dashboard.py for the candlestick timeframe picker — replaces
# st.segmented_control which requires Streamlit ≥1.34).
_RADIO_SEGMENTED_CSS = """<style>
[data-testid="stRadio"] > div[role="radiogroup"] {
    display: inline-flex !important;
    background: #F1F5F9;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid #E2E8F0;
}
[data-testid="stRadio"] > div[role="radiogroup"] > label {
    margin: 0 !important;
    padding: 6px 16px !important;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
    font-weight: 600 !important;
    color: #64748B !important;
}
[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: rgba(30, 64, 175, 0.08);
    color: #1E40AF !important;
}
[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%) !important;
    color: white !important;
    box-shadow: 0 2px 6px rgba(30, 64, 175, 0.25);
}
[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p {
    color: white !important;
}
[data-testid="stRadio"] > div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}
[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
</style>"""


def inject_theme_css(T: dict) -> None:
    # v40 PERF: Cache string CSS theme theo mode (light/dark) trong session_state.
    # _theme_css(T) build chuỗi ~5KB qua f-string interpolation 200+ rules.
    # Trước: rebuild mỗi rerun. Giờ: build 1 lần/session/mode, reuse string.
    _mode_key = 'dark' if T.get('is_dark') else 'light'
    _cache_key = f'_theme_css_str_{_mode_key}'
    if _cache_key not in st.session_state:
        st.session_state[_cache_key] = _theme_css(T)
    st.markdown(st.session_state[_cache_key], unsafe_allow_html=True)
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

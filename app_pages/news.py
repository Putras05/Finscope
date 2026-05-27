"""Trang 'Tin tức & Tâm lý thị trường' — đọc tin RSS + chấm cảm xúc, bổ trợ dự báo."""
import streamlit as st

from core.i18n import t
from core.constants import ticker_sector
from data.news import news_sentiment, _label


def _meter(score, is_en, _T):
    """Thẻ đồng hồ tâm lý theo điểm tổng."""
    lbl, col = _label(score, is_en)
    arrow = '▲' if score > 0 else ('▼' if score < 0 else '＝')
    return (lbl, col, arrow)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Tin tức & Tâm lý Thị trường" if not is_en else "Market News & Sentiment"} — {ticker}</h1>'
        f'<p>{ticker_sector(ticker)} &nbsp;·&nbsp; '
        f'{"Đọc tin RSS (CafeF · VnExpress · Vietstock) + chấm cảm xúc bằng từ điển tài chính tiếng Việt → bổ trợ tín hiệu giao dịch" if not is_en else "RSS news (CafeF · VnExpress · Vietstock) + Vietnamese finance lexicon sentiment → augments the trading signal"}</p>'
        f'</div>', unsafe_allow_html=True)

    with st.spinner('Đang tải & phân tích tin tức...' if not is_en else 'Fetching & analyzing news...'):
        r = news_sentiment(ticker)

    if not r.get('ok'):
        st.warning((r.get('note') or 'Không lấy được tin tức.')
                   + (' Thử lại sau ít phút.' if not is_en else ' Try again shortly.'))
        return

    # ── Hai thẻ tâm lý: Thị trường & theo Mã ───────────────────────────
    _ml, _mc, _ma = _meter(r['market_score'], is_en, _T)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-left:6px solid {_mc};border-radius:14px;padding:18px 22px">'
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'letter-spacing:1px;text-transform:uppercase">{"Tâm lý thị trường" if not is_en else "Market sentiment"}</div>'
            f'<div style="font-size:30px;font-weight:800;color:{_mc};line-height:1.1;margin:4px 0">{_ma} {_ml}</div>'
            f'<div style="font-size:12px;color:{_T["text_muted"]}">'
            f'{"Điểm tổng" if not is_en else "Net score"}: <b style="color:{_mc}">{r["market_score"]:+d}</b> '
            f'· {r["n"]} {"tin" if not is_en else "headlines"}</div>'
            f'</div>', unsafe_allow_html=True)
    with c2:
        if r['ticker_n'] >= 1:
            _tl, _tc, _ta = _meter(r['ticker_score'], is_en, _T)
            _body = (f'<div style="font-size:30px;font-weight:800;color:{_tc};line-height:1.1;margin:4px 0">{_ta} {_tl}</div>'
                     f'<div style="font-size:12px;color:{_T["text_muted"]}">'
                     f'{"Điểm" if not is_en else "Score"}: <b style="color:{_tc}">{r["ticker_score"]:+d}</b> '
                     f'· {r["ticker_n"]} {"tin về mã này" if not is_en else "ticker headlines"}</div>')
        else:
            _tc = _T['text_muted']
            _body = (f'<div style="font-size:18px;font-weight:700;color:{_T["text_secondary"]};margin:8px 0">—</div>'
                     f'<div style="font-size:12px;color:{_T["text_muted"]}">'
                     f'{"Chưa có tin riêng về mã này hôm nay — dùng tâm lý thị trường chung." if not is_en else "No ticker-specific news today — using overall market sentiment."}</div>')
        st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-left:6px solid {_tc};border-radius:14px;padding:18px 22px">'
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'letter-spacing:1px;text-transform:uppercase">{"Tâm lý mã" if not is_en else "Ticker sentiment"} {ticker}</div>'
            f'{_body}</div>', unsafe_allow_html=True)

    # ── Danh sách tin + nhãn cảm xúc ───────────────────────────────────
    st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Tin mới nhất" if not is_en else "Latest headlines"}</div>',
                unsafe_allow_html=True)
    _rows = ''
    for it in r['items']:
        lbl, col = _label(it['score'], is_en)
        _star = ('<span style="color:#0891B2;font-weight:800">★</span> '
                 if it.get('is_ticker') else '')
        _title = it['title']
        _link = it.get('link', '')
        _title_html = (f'<a href="{_link}" target="_blank" style="color:{_T["text_primary"]};text-decoration:none">{_title}</a>'
                       if _link else _title)
        _rows += (
            f'<tr style="border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:9px 10px;white-space:nowrap;vertical-align:top">'
            f'<span style="font-size:11px;font-weight:700;color:{col};'
            f'background:{col}1A;padding:2px 8px;border-radius:6px">{lbl} {it["score"]:+d}</span></td>'
            f'<td style="padding:9px 10px;font-size:13.5px;line-height:1.5">{_star}{_title_html}'
            f'<div style="font-size:10.5px;color:{_T["text_muted"]};margin-top:2px">'
            f'{it.get("source","")} · {it.get("date","")[:25]}</div></td>'
            f'</tr>')
    st.markdown(
        f'<div style="border-radius:12px;overflow:hidden;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;background:{_T["bg_card"]}">'
        f'<tbody>{_rows}</tbody></table></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:12px;line-height:1.6">'
        f'{"★ = tin liên quan trực tiếp tới mã. Cảm xúc chấm bằng từ điển tài chính tiếng Việt (đếm từ tích cực/tiêu cực, có xử lý phủ định) — mang tính tham khảo, hỗ trợ bổ trợ tín hiệu ở trang Chiến lược Giao dịch." if not is_en else "★ = ticker-related news. Sentiment via a Vietnamese finance lexicon (positive/negative word count with negation) — indicative only; augments the signal on the Trading Strategy page."}'
        f'</div>', unsafe_allow_html=True)

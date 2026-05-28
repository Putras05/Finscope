"""Trang 'Tin tức & Tâm lý thị trường' — đọc tin RSS + ĐỌC HIỂU bằng AI.

Lớp đọc hiểu:
  • Chủ đề (aspect) tài chính của mỗi tin + gom nhóm tin cùng chủ đề (deploy-safe).
  • Cảm xúc: từ điển (mặc định) + tùy chọn HỌC SÂU (PhoBERT) để so sánh.
Cảm xúc dùng để diễn giải/bổ trợ — phiếu tín hiệu giao dịch vẫn dùng từ điển
(luôn khả dụng, deploy-safe).
"""
import streamlit as st

from core.constants import ticker_sector
from data.news import news_sentiment, _label
from data import news_ai as NA


def _meter(score, is_en, _T):
    lbl, col = _label(score, is_en)
    arrow = '▲' if score > 0 else ('▼' if score < 0 else '＝')
    return (lbl, col, arrow)


def _chip(text, color, _T):
    return (f'<span style="display:inline-block;font-size:10px;font-weight:700;'
            f'color:{color};background:{color}1A;padding:2px 8px;border-radius:6px;'
            f'margin:2px 4px 2px 0">{text}</span>')


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Tin tức & Đọc hiểu Thị trường" if not is_en else "Market News & AI Reading"} — {ticker}</h1>'
        f'<p>{ticker_sector(ticker)} &nbsp;·&nbsp; '
        f'{"Đọc tin RSS (CafeF · VnExpress · Vietstock) → nhận diện chủ đề, gom nhóm, chấm cảm xúc (từ điển + tùy chọn AI học sâu) → bổ trợ tín hiệu" if not is_en else "RSS news → aspect detection, theme clustering, sentiment (lexicon + optional deep-learning AI) → augments the signal"}</p>'
        f'</div>', unsafe_allow_html=True)

    with st.spinner('Đang tải & phân tích tin tức...' if not is_en else 'Fetching & analyzing news...'):
        r = news_sentiment(ticker)

    if not r.get('ok'):
        st.warning((r.get('note') or 'Không lấy được tin tức.')
                   + (' Thử lại sau ít phút.' if not is_en else ' Try again shortly.'))
        return

    items = r['items']
    _dl_used = bool(r.get('dl_used'))   # PhoBERT đã chạy ngầm — luôn bật khi có sẵn

    # ── Badge trạng thái nguồn cảm xúc (không có toggle — chạy ngầm) ────
    if _dl_used:
        _stat_txt = ('● PhoBERT đang đọc hiểu (AI) + từ điển'
                     if not is_en else '● PhoBERT reading (AI) + lexicon')
        _stat_col = _T['success']
    else:
        _stat_txt = ('○ Dùng từ điển (PhoBERT chưa cài / fallback)'
                     if not is_en else '○ Lexicon mode (PhoBERT not installed / fallback)')
        _stat_col = _T['text_muted']
    st.markdown(
        f'<div style="font-size:11px;color:{_stat_col};margin:0 0 10px;font-weight:600">'
        f'{_stat_txt}'
        f'<span style="color:{_T["text_muted"]};font-weight:400"> · '
        f'{"AI ảnh hưởng đến phiếu tín hiệu Chiến lược và thẻ Tâm lý Dashboard" if not is_en else "AI feeds the Strategy vote and Dashboard sentiment card"}'
        f'</span></div>', unsafe_allow_html=True)

    # ── Hai thẻ tâm lý: Thị trường & theo Mã (từ điển) ─────────────────
    _ml, _mc, _ma = _meter(r['market_score'], is_en, _T)
    c1, c2 = st.columns(2)
    with c1:
        _ai_line = ''
        if _dl_used:
            _ai_net = float(r.get('market_score_dl', 0.0))
            _ai_lbl, _ai_col, _ai_arr = _meter(_ai_net, is_en, _T)
            _ai_line = (f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:4px">'
                        f'{"PhoBERT AI" if not is_en else "PhoBERT AI"}: '
                        f'<b style="color:{_ai_col}">{_ai_arr} {_ai_lbl}</b> '
                        f'({_ai_net:+.2f})</div>')
        st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-left:6px solid {_mc};border-radius:14px;padding:18px 22px">'
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'letter-spacing:1px;text-transform:uppercase">{"Tâm lý thị trường" if not is_en else "Market sentiment"}</div>'
            f'<div style="font-size:30px;font-weight:800;color:{_mc};line-height:1.1;margin:4px 0">{_ma} {_ml}</div>'
            f'<div style="font-size:12px;color:{_T["text_muted"]}">'
            f'{"Từ điển" if not is_en else "Lexicon"}: <b style="color:{_mc}">{r["market_score"]:+d}</b> '
            f'· {r["n"]} {"tin" if not is_en else "headlines"}</div>{_ai_line}'
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

    # ── Chủ đề nổi bật (gom nhóm tin cùng nội dung) ─────────────────────
    _clusters = NA.cluster_themes(tuple(it['title'] for it in items))
    if _clusters:
        st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="sec-hdr">{"Chủ đề nổi bật" if not is_en else "Top themes"}'
                    f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]}">'
                    f'{"— nhóm tin cùng nội dung" if not is_en else "— clustered headlines"}</span></div>',
                    unsafe_allow_html=True)
        _cards = ''
        for cl in _clusters[:4]:
            _rep = items[cl['rep']]
            _asp = NA.aspect_tags(_rep['title'] + ' ' + _rep.get('summary', ''), is_en=is_en)
            _chips = ''.join(_chip(a, _T['accent'], _T) for a in _asp)
            _cards += (
                f'<div style="flex:1 1 280px;min-width:240px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-radius:10px;padding:12px 14px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-size:10px;font-weight:800;color:{_T["accent"]};'
                f'background:{_T["accent"]}1A;padding:2px 8px;border-radius:6px">{cl["size"]} {"tin" if not is_en else "news"}</span>'
                f'</div>'
                f'<div style="font-size:13px;font-weight:600;color:{_T["text_primary"]};margin:6px 0 4px;line-height:1.4">{_rep["title"]}</div>'
                f'<div>{_chips}</div></div>')
        st.markdown(f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cards}</div>',
                    unsafe_allow_html=True)

    # ── Danh sách tin + chủ đề + cảm xúc ───────────────────────────────
    st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Tin mới nhất" if not is_en else "Latest headlines"}</div>',
                unsafe_allow_html=True)
    _rows = ''
    for _k, it in enumerate(items):
        lbl, col = _label(it['score'], is_en)
        _star = ('<span style="color:#0891B2;font-weight:800">★</span> '
                 if it.get('is_ticker') else '')
        _title = it['title']; _link = it.get('link', '')
        _title_html = (f'<a href="{_link}" target="_blank" style="color:{_T["text_primary"]};text-decoration:none">{_title}</a>'
                       if _link else _title)
        _asp = NA.aspect_tags(_title + ' ' + it.get('summary', ''), is_en=is_en)
        _asp_html = ''.join(_chip(a, _T['text_secondary'], _T) for a in _asp)
        # cảm xúc: từ điển + (nếu bật) AI học sâu
        _sent_cell = (f'<span style="font-size:11px;font-weight:700;color:{col};'
                      f'background:{col}1A;padding:2px 8px;border-radius:6px">{lbl} {it["score"]:+d}</span>')
        _ai = it.get('score_dl')
        if _ai is not None:
            _aic = '#16A34A' if _ai > 0.15 else ('#DC2626' if _ai < -0.15 else _T['text_muted'])
            _ail = ('AI+' if _ai > 0.15 else ('AI−' if _ai < -0.15 else 'AI±'))
            _sent_cell += (f'<br><span style="font-size:10px;font-weight:700;color:{_aic};'
                           f'background:{_aic}1A;padding:1px 7px;border-radius:6px;margin-top:3px;'
                           f'display:inline-block">{_ail} {_ai:+.2f}</span>')
        _rows += (
            f'<tr style="border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:9px 10px;white-space:nowrap;vertical-align:top">{_sent_cell}</td>'
            f'<td style="padding:9px 10px;font-size:13.5px;line-height:1.5">{_star}{_title_html}'
            f'<div style="margin-top:3px">{_asp_html}</div>'
            f'<div style="font-size:10.5px;color:{_T["text_muted"]};margin-top:2px">'
            f'{it.get("source","")} · {it.get("date","")[:25]}</div></td>'
            f'</tr>')
    st.markdown(
        f'<div style="border-radius:12px;overflow:hidden;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;background:{_T["bg_card"]}">'
        f'<tbody>{_rows}</tbody></table></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:12px;line-height:1.6">'
        f'{"★ = tin liên quan trực tiếp tới mã · chip xám = chủ đề tài chính. PhoBERT (AI học sâu) đọc hiểu ngầm khi máy có sẵn → cho ra phiếu tâm lý tin tức (dùng ở thẻ Dashboard + tín hiệu Chiến lược). Từ điển vẫn chạy song song để đối chiếu — máy không có transformers/torch thì app tự dùng từ điển (deploy-safe)." if not is_en else "★ = ticker-related · grey chips = financial aspects. PhoBERT (deep-learning AI) reads in background when available → produces the news-sentiment vote (used by Dashboard sentiment card + Strategy signal). Lexicon runs in parallel for comparison — without transformers/torch the app auto-falls back to lexicon (deploy-safe)."}'
        f'</div>', unsafe_allow_html=True)

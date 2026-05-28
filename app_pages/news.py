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

    # ── Toggle học sâu (PhoBERT) — mặc định tắt để app luôn mượt/deploy-safe ──
    _dl_ok = NA.dl_available()
    _cta, _ctb = st.columns([1.4, 2.6])
    with _cta:
        _dl_on = st.toggle(
            ('Đọc hiểu bằng AI học sâu' if not is_en else 'Deep-learning AI reading'),
            value=False, key='news_dl_on', disabled=not _dl_ok,
            help=('Dùng mô hình Transformer tiếng Việt (PhoBERT) để chấm cảm xúc '
                  'thay từ điển. Lần đầu nạp mô hình mất ~15-30s.'
                  if not is_en else
                  'Use a Vietnamese Transformer (PhoBERT) to score sentiment '
                  'instead of the lexicon. First load takes ~15-30s.'))
    with _ctb:
        _stat = (('● AI sẵn sàng (PhoBERT)' if _dl_ok else '○ AI chưa cài (dùng từ điển)')
                 if not is_en else
                 ('● AI ready (PhoBERT)' if _dl_ok else '○ AI not installed (using lexicon)'))
        _scol = _T['success'] if _dl_ok else _T['text_muted']
        st.markdown(
            f'<div style="font-size:11px;color:{_scol};margin-top:14px">{_stat}'
            f'<span style="color:{_T["text_muted"]}"> · '
            f'{"học sâu chỉ phục vụ đọc hiểu, không dùng dự báo giá" if not is_en else "deep learning serves reading only, not price forecasting"}'
            f'</span></div>', unsafe_allow_html=True)

    _dl_scores = None
    if _dl_on and _dl_ok:
        with st.spinner('AI đang đọc hiểu tin...' if not is_en else 'AI is reading the news...'):
            _dl_scores = NA.dl_sentiment_cached(tuple(it['title'] for it in items))
        if _dl_scores is None:
            st.info('AI tạm không khả dụng — dùng từ điển.' if not is_en
                    else 'AI unavailable — falling back to lexicon.')

    # ── Hai thẻ tâm lý: Thị trường & theo Mã (từ điển) ─────────────────
    _ml, _mc, _ma = _meter(r['market_score'], is_en, _T)
    c1, c2 = st.columns(2)
    with c1:
        _ai_line = ''
        if _dl_scores:
            _ai_net = sum(_dl_scores)
            _ai_lbl, _ai_col, _ai_arr = _meter(_ai_net, is_en, _T)
            _ai_line = (f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:4px">'
                        f'{"AI học sâu" if not is_en else "Deep-learning AI"}: '
                        f'<b style="color:{_ai_col}">{_ai_arr} {_ai_lbl}</b> '
                        f'({_ai_net:+.1f})</div>')
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
        if _dl_scores:
            _ai = _dl_scores[_k]
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
        f'{"★ = tin liên quan trực tiếp tới mã · chip xám = chủ đề tài chính (đọc hiểu). Cảm xúc từ điển luôn bật (deploy-safe, dùng cho phiếu tín hiệu); AI học sâu (PhoBERT) là tùy chọn — chỉ phục vụ ĐỌC HIỂU, không dùng dự báo giá. AI có thể lệch ở sắc thái tài chính nên hiển thị song song để đối chiếu." if not is_en else "★ = ticker-related · grey chips = financial aspects. Lexicon sentiment is always on (deploy-safe, used for the signal vote); deep-learning AI (PhoBERT) is optional — for READING only, not price forecasting. AI may misread financial nuance, hence shown side-by-side."}'
        f'</div>', unsafe_allow_html=True)

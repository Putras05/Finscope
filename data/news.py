"""Tin tức thị trường + chấm cảm xúc (sentiment) — bổ trợ dự báo cho FinScope.

- Nguồn: RSS công khai (CafeF, VnExpress Kinh doanh, Vietstock) — KHÔNG cần API key.
- Cảm xúc: từ điển tài chính tiếng Việt (lexicon) + xử lý phủ định đơn giản
  → nhẹ, minh bạch, deploy-safe (không phụ thuộc model nặng / mạng ngoài).
- Chịu lỗi: nếu RSS hỏng → trả rỗng kèm ghi chú, KHÔNG làm sập app.
"""
import re
import html
import urllib.request
import xml.etree.ElementTree as ET

import streamlit as st

# ── Nguồn RSS (thị trường chứng khoán VN) ───────────────────────────────────
_FEEDS = [
    ('CafeF',      'https://cafef.vn/thi-truong-chung-khoan.rss'),
    ('CafeF-DN',   'https://cafef.vn/doanh-nghiep.rss'),
    ('VnExpress',  'https://vnexpress.net/rss/kinh-doanh.rss'),
    ('Vietstock',  'https://vietstock.vn/144/chung-khoan.rss'),
]
_HDR = {'User-Agent': 'Mozilla/5.0 (FinScope news reader)'}

# ── Từ điển cảm xúc tài chính tiếng Việt ────────────────────────────────────
_POS = [
    'tăng trưởng', 'tăng mạnh', 'tăng', 'bứt phá', 'khởi sắc', 'hồi phục',
    'phục hồi', 'lợi nhuận', 'lãi', 'sinh lời', 'kỷ lục', 'cao nhất', 'vượt đỉnh',
    'vượt kế hoạch', 'vượt', 'mua ròng', 'dòng tiền', 'lạc quan', 'tích cực',
    'đột phá', 'hiệu quả', 'cổ tức', 'thưởng', 'mở rộng', 'trúng thầu', 'ký kết',
    'tăng trần', 'kịch trần', 'sắc xanh', 'khả quan', 'thăng hoa', 'dẫn dắt',
    'hút vốn', 'nâng hạng', 'thắng', 'đẩy mạnh', 'ổn định', 'bền vững',
]
_NEG = [
    'giảm mạnh', 'lao dốc', 'giảm sàn', 'kịch sàn', 'giảm', 'lao đao', 'thua lỗ',
    'thua', 'lỗ', 'rủi ro', 'bán tháo', 'bán ròng', 'tiêu cực', 'sụt', 'sụt giảm',
    'sắc đỏ', 'cảnh báo', 'vỡ nợ', 'phá sản', 'suy thoái', 'ảm đạm', 'bi quan',
    'áp lực', 'điều chỉnh giảm', 'thoái vốn', 'đình chỉ', 'xử phạt', 'gian lận',
    'nợ xấu', 'khủng hoảng', 'sa sút', 'mất giá', 'tháo chạy', 'đỏ lửa', 'bốc hơi',
    'thâm hụt', 'đáy', 'cắt lỗ', 'siết', 'điều tra', 'thâu tóm',
]
_NEGATORS = ['không', 'chưa', 'khó', 'thiếu', 'hạn chế']  # đảo dấu nếu đứng ngay trước

# Tên/từ khoá doanh nghiệp VN30 để lọc tin theo mã (bổ sung mã code).
_TICKER_KW = {
    'FPT': ['fpt'], 'HPG': ['hòa phát', 'hoa phat', 'hpg'],
    'VNM': ['vinamilk', 'vnm'], 'VCB': ['vietcombank', 'vcb'],
    'BID': ['bidv', 'bid'], 'CTG': ['vietinbank', 'ctg'],
    'TCB': ['techcombank', 'tcb'], 'MBB': ['mb bank', 'mbbank', 'mbb'],
    'ACB': ['acb'], 'VPB': ['vpbank', 'vpb'], 'STB': ['sacombank', 'stb'],
    'HDB': ['hdbank', 'hdb'], 'TPB': ['tpbank', 'tpb'], 'SHB': ['shb'],
    'VIB': ['vib'], 'VIC': ['vingroup', 'vic'], 'VHM': ['vinhomes', 'vhm'],
    'VRE': ['vincom retail', 'vincom', 'vre'], 'BCM': ['becamex', 'bcm'],
    'GAS': ['pv gas', 'gas'], 'PLX': ['petrolimex', 'plx'],
    'POW': ['pv power', 'pow'], 'GVR': ['cao su', 'gvr'],
    'MSN': ['masan', 'msn'], 'MWG': ['thế giới di động', 'thegioididong', 'mwg', 'điện máy xanh'],
    'SAB': ['sabeco', 'sab'], 'VJC': ['vietjet', 'vjc'],
    'SSI': ['ssi'], 'BVH': ['bảo việt', 'bao viet', 'bvh'],
}


def _strip(s: str) -> str:
    return re.sub(r'<[^>]+>', '', html.unescape(s or '')).strip()


def _parse_feed(raw: str):
    items = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return items
    for it in root.iter('item'):
        title = _strip(it.findtext('title', ''))
        link = (it.findtext('link', '') or '').strip()
        date = (it.findtext('pubDate', '') or '').strip()
        desc = _strip(it.findtext('description', ''))
        if title and len(title) > 10:
            items.append({'title': title, 'link': link, 'date': date, 'summary': desc})
    return items


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_all_news(limit_per_feed: int = 20):
    """Lấy headline từ tất cả nguồn RSS (cache 30 phút)."""
    out = []
    seen = set()
    for src, url in _FEEDS:
        try:
            req = urllib.request.Request(url, headers=_HDR)
            raw = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', 'ignore')
            for it in _parse_feed(raw)[:limit_per_feed]:
                key = it['title'].lower()[:80]
                if key in seen:
                    continue
                seen.add(key)
                it['source'] = src
                out.append(it)
        except Exception:
            continue
    return out


def score_text(text: str) -> int:
    """Điểm cảm xúc 1 dòng tin: (#tích cực − #tiêu cực), có xử lý phủ định."""
    t = ' ' + (text or '').lower() + ' '
    score = 0
    for w in _POS:
        for m in re.finditer(re.escape(w), t):
            pre = t[max(0, m.start() - 18):m.start()]
            score += -1 if any(n in pre for n in _NEGATORS) else 1
    for w in _NEG:
        for m in re.finditer(re.escape(w), t):
            pre = t[max(0, m.start() - 18):m.start()]
            score += 1 if any(n in pre for n in _NEGATORS) else -1
    return score


def _label(score: int, is_en: bool = False):
    if score > 0:
        return ('Tích cực', '#16A34A') if not is_en else ('Positive', '#16A34A')
    if score < 0:
        return ('Tiêu cực', '#DC2626') if not is_en else ('Negative', '#DC2626')
    return ('Trung lập', '#D97706') if not is_en else ('Neutral', '#D97706')


def news_sentiment(ticker: str, max_items: int = 14) -> dict:
    """Trả về tâm lý tin tức: tổng quan thị trường + lọc theo mã.

    {'ok', 'market_score', 'ticker_score', 'vote' (-1/0/1), 'n', 'items':[...],
     'ticker_n', 'note'}
    """
    try:
        allnews = _fetch_all_news()
    except Exception as e:
        return {'ok': False, 'note': f'Không lấy được tin: {str(e)[:80]}',
                'items': [], 'market_score': 0, 'ticker_score': 0, 'vote': 0,
                'n': 0, 'ticker_n': 0}
    if not allnews:
        return {'ok': False, 'note': 'Nguồn tin tạm thời không phản hồi.',
                'items': [], 'market_score': 0, 'ticker_score': 0, 'vote': 0,
                'n': 0, 'ticker_n': 0}

    kws = _TICKER_KW.get(ticker.upper(), [ticker.lower()])
    market_sum = 0
    items = []
    ticker_items = []
    for it in allnews:
        blob = (it['title'] + ' ' + it.get('summary', '')).lower()
        s = score_text(it['title'] + ' ' + it.get('summary', ''))
        it = {**it, 'score': s}
        market_sum += s
        is_tk = any(k in blob for k in kws)
        it['is_ticker'] = is_tk
        items.append(it)
        if is_tk:
            ticker_items.append(it)

    # Ưu tiên hiển thị tin theo mã, rồi tới tin thị trường mới nhất
    items_sorted = ticker_items + [i for i in items if not i['is_ticker']]
    items_sorted = items_sorted[:max_items]

    ticker_sum = sum(i['score'] for i in ticker_items)
    # Phiếu: ưu tiên tâm lý theo mã nếu có đủ tin, ngược lại dùng thị trường
    if len(ticker_items) >= 2:
        vote_src = ticker_sum
    else:
        vote_src = market_sum
    vote = 1 if vote_src > 1 else (-1 if vote_src < -1 else 0)

    return {
        'ok': True, 'note': '',
        'market_score': market_sum, 'ticker_score': ticker_sum,
        'vote': vote, 'n': len(allnews), 'ticker_n': len(ticker_items),
        'items': items_sorted,
    }

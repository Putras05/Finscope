"""Tin tức thị trường + chấm cảm xúc (sentiment) — bổ trợ dự báo cho FinScope.

- Nguồn: RSS công khai (CafeF, VnExpress Kinh doanh, Vietstock) — KHÔNG cần API key.
- Cảm xúc: từ điển tài chính tiếng Việt (lexicon) + xử lý phủ định đơn giản
  → nhẹ, minh bạch, deploy-safe (không phụ thuộc model nặng / mạng ngoài).
- Chịu lỗi: nếu RSS hỏng → trả rỗng kèm ghi chú, KHÔNG làm sập app.
"""
import re
import html
import email.utils
import datetime
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

# ── Từ điển cảm xúc tài chính tiếng Việt (có trọng số mạnh/yếu) ──────────────
# Trọng số ±2 = tín hiệu mạnh, ±1 = tín hiệu thường.
_POS_STRONG = [
    'kịch trần', 'tăng trần', 'bứt phá', 'kỷ lục', 'lãi kỷ lục', 'vượt đỉnh',
    'tăng mạnh', 'tăng vọt', 'lãi lớn', 'mua ròng mạnh', 'bùng nổ', 'lập đỉnh',
]
_POS = [
    'tăng trưởng', 'tăng', 'khởi sắc', 'hồi phục', 'phục hồi', 'lợi nhuận',
    'lãi', 'sinh lời', 'cao nhất', 'vượt kế hoạch', 'vượt', 'mua ròng',
    'dòng tiền', 'lạc quan', 'tích cực', 'đột phá', 'hiệu quả', 'cổ tức',
    'thưởng', 'mở rộng', 'trúng thầu', 'ký kết', 'sắc xanh', 'khả quan',
    'thăng hoa', 'dẫn dắt', 'hút vốn', 'nâng hạng', 'thắng', 'đẩy mạnh',
    'ổn định', 'bền vững', 'phục vụ', 'hợp tác', 'đầu tư', 'mở bán', 'niêm yết',
]
_NEG_STRONG = [
    'giảm sàn', 'kịch sàn', 'bán tháo', 'lao dốc', 'vỡ nợ', 'phá sản',
    'khủng hoảng', 'thua lỗ nặng', 'sụt mạnh', 'giảm mạnh', 'đỏ lửa',
    'tháo chạy', 'bốc hơi', 'lao đao', 'bán ròng mạnh',
]
_NEG = [
    'giảm', 'thua lỗ', 'thua', 'lỗ', 'rủi ro', 'bán tháo', 'bán ròng',
    'tiêu cực', 'sụt', 'sụt giảm', 'sắc đỏ', 'cảnh báo', 'suy thoái', 'ảm đạm',
    'bi quan', 'áp lực', 'điều chỉnh giảm', 'thoái vốn', 'đình chỉ', 'xử phạt',
    'gian lận', 'nợ xấu', 'sa sút', 'mất giá', 'thâm hụt', 'đáy', 'cắt lỗ',
    'siết', 'điều tra', 'chậm', 'hoãn', 'đình trệ', 'thu hồi',
]
_NEGATORS = ['không', 'chưa', 'khó', 'thiếu', 'hạn chế']  # đảo dấu nếu đứng ngay trước

# Bảng tra (phrase, trọng số có dấu), sắp giảm dần độ dài để khớp cụm dài/mạnh trước.
_LEX = sorted(
    [(w, 2) for w in _POS_STRONG] + [(w, 1) for w in _POS]
    + [(w, -2) for w in _NEG_STRONG] + [(w, -1) for w in _NEG],
    key=lambda kv: -len(kv[0]))

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
    """Điểm cảm xúc 1 dòng tin theo từ điển có trọng số (±2 mạnh, ±1 thường).

    Quét cụm dài/mạnh trước rồi "xoá" vùng đã khớp (thay bằng khoảng trắng) để
    không đếm trùng cụm con (vd. 'tăng mạnh' đã tính thì không tính lại 'tăng').
    Xử lý phủ định: nếu ngay trước cụm (≤18 ký tự) có từ phủ định → đảo dấu.
    """
    t = ' ' + (text or '').lower() + ' '
    score = 0
    for w, wt in _LEX:
        while w in t:
            i = t.index(w)
            pre = t[max(0, i - 18):i]
            sign = -1 if any(n in pre for n in _NEGATORS) else 1
            score += sign * wt
            t = t[:i] + ' ' * len(w) + t[i + len(w):]   # xoá vùng đã khớp
    return score


def _recency_weight(date_str: str) -> float:
    """Trọng số theo độ mới của tin (half-life ~48h). Tin càng mới càng nặng.

    Không phân tích được ngày → trả 1.0 (coi như mới). Luôn nằm trong (0,1].
    """
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt is None:
            return 1.0
        now = (datetime.datetime.now(dt.tzinfo) if dt.tzinfo
               else datetime.datetime.now())
        age_h = max(0.0, (now - dt).total_seconds() / 3600.0)
        return float(0.5 ** (age_h / 48.0))
    except Exception:
        return 1.0


def _label(score: int, is_en: bool = False):
    if score > 0:
        return ('Tích cực', '#16A34A') if not is_en else ('Positive', '#16A34A')
    if score < 0:
        return ('Tiêu cực', '#DC2626') if not is_en else ('Negative', '#DC2626')
    return ('Trung lập', '#D97706') if not is_en else ('Neutral', '#D97706')


@st.cache_data(ttl=1800, show_spinner=False)
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
    market_w = 0.0           # tổng có trọng số độ-mới (dùng cho phiếu)
    items = []
    ticker_items = []
    for it in allnews:
        blob = (it['title'] + ' ' + it.get('summary', '')).lower()
        s = score_text(it['title'] + ' ' + it.get('summary', ''))
        rw = _recency_weight(it.get('date', ''))
        it = {**it, 'score': s, 'rw': rw}
        market_sum += s
        market_w += s * rw
        is_tk = any(k in blob for k in kws)
        it['is_ticker'] = is_tk
        items.append(it)
        if is_tk:
            ticker_items.append(it)

    # Ưu tiên hiển thị tin theo mã, rồi tới tin thị trường mới nhất
    items_sorted = ticker_items + [i for i in items if not i['is_ticker']]
    items_sorted = items_sorted[:max_items]

    ticker_sum = sum(i['score'] for i in ticker_items)
    ticker_w = sum(i['score'] * i['rw'] for i in ticker_items)

    # ── ĐỌC HIỂU BẰNG AI HỌC SÂU (PhoBERT) — luôn bật nếu có sẵn (đã được
    #    warm ngầm ở trang bìa). Liên kết: điểm DL được nhân với trọng số
    #    độ-mới và DÙNG LÀM PHIẾU CHÍNH cho thẻ Dashboard + tín hiệu Chiến
    #    lược. Thiếu transformers/torch → tự về từ điển (deploy-safe). ──
    dl_used = False
    market_dl = 0.0
    ticker_dl = 0.0
    try:
        from data.news_ai import dl_available, dl_sentiment_cached
        if dl_available():
            _titles = tuple(it['title'] for it in items_sorted)
            _dl = dl_sentiment_cached(_titles)
            if _dl is not None:
                dl_used = True
                # Gắn DL score vào từng item hiển thị + cộng dồn (có trọng số độ-mới)
                for it, ds in zip(items_sorted, _dl):
                    it['score_dl'] = float(ds)
                    market_dl += float(ds) * it.get('rw', 1.0)
                    if it.get('is_ticker'):
                        ticker_dl += float(ds) * it.get('rw', 1.0)
    except Exception:
        pass

    # Phiếu tổng hợp: ƯU TIÊN DL khi có sẵn; ngưỡng nhẹ hơn vì DL score ∈ [−1,1].
    if dl_used:
        _tk_n = sum(1 for it in items_sorted if it.get('is_ticker'))
        vote_src = ticker_dl if _tk_n >= 2 else market_dl
        vote = 1 if vote_src > 0.6 else (-1 if vote_src < -0.6 else 0)
    else:
        vote_src = ticker_w if len(ticker_items) >= 2 else market_w
        vote = 1 if vote_src > 1.0 else (-1 if vote_src < -1.0 else 0)

    return {
        'ok': True, 'note': '',
        'market_score': market_sum, 'ticker_score': ticker_sum,
        'market_score_dl': market_dl, 'ticker_score_dl': ticker_dl,
        'dl_used': dl_used,
        'vote': vote, 'n': len(allnews), 'ticker_n': len(ticker_items),
        'items': items_sorted,
    }

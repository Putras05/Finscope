"""ĐỌC HIỂU TIN TỨC bằng AI cho FinScope — bổ trợ dự báo.

Triết lý (đồng bộ với phần học sâu của app): "deploy-safe + tùy chọn".
  • Mặc định: NLP nhẹ (deploy-safe) — nhận diện CHỦ ĐỀ (aspect) tài chính của
    từng tin + GOM NHÓM tin cùng chủ đề (TF-IDF + cosine, sklearn).
  • Tùy chọn: cảm xúc bằng HỌC SÂU — mô hình Transformer tiếng Việt
    (PhoBERT sentiment). Nạp LƯỜI + cache; nếu thiếu transformers/torch hoặc
    tải lỗi → tự fallback về từ điển (data.news.score_text) → app KHÔNG vỡ.

KHÔNG import torch/transformers ở cấp module → khởi động nhanh, deploy nhẹ.
Cảm xúc học sâu chỉ dùng cho "đọc hiểu" (hiển thị/diễn giải tin), KHÔNG dùng
để dự báo giá — theo đúng định hướng: học sâu phục vụ ĐỌC HIỂU.
"""
import re
import streamlit as st

# Tên mô hình sentiment tiếng Việt (PhoBERT). Có thể đổi qua biến môi trường.
import os
_DL_MODEL = os.environ.get('FINSCOPE_SENTIMENT_MODEL',
                           'wonrax/phobert-base-vietnamese-sentiment')

# ── Nhận diện CHỦ ĐỀ tài chính (aspect) — rule-based, deploy-safe ────────────
_ASPECTS = [
    ('Kết quả KD', 'Earnings', ['lợi nhuận', 'doanh thu', 'lãi', 'thua lỗ', ' lỗ ', 'kqkd',
                                'báo cáo tài chính', 'quý ', 'biên lợi nhuận', 'eps']),
    ('Cổ tức', 'Dividend', ['cổ tức', 'chia thưởng', 'cổ phiếu thưởng', 'tạm ứng cổ tức']),
    ('M&A · Thoái vốn', 'M&A · Divestment', ['sáp nhập', 'mua lại', 'thâu tóm', 'thoái vốn',
                                             'chuyển nhượng', 'chào mua', 'm&a']),
    ('Phát hành · Niêm yết', 'Issuance · Listing', ['phát hành', 'niêm yết', 'tăng vốn', 'trái phiếu',
                                                    'ipo', 'quyền mua', 'chào bán', 'lên sàn']),
    ('Lãnh đạo · Cổ đông', 'Leadership · Shareholders', ['chủ tịch', 'tổng giám đốc', 'ceo', 'từ nhiệm',
                                                         'bổ nhiệm', 'cổ đông lớn', 'đăng ký mua',
                                                         'đăng ký bán', 'nội bộ']),
    ('Pháp lý · Vi phạm', 'Legal · Violation', ['xử phạt', 'vi phạm', 'điều tra', 'khởi tố',
                                                'thanh tra', 'truy thu', 'đình chỉ', 'gian lận',
                                                'thao túng', 'cảnh báo']),
    ('Vĩ mô · Lãi suất', 'Macro · Rates', ['lãi suất', 'tỷ giá', 'lạm phát', 'fed', 'gdp',
                                           'ngân hàng nhà nước', 'room tín dụng', 'tín dụng',
                                           'vĩ mô', 'cpi']),
    ('Khối ngoại', 'Foreign flows', ['khối ngoại', 'nước ngoài', 'mua ròng', 'bán ròng',
                                     'etf', 'quỹ ngoại']),
    ('Dự án · Đầu tư', 'Projects · Capex', ['dự án', 'khởi công', 'nhà máy', 'mở rộng',
                                            'trúng thầu', 'ký kết', 'hợp đồng', 'đầu tư']),
]


def aspect_tags(text: str, max_tags: int = 3, is_en: bool = False) -> list:
    """Trả các nhãn chủ đề tài chính khớp trong tin (tối đa max_tags).

    is_en=True → trả nhãn tiếng Anh (app song ngữ)."""
    t = ' ' + (text or '').lower() + ' '
    hits = []
    for name_vi, name_en, kws in _ASPECTS:
        c = sum(1 for k in kws if k in t)
        if c:
            hits.append((name_en if is_en else name_vi, c))
    hits.sort(key=lambda x: -x[1])
    return [h[0] for h in hits[:max_tags]]


# ── Cảm xúc HỌC SÂU (Transformer) — lazy + fail-safe ────────────────────────
def dl_available() -> bool:
    """transformers + torch có sẵn để chạy học sâu không?"""
    import importlib.util as _u
    return (_u.find_spec('transformers') is not None
            and _u.find_spec('torch') is not None)


@st.cache_resource(show_spinner=False)
def _load_dl_pipeline(model_name: str = _DL_MODEL):
    """Nạp pipeline sentiment tiếng Việt 1 lần/phiên. Lỗi → None (fallback)."""
    try:
        os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error')
        os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
        from transformers import pipeline
        return pipeline('sentiment-analysis', model=model_name,
                        truncation=True, max_length=256, top_k=None)
    except Exception:
        return None


# Nhãn của các mô hình sentiment tiếng Việt phổ biến → dấu cảm xúc.
_POS_LABELS = {'POS', 'POSITIVE', 'LABEL_2', 'TÍCH CỰC', 'TICH CUC'}
_NEG_LABELS = {'NEG', 'NEGATIVE', 'LABEL_0', 'TIÊU CỰC', 'TIEU CUC'}


def _label_to_signed(label: str, score: float) -> float:
    u = (label or '').upper()
    if u in _POS_LABELS:
        return float(score)
    if u in _NEG_LABELS:
        return -float(score)
    return 0.0


def dl_sentiment(texts: list) -> list | None:
    """Điểm cảm xúc học sâu cho list văn bản → list float trong [-1, 1].

    Trả None nếu học sâu không khả dụng (caller sẽ fallback sang lexicon).
    """
    if not texts or not dl_available():
        return None
    pipe = _load_dl_pipeline()
    if pipe is None:
        return None
    try:
        raw = pipe(list(texts))
        out = []
        for r in raw:
            # top_k=None → list dict; lấy nhãn điểm cao nhất
            best = max(r, key=lambda d: d['score']) if isinstance(r, list) else r
            out.append(_label_to_signed(best['label'], best['score']))
        return out
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def dl_sentiment_cached(titles: tuple) -> list | None:
    """Bọc cache cho dl_sentiment (key theo tuple tiêu đề) → đổi tab/rerun nhanh."""
    return dl_sentiment(list(titles))


# ── Gom nhóm tin cùng CHỦ ĐỀ (TF-IDF + cosine) — deploy-safe ────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def cluster_themes(titles: tuple, sim_thr: float = 0.34, min_size: int = 2) -> list:
    """Gom các tiêu đề gần nhau về nội dung thành CHỦ ĐỀ.

    titles: tuple[str] (tuple để hashable cho cache). Trả list cluster:
    [{'rep': idx_đại_diện, 'members': [idx...], 'size': n}], xếp theo kích cỡ.
    """
    titles = list(titles)
    n = len(titles)
    if n < min_size:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.9)
        X = vec.fit_transform([(t or '').lower() for t in titles])
        S = cosine_similarity(X)
    except Exception:
        return []

    assigned = [False] * n
    clusters = []
    order = sorted(range(n), key=lambda i: -float(S[i].sum()))   # tâm trước
    for i in order:
        if assigned[i]:
            continue
        members = [i]; assigned[i] = True
        for j in range(n):
            if not assigned[j] and S[i, j] >= sim_thr:
                members.append(j); assigned[j] = True
        if len(members) >= min_size:
            clusters.append({'rep': i, 'members': members, 'size': len(members)})
    clusters.sort(key=lambda c: -c['size'])
    return clusters

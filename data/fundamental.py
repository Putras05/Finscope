"""Phân tích cơ bản (Fundamental) — báo cáo tài chính + tỷ số tài chính.

Nguồn: vnstock 4.x VCI source (`finance.income_statement` + `balance_sheet`).
Bản miễn phí cộng đồng giới hạn 4 KỲ gần nhất — đủ để tính TTM (trailing 12
months) cho các tỷ số quan trọng (P/E, P/B, ROE, ROA, EPS, biên LN…).

Endpoint `ratio()` chỉ trả demo 2018 nên KHÔNG dùng; ta TỰ TÍNH ratio từ
income+balance+giá thị trường → số liệu REAL của quý gần nhất.
"""
import streamlit as st
import pandas as pd
import numpy as np


# Các tên dòng (item) cần trích ra từ báo cáo. Map: key nội bộ → list các
# pattern (case-insensitive) trong cột 'item' của vnstock.
_INC_MAP = {
    # 'Doanh thu thuần' (DN thường) | 'Tổng thu nhập hoạt động' (ngân hàng)
    'revenue':       ['Doanh thu thuần', 'Tổng thu nhập hoạt động'],
    # 'Lợi nhuận gộp' (DN) | bank dùng "LN thuần HĐ trước trích lập" làm gross-tương đương
    'gross_profit':  ['Lợi nhuận gộp', 'Lợi nhuận thuần hoạt động trước khi trích lập dự phòng'],
    'op_profit':     ['Lãi/(lỗ) từ hoạt động kinh doanh', 'Lợi nhuận thuần từ hoạt động kinh doanh'],
    # bank: 'Tổng lợi nhuận/lỗ trước thuế' | DN: 'Lãi/(lỗ) trước thuế'
    'pretax':        ['Tổng lợi nhuận/lỗ trước thuế', 'Lãi/(lỗ) trước thuế', 'Lợi nhuận trước thuế'],
    # bank: 'Cổ đông của Công ty mẹ' | DN: 'Lợi nhuận của Cổ đông của Công ty mẹ'
    # Pattern ngắn 'Cổ đông của Công ty mẹ' contains-match cả 2 → đúng cho cả 2.
    'net_income':    ['Cổ đông của Công ty mẹ', 'Lợi nhuận sau thuế'],
    'eps':           ['Lãi cơ bản trên cổ phiếu', 'EPS'],
}
_BAL_MAP = {
    # DN: 'TỔNG CỘNG TÀI SẢN' | bank: 'TỔNG TÀI SẢN' — match cả 2 qua substring 'TÀI SẢN'... quá rộng;
    # nên giữ 2 pattern riêng, _find_row trả pattern khớp ĐẦU TIÊN.
    'total_assets':  ['TỔNG CỘNG TÀI SẢN', 'TỔNG TÀI SẢN'],
    'equity':        ['Vốn chủ sở hữu'],   # contains-case-insensitive matches cả 'VỐN CHỦ SỞ HỮU'
    # 'NỢ PHẢI TRẢ' contains-match cả 'NỢ PHẢI TRẢ' (DN) và 'TỔNG NỢ PHẢI TRẢ' (bank).
    'total_debt':    ['NỢ PHẢI TRẢ'],
    'short_debt':    ['Nợ ngắn hạn'],         # DN: có · bank: NaN (chấp nhận)
    'long_debt':     ['Nợ dài hạn'],          # DN: có · bank: NaN
    # bank không có 'Tiền và tương đương tiền' theo đúng nghĩa → NaN, chấp nhận.
    'cash':          ['Tiền và tương đương tiền'],
}


def _find_row(df: pd.DataFrame, patterns: list):
    """Tìm dòng đầu tiên trong df có cột 'item' khớp 1 trong các pattern."""
    if df is None or df.empty:
        return None
    for p in patterns:
        mask = df['item'].astype(str).str.contains(p, case=False, regex=False, na=False)
        m = df[mask]
        if len(m):
            return m.iloc[0]
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financials(ticker: str) -> dict:
    """Lấy income + balance sheet 4 quý gần nhất (vnstock 4.x VCI).

    Trả {'ok', 'note', 'periods': [...], 'income': df, 'balance': df}.
    Lỗi mạng/API → ok=False, không ném exception."""
    try:
        import contextlib, io
        from concurrent.futures import ThreadPoolExecutor
        from vnstock import Vnstock
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            s = Vnstock().stock(symbol=ticker.upper(), source='VCI')
            # Income + Balance SONG SONG → giảm chờ network từ ~6s xuống ~3s
            # (vnstock 4 mỗi call mất ~2-3s; chạy đồng thời chỉ tốn max).
            with ThreadPoolExecutor(max_workers=2) as _ex:
                _f_inc = _ex.submit(s.finance.income_statement, period='quarter', lang='vi')
                _f_bal = _ex.submit(s.finance.balance_sheet, period='quarter', lang='vi')
                inc = _f_inc.result()
                bal = _f_bal.result()
        periods = [c for c in inc.columns if c not in ('item', 'item_en', 'item_id')]
        return {'ok': True, 'note': '', 'periods': periods,
                'income': inc, 'balance': bal}
    except Exception as e:
        return {'ok': False, 'note': f'Không lấy được BCTC: {str(e)[:120]}',
                'periods': [], 'income': None, 'balance': None}


def _row_to_list(row, periods: list) -> list:
    """Trả list giá trị float của row theo thứ tự periods (NaN nếu thiếu)."""
    if row is None:
        return [float('nan')] * len(periods)
    out = []
    for p in periods:
        try:
            v = row[p]; out.append(float(v) if v is not None else float('nan'))
        except Exception:
            out.append(float('nan'))
    return out


def extract_series(fin: dict) -> dict:
    """Trả {key: [values 4 quý]} cho mỗi metric quan trọng + periods."""
    if not fin or not fin.get('ok'):
        return {'periods': [], 'income': {}, 'balance': {}}
    periods = fin['periods']
    inc = fin['income']; bal = fin['balance']
    income_s = {k: _row_to_list(_find_row(inc, pats), periods)
                for k, pats in _INC_MAP.items()}
    balance_s = {k: _row_to_list(_find_row(bal, pats), periods)
                 for k, pats in _BAL_MAP.items()}
    return {'periods': periods, 'income': income_s, 'balance': balance_s}


def compute_kpis(ext: dict, last_price_vnd: float = 0.0,
                 listed_share: float = 0.0) -> dict:
    """Tính các tỷ số cơ bản TỰ DERIVED từ income + balance + giá thị trường.

    last_price_vnd: giá hiện tại (đồng/cp). listed_share: số CP lưu hành.
    Nếu thiếu market info → P/E, P/B = NaN (vẫn tính được ROE/ROA/biên LN).
    """
    if not ext or not ext['periods']:
        return {'ok': False}
    inc = ext['income']; bal = ext['balance']

    def _ttm(arr):
        """TTM = tổng 4 kỳ (giả định 4 quý gần nhất là TTM)."""
        vals = [v for v in arr if v == v]                # not NaN
        return sum(vals) if vals else float('nan')

    def _last(arr):
        for v in arr:
            if v == v: return v
        return float('nan')

    rev_ttm   = _ttm(inc['revenue'])
    gp_ttm    = _ttm(inc['gross_profit'])
    ni_ttm    = _ttm(inc['net_income'])
    eps_ttm   = _ttm(inc['eps'])
    pretax_ttm= _ttm(inc['pretax'])

    assets    = _last(bal['total_assets'])
    equity    = _last(bal['equity'])
    debt      = _last(bal['total_debt'])
    cash      = _last(bal['cash'])

    # Tỷ số tự tính
    gross_margin = (gp_ttm / rev_ttm * 100) if rev_ttm > 0 else float('nan')
    net_margin   = (ni_ttm / rev_ttm * 100) if rev_ttm > 0 else float('nan')
    roe          = (ni_ttm / equity * 100) if equity > 0 else float('nan')
    roa          = (ni_ttm / assets * 100) if assets > 0 else float('nan')
    debt_equity  = (debt / equity) if equity > 0 else float('nan')

    # Fallback EPS: nếu vnstock không có EPS sẵn (vd TCB trả 0), tự tính từ
    # TTM NI / số CP lưu hành. Đánh dấu nguồn để UI biết.
    eps_source = 'reported'
    if (eps_ttm == eps_ttm and eps_ttm > 0):
        pass    # giữ nguyên
    elif ni_ttm == ni_ttm and listed_share > 0:
        eps_ttm = ni_ttm / listed_share
        eps_source = 'computed'   # tính: TTM NI / số CP

    mcap = (last_price_vnd * listed_share) if (last_price_vnd > 0 and listed_share > 0) else float('nan')
    pe   = (last_price_vnd / eps_ttm) if (last_price_vnd > 0 and eps_ttm == eps_ttm and eps_ttm > 0) else float('nan')
    bvps = (equity / listed_share) if listed_share > 0 else float('nan')
    pb   = (last_price_vnd / bvps) if (last_price_vnd > 0 and bvps > 0) else float('nan')

    # YoY growth: so cùng quý năm trước nếu có (Q1 năm nay vs Q1 năm trước thường KHÔNG có với 4 quý).
    # 4 kỳ gần nhất thường là Q-1, Q-2, Q-3, Q-4 (4 quý gần nhất), nên YoY khả thi
    # = quý hiện tại / quý cách đó 4 (nếu có quý 5 trở đi → chưa có).
    # Với 4 kỳ: chỉ có Q-on-Q (so quý gần nhất với quý liền trước).
    def _qoq(arr):
        if len(arr) >= 2 and arr[0] == arr[0] and arr[1] == arr[1] and arr[1] != 0:
            return (arr[0] - arr[1]) / abs(arr[1]) * 100
        return float('nan')
    rev_qoq = _qoq(inc['revenue'])
    ni_qoq  = _qoq(inc['net_income'])

    return {
        'ok': True,
        'rev_ttm': rev_ttm, 'gp_ttm': gp_ttm, 'ni_ttm': ni_ttm,
        'eps_ttm': eps_ttm, 'eps_source': eps_source, 'pretax_ttm': pretax_ttm,
        'gross_margin': gross_margin, 'net_margin': net_margin,
        'roe': roe, 'roa': roa, 'debt_equity': debt_equity,
        'total_assets': assets, 'equity': equity, 'total_debt': debt, 'cash': cash,
        'market_cap': mcap, 'pe': pe, 'pb': pb, 'bvps': bvps,
        'last_price': last_price_vnd, 'listed_share': listed_share,
        'rev_qoq': rev_qoq, 'ni_qoq': ni_qoq,
    }

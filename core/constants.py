import hashlib
import streamlit as st

# ── Danh sách mã VN30 (HOSE) ────────────────────────────────────────────────
# 3 mã đầu (FPT, HPG, VNM) giữ làm mặc định/đại diện 3 nhóm tính chất khác nhau.
TICKERS = [
    'FPT', 'HPG', 'VNM',
    'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB', 'VPB', 'STB', 'HDB', 'TPB', 'SHB', 'VIB',
    'VIC', 'VHM', 'VRE', 'BCM',
    'GAS', 'PLX', 'POW', 'GVR',
    'MSN', 'MWG', 'SAB', 'VJC', 'SSI', 'BVH',
    # ── Mã HOSE thanh khoản cao bổ sung (ngoài VN30) ──
    'PNJ', 'REE', 'GMD', 'DGC', 'DCM', 'DPM', 'HSG', 'NKG',
    'PDR', 'DXG', 'KDH', 'NLG', 'KBC', 'VND', 'HCM', 'VCI',
    'FRT', 'DGW', 'GEX', 'VHC', 'DBC', 'BMP', 'PVD', 'SZC',
]

# Nhóm ngành (đơn ngữ, đa số là danh từ riêng + sàn) — dùng cho nhãn hiển thị.
TICKER_INFO = {
    'FPT': 'Công nghệ thông tin · HOSE',
    'HPG': 'Thép — Vật liệu xây dựng · HOSE',
    'VNM': 'Thực phẩm — Đồ uống · HOSE',
    'VCB': 'Ngân hàng · HOSE', 'BID': 'Ngân hàng · HOSE', 'CTG': 'Ngân hàng · HOSE',
    'TCB': 'Ngân hàng · HOSE', 'MBB': 'Ngân hàng · HOSE', 'ACB': 'Ngân hàng · HOSE',
    'VPB': 'Ngân hàng · HOSE', 'STB': 'Ngân hàng · HOSE', 'HDB': 'Ngân hàng · HOSE',
    'TPB': 'Ngân hàng · HOSE', 'SHB': 'Ngân hàng · HOSE', 'VIB': 'Ngân hàng · HOSE',
    'VIC': 'Tập đoàn đa ngành · HOSE', 'VHM': 'Bất động sản · HOSE',
    'VRE': 'Bất động sản bán lẻ · HOSE', 'BCM': 'Bất động sản KCN · HOSE',
    'GAS': 'Dầu khí · HOSE', 'PLX': 'Xăng dầu · HOSE', 'POW': 'Điện · HOSE',
    'GVR': 'Cao su · HOSE',
    'MSN': 'Tiêu dùng — Bán lẻ · HOSE', 'MWG': 'Bán lẻ · HOSE',
    'SAB': 'Đồ uống · HOSE', 'VJC': 'Hàng không · HOSE',
    'SSI': 'Chứng khoán · HOSE', 'BVH': 'Bảo hiểm · HOSE',
    # ── Bổ sung ngoài VN30 ──
    'PNJ': 'Bán lẻ trang sức · HOSE', 'REE': 'Điện — Hạ tầng · HOSE',
    'GMD': 'Cảng biển — Logistics · HOSE', 'DGC': 'Hóa chất · HOSE',
    'DCM': 'Phân bón · HOSE', 'DPM': 'Phân bón · HOSE',
    'HSG': 'Tôn — Thép · HOSE', 'NKG': 'Tôn — Thép · HOSE',
    'PDR': 'Bất động sản · HOSE', 'DXG': 'Bất động sản · HOSE',
    'KDH': 'Bất động sản · HOSE', 'NLG': 'Bất động sản · HOSE',
    'KBC': 'Bất động sản KCN · HOSE', 'VND': 'Chứng khoán · HOSE',
    'HCM': 'Chứng khoán · HOSE', 'VCI': 'Chứng khoán · HOSE',
    'FRT': 'Bán lẻ công nghệ — dược · HOSE', 'DGW': 'Phân phối công nghệ · HOSE',
    'GEX': 'Đầu tư đa ngành · HOSE', 'VHC': 'Thủy sản · HOSE',
    'DBC': 'Chăn nuôi — Nông nghiệp · HOSE', 'BMP': 'Nhựa xây dựng · HOSE',
    'PVD': 'Dầu khí — Khoan · HOSE', 'SZC': 'Bất động sản KCN · HOSE',
}
TICKER_DESC = {
    'FPT': 'Cổ phiếu tăng trưởng bền vững, xu hướng tăng tuyến tính dài hạn.',
    'HPG': 'Cổ phiếu chu kỳ biến động cao, nhạy cảm với giá thép và đầu tư công.',
    'VNM': 'Cổ phiếu phòng thủ xu hướng giảm, biên độ thấp và ổn định.',
}


def ticker_sector(tk: str) -> str:
    """Nhãn ngành của mã, fallback gọn cho mã ngoài danh mục."""
    return TICKER_INFO.get(tk, f'{tk} · HOSE')


def ticker_desc(tk: str) -> str:
    """Mô tả ngắn của mã, fallback dùng nhãn ngành."""
    return TICKER_DESC.get(tk, ticker_sector(tk))


# ── Bảng màu tự sinh cho mã bất kỳ (giữ tương thích CLR[ticker]) ────────────
_PALETTE_LIGHT = [
    '#1565C0', '#6A1B9A', '#2E7D32', '#C2185B', '#00838F', '#E65100',
    '#283593', '#AD1457', '#0277BD', '#558B2F', '#4527A0', '#00695C',
    '#BF360C', '#1B5E20', '#4A148C', '#01579B',
]
_PALETTE_DARK = [
    '#60A5FA', '#C084FC', '#34D399', '#F472B6', '#22D3EE', '#FB923C',
    '#818CF8', '#F9A8D4', '#38BDF8', '#A3E635', '#A78BFA', '#2DD4BF',
    '#FCA5A5', '#86EFAC', '#D8B4FE', '#7DD3FC',
]


class _ColorMap(dict):
    """dict màu theo ticker; mã chưa khai báo → tự gán màu ổn định từ palette."""
    def __init__(self, base, palette):
        super().__init__(base)
        self._palette = palette

    def __missing__(self, key):
        h = int(hashlib.md5(str(key).encode('utf-8')).hexdigest(), 16)
        return self._palette[h % len(self._palette)]


CLR = _ColorMap(
    {'FPT': '#1565C0', 'HPG': '#6A1B9A', 'VNM': '#2E7D32', 'pred': '#C62828'},
    _PALETTE_LIGHT,
)
CLR_DARK = _ColorMap(
    {'FPT': '#60A5FA', 'HPG': '#C084FC', 'VNM': '#34D399', 'pred': '#F87171'},
    _PALETTE_DARK,
)

COLORS = {
    'buy': '#2E7D32', 'sell': '#C62828', 'warn': '#F9A825', 'neut': '#546E8A',
    'text_primary': '#1A2A4A', 'text_secondary': '#556888', 'text_muted': '#8090B0',
    'border': '#DDE8F5', 'bg_card': '#FFFFFF', 'blue': '#1565C0', 'purple': '#6A1B9A',
}


def get_clr(T: dict) -> dict:
    return CLR_DARK if T.get('is_dark', False) else CLR

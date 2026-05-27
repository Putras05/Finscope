"""Phân tích kỹ thuật cổ điển cho FinScope — thuần numpy/pandas, nhẹ & nhanh.

Gồm các kỹ thuật được dùng phổ biến nhất trong giao dịch chứng khoán:
  • swing_points       — điểm đảo chiều (đỉnh/đáy cục bộ) theo fractal.
  • support_resistance — gom các đỉnh/đáy thành vùng HỖ TRỢ / KHÁNG CỰ.
  • fibonacci_levels   — các mức thoái lui Fibonacci từ sóng lớn gần nhất.
  • pivot_points       — điểm xoay sàn giao dịch (PP, R1-3, S1-3).
  • trend_channel      — kênh xu hướng hồi quy tuyến tính (giữa ± k·σ).
  • zigzag             — đường ZigZag nối các điểm đảo chiều (nền tảng đếm sóng).

Tất cả hàm CHỊU LỖI: thiếu dữ liệu → trả cấu trúc rỗng, không ném exception.
Giá trong df ở đơn vị "nghìn đồng" (như toàn app); hàm không nhân 1000.
"""
import numpy as np
import pandas as pd


# ── Điểm swing (đỉnh/đáy cục bộ) ────────────────────────────────────────────
def swing_points(df: pd.DataFrame, window: int = 5) -> dict:
    """Tìm đỉnh/đáy cục bộ: nến cao/thấp nhất trong cửa sổ ±window.

    Trả {'high_idx', 'high_px', 'low_idx', 'low_px'} (chỉ số theo vị trí hàng).
    """
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    n = len(df)
    hi_idx, lo_idx = [], []
    if n < 2 * window + 1:
        return {'high_idx': [], 'high_px': [], 'low_idx': [], 'low_px': []}
    for i in range(window, n - window):
        seg_h = high[i - window:i + window + 1]
        seg_l = low[i - window:i + window + 1]
        if high[i] == seg_h.max() and high[i] > high[i - 1]:
            hi_idx.append(i)
        if low[i] == seg_l.min() and low[i] < low[i - 1]:
            lo_idx.append(i)
    return {
        'high_idx': hi_idx, 'high_px': [float(high[i]) for i in hi_idx],
        'low_idx': lo_idx,  'low_px': [float(low[i]) for i in lo_idx],
    }


# ── Hỗ trợ / Kháng cự (gom cụm mức giá swing) ───────────────────────────────
def support_resistance(df: pd.DataFrame, window: int = 5,
                       max_levels: int = 6, tol: float = 0.015,
                       lookback: int = 260) -> dict:
    """Gom các đỉnh/đáy gần nhau (trong ±tol) thành VÙNG S/R, xếp theo độ mạnh.

    Chỉ xét `lookback` phiên gần nhất (mặc định ~1 năm) để mức S/R còn ý nghĩa
    với giá hiện tại — tránh các mức quá cũ từ nhiều năm trước.
    Độ mạnh = số lần giá chạm vùng (số swing trong cụm). Phân loại theo giá
    hiện tại: mức ≥ giá hiện tại → kháng cự, < giá hiện tại → hỗ trợ.

    Trả {'resistance': [(price, strength)...], 'support': [...], 'last': giá}.
    """
    if lookback and len(df) > lookback:
        df = df.tail(lookback)
    sp = swing_points(df, window)
    pts = sorted(sp['high_px'] + sp['low_px'])
    if not pts:
        return {'resistance': [], 'support': [], 'last': float(df['Close'].iloc[-1]) if len(df) else 0.0}

    # Gom cụm tham lam: mức kề nhau trong ±tol (theo %) → 1 vùng.
    clusters = []
    cur = [pts[0]]
    for p in pts[1:]:
        if abs(p - cur[-1]) / max(cur[-1], 1e-9) <= tol:
            cur.append(p)
        else:
            clusters.append(cur); cur = [p]
    clusters.append(cur)

    levels = [(float(np.mean(c)), len(c)) for c in clusters]
    last = float(df['Close'].iloc[-1])
    res = sorted([lv for lv in levels if lv[0] >= last], key=lambda x: x[0])
    sup = sorted([lv for lv in levels if lv[0] < last], key=lambda x: -x[0])
    # Giữ vùng MẠNH nhất, ưu tiên gần giá hiện tại
    res = sorted(res, key=lambda x: (-x[1], x[0]))[:max_levels]
    sup = sorted(sup, key=lambda x: (-x[1], -x[0]))[:max_levels]
    return {'resistance': res, 'support': sup, 'last': last}


# ── Fibonacci thoái lui (retracement) ───────────────────────────────────────
_FIB = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def fibonacci_levels(df: pd.DataFrame, lookback: int = 120) -> dict:
    """Mức Fibonacci từ sóng lớn nhất trong `lookback` phiên gần nhất.

    Xác định swing-high & swing-low của đoạn; nếu đỉnh xuất hiện SAU đáy →
    xu hướng tăng (đo thoái lui xuống), ngược lại xu hướng giảm.

    Trả {'levels': [(ratio, price)...], 'hi', 'lo', 'uptrend', 'lookback'}.
    """
    seg = df.tail(lookback)
    if len(seg) < 10:
        return {'levels': [], 'hi': np.nan, 'lo': np.nan, 'uptrend': True, 'lookback': len(seg)}
    h = seg['High'].values.astype(float)
    l = seg['Low'].values.astype(float)
    i_hi = int(np.argmax(h)); i_lo = int(np.argmin(l))
    hi, lo = float(h[i_hi]), float(l[i_lo])
    if hi <= lo:
        return {'levels': [], 'hi': hi, 'lo': lo, 'uptrend': True, 'lookback': len(seg)}
    uptrend = i_hi > i_lo                      # đỉnh sau đáy → đang trong nhịp tăng
    rng = hi - lo
    if uptrend:                                # thoái lui TỪ đỉnh xuống
        levels = [(r, hi - r * rng) for r in _FIB]
    else:                                      # hồi phục TỪ đáy lên
        levels = [(r, lo + r * rng) for r in _FIB]
    return {'levels': levels, 'hi': hi, 'lo': lo, 'uptrend': uptrend, 'lookback': len(seg)}


# ── Pivot Points (điểm xoay sàn giao dịch — công thức cổ điển) ──────────────
def pivot_points(df: pd.DataFrame) -> dict:
    """Pivot cổ điển từ H/L/C phiên gần nhất: PP, R1-3, S1-3."""
    if len(df) < 1:
        return {}
    last = df.iloc[-1]
    H, L, C = float(last['High']), float(last['Low']), float(last['Close'])
    PP = (H + L + C) / 3.0
    R1 = 2 * PP - L; S1 = 2 * PP - H
    R2 = PP + (H - L); S2 = PP - (H - L)
    R3 = H + 2 * (PP - L); S3 = L - 2 * (H - PP)
    return {'PP': PP, 'R1': R1, 'R2': R2, 'R3': R3, 'S1': S1, 'S2': S2, 'S3': S3}


# ── Kênh xu hướng hồi quy tuyến tính ────────────────────────────────────────
def trend_channel(df: pd.DataFrame, lookback: int = 90) -> dict:
    """Hồi quy tuyến tính giá đóng cửa trong `lookback` phiên → đường giữa +
    biên trên/dưới = đường giữa ± k·độ lệch chuẩn phần dư (k chọn để bao ~95%).

    Trả {'idx', 'mid', 'upper', 'lower', 'slope_pct', 'lookback'} với idx là
    vị trí hàng tuyệt đối trong df (để vẽ đúng trục thời gian).
    """
    seg = df.tail(lookback)
    n = len(seg)
    if n < 10:
        return {'idx': [], 'mid': [], 'upper': [], 'lower': [], 'slope_pct': 0.0, 'lookback': n}
    y = seg['Close'].values.astype(float)
    x = np.arange(n, dtype=float)
    a, b = np.polyfit(x, y, 1)                 # y ≈ a·x + b
    mid = a * x + b
    resid = y - mid
    k = 2.0
    band = k * float(np.std(resid))
    start = len(df) - n
    idx = list(range(start, len(df)))
    slope_pct = (a / (float(np.mean(y)) or 1e-9)) * 100.0   # %/phiên
    return {'idx': idx, 'mid': mid, 'upper': mid + band, 'lower': mid - band,
            'slope_pct': float(slope_pct), 'lookback': n}


# ── ZigZag (nối các điểm đảo chiều ≥ pct) — nền tảng đếm sóng ────────────────
def zigzag(df: pd.DataFrame, pct: float = 0.05) -> dict:
    """Đường ZigZag: chỉ giữ các đảo chiều có biên độ ≥ `pct` (mặc định 5%).

    Lọc nhiễu nhỏ → còn lại "bộ xương" sóng giá (cơ sở đánh số sóng Elliott
    thủ công). Trả {'idx', 'px', 'dirs'} — idx vị trí hàng, px giá, dirs ±1.
    """
    if len(df) < 3:
        return {'idx': [], 'px': [], 'dirs': []}
    close = df['Close'].values.astype(float)
    idx = [0]; px = [close[0]]; dirs = []
    last_ext = close[0]; trend = 0                    # 0 chưa rõ, 1 lên, -1 xuống
    for i in range(1, len(close)):
        chg = (close[i] - last_ext) / max(abs(last_ext), 1e-9)
        if trend >= 0 and chg <= -pct:                # đảo chiều xuống
            dirs.append(1); idx.append(i); px.append(close[i]); last_ext = close[i]; trend = -1
        elif trend <= 0 and chg >= pct:               # đảo chiều lên
            dirs.append(-1); idx.append(i); px.append(close[i]); last_ext = close[i]; trend = 1
        else:                                         # cùng chiều → cập nhật cực trị
            if trend >= 0 and close[i] > last_ext:
                last_ext = close[i]; idx[-1] = i; px[-1] = close[i]
            elif trend <= 0 and close[i] < last_ext:
                last_ext = close[i]; idx[-1] = i; px[-1] = close[i]
    return {'idx': idx, 'px': px, 'dirs': dirs}


# ── Tóm tắt vị thế kỹ thuật cho thẻ/bảng ────────────────────────────────────
def technical_summary(df: pd.DataFrame) -> dict:
    """Gộp các chỉ số vị thế cho bảng tóm tắt: hỗ trợ/kháng cự gần nhất,
    vị trí Fibonacci, hệ số dốc kênh, biên độ kênh hiện tại."""
    last = float(df['Close'].iloc[-1]) if len(df) else 0.0
    sr = support_resistance(df)
    fib = fibonacci_levels(df)
    ch = trend_channel(df)
    near_res = sr['resistance'][0][0] if sr['resistance'] else np.nan
    near_sup = sr['support'][0][0] if sr['support'] else np.nan
    # Vùng Fib bao quanh giá hiện tại
    fib_zone = ''
    if fib['levels']:
        lv = sorted(fib['levels'], key=lambda x: x[1])
        for j in range(len(lv) - 1):
            if lv[j][1] <= last <= lv[j + 1][1]:
                fib_zone = f"{lv[j][0]*100:.1f}%–{lv[j+1][0]*100:.1f}%"
                break
    ch_pos = ''
    if len(ch['mid']):
        m = ch['mid'][-1]; up = ch['upper'][-1]; lo = ch['lower'][-1]
        if up > lo:
            r = (last - lo) / (up - lo)
            ch_pos = ('Biên trên' if r > 0.8 else 'Biên dưới' if r < 0.2 else 'Giữa kênh')
    return {
        'last': last, 'near_res': near_res, 'near_sup': near_sup,
        'fib_zone': fib_zone, 'fib_uptrend': fib.get('uptrend', True),
        'slope_pct': ch.get('slope_pct', 0.0), 'channel_pos': ch_pos,
        'n_res': len(sr['resistance']), 'n_sup': len(sr['support']),
    }

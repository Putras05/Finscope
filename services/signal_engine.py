"""Signal Engine — tổng hợp 8 trụ cột tín hiệu thành conviction score [-100, +100].

Mục tiêu: thay vì user mở/đóng vị thế "lung tung" trên Paper Trading, engine
này cung cấp ĐIỂM TIN CẬY có giải trình (reason chain) — giống cách quỹ
discretionary chấm điểm 1 mã trước khi giao dịch.

Tám trụ cột (mỗi trụ trả `(score [-2..+2], lý do, mã tag)`):

  1. Trend regime    — MA20 vs MA50 vs Close; slope kênh hồi quy.
  2. Ichimoku        — 4 tầng Hosoda (Kumo, TK cross, Chikou, mây tương lai).
  3. Momentum        — RSI(14) zones + RSI slope + Stoch(%K) + MACD-lite.
  4. Volume          — Volume / MA5_Vol + OBV slope.
  5. Volatility      — ATR%(Close) regime (thấp = tốt cho entry, cao = chờ).
  6. Support/Resist  — proximity tới S/R gần nhất + zone bounce/reject.
  7. Pattern         — mẫu hình nến mới nhất trong 5 phiên.
  8. Fundamentals    — P/E + ROE so peer (qua data.fundamental.peer_kpis).

Tổng điểm thô = Σ(score × weight) chuẩn hoá về thang [-100, +100]. Weight
mặc định cân bằng technical-fundamental theo trường phái "evidence-based
trading" (xem D. Aronson, 2007). Hỗ trợ truyền weights tuỳ chỉnh.

Đầu ra `build_signal_report` là dict thuần (JSON-serializable) để dễ test,
dễ log, dễ render UI. KHÔNG phụ thuộc streamlit.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional

from data import technicals as TA
from data.ichimoku import (
    add_ichimoku, classify_primary_trend, detect_tk_cross,
    classify_trading_signal, classify_chikou_confirmation,
    classify_future_kumo,
)


# Hash fingerprint hợp nhất ở core/cache.py (v55) — single source of truth.
from core.cache import df_fingerprint as _df_fingerprint


# ─────────────────────────────────────────────────────────────────────
#  WEIGHT MẶC ĐỊNH
# ─────────────────────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    'trend':    1.5,
    'ichimoku': 1.4,
    'momentum': 1.2,
    'volume':   0.8,
    'volatility': 0.6,
    'sr':       1.0,
    'pattern':  0.7,
    'fund':     0.8,
}

# Mức điểm tối đa cho 1 trụ (cùng thang để dễ visualize) — đầu ra mỗi trụ
# nằm trong [-MAX_PILLAR_SCORE, +MAX_PILLAR_SCORE].
MAX_PILLAR_SCORE = 2.0


# ─────────────────────────────────────────────────────────────────────
#  Helper: chuẩn hoá điểm về [-100, +100]
# ─────────────────────────────────────────────────────────────────────
def _normalize(weighted_sum: float, total_weight: float) -> float:
    if total_weight <= 0:
        return 0.0
    raw = weighted_sum / (total_weight * MAX_PILLAR_SCORE)
    return float(max(-100.0, min(100.0, raw * 100.0)))


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 1 — TREND REGIME (MA + slope kênh)
# ─────────────────────────────────────────────────────────────────────
def _pillar_trend(df: pd.DataFrame) -> dict:
    if len(df) < 50:
        return {'score': 0.0, 'reason': 'Chưa đủ 50 phiên để xác định xu hướng.',
                'tag': 'na', 'details': {}}
    close = float(df['Close'].iloc[-1])
    ma20  = float(df['MA20'].iloc[-1])
    ma50  = float(df['MA50'].iloc[-1])
    score = 0.0
    bits  = []

    # Quan hệ giá vs MA20 vs MA50
    if close > ma20 > ma50:
        score += 1.0
        bits.append('Close > MA20 > MA50 (uptrend xếp lớp)')
    elif close < ma20 < ma50:
        score -= 1.0
        bits.append('Close < MA20 < MA50 (downtrend xếp lớp)')
    elif close > ma50 and close > ma20:
        score += 0.5; bits.append('Trên cả MA20 & MA50')
    elif close < ma50 and close < ma20:
        score -= 0.5; bits.append('Dưới cả MA20 & MA50')

    # Slope kênh hồi quy 90 phiên
    ch = TA.trend_channel(df, lookback=90)
    slope = ch.get('slope_pct', 0.0)
    if slope > 0.15:
        score += 1.0; bits.append(f'Kênh dốc lên +{slope:.2f}%/phiên')
    elif slope > 0.05:
        score += 0.5; bits.append(f'Kênh dốc nhẹ +{slope:.2f}%/phiên')
    elif slope < -0.15:
        score -= 1.0; bits.append(f'Kênh dốc xuống {slope:.2f}%/phiên')
    elif slope < -0.05:
        score -= 0.5; bits.append(f'Kênh dốc nhẹ {slope:.2f}%/phiên')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.5 else 'bear' if score < -0.5 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'Xu hướng không rõ ràng.',
            'tag': tag,
            'details': {'close': close, 'ma20': ma20, 'ma50': ma50,
                        'slope_pct': slope}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 2 — ICHIMOKU 4 TẦNG
# ─────────────────────────────────────────────────────────────────────
def _pillar_ichimoku(df: pd.DataFrame) -> dict:
    if len(df) < 80:
        return {'score': 0.0, 'reason': 'Chưa đủ 80 phiên cho Ichimoku.',
                'tag': 'na', 'details': {}}
    try:
        ichi = add_ichimoku(df)
    except Exception as e:
        return {'score': 0.0, 'reason': f'Ichimoku lỗi: {e}',
                'tag': 'na', 'details': {}}
    score = 0.0; bits = []
    last = ichi.iloc[-1]
    close = float(last['Close'])

    # Tầng 1 — vị trí so với Kumo
    p_code, p_msg = classify_primary_trend(
        close, float(last['Kumo_top']), float(last['Kumo_bot']))
    if p_code == 'bull': score += 1.0; bits.append('Giá trên mây')
    elif p_code == 'bear': score -= 1.0; bits.append('Giá dưới mây')
    elif p_code == 'neut': bits.append('Trong mây — tích lũy')

    # Tầng 2 — TK cross trong 5 phiên + xác nhận
    tk_code, tk_msg, _off = detect_tk_cross(ichi['Tenkan'], ichi['Kijun'], lookback=5)
    sig_code, sig_msg = classify_trading_signal(tk_code, p_code)
    if sig_code in ('strong_buy',):    score += 1.0; bits.append('TK cross mua mạnh')
    elif sig_code in ('weak_buy',):    score += 0.4; bits.append('TK cross mua yếu')
    elif sig_code in ('counter_buy',): score += 0.0; bits.append('Cross ngược xu hướng → bỏ qua')
    elif sig_code in ('strong_sell',): score -= 1.0; bits.append('TK cross bán mạnh')
    elif sig_code in ('weak_sell',):   score -= 0.4; bits.append('TK cross bán yếu')

    # Tầng 4 — mây TƯƠNG LAI tại t+26.
    # CRITICAL: dùng Senkou_*_raw (chưa shift); Senkou_A/Senkou_B đã shift
    # +26 nên .iloc[-1] = giá trị t-26 (mây quá khứ, KHÔNG phải tương lai).
    # Hosoda: Senkou_A_future[t+26] = (Tenkan[t] + Kijun[t]) / 2 = sen_a_raw[t].
    sa_raw = last.get('Senkou_A_raw', last['Senkou_A'])
    sb_raw = last.get('Senkou_B_raw', last['Senkou_B'])
    fk_code, _ = classify_future_kumo(
        float(sa_raw) if pd.notna(sa_raw) else np.nan,
        float(sb_raw) if pd.notna(sb_raw) else np.nan)
    if fk_code == 'bull_kumo': score += 0.4; bits.append('Mây tương lai xanh')
    elif fk_code == 'bear_kumo': score -= 0.4; bits.append('Mây tương lai đỏ')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.5 else 'bear' if score < -0.5 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'Ichimoku trung tính.',
            'tag': tag,
            'details': {'primary': p_code, 'tk_cross': tk_code,
                        'signal': sig_code, 'future_kumo': fk_code}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 3 — MOMENTUM (RSI + Stoch + MACD-lite)
# ─────────────────────────────────────────────────────────────────────
def _pillar_momentum(df: pd.DataFrame) -> dict:
    if len(df) < 30:
        return {'score': 0.0, 'reason': 'Chưa đủ 30 phiên cho RSI/Stoch.',
                'tag': 'na', 'details': {}}
    rsi = float(df['RSI14'].iloc[-1])
    rsi_prev = float(df['RSI14'].iloc[-5]) if len(df) > 5 else rsi
    score = 0.0; bits = []

    # RSI zones — KHÔNG đảo chiều ngay khi <30 (đó là phim đoán đáy);
    # trọng số nhẹ vùng cực đoan, mạnh hơn khi thoát vùng + dốc lên.
    if 50 < rsi < 70:
        score += 0.6; bits.append(f'RSI={rsi:.1f} (đà tăng vùng tích cực)')
    elif rsi >= 70:
        score -= 0.3; bits.append(f'RSI={rsi:.1f} (quá mua, có thể điều chỉnh)')
    elif 30 < rsi <= 50:
        score -= 0.4; bits.append(f'RSI={rsi:.1f} (đà yếu)')
    else:
        score -= 0.8; bits.append(f'RSI={rsi:.1f} (quá bán, rủi ro dao kéo)')

    # RSI slope 5 phiên — xác nhận momentum
    rsi_chg = rsi - rsi_prev
    if rsi_chg > 5:    score += 0.4; bits.append(f'RSI dốc lên (+{rsi_chg:.1f})')
    elif rsi_chg < -5: score -= 0.4; bits.append(f'RSI dốc xuống ({rsi_chg:.1f})')

    # Stochastic
    try:
        st_ = TA.stochastic(df)
        k = float(st_['k'][-1]); d = float(st_['d'][-1])
        if k > d and k < 80: score += 0.4; bits.append(f'%K({k:.0f}) > %D({d:.0f})')
        elif k < d and k > 20: score -= 0.4; bits.append(f'%K({k:.0f}) < %D({d:.0f})')
    except Exception:
        pass

    # MACD-lite từ MA5/MA20 (đơn giản, nhanh, không cần thêm cột)
    if len(df) >= 35:
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        sig = macd.ewm(span=9, adjust=False).mean()
        m_last = float(macd.iloc[-1]); s_last = float(sig.iloc[-1])
        m_prev = float(macd.iloc[-2]); s_prev = float(sig.iloc[-2])
        if m_prev <= s_prev and m_last > s_last:
            score += 0.6; bits.append('MACD bull cross')
        elif m_prev >= s_prev and m_last < s_last:
            score -= 0.6; bits.append('MACD bear cross')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.5 else 'bear' if score < -0.5 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'Momentum trung tính.',
            'tag': tag, 'details': {'rsi': rsi, 'rsi_chg5': rsi_chg}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 4 — VOLUME (vol vs MA5_Vol + OBV slope)
# ─────────────────────────────────────────────────────────────────────
def _pillar_volume(df: pd.DataFrame) -> dict:
    if len(df) < 20:
        return {'score': 0.0, 'reason': 'Chưa đủ 20 phiên.', 'tag': 'na', 'details': {}}
    v_ratio = float(df['Volume_ratio'].iloc[-1])
    ret_last = float(df['Return'].iloc[-1])
    score = 0.0; bits = []

    # Volume xác nhận chiều giá
    if v_ratio >= 1.5 and ret_last > 0:
        score += 1.0; bits.append(f'Vol {v_ratio:.1f}× MA5 + giá tăng (cầu thực)')
    elif v_ratio >= 1.5 and ret_last < 0:
        score -= 0.8; bits.append(f'Vol {v_ratio:.1f}× MA5 + giá giảm (bán mạnh)')
    elif v_ratio < 0.6:
        bits.append(f'Vol thấp ({v_ratio:.1f}× MA5) — kém xác nhận')

    # OBV slope 10 phiên — Granville 1963: GIÁ TRỊ chính của OBV là khả năng
    # phát hiện DIVERGENCE (OBV vs giá ngược chiều). AND-gate với ret_last
    # trước đây loại bỏ phân kỳ → hỏng mục đích.
    try:
        ob = TA.obv(df)
        if len(ob) >= 10:
            slope = ob[-1] - ob[-10]
            price_chg_10 = float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-10])
            if slope > 0 and price_chg_10 > 0:
                score += 0.4; bits.append('OBV + giá cùng tăng (tích lũy thực)')
            elif slope < 0 and price_chg_10 < 0:
                score -= 0.4; bits.append('OBV + giá cùng giảm (phân phối thực)')
            elif slope > 0 and price_chg_10 < 0:
                # PHÂN KỲ TÍCH CỰC — giá giảm nhưng OBV tăng → smart money buy
                score += 0.6; bits.append('Phân kỳ OBV↑ giá↓ (smart money tích lũy)')
            elif slope < 0 and price_chg_10 > 0:
                # PHÂN KỲ TIÊU CỰC — giá tăng nhưng OBV giảm → cảnh báo
                score -= 0.6; bits.append('Phân kỳ OBV↓ giá↑ (cảnh báo phân phối)')
    except Exception:
        pass

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.4 else 'bear' if score < -0.4 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'Khối lượng bình thường.',
            'tag': tag, 'details': {'volume_ratio': v_ratio}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 5 — VOLATILITY (ATR%) — KHÔNG có chiều, chỉ regime
# ─────────────────────────────────────────────────────────────────────
def _pillar_volatility(df: pd.DataFrame) -> dict:
    from services.risk import atr_series
    if len(df) < 30:
        return {'score': 0.0, 'reason': 'Chưa đủ 30 phiên.', 'tag': 'na', 'details': {}}
    atr = atr_series(df, 14)
    close = float(df['Close'].iloc[-1])
    if not len(atr) or close <= 0:
        return {'score': 0.0, 'reason': 'Không tính được ATR.', 'tag': 'na', 'details': {}}
    atr_last = float(atr[-1]) if atr[-1] == atr[-1] else 0.0
    atr_pct = atr_last / close * 100.0

    # Lý lẽ: ATR% rất thấp (≤1.2%) → entry an toàn, R nhỏ. ATR% cao (≥4%)
    # → risk per share lớn, khó set stop hợp lý — giảm conviction.
    score = 0.0; bits = []
    if atr_pct <= 1.2:
        score += 0.6; bits.append(f'ATR%={atr_pct:.2f}% (biến động thấp, entry an toàn)')
    elif atr_pct <= 2.5:
        score += 0.2; bits.append(f'ATR%={atr_pct:.2f}% (vol bình thường)')
    elif atr_pct <= 4.0:
        score -= 0.4; bits.append(f'ATR%={atr_pct:.2f}% (vol cao — cẩn trọng size)')
    else:
        score -= 1.0; bits.append(f'ATR%={atr_pct:.2f}% (vol rất cao — đứng ngoài)')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'calm' if score > 0 else 'wild' if score < -0.4 else 'neut'
    return {'score': float(score), 'reason': '; '.join(bits),
            'tag': tag, 'details': {'atr_pct': atr_pct, 'atr': atr_last}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 6 — SUPPORT / RESISTANCE proximity
# ─────────────────────────────────────────────────────────────────────
def _pillar_sr(df: pd.DataFrame) -> dict:
    sr = TA.support_resistance(df)
    score = 0.0; bits = []
    if not sr['resistance'] and not sr['support']:
        return {'score': 0.0, 'reason': 'Không xác định được vùng S/R.',
                'tag': 'na', 'details': {}}
    last = float(sr['last'])
    near_res = sr['resistance'][0][0] if sr['resistance'] else None
    near_sup = sr['support'][0][0] if sr['support'] else None
    res_pct = ((near_res - last) / last * 100.0) if near_res else None
    sup_pct = ((last - near_sup) / last * 100.0) if near_sup else None

    # Quy tắc: gần hỗ trợ trong 1.5% → bullish bias (bounce); gần kháng cự
    # ≤1.5% → bearish bias (reject). Cách xa cả 2 → neutral.
    if sup_pct is not None and sup_pct < 1.5 and (res_pct is None or res_pct > 3):
        score += 1.0; bits.append(f'Sát hỗ trợ ({sup_pct:.1f}%) — kỳ vọng bật')
    elif res_pct is not None and res_pct < 1.5 and (sup_pct is None or sup_pct > 3):
        score -= 1.0; bits.append(f'Sát kháng cự ({res_pct:.1f}%) — rủi ro bị reject')
    elif sup_pct is not None and sup_pct > 5 and res_pct is not None and res_pct > 5:
        bits.append('Cách xa cả S/R — chưa có lực kéo rõ')
    elif sup_pct is not None and res_pct is not None:
        # Trong vùng giữa: ưu tiên hướng có nhiều room hơn
        if res_pct > sup_pct * 1.6:
            score += 0.4; bits.append(f'Còn room lên ({res_pct:.1f}% vs {sup_pct:.1f}%)')
        elif sup_pct > res_pct * 1.6:
            score -= 0.4; bits.append(f'Ít room lên ({res_pct:.1f}% vs {sup_pct:.1f}%)')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.4 else 'bear' if score < -0.4 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'S/R không gần.',
            'tag': tag,
            'details': {'last': last, 'near_res': near_res, 'near_sup': near_sup,
                        'res_pct': res_pct, 'sup_pct': sup_pct}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 7 — CANDLESTICK PATTERN (lookback 5 phiên)
# ─────────────────────────────────────────────────────────────────────
def _pillar_pattern(df: pd.DataFrame) -> dict:
    pats = TA.candlestick_patterns(df, lookback=5)
    if not pats:
        return {'score': 0.0, 'reason': 'Không có mẫu hình rõ ràng trong 5 phiên.',
                'tag': 'neut', 'details': {}}
    latest = pats[-1]
    d = int(latest.get('dir', 0))
    score = 0.0; bits = []
    if d > 0:
        score += 0.9; bits.append(f"Mẫu {latest['name']} (đảo chiều tăng)")
    elif d < 0:
        score -= 0.9; bits.append(f"Mẫu {latest['name']} (đảo chiều giảm)")
    else:
        bits.append(f"Mẫu {latest['name']} (lưỡng lự)")
    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0 else 'bear' if score < 0 else 'neut'
    return {'score': float(score), 'reason': '; '.join(bits),
            'tag': tag, 'details': {'pattern': latest['name'], 'dir': d}}


# ─────────────────────────────────────────────────────────────────────
#  TRỤ 8 — FUNDAMENTALS so peer (P/E, ROE)
# ─────────────────────────────────────────────────────────────────────
def _pillar_fundamentals(ticker: str) -> dict:
    try:
        from data.fundamental import peer_kpis
        peers = peer_kpis(ticker, max_peers=6)
    except Exception as e:
        return {'score': 0.0, 'reason': f'Không lấy được dữ liệu CB peer ({e}).',
                'tag': 'na', 'details': {}}
    if not peers or 'self' not in peers:
        return {'score': 0.0, 'reason': 'Thiếu dữ liệu cơ bản.', 'tag': 'na', 'details': {}}
    me = peers.get('self') or {}
    others = peers.get('peers') or []
    if not others:
        return {'score': 0.0, 'reason': 'Không có peer để so sánh.',
                'tag': 'na', 'details': me}

    pe = me.get('pe')
    roe = me.get('roe')
    score = 0.0; bits = []

    # P/E vs trung vị peer
    pe_peers = [p.get('pe') for p in others if isinstance(p.get('pe'), (int, float))]
    if pe is not None and pe_peers:
        med_pe = float(np.median(pe_peers))
        if pe > 0 and med_pe > 0:
            if pe < med_pe * 0.85:
                score += 0.6; bits.append(f'P/E={pe:.1f} thấp hơn trung vị ngành ({med_pe:.1f})')
            elif pe > med_pe * 1.25:
                score -= 0.4; bits.append(f'P/E={pe:.1f} cao hơn trung vị ngành ({med_pe:.1f})')

    # ROE vs trung vị peer
    roe_peers = [p.get('roe') for p in others if isinstance(p.get('roe'), (int, float))]
    if roe is not None and roe_peers:
        med_roe = float(np.median(roe_peers))
        if roe > med_roe * 1.15:
            score += 0.6; bits.append(f'ROE={roe:.1f}% vượt trung vị ngành ({med_roe:.1f}%)')
        elif roe < med_roe * 0.85:
            score -= 0.4; bits.append(f'ROE={roe:.1f}% kém trung vị ngành ({med_roe:.1f}%)')

    score = max(-MAX_PILLAR_SCORE, min(MAX_PILLAR_SCORE, score))
    tag = 'bull' if score > 0.4 else 'bear' if score < -0.4 else 'neut'
    return {'score': float(score),
            'reason': '; '.join(bits) if bits else 'Cơ bản tương đương ngành.',
            'tag': tag, 'details': {'pe': pe, 'roe': roe}}


# ─────────────────────────────────────────────────────────────────────
#  ENGINE CHÍNH
# ─────────────────────────────────────────────────────────────────────
def _build_signal_report_impl(df: pd.DataFrame, ticker: str,
                                weights: Optional[dict] = None,
                                include_fundamentals: bool = True) -> dict:
    """Implementation thuần — KHÔNG cache. Dùng cho backtest walk-forward
    (mỗi slice df[:t+1] khác nhau, cache key luôn miss + lưu rác evict
    cache live). Cũng là core cho `build_signal_report` cached.

    Trả dict:
      {
        'ticker', 'conviction' (-100..+100), 'bias' ('BUY'|'SELL'|'HOLD'),
        'pillars': {name: {score, reason, tag, weight, contribution}},
        'reasons_positive': [...],
        'reasons_negative': [...],
        'last_price', 'atr', 'atr_pct',
      }
    """
    w = dict(DEFAULT_WEIGHTS, **(weights or {}))
    if not include_fundamentals:
        w['fund'] = 0.0

    pillars = {
        'trend':      _pillar_trend(df),
        'ichimoku':   _pillar_ichimoku(df),
        'momentum':   _pillar_momentum(df),
        'volume':     _pillar_volume(df),
        'volatility': _pillar_volatility(df),
        'sr':         _pillar_sr(df),
        'pattern':    _pillar_pattern(df),
        'fund':       _pillar_fundamentals(ticker) if w['fund'] > 0
                       else {'score': 0.0, 'reason': '(đã tắt)', 'tag': 'na', 'details': {}},
    }

    weighted_sum = 0.0
    total_weight = 0.0
    for k, p in pillars.items():
        wk = float(w.get(k, 0.0))
        # bỏ qua trụ NA khỏi mẫu số → conviction không bị "loãng" khi thiếu dữ liệu
        if p['tag'] == 'na':
            p['weight'] = wk
            p['contribution'] = 0.0
            continue
        weighted_sum += p['score'] * wk
        total_weight += wk
        p['weight'] = wk
        p['contribution'] = float(p['score'] * wk)

    conviction = _normalize(weighted_sum, total_weight)

    # ATR cho trade planner
    from services.risk import last_atr
    atr_val = last_atr(df, 14)
    last_close = float(df['Close'].iloc[-1]) if len(df) else 0.0
    atr_pct = (atr_val / last_close * 100.0) if last_close > 0 else 0.0

    if conviction >= 35:
        bias = 'BUY'
    elif conviction <= -35:
        bias = 'SELL'
    else:
        bias = 'HOLD'

    # Tách reasons để render UI gọn
    pos, neg = [], []
    for name, p in pillars.items():
        if p['score'] > 0.3 and p['reason']:
            pos.append(p['reason'])
        elif p['score'] < -0.3 and p['reason']:
            neg.append(p['reason'])

    return {
        'ticker': ticker,
        'conviction': float(conviction),
        'bias': bias,
        'pillars': pillars,
        'reasons_positive': pos,
        'reasons_negative': neg,
        'last_price': last_close,
        'atr': atr_val,
        'atr_pct': atr_pct,
    }


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: _df_fingerprint})
def build_signal_report(df: pd.DataFrame, ticker: str,
                        weights: Optional[dict] = None,
                        include_fundamentals: bool = True) -> dict:
    """Wrapper cache TTL 15 phút quanh `_build_signal_report_impl`.

    Cache key = (ticker, df fingerprint, weights, include_fundamentals).
    Dùng cho UI (Pro Suggest tab, single ticker repeat calls). Backtest
    walk-forward NÊN gọi `_build_signal_report_impl` trực tiếp để tránh
    pollute cache với hàng trăm slice khác nhau.
    """
    return _build_signal_report_impl(df, ticker, weights, include_fundamentals)

"""
Trang "Tín hiệu & Cảnh báo" — alerts dashboard đa chỉ báo + Ichimoku chi tiết.

Cấu trúc:
  PHẦN 1 — Cảnh báo đang kích hoạt (Active Alerts):
    RSI · MACD cross · Bollinger break · Stochastic · MA5/20 cross · Volume spike
    · PSAR flip · ADX trend · Mẫu hình nến · Ichimoku consensus · Tâm lý tin tức
  PHẦN 2 — Phân tích Ichimoku chi tiết (4 tầng + chart + 3 đặc trưng dẫn xuất).

Ichimoku theo Hosoda (1969) — xem data/ichimoku.py cho công thức + anti-leak.
"""
import streamlit as st
import numpy as np
import pandas as pd

from core.i18n import t
from charts.base import _PLOTLY_CONFIG
from data.ichimoku import (
    add_ichimoku, classify_primary_trend, detect_tk_cross,
    classify_trading_signal, classify_chikou_confirmation,
    classify_future_kumo, aggregate_signals,
    _donchian_mid, SENKOU_N, DISPLACE,
)
from charts.ichimoku import chart_ichimoku_plotly
from data import technicals as TA
from data.news import news_sentiment
from app_pages.strategy import _compute_indicators
from charts.technicals import chart_technical


# ── Bảng phân loại màu/icon — exact set lookup, không dùng substring ────────
_BULL_CODES    = {'bull', 'strong_buy', 'weak_buy', 'bull_conf', 'bull_kumo',
                  'strong_bull', 'mild_bull'}
_BEAR_CODES    = {'bear', 'strong_sell', 'weak_sell', 'bear_conf', 'bear_kumo',
                  'strong_bear', 'mild_bear'}
_COUNTER_CODES = {'counter_buy', 'counter_sell'}


def _sig_color(code: str, is_dark: bool) -> str:
    if code in _COUNTER_CODES: return '#FBBF24' if is_dark else '#B45309'
    if code in _BULL_CODES:    return '#34D399' if is_dark else '#15803D'
    if code in _BEAR_CODES:    return '#F87171' if is_dark else '#C62828'
    return '#94A3B8' if is_dark else '#475569'


def _sig_bg(code: str, is_dark: bool) -> str:
    if code in _COUNTER_CODES: return 'rgba(251,191,36,0.12)' if is_dark else 'rgba(180,83,9,0.07)'
    if code in _BULL_CODES:    return 'rgba(52,211,153,0.10)'  if is_dark else 'rgba(21,128,61,0.07)'
    if code in _BEAR_CODES:    return 'rgba(248,113,113,0.12)' if is_dark else 'rgba(198,40,40,0.07)'
    return 'rgba(148,163,184,0.08)'


def _sig_icon(code: str) -> str:
    """Trả về SVG icon tự build (bolt cho counter, up-arrow cho bull, down-arrow cho bear)."""
    if code in _COUNTER_CODES:
        # SVG tia sét (bolt) — tự vẽ từ 2 polygon, không dùng emoji
        return (
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" '
            'stroke="currentColor" stroke-width="0.5" stroke-linejoin="round" '
            'style="display:inline-block;vertical-align:-2px">'
            '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'
            '</svg>'
        )
    if code in _BULL_CODES:
        return (
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" '
            'stroke="currentColor" stroke-width="1" stroke-linejoin="round" '
            'style="display:inline-block;vertical-align:-1px">'
            '<path d="M12 4 22 18H2z"/>'
            '</svg>'
        )
    if code in _BEAR_CODES:
        return (
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" '
            'stroke="currentColor" stroke-width="1" stroke-linejoin="round" '
            'style="display:inline-block;vertical-align:-1px">'
            '<path d="M12 20 2 6h20z"/>'
            '</svg>'
        )
    # Neutral — em-dash char (không phải emoji)
    return ('<span style="display:inline-block;font-weight:700;'
            'font-family:monospace">—</span>')


def _build_alerts(df, df_ichi, ns, ichi_score, ichi_overall_code, is_en=False) -> list:
    """Quét toàn bộ chỉ báo + tin tức → trả list các cảnh báo ĐANG triggered.

    Mỗi alert: {'cat', 'name', 'level' (info/warn/danger/success), 'msg', 'val'}.
    """
    out = []
    d = _compute_indicators(df)
    if len(d) < 2:
        return out
    last = d.iloc[-1]
    prev = d.iloc[-2]

    def _add(cat, name, level, msg, val=''):
        out.append({'cat': cat, 'name': name, 'level': level, 'msg': msg, 'val': str(val)})

    # ── RSI extremes ─────────────────────────────────────────────────────
    rsi = last.get('RSI14', np.nan)
    if rsi == rsi:
        if rsi > 70:
            _add('momentum',
                 'RSI quá mua' if not is_en else 'RSI overbought',
                 'danger',
                 'RSI > 70 — rủi ro điều chỉnh giảm' if not is_en else 'RSI > 70 — pullback risk',
                 f'{rsi:.1f}')
        elif rsi < 30:
            _add('momentum',
                 'RSI quá bán' if not is_en else 'RSI oversold',
                 'success',
                 'RSI < 30 — khả năng bật lên' if not is_en else 'RSI < 30 — possible bounce',
                 f'{rsi:.1f}')

    # ── MACD signal cross (vừa giao cắt trong phiên này) ───────────────
    if last['MACD'] > last['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
        _add('momentum',
             'MACD giao cắt tăng (Golden)' if not is_en else 'MACD bullish cross (Golden)',
             'success',
             'MACD vừa cắt lên đường tín hiệu — đà tăng' if not is_en else 'MACD just crossed above signal — bullish momentum',
             f'{last["MACD"]:.4f}')
    elif last['MACD'] < last['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
        _add('momentum',
             'MACD giao cắt giảm (Death)' if not is_en else 'MACD bearish cross (Death)',
             'danger',
             'MACD vừa cắt xuống — đà giảm' if not is_en else 'MACD just crossed below — bearish momentum',
             f'{last["MACD"]:.4f}')

    # ── Bollinger band break ───────────────────────────────────────────
    if not np.isnan(last.get('BB_up', np.nan)):
        if last['Close'] > last['BB_up']:
            _add('volatility',
                 'Vượt dải Bollinger trên' if not is_en else 'Above upper Bollinger',
                 'warn',
                 'Giá vượt biên trên — quá mua hoặc breakout' if not is_en else 'Above upper band — overbought or breakout',
                 f'%B={last.get("BB_pctB",0):.2f}')
        elif last['Close'] < last['BB_lo']:
            _add('volatility',
                 'Thủng dải Bollinger dưới' if not is_en else 'Below lower Bollinger',
                 'warn',
                 'Giá thủng biên dưới — quá bán hoặc breakdown' if not is_en else 'Below lower band — oversold or breakdown',
                 f'%B={last.get("BB_pctB",0):.2f}')

    # ── Stochastic %K, %D extremes ─────────────────────────────────────
    stoch = TA.stochastic(df)
    if len(stoch['k']) > 1:
        k_last = stoch['k'][-1]; d_last = stoch['d'][-1]
        if k_last == k_last and d_last == d_last:
            if k_last > 80 and d_last > 80:
                _add('momentum',
                     'Stochastic quá mua' if not is_en else 'Stochastic overbought',
                     'danger',
                     '%K, %D > 80 — rủi ro đảo chiều' if not is_en else '%K, %D > 80 — reversal risk',
                     f'{k_last:.0f}/{d_last:.0f}')
            elif k_last < 20 and d_last < 20:
                _add('momentum',
                     'Stochastic quá bán' if not is_en else 'Stochastic oversold',
                     'success',
                     '%K, %D < 20 — khả năng đảo chiều tăng' if not is_en else '%K, %D < 20 — bullish reversal possible',
                     f'{k_last:.0f}/{d_last:.0f}')

    # ── MA5/MA20 cross (vừa cắt) ────────────────────────────────────────
    if (prev['MA5'] <= prev['MA20'] and last['MA5'] > last['MA20']):
        _add('trend',
             'MA5 cắt lên MA20' if not is_en else 'MA5 crosses above MA20',
             'success', 'Tín hiệu xu hướng ngắn hạn ĐẢO LÊN' if not is_en else 'Short-term trend FLIPS UP',
             '')
    elif (prev['MA5'] >= prev['MA20'] and last['MA5'] < last['MA20']):
        _add('trend',
             'MA5 cắt xuống MA20' if not is_en else 'MA5 crosses below MA20',
             'danger', 'Tín hiệu xu hướng ngắn hạn ĐẢO XUỐNG' if not is_en else 'Short-term trend FLIPS DOWN',
             '')

    # ── Volume spike ─────────────────────────────────────────────────────
    vr = float(last.get('Volume_ratio', 1) or 1)
    if vr > 2.0:
        _add('volume',
             'Khối lượng đột biến' if not is_en else 'Volume spike',
             'warn',
             f'Volume gấp {vr:.1f}× trung bình 5 phiên' if not is_en else f'Volume {vr:.1f}× the 5-bar average',
             f'×{vr:.1f}')

    # ── ADX trend strength (>25 = strong) ──────────────────────────────
    adx_arr = TA.adx(df)
    if len(adx_arr):
        a = adx_arr[-1]
        if a == a and a > 25:
            slope = float(df['Close'].iloc[-1] - df['Close'].iloc[-15]) if len(df) >= 15 else 0.0
            _add('trend',
                 ('Xu hướng MẠNH (ADX' + f' {a:.0f})') if not is_en else f'STRONG trend (ADX {a:.0f})',
                 'info',
                 ('Xu hướng tăng mạnh' if slope > 0 else 'Xu hướng giảm mạnh')
                 if not is_en else ('Strong uptrend' if slope > 0 else 'Strong downtrend'),
                 f'{a:.0f}')

    # ── Parabolic SAR flip (vừa đổi vị trí) ────────────────────────────
    psar = TA.parabolic_sar(df)
    if len(psar) >= 2 and psar[-1] == psar[-1] and psar[-2] == psar[-2]:
        was_above = psar[-2] > df['High'].iloc[-2]
        now_above = psar[-1] > df['High'].iloc[-1]
        if was_above and not now_above:
            _add('trend',
                 'Parabolic SAR đảo chiều TĂNG' if not is_en else 'Parabolic SAR flips UP',
                 'success', 'Chấm SAR chuyển xuống dưới giá — xu hướng tăng' if not is_en else 'SAR moved below price — uptrend',
                 '')
        elif not was_above and now_above:
            _add('trend',
                 'Parabolic SAR đảo chiều GIẢM' if not is_en else 'Parabolic SAR flips DOWN',
                 'danger', 'Chấm SAR chuyển lên trên giá — xu hướng giảm' if not is_en else 'SAR moved above price — downtrend',
                 '')

    # ── Mẫu hình nến (1-3 phiên gần nhất) ──────────────────────────────
    pats = TA.candlestick_patterns(df, lookback=3)
    if pats:
        p = pats[-1]
        if p['dir'] != 0:
            _nm = p['name_en'] if is_en else p['name']
            _add('pattern', _nm,
                 'success' if p['dir'] > 0 else 'danger',
                 (p['desc_en'] if is_en else p['desc']),
                 '')

    # ── Ichimoku consensus mạnh (|score| ≥ 3) ──────────────────────────
    if abs(ichi_score) >= 3:
        if is_en:
            _ichi_nm = ('Strong Ichimoku ' +
                        ('bullish' if ichi_score > 0 else 'bearish') + ' consensus')
            _ichi_msg = f'All 4 Ichimoku tiers agree ({ichi_score:+d}/5)'
        else:
            _ichi_nm = ('Ichimoku đồng thuận MẠNH ' +
                        ('tăng' if ichi_score > 0 else 'giảm'))
            _ichi_msg = (f'4 tầng Ichimoku đồng thuận '
                         f'{"tăng" if ichi_score>0 else "giảm"} ({ichi_score:+d}/5)')
        _add('cycle', _ichi_nm,
             'success' if ichi_score > 0 else 'danger',
             _ichi_msg, f'{ichi_score:+d}')

    # ── Tâm lý tin tức (PhoBERT + lexicon vote) ────────────────────────
    if ns.get('ok'):
        nv = ns.get('vote', 0)
        if nv != 0:
            src = 'PhoBERT AI' if ns.get('dl_used') else ('Từ điển' if not is_en else 'Lexicon')
            if is_en:
                _nws_nm = 'News sentiment ' + ('positive' if nv > 0 else 'negative')
                _nws_msg = (f'{src} consensus {("up" if nv>0 else "down")} '
                            f'across {ns.get("n", 0)} headlines')
            else:
                _nws_nm = 'Tâm lý tin tức ' + ('tích cực' if nv > 0 else 'tiêu cực')
                _nws_msg = (f'{src} đồng thuận {("tăng" if nv>0 else "giảm")} '
                            f'qua {ns.get("n", 0)} tin')
            _add('news', _nws_nm, 'success' if nv > 0 else 'danger',
                 _nws_msg, src)
    return out


def _indicator_states(df, df_ichi, ns, ichi_score, is_en=False) -> list:
    """Trạng thái HIỆN TẠI của 11 chỉ báo (cả khi CHƯA kích hoạt) — cho user
    thấy bức tranh đầy đủ, không chỉ những cảnh báo đang đỏ.

    Mỗi state: {'name', 'value', 'status', 'color'} — status ∈ {'trigger','neutral','watch'}.
    """
    d = _compute_indicators(df)
    if len(d) < 2:
        return []
    last = d.iloc[-1]; prev = d.iloc[-2]
    out = []
    def _add(name, value, status, color, hint=''):
        out.append({'name': name, 'value': value, 'status': status,
                    'color': color, 'hint': hint})

    # ── RSI14 ──────────────────────────────────────────────────────────
    rsi = last.get('RSI14', np.nan)
    if rsi == rsi:
        if rsi > 70:
            _add('RSI14', f'{rsi:.1f}', 'trigger', '#DC2626',
                 'Quá mua (>70)' if not is_en else 'Overbought (>70)')
        elif rsi < 30:
            _add('RSI14', f'{rsi:.1f}', 'trigger', '#16A34A',
                 'Quá bán (<30)' if not is_en else 'Oversold (<30)')
        elif rsi > 60 or rsi < 40:
            _add('RSI14', f'{rsi:.1f}', 'watch', '#D97706',
                 'Tiến gần ngưỡng' if not is_en else 'Approaching threshold')
        else:
            _add('RSI14', f'{rsi:.1f}', 'neutral', '#64748B',
                 'Vùng trung tính 40-60' if not is_en else 'Neutral 40-60')

    # ── MACD vs Signal ─────────────────────────────────────────────────
    if not np.isnan(last.get('MACD', np.nan)):
        above = last['MACD'] > last['MACD_signal']
        prev_above = prev['MACD'] > prev['MACD_signal']
        if above != prev_above:
            _add('MACD', '↑ vừa cắt' if above else '↓ vừa cắt',
                 'trigger', '#16A34A' if above else '#DC2626',
                 'Golden cross' if above else 'Death cross')
        else:
            _add('MACD',
                 ('Trên signal' if above else 'Dưới signal') if not is_en
                 else ('Above signal' if above else 'Below signal'),
                 'neutral', '#16A34A' if above else '#DC2626',
                 f'MACD={last["MACD"]:.3f}')

    # ── Bollinger %B ──────────────────────────────────────────────────
    pb = last.get('BB_pctB', np.nan)
    if pb == pb:
        if pb > 1:
            _add('Bollinger %B', f'{pb:.2f}', 'trigger', '#DC2626',
                 'Vượt dải trên' if not is_en else 'Above upper band')
        elif pb < 0:
            _add('Bollinger %B', f'{pb:.2f}', 'trigger', '#16A34A',
                 'Thủng dải dưới' if not is_en else 'Below lower band')
        elif pb > 0.8 or pb < 0.2:
            _add('Bollinger %B', f'{pb:.2f}', 'watch', '#D97706',
                 'Gần biên' if not is_en else 'Near edge')
        else:
            _add('Bollinger %B', f'{pb:.2f}', 'neutral', '#64748B',
                 'Trong dải' if not is_en else 'Within band')

    # ── Stochastic ────────────────────────────────────────────────────
    stoch = TA.stochastic(df)
    if len(stoch['k']) and stoch['k'][-1] == stoch['k'][-1]:
        kv = stoch['k'][-1]; dv = stoch['d'][-1]
        if kv > 80 and dv > 80:
            _add('Stochastic', f'%K {kv:.0f}', 'trigger', '#DC2626',
                 'Quá mua' if not is_en else 'Overbought')
        elif kv < 20 and dv < 20:
            _add('Stochastic', f'%K {kv:.0f}', 'trigger', '#16A34A',
                 'Quá bán' if not is_en else 'Oversold')
        else:
            _add('Stochastic', f'%K {kv:.0f}', 'neutral', '#64748B',
                 f'%D {dv:.0f}')

    # ── MA5/MA20 cross status ─────────────────────────────────────────
    if not np.isnan(last.get('MA5', np.nan)) and not np.isnan(last.get('MA20', np.nan)):
        ma_above = last['MA5'] > last['MA20']
        prev_ma_above = prev['MA5'] > prev['MA20']
        if ma_above != prev_ma_above:
            _add('MA5/MA20', '↑ vừa cắt' if ma_above else '↓ vừa cắt',
                 'trigger', '#16A34A' if ma_above else '#DC2626',
                 'Đảo xu hướng ngắn hạn' if not is_en else 'Short-term trend flip')
        else:
            _add('MA5/MA20',
                 ('MA5 > MA20' if ma_above else 'MA5 < MA20'),
                 'neutral', '#16A34A' if ma_above else '#DC2626',
                 'Trend ngắn hạn' if not is_en else 'Short-term trend')

    # ── Volume ratio ──────────────────────────────────────────────────
    vr = float(last.get('Volume_ratio', 1) or 1)
    if vr > 2:
        _add('Volume', f'×{vr:.1f}', 'trigger', '#D97706',
             'Đột biến' if not is_en else 'Spike')
    elif vr > 1.5:
        _add('Volume', f'×{vr:.1f}', 'watch', '#D97706',
             'Cao' if not is_en else 'High')
    elif vr < 0.5:
        _add('Volume', f'×{vr:.1f}', 'watch', '#0891B2',
             'Thấp' if not is_en else 'Low')
    else:
        _add('Volume', f'×{vr:.1f}', 'neutral', '#64748B',
             'Bình thường' if not is_en else 'Normal')

    # ── ADX ─────────────────────────────────────────────────────────────
    adx_arr = TA.adx(df)
    if len(adx_arr) and adx_arr[-1] == adx_arr[-1]:
        a = adx_arr[-1]
        if a > 25:
            _add('ADX', f'{a:.0f}', 'trigger', '#0891B2',
                 'Trend MẠNH' if not is_en else 'STRONG trend')
        elif a > 20:
            _add('ADX', f'{a:.0f}', 'watch', '#D97706',
                 'Trend nhẹ' if not is_en else 'Mild trend')
        else:
            _add('ADX', f'{a:.0f}', 'neutral', '#64748B',
                 'Sideway' if not is_en else 'Ranging')

    # ── Parabolic SAR ─────────────────────────────────────────────────
    psar = TA.parabolic_sar(df)
    if len(psar) >= 2 and psar[-1] == psar[-1] and psar[-2] == psar[-2]:
        was_above = psar[-2] > df['High'].iloc[-2]
        now_above = psar[-1] > df['High'].iloc[-1]
        if was_above != now_above:
            _add('Parabolic SAR', '⇅ vừa đảo', 'trigger',
                 '#DC2626' if now_above else '#16A34A',
                 'Đổi vị trí' if not is_en else 'Flipped')
        else:
            _add('Parabolic SAR',
                 ('Trên giá' if now_above else 'Dưới giá')
                 if not is_en else ('Above price' if now_above else 'Below price'),
                 'neutral', '#DC2626' if now_above else '#16A34A',
                 ('Bear' if now_above else 'Bull'))

    # ── Mẫu hình nến gần nhất (≤3 phiên) ──────────────────────────────
    pats = TA.candlestick_patterns(df, lookback=3)
    if pats:
        p = pats[-1]
        nm = p['name_en'] if is_en else p['name']
        if p['dir'] != 0:
            _add('Mẫu nến' if not is_en else 'Pattern', nm.split(' (')[0],
                 'trigger', '#16A34A' if p['dir'] > 0 else '#DC2626',
                 'Trong 3 phiên' if not is_en else 'Within 3 bars')
        else:
            _add('Mẫu nến' if not is_en else 'Pattern', nm,
                 'watch', '#D97706',
                 'Lưỡng lự' if not is_en else 'Indecision')
    else:
        _add('Mẫu nến' if not is_en else 'Pattern',
             '—', 'neutral', '#64748B',
             'Không mẫu gần đây' if not is_en else 'No recent pattern')

    # ── Ichimoku consensus (đã có sẵn) ────────────────────────────────
    if abs(ichi_score) >= 3:
        _add('Ichimoku', f'{ichi_score:+d}/5', 'trigger',
             '#16A34A' if ichi_score > 0 else '#DC2626',
             'Đồng thuận MẠNH' if not is_en else 'STRONG consensus')
    elif abs(ichi_score) >= 1:
        _add('Ichimoku', f'{ichi_score:+d}/5', 'watch',
             '#16A34A' if ichi_score > 0 else '#DC2626',
             'Đồng thuận nhẹ' if not is_en else 'Mild consensus')
    else:
        _add('Ichimoku', '0/5', 'neutral', '#64748B',
             'Trung tính' if not is_en else 'Neutral')

    # ── Tâm lý tin tức ────────────────────────────────────────────────
    if ns.get('ok'):
        nv = ns.get('vote', 0); n = ns.get('n', 0)
        src = 'PhoBERT AI' if ns.get('dl_used') else ('Từ điển' if not is_en else 'Lex')
        if nv != 0:
            _add('Tin tức' if not is_en else 'News',
                 ('Tích cực' if nv > 0 else 'Tiêu cực') if not is_en
                 else ('Positive' if nv > 0 else 'Negative'),
                 'trigger', '#16A34A' if nv > 0 else '#DC2626',
                 f'{src} · {n} tin' if not is_en else f'{src} · {n} headlines')
        else:
            _add('Tin tức' if not is_en else 'News',
                 'Trung lập' if not is_en else 'Neutral',
                 'neutral', '#64748B',
                 f'{src} · {n} tin' if not is_en else f'{src} · {n} headlines')
    return out


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{t("nav.signals")} — {ticker}</h1>'
        f'<p>{t("signal.subtitle", ticker=ticker)}</p>'
        f'</div>', unsafe_allow_html=True)

    is_dark  = _T.get('is_dark', False)
    _fg      = _T['text_primary']
    _fg_s    = _T['text_secondary']
    _bg_card = _T['bg_card']
    _bg_elev = _T['bg_elevated']
    _brd     = _T['border']
    _acc     = _T.get('accent', '#1565C0')
    _muted   = _T.get('text_muted', '#64748B')

    # ── Dữ liệu hiện tại ─────────────────────────────────────────────────
    ngay  = str(df['Ngay'].iloc[-1])
    close = float(df['Close'].iloc[-1])

    # ── Tính Ichimoku ────────────────────────────────────────────────────
    df_ichi = add_ichimoku(df)
    last    = df_ichi.iloc[-1]

    # ── Tầng 1 — Primary Trend ──────────────────────────────────────────
    primary_code, _ = classify_primary_trend(
        close,
        float(last['Kumo_top']) if not np.isnan(last['Kumo_top']) else float('nan'),
        float(last['Kumo_bot']) if not np.isnan(last['Kumo_bot']) else float('nan'),
    )
    primary_label = t(f'ichi.primary.{primary_code}')

    # ── Tầng 2 — TK Cross + Trading Signal ─────────────────────────────
    tk_code, _, _tk_off = detect_tk_cross(df_ichi['Tenkan'], df_ichi['Kijun'])
    tk_label = t(f'ichi.tk.{tk_code}', off=_tk_off if _tk_off is not None else 0)
    trading_code, _ = classify_trading_signal(tk_code, primary_code)
    trading_label = t(f'ichi.trading.{trading_code}')

    # ── Tầng 3 — Chikou Confirmation ───────────────────────────────────
    # So sánh: Close[t] vs Close[t-26]. Tại t cả 2 đều đã biết → không leak.
    close_now   = float(df_ichi['Close'].iloc[-1])
    close_26ago = float(df_ichi['Close'].iloc[-27]) if len(df_ichi) >= 27 else float('nan')
    chikou_code, _ = classify_chikou_confirmation(close_now, close_26ago)
    if not (np.isnan(close_now) or np.isnan(close_26ago) or close_26ago == 0):
        _chk_pct = (close_now - close_26ago) / close_26ago * 100.0
        chikou_label = t(f'ichi.chikou.{chikou_code}', pct=f'{_chk_pct:+.2f}')
    else:
        chikou_label = t('ichi.chikou.na')

    # ── Tầng 4 — Future Kumo tại T+26 ──────────────────────────────────
    # sen_a_future[t+26] = (Tenkan[t] + Kijun[t])/2  — dữ liệu tại t, không leak.
    _ten_now = float(df_ichi['Tenkan'].iloc[-1])
    _kij_now = float(df_ichi['Kijun'].iloc[-1])
    future_a = (_ten_now + _kij_now) / 2.0
    future_b = float(_donchian_mid(df['High'], df['Low'], SENKOU_N).iloc[-1])
    future_code, _ = classify_future_kumo(future_a, future_b)
    if not (np.isnan(future_a) or np.isnan(future_b)):
        _mid = (future_a + future_b) / 2.0
        _fut_pct = (future_a - future_b) / _mid * 100.0 if _mid != 0 else 0.0
        future_label = t(f'ichi.future.{future_code}', pct=f'{_fut_pct:+.2f}')
    else:
        future_label = t('ichi.future.na')

    # ── Tổng hợp ─────────────────────────────────────────────────────────
    overall_code, _, score = aggregate_signals(
        primary_code, trading_code, chikou_code, future_code
    )
    overall_label = t(f'ichi.overall.{overall_code}')

    # Lưu tóm tắt Ichimoku vào session_state để các trang khác (AI Insight) dùng lại
    st.session_state['ichimoku_summary'] = {
        'label':        overall_label,
        'code':         overall_code,
        'score':        int(score),
        'primary':      primary_code,
        'trading':      trading_code,
        'chikou':       chikou_code,
        'future_kumo':  future_code,
    }

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 1 — CẢNH BÁO ĐANG KÍCH HOẠT (đa chỉ báo)
    # ════════════════════════════════════════════════════════════════════
    _is_en_sig = st.session_state.get('lang', 'VI') == 'EN'
    try:
        _ns_for_alerts = news_sentiment(ticker)
    except Exception:
        _ns_for_alerts = {'ok': False, 'vote': 0}
    alerts = _build_alerts(df, df_ichi, _ns_for_alerts, int(score),
                            overall_code, is_en=_is_en_sig)

    _alerts_subtitle = ('cảnh báo từ chỉ báo kỹ thuật, mẫu hình nến, Ichimoku & tin tức'
                        if not _is_en_sig else
                        'from technicals, candlestick, Ichimoku & news')
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Cảnh báo đang kích hoạt" if not _is_en_sig else "Active Alerts"}'
        f' <span style="font-size:11px;font-weight:600;color:{_muted};margin-left:8px">'
        f'{len(alerts)} {_alerts_subtitle}'
        f'</span></div>', unsafe_allow_html=True)

    if not alerts:
        st.markdown(
            f'<div class="info-box" style="margin-bottom:18px;padding:14px 20px">'
            f'<span style="color:{_T["success"]};font-weight:700">●</span> '
            f'{"Không có cảnh báo nào đang kích hoạt — thị trường ổn định." if not _is_en_sig else "No active alerts — market is calm."}'
            f'</div>', unsafe_allow_html=True)
    else:
        _LEVEL_CLR = {
            'success': _T['success'], 'danger': _T['danger'],
            'warn':    _T['warning'], 'info':   _T['accent'],
        }
        _LEVEL_BG = {
            'success': 'rgba(22,163,74,0.10)', 'danger': 'rgba(220,38,38,0.10)',
            'warn':    'rgba(217,119,6,0.10)', 'info':   'rgba(8,145,178,0.10)',
        }
        _CAT_LBL = {
            'momentum':   ('Động lượng' if not _is_en_sig else 'Momentum'),
            'trend':      ('Xu hướng'   if not _is_en_sig else 'Trend'),
            'volatility': ('Biến động'  if not _is_en_sig else 'Volatility'),
            'volume':     ('Khối lượng' if not _is_en_sig else 'Volume'),
            'pattern':    ('Mẫu nến'    if not _is_en_sig else 'Pattern'),
            'cycle':      ('Chu kỳ'     if not _is_en_sig else 'Cycle'),
            'news':       ('Tin tức'    if not _is_en_sig else 'News'),
        }
        _cards = ''
        # Sắp theo độ ưu tiên: danger > warn > success > info
        _ORDER = {'danger': 0, 'warn': 1, 'success': 2, 'info': 3}
        for a in sorted(alerts, key=lambda x: _ORDER.get(x['level'], 9)):
            _c = _LEVEL_CLR.get(a['level'], _T['text_primary'])
            _bg = _LEVEL_BG.get(a['level'], 'rgba(0,0,0,0.04)')
            _cat = _CAT_LBL.get(a['cat'], a['cat'])
            _val = (f'<span style="font-size:11px;font-weight:800;color:{_c};'
                    f'background:{_bg};padding:2px 8px;border-radius:6px;'
                    f'margin-left:8px">{a["val"]}</span>' if a['val'] else '')
            _cards += (
                f'<div style="flex:1 1 280px;min-width:240px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-left:4px solid {_c};border-radius:10px;'
                f'padding:12px 14px">'
                f'<div style="display:flex;justify-content:space-between;align-items:start;gap:8px">'
                f'<div style="font-size:10px;font-weight:700;color:{_muted};'
                f'text-transform:uppercase;letter-spacing:.5px">{_cat}</div>{_val}</div>'
                f'<div style="font-size:13px;font-weight:700;color:{_c};margin-top:5px">{a["name"]}</div>'
                f'<div style="font-size:11px;color:{_fg_s};margin-top:3px;line-height:1.5">{a["msg"]}</div>'
                f'</div>')
        st.markdown(
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px">{_cards}</div>',
            unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 2 — TRẠNG THÁI 11 CHỈ BÁO THEO DÕI (kể cả khi chưa kích hoạt)
    # ════════════════════════════════════════════════════════════════════
    states = _indicator_states(df, df_ichi, _ns_for_alerts, int(score), is_en=_is_en_sig)
    if states:
        _n_trig = sum(1 for s in states if s['status'] == 'trigger')
        _n_wat = sum(1 for s in states if s['status'] == 'watch')
        st.markdown(
            f'<div class="sec-hdr">'
            f'{"Trạng thái chỉ báo theo dõi" if not _is_en_sig else "Monitored indicator status"}'
            f' <span style="font-size:11px;font-weight:600;color:{_muted};margin-left:8px">'
            f'{len(states)} {"chỉ báo" if not _is_en_sig else "indicators"} · '
            f'<span style="color:{_T["danger"]}">{_n_trig} {"kích hoạt" if not _is_en_sig else "triggered"}</span> · '
            f'<span style="color:{_T["warning"]}">{_n_wat} {"cảnh giới" if not _is_en_sig else "watch"}</span></span></div>',
            unsafe_allow_html=True)
        _ICON = {'trigger': '●', 'watch': '◐', 'neutral': '○'}
        _cells = ''
        # Sắp triggered → watch → neutral
        _ORDER2 = {'trigger': 0, 'watch': 1, 'neutral': 2}
        for s in sorted(states, key=lambda x: _ORDER2.get(x['status'], 9)):
            _cells += (
                f'<div style="flex:1 1 180px;min-width:170px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-left:3px solid {s["color"]};'
                f'border-radius:8px;padding:9px 12px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-size:10.5px;font-weight:700;color:{_T["text_muted"]};'
                f'text-transform:uppercase;letter-spacing:.4px">{s["name"]}</span>'
                f'<span style="font-size:13px;color:{s["color"]}">{_ICON[s["status"]]}</span>'
                f'</div>'
                f'<div style="font-size:15px;font-weight:800;color:{s["color"]};margin-top:2px;line-height:1.2">{s["value"]}</div>'
                f'<div style="font-size:10.5px;color:{_T["text_secondary"]};margin-top:2px">{s["hint"]}</div>'
                f'</div>')
        st.markdown(
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">{_cells}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:11px;color:{_muted};margin:-8px 0 14px;line-height:1.5">'
            f'● {"đang KÍCH HOẠT" if not _is_en_sig else "TRIGGERED"} (điều kiện đạt ngưỡng) · '
            f'◐ {"CẢNH GIỚI" if not _is_en_sig else "WATCH"} (tiến gần ngưỡng) · '
            f'○ {"trung tính" if not _is_en_sig else "neutral"} — '
            f'{"chip ● khớp cards ở phần Cảnh báo phía trên" if not _is_en_sig else "● dots match cards in Active Alerts above"}'
            f'</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 3 — BIỂU ĐỒ KỸ THUẬT TỔNG HỢP (multi-indicator, không chỉ Ichimoku)
    # ════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Biểu đồ kỹ thuật tổng hợp" if not _is_en_sig else "Comprehensive technical chart"}'
        f' <span style="font-size:11px;font-weight:600;color:{_muted};margin-left:8px">'
        f'{"Nến + S/R + Fibonacci + Kênh + Sóng (ZigZag) + Mẫu nến + VWAP + Parabolic SAR (180 phiên)" if not _is_en_sig else "Candles + S/R + Fibonacci + Channel + Waves (ZigZag) + Patterns + VWAP + Parabolic SAR (180 bars)"}'
        f'</span></div>', unsafe_allow_html=True)
    try:
        _fig_tech = chart_technical(
            df, ticker, _T, window=180,
            show_sr=True, show_fib=True, show_channel=True,
            show_zigzag=True, show_patterns=True,
            show_vwap=True, show_psar=True,
            is_en=_is_en_sig,
        )
        st.plotly_chart(_fig_tech, use_container_width=True,
                        config={**_PLOTLY_CONFIG, 'scrollZoom': True,
                                'toImageButtonOptions': {
                                    **_PLOTLY_CONFIG['toImageButtonOptions'],
                                    'filename': f'{ticker}_technical_signals'}})
    except Exception as _e:
        st.caption(f'⚠ {_e}')

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 4 — Kết luận tổng hợp Ichimoku (chuyên sâu)
    # ════════════════════════════════════════════════════════════════════
    st.markdown(f'<div class="sec-hdr">{t("signal.summary_hdr")}</div>',
                unsafe_allow_html=True)

    _ov_color  = _sig_color(overall_code, is_dark)
    _ov_bg     = _sig_bg(overall_code, is_dark)
    _score_lbl = f'+{score}' if score > 0 else str(score)
    _bar_n     = min(abs(score), 5)

    # Score bar bằng SVG — render nhất quán trên mọi font/browser
    _cell_w, _cell_h, _cell_gap = 26, 10, 5
    _bar_w = 5 * _cell_w + 4 * _cell_gap
    _cells_svg = ''
    for _i in range(5):
        _x = _i * (_cell_w + _cell_gap)
        _fill = _ov_color if _i < _bar_n else _bg_elev
        _cells_svg += (
            f'<rect x="{_x}" y="0" width="{_cell_w}" height="{_cell_h}" '
            f'rx="2" fill="{_fill}"/>'
        )
    _bar_svg = (
        f'<svg width="{_bar_w}" height="{_cell_h}" '
        f'style="display:inline-block;vertical-align:middle;margin-left:8px">'
        f'{_cells_svg}</svg>'
    )

    _ov_title = t(f'signal.overall.{overall_code}')

    st.markdown(f"""
<div style="background:{_ov_bg};border:2px solid {_ov_color};border-radius:14px;
            padding:18px 22px;margin-bottom:18px;display:flex;
            align-items:center;gap:20px;flex-wrap:wrap">
  <div style="font-size:32px;font-weight:900;color:{_ov_color};min-width:52px;line-height:1">
    {_score_lbl}
  </div>
  <div style="flex:1;min-width:180px">
    <div style="font-size:19px;font-weight:800;color:{_ov_color}">{_ov_title}</div>
    <div style="font-size:13px;color:{_fg_s};margin-top:4px">{overall_label}</div>
    <div style="font-size:11px;color:{_muted};margin-top:3px;display:flex;align-items:center;gap:2px">
      <span style="font-family:monospace">Score {_score_lbl} / 5</span>
      {_bar_svg}
    </div>
  </div>
  <div style="font-size:12px;color:{_fg_s};text-align:right;white-space:nowrap">
    <div style="font-weight:700">{ticker} · {ngay}</div>
    <div>{t('common.price')}: {close*1000:,.0f} đ</div>
    <div style="font-size:11px;color:{_muted};margin-top:2px">
      {t('signal.kumo_range')} [{float(last["Kumo_bot"])*1000:,.0f} – {float(last["Kumo_top"])*1000:,.0f}]
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 2 — Bốn tầng tín hiệu Ichimoku
    # ════════════════════════════════════════════════════════════════════
    st.markdown(f'<div class="sec-hdr">{t("signal.tiers_hdr")}</div>',
                unsafe_allow_html=True)

    _layers = [
        (t('signal.tier1_title'),
         primary_code, primary_label,
         t('signal.tier1_note')),

        (t('signal.tier2_title'),
         trading_code, trading_label,
         t('signal.tier2_note', status=tk_label)),

        (t('signal.tier3_title'),
         chikou_code, chikou_label,
         t('signal.tier3_note',
           now=f'{close*1000:,.0f}',
           past=f'{close_26ago*1000:,.0f}',
           muted=_muted)),

        (t('signal.tier4_title'),
         future_code, future_label,
         t('signal.tier4_note',
           a=f'{future_a:.3f}',
           b=f'{future_b:.3f}')),
    ]

    col_l1, col_l2 = st.columns(2)
    for _i, (title, code, label, note) in enumerate(_layers):
        _col   = col_l1 if _i % 2 == 0 else col_l2
        _c     = _sig_color(code, is_dark)
        _bg_ly = _sig_bg(code, is_dark)
        _ic    = _sig_icon(code)
        with _col:
            st.markdown(f"""
<div style="background:{_bg_ly};border:1px solid {_brd};border-radius:10px;
            padding:12px 14px;margin-bottom:10px">
  <div style="font-size:10px;font-weight:700;color:{_muted};text-transform:uppercase;
              letter-spacing:0.5px;margin-bottom:5px">{title}</div>
  <div style="font-size:15px;font-weight:800;color:{_c}">{_ic} {label}</div>
  <div style="font-size:11px;color:{_fg_s};margin-top:6px;line-height:1.4">{note}</div>
</div>
""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 3 — Biểu đồ Ichimoku Kinko Hyo
    # ════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div class="sec-hdr" style="margin-top:16px">'
        f'{t("signal.ichi_chart_hdr", ticker=ticker)}</div>',
        unsafe_allow_html=True)
    try:
        _fig_ichi = chart_ichimoku_plotly(df_ichi, ticker, T=_T)
        st.plotly_chart(_fig_ichi, use_container_width=True,
            config={**_PLOTLY_CONFIG, 'toImageButtonOptions': {
                **_PLOTLY_CONFIG['toImageButtonOptions'],
                'filename': f'{ticker}_ichimoku',
            }})
    except Exception as _e:
        st.error(t('signal.error_ichi', e=str(_e)))

    # ════════════════════════════════════════════════════════════════════
    # PHẦN 4 — Ba đặc trưng dẫn xuất Ichimoku
    # ════════════════════════════════════════════════════════════════════
    st.markdown(f'<div class="sec-hdr" style="margin-top:16px">{t("signal.features_hdr")}</div>',
                unsafe_allow_html=True)

    _tk_mom   = float(df_ichi['TK_momentum'].iloc[-1])
    _cld_dist = float(df_ichi['Cloud_dist'].iloc[-1])
    _chk_mom  = float(df_ichi['Chikou_momentum'].iloc[-1])

    def _feat_card(col, title, formula, val_str, desc, code):
        _c = _sig_color(code, is_dark)
        col.markdown(f"""
<div style="background:{_bg_card};border:1px solid {_brd};border-radius:10px;
            padding:14px 16px;height:100%">
  <div style="font-size:11px;color:{_muted};font-weight:700;margin-bottom:3px">{title}</div>
  <div style="font-size:10px;color:{_muted};font-family:monospace;margin-bottom:6px;
              font-style:italic">{formula}</div>
  <div style="font-size:22px;font-weight:900;color:{_c}">{val_str}</div>
  <div style="font-size:11px;color:{_fg_s};margin-top:5px;line-height:1.4">{desc}</div>
</div>""", unsafe_allow_html=True)

    _f1, _f2, _f3 = st.columns(3)

    # [1] TK Momentum
    _tk_c    = ('bull' if _tk_mom >  0.05 else
                'bear' if _tk_mom < -0.05 else 'neut')
    _tk_str  = f'{_tk_mom:+.3f}%' if not np.isnan(_tk_mom) else 'N/A'
    _tk_desc = (t('signal.feat_tk_bull') if _tk_mom > 0.05 else
                (t('signal.feat_tk_bear') if _tk_mom < -0.05 else
                 t('signal.feat_tk_neut')))
    _feat_card(_f1, t('signal.feat_tk_momentum'),
               t('signal.feat_tk_formula'),
               _tk_str, _tk_desc, _tk_c)

    # [2] Cloud Distance
    _cd_c    = ('bull' if _cld_dist >  0.5 else
                'bear' if _cld_dist < -0.5 else 'neut')
    _cd_str  = f'{_cld_dist:+.3f}%' if not np.isnan(_cld_dist) else 'N/A'
    _cd_desc = (t('signal.feat_cd_bull') if _cld_dist > 0.5 else
                (t('signal.feat_cd_bear') if _cld_dist < -0.5 else
                 t('signal.feat_cd_neut')))
    _feat_card(_f2, t('signal.feat_cd_name'),
               t('signal.feat_cd_formula'),
               _cd_str, _cd_desc, _cd_c)

    # [3] Chikou Momentum
    _cm_c    = ('bull' if _chk_mom >  0.5 else
                'bear' if _chk_mom < -0.5 else 'neut')
    _cm_str  = f'{_chk_mom:+.3f}%' if not np.isnan(_chk_mom) else 'N/A'
    _cm_desc = (t('signal.feat_cm_bull') if _chk_mom > 0.5 else
                (t('signal.feat_cm_bear') if _chk_mom < -0.5 else
                 t('signal.feat_cm_neut')))
    _feat_card(_f3, t('signal.feat_cm_name'),
               t('signal.feat_cm_formula'),
               _cm_str, _cm_desc, _cm_c)

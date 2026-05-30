"""Trang 'Chiến lược Giao dịch' — xác định điểm mua/bán & kế hoạch vào lệnh.

Kết hợp:
  • Phân tích kỹ thuật: xu hướng (MA50), giao cắt MA5/MA20, MACD, RSI14,
    Bollinger %B, Ichimoku (tổng hợp 4 tầng).
  • Đồng thuận dự báo: hướng dự báo phiên kế tiếp của 7 mô hình.
→ Tín hiệu tổng hợp MUA / BÁN / GIỮ + điểm vào lệnh, cắt lỗ (SL), chốt lời (TP)
  theo ATR, và backtest nhanh chiến lược kỹ thuật trên lịch sử.

Lưu ý: công cụ hỗ trợ học thuật, KHÔNG phải khuyến nghị đầu tư.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.i18n import t
from core.constants import ticker_sector
from charts.base import _PLOTLY_CONFIG, _plotly_axes_style


# ── Chỉ báo kỹ thuật (series) ───────────────────────────────────────────────
def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: lambda d: (
                     int(len(d)), str(d['Ngay'].iloc[0]) if len(d) else 'empty',
                     str(d['Ngay'].iloc[-1]) if len(d) else 'empty',
                     float(d['Close'].iloc[-1]) if len(d) else 0.0)})
def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    close, high, low = d['Close'], d['High'], d['Low']
    # MACD (12,26,9)
    macd = _ema(close, 12) - _ema(close, 26)
    d['MACD'] = macd
    d['MACD_signal'] = _ema(macd, 9)
    d['MACD_hist'] = d['MACD'] - d['MACD_signal']
    # Bollinger (20, 2σ)
    ma20 = close.rolling(20).mean()
    sd20 = close.rolling(20).std()
    d['BB_up'] = ma20 + 2 * sd20
    d['BB_lo'] = ma20 - 2 * sd20
    d['BB_pctB'] = (close - d['BB_lo']) / (d['BB_up'] - d['BB_lo']).replace(0, np.nan)
    # ATR (14) — làm trơn Wilder (RMA, alpha=1/14) đúng chuẩn Wilder 1978
    prev_c = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_c).abs(), (low - prev_c).abs()], axis=1).max(axis=1)
    d['ATR'] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    return d


def _tech_votes(row) -> dict:
    """Phiếu bầu của từng chỉ báo: +1 tăng / -1 giảm / 0 trung lập."""
    v = {}
    c = float(row['Close'])
    v['trend'] = 1 if (not np.isnan(row.get('MA50', np.nan)) and c > row['MA50']) else (-1 if not np.isnan(row.get('MA50', np.nan)) else 0)
    v['ma_cross'] = 1 if row['MA5'] > row['MA20'] else -1
    v['macd'] = 1 if row['MACD'] > row['MACD_signal'] else -1
    _rsi = row.get('RSI14', np.nan)
    if np.isnan(_rsi):
        v['rsi'] = 0
    elif _rsi < 35:
        v['rsi'] = 1          # quá bán → cơ hội mua
    elif _rsi > 70:
        v['rsi'] = -1         # quá mua → rủi ro
    else:
        v['rsi'] = 1 if _rsi >= 50 else -1
    _pb = row.get('BB_pctB', np.nan)
    if np.isnan(_pb):
        v['bollinger'] = 0
    elif _pb < 0.05:
        v['bollinger'] = 1    # chạm/ thủng dải dưới → bật lên
    elif _pb > 0.95:
        v['bollinger'] = -1
    else:
        v['bollinger'] = 0
    return v


def _tech_signal_series(d: pd.DataFrame) -> pd.Series:
    """Tín hiệu kỹ thuật theo ngày (long-only) cho backtest: 1=giữ long, 0=đứng ngoài.
    Long khi xu hướng + động lượng đồng thuận và chưa quá mua."""
    long_cond = (
        (d['MA5'] > d['MA20']) &
        (d['Close'] > d['MA50']) &
        (d['MACD'] > d['MACD_signal']) &
        (d['RSI14'] < 75)
    )
    return long_cond.astype(int)


def _backtest_longonly(d: pd.DataFrame, nt: int, fee_side: float = 0.0015):
    """Backtest long-only: vào lệnh theo tín hiệu kỹ thuật (vào ở phiên kế tiếp).

    Có tính PHÍ GIAO DỊCH thực tế: mỗi lần đổi trạng thái (vào/thoát) trừ
    `fee_side` (mặc định 0.15%/chiều → khứ hồi ≈ 0.3%, sát phí + thuế HOSE).
    Trả về dict metrics + chuỗi equity (chiến lược NET vs mua&giữ)."""
    sig = _tech_signal_series(d)
    pos = sig.shift(1).fillna(0)                 # vào lệnh phiên sau khi có tín hiệu
    ret = d['Close'].pct_change().fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())    # 1 tại mỗi lần vào hoặc thoát lệnh
    fee = turn * fee_side                        # chi phí giao dịch theo phiên
    strat_ret = pos * ret - fee                  # lợi suất ĐÃ TRỪ PHÍ
    eq_strat = (1 + strat_ret).cumprod()
    eq_bh = (1 + ret).cumprod()
    total_fee = float(fee.sum() * 100)           # tổng phí (% trên vốn, xấp xỉ)
    # Số lệnh = số lần chuyển 0→1
    entries = ((pos == 1) & (pos.shift(1) == 0)).sum()
    # Win rate theo "lệnh": gom các đoạn giữ long liên tiếp
    trades = []
    in_pos = False; entry_px = None
    closes = d['Close'].values
    posv = pos.values
    for i in range(len(posv)):
        if posv[i] == 1 and not in_pos:
            in_pos = True; entry_px = closes[i]
        elif posv[i] == 0 and in_pos:
            in_pos = False
            if entry_px:
                trades.append(closes[i] / entry_px - 1)
    if in_pos and entry_px:
        trades.append(closes[-1] / entry_px - 1)
    wins = sum(1 for x in trades if x > 0)
    win_rate = (wins / len(trades) * 100) if trades else 0.0
    # Max drawdown của chiến lược
    roll_max = eq_strat.cummax()
    dd = (eq_strat / roll_max - 1).min() * 100
    # Sharpe (hàng năm, từ strat_ret)
    sd = strat_ret.std()
    sharpe = (strat_ret.mean() / sd * (252 ** 0.5)) if sd > 0 else 0.0
    return dict(
        eq_strat=eq_strat, eq_bh=eq_bh, dates=pd.to_datetime(d['Ngay']),
        total_strat=(eq_strat.iloc[-1] - 1) * 100,
        total_bh=(eq_bh.iloc[-1] - 1) * 100,
        n_trades=int(len(trades)), win_rate=win_rate,
        max_dd=float(dd), sharpe=float(sharpe),
        total_fee=total_fee, fee_side=fee_side,
        sig=sig,
    )


@st.fragment
def _technical_analysis_section(df, ticker, _T, is_en):
    """Phân tích kỹ thuật nâng cao — toggle các lớp KHÔNG rerun toàn trang.

    Hỗ trợ/Kháng cự · Fibonacci · Kênh xu hướng · Sóng (ZigZag) + bảng tóm tắt
    vị thế kỹ thuật + Pivot Points.
    """
    from charts.technicals import chart_technical
    from data import technicals as TA
    from charts.base import _PLOTLY_CONFIG

    st.markdown("<div style='margin:18px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Phân tích Kỹ thuật nâng cao" if not is_en else "Advanced technical analysis"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]}">'
        f'{"— Hỗ trợ/Kháng cự · Fibonacci · Kênh xu hướng · Sóng" if not is_en else "— Support/Resistance · Fibonacci · Trend channel · Waves"}'
        f'</span></div>', unsafe_allow_html=True)

    # Hàng 1: 4 toggle phổ thông + cửa sổ
    c1, c2, c3, c4, c_win = st.columns([1, 1, 1, 1, 1.3])
    _sr  = c1.toggle(('Hỗ trợ/Kháng cự' if not is_en else 'S/R'),  value=True, key=f'ta_sr_{ticker}')
    _fib = c2.toggle('Fibonacci',                                   value=True, key=f'ta_fib_{ticker}')
    _ch  = c3.toggle(('Kênh xu hướng' if not is_en else 'Channel'), value=True, key=f'ta_ch_{ticker}')
    _zz  = c4.toggle(('Sóng (ZigZag)' if not is_en else 'Waves'),   value=True, key=f'ta_zz_{ticker}')
    _win = c_win.radio(('Cửa sổ' if not is_en else 'Window'),
                       options=[120, 180, 365], index=1, horizontal=True,
                       key=f'ta_win_{ticker}', label_visibility='collapsed')
    # Hàng 2: mẫu nến + VWAP + PSAR (mặc định tắt VWAP/PSAR cho gọn)
    c5, c6, c7, _, _ = st.columns([1, 1, 1, 1, 1.3])
    _pat  = c5.toggle(('Mẫu nến' if not is_en else 'Patterns'),    value=True,  key=f'ta_pat_{ticker}')
    _vwap = c6.toggle('VWAP',                                       value=True,  key=f'ta_vwap_{ticker}',
                      help=('Giá trung bình theo khối lượng 20 phiên'
                            if not is_en else 'Volume-weighted average price (20)'))
    _psar = c7.toggle('Parabolic SAR',                              value=True,  key=f'ta_psar_{ticker}',
                      help=('Chấm dừng lỗ / điểm đảo chiều (Wilder 1978)'
                            if not is_en else 'Stop-and-Reverse points (Wilder 1978)'))

    try:
        fig = chart_technical(df, ticker, _T, window=int(_win), show_sr=_sr,
                              show_fib=_fib, show_channel=_ch, show_zigzag=_zz,
                              show_patterns=_pat, show_vwap=_vwap,
                              show_psar=_psar, is_en=is_en)
        st.plotly_chart(fig, use_container_width=True, config={
            **_PLOTLY_CONFIG, 'scrollZoom': True})
    except Exception as _e:
        st.caption(f'⚠ {_e}')

    # ── Mẫu hình nến gần đây (panel) ────────────────────────────────────
    _pats = TA.candlestick_patterns(df, lookback=20)
    if _pats:
        _chips = ''
        for p in _pats[-6:][::-1]:
            _pc = ('#16A34A' if p['dir'] > 0 else '#DC2626' if p['dir'] < 0
                   else _T['text_muted'])
            _parr = '▲' if p['dir'] > 0 else '▼' if p['dir'] < 0 else '◆'
            _pnm = p['name_en'] if is_en else p['name']
            _pds = p['desc_en'] if is_en else p['desc']
            # v58.3 — padding bottom + line-height 1.5 cho descender 'g','y'
            # không bị cut. min-height đều card; break-word cho mô tả dài.
            _chips += (
                f'<div style="flex:1 1 220px;min-width:200px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-left:3px solid {_pc};'
                f'border-radius:8px;padding:10px 12px 12px;min-height:74px;'
                f'word-break:break-word">'
                f'<div style="font-size:12px;font-weight:700;color:{_pc};'
                f'line-height:1.4">{_parr} {_pnm}</div>'
                f'<div style="font-size:10.5px;color:{_T["text_muted"]};'
                f'margin-top:4px;line-height:1.55">'
                f'{str(p["date"])[:10]} · {_pds}</div></div>')
        st.markdown(
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'text-transform:uppercase;letter-spacing:.5px;margin:10px 0 6px">'
            f'{"Mẫu hình nến gần đây" if not is_en else "Recent candlestick patterns"}</div>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap">{_chips}</div>',
            unsafe_allow_html=True)

    # ── Bảng tóm tắt vị thế kỹ thuật + Pivot Points ─────────────────────
    s = TA.technical_summary(df.tail(int(_win)))
    pv = TA.pivot_points(df)
    K = 1000.0
    last = s['last'] * K

    def _fmt(v):
        return f'{v*K:,.0f} đ' if (v == v) else '—'   # v==v: not NaN

    _rows = [
        (('Giá hiện tại' if not is_en else 'Current price'), f'{last:,.0f} đ', _T['text_primary']),
        (('Kháng cự gần nhất' if not is_en else 'Nearest resistance'), _fmt(s['near_res']), '#DC2626'),
        (('Hỗ trợ gần nhất' if not is_en else 'Nearest support'), _fmt(s['near_sup']), '#16A34A'),
        (('Vùng Fibonacci' if not is_en else 'Fibonacci zone'), s['fib_zone'] or '—', '#7C3AED'),
        (('Vị trí trong kênh' if not is_en else 'Channel position'),
         {'upper': 'Biên trên' if not is_en else 'Upper band',
          'lower': 'Biên dưới' if not is_en else 'Lower band',
          'mid':   'Giữa kênh' if not is_en else 'Mid-channel'}.get(s['channel_pos'], '—'),
         '#0891B2'),
        (('Độ dốc kênh (%/phiên)' if not is_en else 'Channel slope (%/bar)'),
         f'{s["slope_pct"]:+.3f}%', _T['success'] if s['slope_pct'] >= 0 else _T['danger']),
    ]
    _cells = ''.join(
        f'<div style="flex:1 1 180px;min-width:160px;background:{_T["bg_card"]};'
        f'border:1px solid {_T["border"]};border-top:3px solid {col};border-radius:10px;'
        f'padding:12px 14px;min-height:82px;word-break:break-word">'
        f'<div style="font-size:10px;color:{_T["text_muted"]};font-weight:700;'
        f'text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;'
        f'line-height:1.35">{lbl}</div>'
        f'<div style="font-size:clamp(14px, 1.45vw, 16px);font-weight:800;'
        f'color:{col};line-height:1.2">{val}</div></div>'
        for lbl, val, col in _rows)
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">{_cells}</div>',
        unsafe_allow_html=True)

    # Pivot Points (R3..S3)
    if pv:
        _piv_order = ['R3', 'R2', 'R1', 'PP', 'S1', 'S2', 'S3']
        _piv_cells = ''
        for k in _piv_order:
            _c = ('#DC2626' if k.startswith('R') else '#16A34A' if k.startswith('S')
                  else _T['accent'])
            _piv_cells += (
                f'<div style="flex:1;text-align:center;padding:6px 4px;'
                f'border-right:1px solid {_T["divider"]}">'
                f'<div style="font-size:10px;font-weight:700;color:{_c}">{k}</div>'
                f'<div style="font-size:12px;color:{_T["text_primary"]};font-weight:600">'
                f'{pv[k]*K:,.0f}</div></div>')
        st.markdown(
            f'<div style="margin-top:10px;border:1px solid {_T["border"]};border-radius:10px;'
            f'overflow:hidden"><div style="font-size:10px;font-weight:700;'
            f'color:{_T["text_secondary"]};padding:6px 12px;background:{_T["bg_elevated"]};'
            f'text-transform:uppercase;letter-spacing:.5px">'
            f'{"Pivot Points (điểm xoay — phiên gần nhất)" if not is_en else "Pivot Points (latest session)"}</div>'
            f'<div style="display:flex">{_piv_cells}</div></div>',
            unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:10px;line-height:1.6">'
        f'{"Hỗ trợ/Kháng cự gom từ các đỉnh/đáy swing (số sau dấu · = số lần chạm vùng). Fibonacci đo trên sóng lớn nhất của cửa sổ. Kênh xu hướng = hồi quy tuyến tính ±2σ. ZigZag lọc đảo chiều ≥6% để lộ bộ khung sóng (cơ sở đếm sóng Elliott thủ công, KHÔNG phải đếm sóng tự động)." if not is_en else "Support/Resistance clustered from swing highs/lows (number after · = touches). Fibonacci on the window largest swing. Channel = linear regression ±2σ. ZigZag filters ≥6% reversals to reveal the wave skeleton (basis for manual Elliott counting, NOT automatic)."}'
        f'</div>', unsafe_allow_html=True)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Chiến lược Giao dịch" if not is_en else "Trading Strategy"} — {ticker}</h1>'
        f'<p>{ticker_sector(ticker)} &nbsp;·&nbsp; '
        f'{"Kết hợp phân tích kỹ thuật & đồng thuận dự báo → điểm mua/bán + kế hoạch vào lệnh" if not is_en else "Technical analysis + forecast consensus → entry/exit points + trade plan"}</p>'
        f'</div>', unsafe_allow_html=True)

    d = _compute_indicators(df)
    last = d.iloc[-1]
    last_c = float(last['Close'])
    atr = float(last['ATR']) if not np.isnan(last['ATR']) else float(d['Close'].pct_change().std() * last_c)

    # ── Đồng thuận dự báo 7 mô hình ─────────────────────────────────────
    _spin = ('Đang tổng hợp dự báo các mô hình...' if not is_en
             else 'Aggregating model forecasts...')
    with st.spinner(_spin):
        from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
        from models.ml import run_gbr
        _adv = {}
        for _nm, _fn in [('SARIMA', run_sarima), ('Holt-Winters', run_ets),
                         ('GARCH', run_garch), ('SARIMAX', run_sarimax),
                         ('Gradient Boosting', run_gbr)]:
            try:
                _adv[_nm] = _fn(ticker, train_ratio, p=ar_order,
                                date_from=date_from, date_to=date_to)
            except Exception:
                _adv[_nm] = None

    _fc = [(f'AR({ar_order})', float(r1['next_pred'])), ('MLR', float(r2['next_pred'])),
           ('ARIMA', float(r3['next_pred']))]
    for _nm in ('SARIMA', 'Holt-Winters', 'GARCH', 'SARIMAX', 'Gradient Boosting'):
        _rr = _adv.get(_nm)
        if _rr is not None and np.isfinite(_rr.get('next_pred', np.nan)):
            _fc.append((_nm, float(_rr['next_pred'])))
    _up = sum(1 for _, p in _fc if p > last_c)
    _down = sum(1 for _, p in _fc if p < last_c)
    _n_models = len(_fc)
    _fc_vote = 1 if _up > _down else (-1 if _down > _up else 0)
    _mean_pred = float(np.mean([p for _, p in _fc]))
    _mean_chg = (_mean_pred - last_c) / last_c * 100 if last_c else 0

    # ── Ichimoku tổng hợp (tái dùng logic dashboard) ───────────────────
    try:
        from app_pages.dashboard import _ichi_dashboard_summary
        _ov_code = _ichi_dashboard_summary(df)[0]
    except Exception:
        _ov_code = 'na'
    _ichi_vote = (1 if _ov_code in ('strong_bull', 'mild_bull')
                  else -1 if _ov_code in ('strong_bear', 'mild_bear') else 0)

    # ── Tâm lý tin tức (bổ trợ) ─────────────────────────────────────────
    try:
        from data.news import news_sentiment
        _ns = news_sentiment(ticker)
        _news_vote = int(_ns.get('vote', 0)) if _ns.get('ok') else 0
    except Exception:
        _ns = {'ok': False}; _news_vote = 0

    # ── Mẫu hình nến gần nhất (trong 3 phiên) → phiếu ──────────────────
    try:
        from data.technicals import candlestick_patterns
        _recent_pats = candlestick_patterns(df, lookback=3)
        if _recent_pats:
            _pat_vote = _recent_pats[-1]['dir']
            _pat_name = _recent_pats[-1]['name_en' if is_en else 'name']
        else:
            _pat_vote, _pat_name = 0, None
    except Exception:
        _pat_vote, _pat_name = 0, None

    # ── Stochastic / ADX / OBV — 3 chỉ báo cổ điển bổ sung ──────────────
    try:
        from data import technicals as _TA2
        _stoch = _TA2.stochastic(df)
        _k = float(_stoch['k'][-1]); _d_ = float(_stoch['d'][-1])
        if _k != _k:               # NaN guard
            _stoch_vote = 0
        elif _k < 30 and _d_ < 30:
            _stoch_vote = 1        # quá bán → cơ hội bật lên
        elif _k > 70 and _d_ > 70:
            _stoch_vote = -1       # quá mua → rủi ro
        else:
            _stoch_vote = 0
    except Exception:
        _stoch_vote = 0
    try:
        _adx_arr = _TA2.adx(df); _adx_v = float(_adx_arr[-1])
        # ADX kết hợp slope giá: trend MẠNH (>20) + slope dương → +1; ngược lại
        _slope14 = float(df['Close'].iloc[-1] - df['Close'].iloc[-15]) if len(df) >= 15 else 0.0
        if _adx_v == _adx_v and _adx_v > 20:
            _adx_vote = 1 if _slope14 > 0 else -1
        else:
            _adx_vote = 0          # trend yếu → không bỏ phiếu
    except Exception:
        _adx_v = float('nan'); _adx_vote = 0
    try:
        _obv_arr = _TA2.obv(df)
        if len(_obv_arr) >= 15:
            _obv_vote = 1 if _obv_arr[-1] > _obv_arr[-15] else -1
        else:
            _obv_vote = 0
    except Exception:
        _obv_vote = 0

    # ── Tổng hợp phiếu (12 phiếu — đầy đủ bộ chỉ báo cổ điển) ──────────
    tv = _tech_votes(last)
    votes = [
        ('Xu hướng (MA50)' if not is_en else 'Trend (MA50)', tv['trend']),
        ('Giao cắt MA5/MA20' if not is_en else 'MA5/MA20 cross', tv['ma_cross']),
        ('MACD', tv['macd']),
        ('RSI14', tv['rsi']),
        ('Bollinger %B', tv['bollinger']),
        ('Stochastic', _stoch_vote),
        ('ADX' + (f' ({_adx_v:.0f})' if _adx_v == _adx_v else ''), _adx_vote),
        ('OBV', _obv_vote),
        ('Ichimoku', _ichi_vote),
        (('Mẫu hình nến' if not is_en else 'Candlestick') + (f' · {_pat_name.split(" (")[0]}' if _pat_name else ''), _pat_vote),
        ('Đồng thuận dự báo' if not is_en else 'Forecast consensus', _fc_vote),
        ('Tâm lý tin tức' if not is_en else 'News sentiment', _news_vote),
    ]
    score = sum(v for _, v in votes)
    n_votes = len(votes)
    # Ngưỡng ±4 trên tổng 12 phiếu (~33% đồng thuận ròng) — giữ tín hiệu chắc tay.
    if score >= 4:
        sig_code, sig_lbl, sig_col = 'buy', ('MUA' if not is_en else 'BUY'), '#16A34A'
    elif score <= -4:
        sig_code, sig_lbl, sig_col = 'sell', ('BÁN' if not is_en else 'SELL'), '#DC2626'
    else:
        sig_code, sig_lbl, sig_col = 'hold', ('GIỮ / QUAN SÁT' if not is_en else 'HOLD / WATCH'), '#D97706'

    # ── Kế hoạch vào lệnh theo ATR ─────────────────────────────────────
    if sig_code == 'buy':
        entry = last_c; sl = last_c - 1.5 * atr; tp = last_c + 2.5 * atr
    elif sig_code == 'sell':
        entry = last_c; sl = last_c + 1.5 * atr; tp = last_c - 2.5 * atr
    else:
        entry = last_c; sl = last_c - 1.5 * atr; tp = last_c + 2.0 * atr
    rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 1e-9 else 0

    # ── THẺ TÍN HIỆU + KẾ HOẠCH ────────────────────────────────────────
    cL, cR = st.columns([1.15, 1])
    with cL:
        _bar = max(min(score, n_votes), -n_votes)
        st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-left:6px solid {sig_col};border-radius:14px;padding:20px 24px;'
            f'box-shadow:{_T["shadow_md"]}">'
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'letter-spacing:1px;text-transform:uppercase">{"Khuyến nghị tổng hợp" if not is_en else "Composite recommendation"}</div>'
            f'<div style="font-size:38px;font-weight:800;color:{sig_col};line-height:1.1;margin:6px 0">{sig_lbl}</div>'
            f'<div style="font-size:13px;color:{_T["text_secondary"]}">'
            f'{"Điểm tổng hợp" if not is_en else "Composite score"}: '
            f'<b style="color:{sig_col}">{score:+d}</b> / ±{n_votes} &nbsp;·&nbsp; '
            f'{"Dự báo TB" if not is_en else "Avg forecast"}: <b>{_mean_pred*1000:,.0f} đ</b> '
            f'(<span style="color:{"#16A34A" if _mean_chg>=0 else "#DC2626"}">{_mean_chg:+.2f}%</span>)</div>'
            f'<div style="font-size:12px;color:{_T["text_muted"]};margin-top:6px">'
            f'{_up}/{_n_models} {"mô hình dự báo TĂNG" if not is_en else "models forecast UP"} · '
            f'{_down}/{_n_models} {"dự báo GIẢM" if not is_en else "forecast DOWN"}</div>'
            f'</div>', unsafe_allow_html=True)
    with cR:
        _plan_rows = [
            (('Giá vào lệnh' if not is_en else 'Entry'), entry, _T['text_primary']),
            (('Cắt lỗ (SL)' if not is_en else 'Stop-loss (SL)'), sl, '#DC2626'),
            (('Chốt lời (TP)' if not is_en else 'Take-profit (TP)'), tp, '#16A34A'),
        ]
        _pr = ''.join(
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
            f'border-bottom:1px solid {_T["divider"]}">'
            f'<span style="color:{_T["text_secondary"]};font-size:13px">{lbl}</span>'
            f'<b style="color:{col};font-size:14px">{val*1000:,.0f} đ</b></div>'
            for lbl, val, col in _plan_rows)
        st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-radius:14px;padding:18px 22px;box-shadow:{_T["shadow_md"]}">'
            f'<div style="font-size:11px;font-weight:700;color:{_T["text_secondary"]};'
            f'letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">'
            f'{"Kế hoạch vào lệnh (theo ATR)" if not is_en else "Trade plan (ATR-based)"}</div>'
            f'{_pr}'
            f'<div style="font-size:12px;color:{_T["text_muted"]};'
            f'margin-top:10px;line-height:1.6;padding-bottom:2px">'
            f'ATR(14) = <b>{atr*1000:,.0f} đ</b> &nbsp;·&nbsp; R:R ≈ <b>{rr:.2f}</b></div>'
            f'</div>', unsafe_allow_html=True)

    # ── BẢNG PHIẾU CHỈ BÁO ─────────────────────────────────────────────
    st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Bảng tín hiệu chi tiết" if not is_en else "Signal breakdown"}</div>',
                unsafe_allow_html=True)
    _vr = ''
    for lbl, v in votes:
        if v > 0:
            _txt, _c = ('TĂNG' if not is_en else 'UP'), '#16A34A'
        elif v < 0:
            _txt, _c = ('GIẢM' if not is_en else 'DOWN'), '#DC2626'
        else:
            _txt, _c = ('TRUNG LẬP' if not is_en else 'NEUTRAL'), _T['text_muted']
        _vr += (f'<tr style="border-top:1px solid {_T["divider"]}">'
                f'<td style="padding:8px 12px;color:{_T["text_primary"]}">{lbl}</td>'
                f'<td style="padding:8px 12px;text-align:center;font-weight:700;color:{_c}">{_txt} ({v:+d})</td>'
                f'</tr>')
    st.markdown(
        f'<div style="border-radius:12px;overflow:hidden;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">'
        f'<th style="padding:8px 12px;text-align:left">{"Chỉ báo" if not is_en else "Indicator"}</th>'
        f'<th style="padding:8px 12px;text-align:center">{"Tín hiệu" if not is_en else "Signal"}</th>'
        f'</tr></thead><tbody>{_vr}</tbody></table></div>',
        unsafe_allow_html=True)

    # ── BIỂU ĐỒ GIÁ + BOLLINGER + ENTRY/SL/TP + ĐIỂM VÀO/RA ────────────
    st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Biểu đồ kỹ thuật & điểm vào/ra (backtest)" if not is_en else "Technical chart & backtest entries/exits"}</div>',
                unsafe_allow_html=True)
    _W = 180
    dd = d.tail(_W).reset_index(drop=True)
    _dt = pd.to_datetime(dd['Ngay'])
    sig_w = _tech_signal_series(d).tail(_W).reset_index(drop=True)
    chg = sig_w.diff().fillna(0)
    buy_idx = dd.index[chg == 1]
    sell_idx = dd.index[chg == -1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=_dt, y=dd['BB_up']*1000, mode='lines', line=dict(width=0),
                             showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=_dt, y=dd['BB_lo']*1000, mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor='rgba(8,145,178,0.08)',
                             name='Bollinger', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=_dt, y=dd['Close']*1000, mode='lines',
                             line=dict(color='#0F172A' if not _T.get('is_dark') else '#F1F5F9', width=1.6),
                             name=('Giá đóng cửa' if not is_en else 'Close'),
                             hovertemplate='%{x|%Y-%m-%d}<br>%{y:,.0f} đ<extra></extra>'))
    fig.add_trace(go.Scatter(x=_dt, y=dd['MA20']*1000, mode='lines',
                             line=dict(color='#8B5CF6', width=1.2, dash='dot'), name='MA20'))
    fig.add_trace(go.Scatter(x=_dt[buy_idx], y=dd['Close'][buy_idx]*1000, mode='markers',
                             marker=dict(symbol='triangle-up', size=11, color='#16A34A',
                                         line=dict(color='#fff', width=1)),
                             name=('Vào lệnh' if not is_en else 'Entry')))
    fig.add_trace(go.Scatter(x=_dt[sell_idx], y=dd['Close'][sell_idx]*1000, mode='markers',
                             marker=dict(symbol='triangle-down', size=11, color='#DC2626',
                                         line=dict(color='#fff', width=1)),
                             name=('Thoát lệnh' if not is_en else 'Exit')))
    for _lvl, _c, _nm in [(entry, _T['text_muted'], 'Entry'), (sl, '#DC2626', 'SL'), (tp, '#16A34A', 'TP')]:
        fig.add_hline(y=_lvl*1000, line=dict(color=_c, width=1, dash='dash'),
                      annotation_text=_nm, annotation_position='right',
                      annotation_font=dict(size=9, color=_c))
    fig.update_layout(
        height=440, margin=dict(l=46, r=20, t=20, b=40),
        paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
        font=dict(family='Inter', size=11, color=_T['text_primary']),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10)))
    _plotly_axes_style(fig, _T)
    fig.update_xaxes(tickformat='%m/%Y')
    st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    # ── PHÂN TÍCH KỸ THUẬT NÂNG CAO (S/R · Fib · Kênh · Sóng) ───────────
    _technical_analysis_section(df, ticker, _T, is_en)

    # ── BACKTEST ───────────────────────────────────────────────────────
    st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{"Backtest chiến lược kỹ thuật (long-only)" if not is_en else "Technical strategy backtest (long-only)"}</div>',
                unsafe_allow_html=True)
    nt = int(len(d) * train_ratio)
    bt = _backtest_longonly(d, nt)
    figb = go.Figure()
    figb.add_trace(go.Scatter(x=bt['dates'], y=(bt['eq_strat'] - 1) * 100, mode='lines',
                              line=dict(color='#0891B2', width=2),
                              name=('Chiến lược' if not is_en else 'Strategy'),
                              hovertemplate='%{x|%Y-%m-%d}<br>%{y:.1f}%<extra></extra>'))
    figb.add_trace(go.Scatter(x=bt['dates'], y=(bt['eq_bh'] - 1) * 100, mode='lines',
                              line=dict(color=_T['text_muted'], width=1.4, dash='dot'),
                              name=('Mua & Giữ' if not is_en else 'Buy & Hold')))
    figb.add_hline(y=0, line=dict(color=_T['text_muted'], width=0.8))
    figb.update_layout(
        height=340, margin=dict(l=46, r=20, t=20, b=40),
        paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
        font=dict(family='Inter', size=11, color=_T['text_primary']),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=-0.22, xanchor='center', x=0.5,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10)))
    _plotly_axes_style(figb, _T)
    figb.update_xaxes(tickformat='%m/%Y')
    figb.update_yaxes(title=dict(text=('Lợi nhuận tích lũy (%)' if not is_en else 'Cumulative return (%)'),
                                 font=dict(size=11, color=_T['text_secondary'])))
    st.plotly_chart(figb, use_container_width=True, config=_PLOTLY_CONFIG)

    _stats = [
        (('Lợi nhuận chiến lược' if not is_en else 'Strategy return'), f'{bt["total_strat"]:+.1f}%',
         _T['success'] if bt['total_strat'] >= 0 else _T['danger']),
        (('Mua & Giữ' if not is_en else 'Buy & Hold'), f'{bt["total_bh"]:+.1f}%',
         _T['success'] if bt['total_bh'] >= 0 else _T['danger']),
        (('Số lệnh' if not is_en else 'Trades'), f'{bt["n_trades"]}', _T['text_primary']),
        (('Tỷ lệ thắng' if not is_en else 'Win rate'), f'{bt["win_rate"]:.0f}%', _T['accent']),
        (('Sụt giảm tối đa' if not is_en else 'Max drawdown'), f'{bt["max_dd"]:.1f}%', _T['danger']),
        (('Sharpe (năm)' if not is_en else 'Sharpe (ann.)'), f'{bt["sharpe"]:.2f}', _T['accent']),
        (('Phí giao dịch' if not is_en else 'Fee drag'), f'-{bt["total_fee"]:.1f}%', _T['warning']),
    ]
    _sc = st.columns(len(_stats))
    for _col, (_l, _v, _c) in zip(_sc, _stats):
        _col.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-top:3px solid {_c};border-radius:10px;'
            f'padding:12px 14px;text-align:center;min-height:82px;word-break:break-word">'
            f'<div style="font-size:10px;color:{_T["text_muted"]};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;'
            f'line-height:1.35">{_l}</div>'
            f'<div style="font-size:clamp(14px, 1.5vw, 17px);font-weight:800;'
            f'color:{_c};line-height:1.2">{_v}</div></div>',
            unsafe_allow_html=True)

    _fee1 = bt['fee_side'] * 100      # %/chiều
    _fee2 = bt['fee_side'] * 200      # % khứ hồi
    if not is_en:
        _disc = (f'⚠️ Công cụ hỗ trợ phân tích học thuật, KHÔNG phải khuyến nghị '
                 f'đầu tư. Quy tắc vào lệnh: long khi MA5>MA20, giá>MA50, '
                 f'MACD>signal và RSI<75; SL/TP theo bội số ATR(14). Backtest ĐÃ '
                 f'TRỪ phí giao dịch {_fee1:.2f}%/chiều (khứ hồi ≈ {_fee2:.2f}%, '
                 f'sát phí + thuế HOSE) nhưng chưa tính trượt giá.')
    else:
        _disc = (f'⚠️ Academic analysis tool, NOT investment advice. Entry rule: '
                 f'long when MA5>MA20, price>MA50, MACD>signal and RSI<75; SL/TP '
                 f'as ATR(14) multiples. Backtest is NET of {_fee1:.2f}%/side fees '
                 f'(round-trip ≈ {_fee2:.2f}%, close to HOSE fee + tax) but ignores '
                 f'slippage.')
    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:14px;line-height:1.6">'
        f'{_disc}</div>', unsafe_allow_html=True)

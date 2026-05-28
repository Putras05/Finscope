import streamlit as st
import numpy as np

from core.i18n import t
from core.constants import CLR, ticker_sector
from core.themes import theme
from data.metrics import _ci95, _star, calc_metrics
import pandas as pd
from data.ichimoku import (
    add_ichimoku, classify_primary_trend, detect_tk_cross,
    classify_trading_signal, classify_chikou_confirmation,
    classify_future_kumo, aggregate_signals,
    _donchian_mid, SENKOU_N, _df_fingerprint,
)


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _df_fingerprint})
def _ichi_dashboard_summary(df: pd.DataFrame) -> tuple:
    """Tính toán Ichimoku card data 1 lần — cache theo df fingerprint.

    Returns: (ov_code, ov_label, score, prim, trd, chk, fut,
              close_now, c26, fa, fb)
    """
    if len(df) == 0:
        nan = float('nan')
        return ('na', 'Không đủ dữ liệu', 0,
                'na', 'hold', 'na', 'na',
                nan, nan, nan, nan)
    _df_ichi = add_ichimoku(df)
    _ichi_last = _df_ichi.iloc[-1]
    _close_now = float(_ichi_last['Close'])

    _prim_code, _ = classify_primary_trend(
        _close_now,
        float(_ichi_last['Kumo_top']) if not np.isnan(_ichi_last['Kumo_top']) else float('nan'),
        float(_ichi_last['Kumo_bot']) if not np.isnan(_ichi_last['Kumo_bot']) else float('nan'),
    )
    _tk_code, _, _ = detect_tk_cross(_df_ichi['Tenkan'], _df_ichi['Kijun'])
    _trd_code, _   = classify_trading_signal(_tk_code, _prim_code)
    _c26 = float(_df_ichi['Close'].iloc[-27]) if len(_df_ichi) >= 27 else float('nan')
    _chk_code, _   = classify_chikou_confirmation(_close_now, _c26)
    _ten_n = float(_ichi_last['Tenkan']); _kij_n = float(_ichi_last['Kijun'])
    _fa = (_ten_n + _kij_n) / 2.0
    _fb = float(_donchian_mid(df['High'], df['Low'], SENKOU_N).iloc[-1])
    _fut_code, _   = classify_future_kumo(_fa, _fb)

    _ov_code, _ov_label, _score = aggregate_signals(
        _prim_code, _trd_code, _chk_code, _fut_code)
    return (_ov_code, _ov_label, _score,
            _prim_code, _trd_code, _chk_code, _fut_code,
            _close_now, _c26, _fa, _fb)
from ui.components import (
    sparkline_svg, render_ai_insight,
    render_param_timeline, render_param_badge,
)
from charts.comparison import chart_price_candlestick, render_candlestick_info_bar
from charts.base import _PLOTLY_CONFIG


@st.fragment
def _candlestick_section(df, ticker, _T, _is_en_cmp):
    """Toggle/zoom chart KHÔNG rerun toàn page — chỉ rerun fragment này.

    Streamlit 1.32+ st.fragment isolates reruns — đổi SMA/Ichimoku/Timeframe
    không gọi lại render() cha (KPI, forecast cards). Cảm giác instant.
    """
    # Hàng 1: Timeframe radio (1D/1W/1M/3M) chiếm full row
    _tf_label = 'Khung thời gian' if not _is_en_cmp else 'Timeframe'
    _tf_options = ['1D', '1W', '1M', '3M']
    _selected_tf = st.radio(
        _tf_label,
        options=_tf_options,
        index=0,
        horizontal=True,
        key=f'cs_tf_{ticker}',
        label_visibility='collapsed',
    )

    # Hàng 2: 6 toggle compact dưới timeframe
    if True:
        # 6 toggle xếp ngang trong 6 cột — KHÔNG popover/expander để tránh
        # extra DOM layer + lag cảm nhận. Compact label 1-2 chữ + help text
        # full khi hover. Default SMA ON, 5 cái khác OFF (không recompute thừa).
        _ocols = st.columns(6, gap='small')
        with _ocols[0]:
            _show_sma = st.toggle(
                'SMA', value=True, key=f'cs_sma_{ticker}',
                help='SMA 5 (cam) & SMA 20 (tím)' if not _is_en_cmp
                     else 'SMA 5 (orange) & SMA 20 (purple)')
        with _ocols[1]:
            _show_ichimoku = st.toggle(
                'Ichi', value=False, key=f'cs_ichi_{ticker}',
                help='Ichimoku — Tenkan, Kijun, Mây Kumo, Chikou (cần ≥30 phiên)'
                     if not _is_en_cmp else 'Ichimoku — Tenkan, Kijun, Kumo, Chikou')
        with _ocols[2]:
            _show_bb = st.toggle(
                'BB', value=False, key=f'cs_bb_{ticker}',
                help='Bollinger Bands 20·2σ — biên trên/dưới ± 2 độ lệch chuẩn'
                     if not _is_en_cmp else 'Bollinger Bands 20·2σ')
        with _ocols[3]:
            _show_vwap = st.toggle(
                'VWAP', value=False, key=f'cs_vwap_{ticker}',
                help='VWAP 20 — giá bình quân gia quyền theo khối lượng (cuộn 20 phiên)'
                     if not _is_en_cmp else 'VWAP 20 — volume-weighted avg price')
        with _ocols[4]:
            _show_sr = st.toggle(
                'S/R', value=False, key=f'cs_sr_{ticker}',
                help='Hỗ trợ / Kháng cự — mức từ swing-high/low gom cụm 260 phiên gần nhất'
                     if not _is_en_cmp else 'Support/Resistance from last 260 sessions')
        with _ocols[5]:
            _show_psar = st.toggle(
                'PSAR', value=False, key=f'cs_psar_{ticker}',
                help='Parabolic SAR — chấm dừng lỗ Wilder (dưới giá ⇒ up, trên ⇒ down)'
                     if not _is_en_cmp else 'Parabolic SAR — Wilder stop-and-reverse')
    if _selected_tf is None:
        _selected_tf = '1D'

    if _show_ichimoku and _selected_tf == '3M':
        st.caption(
            'ℹ️ Khung 3M có ≤20 phiên — Ichimoku chỉ hiển thị một phần.'
            if not _is_en_cmp else
            'ℹ️ 3M timeframe has ≤20 bars — Ichimoku will be partial.'
        )

    _cmp_hint = (
        'Đơn vị giá: <b>nghìn đ</b> · Chọn khung thời gian <b>1D/1W/1M/3M</b> · '
        'Nến <span style="color:#10B981">xanh</span> = tăng, '
        '<span style="color:#EF4444">đỏ</span> = giảm · '
        'Đường <span style="color:#F59E0B">SMA 5</span> & '
        '<span style="color:#8B5CF6">SMA 20</span> · '
        'Kéo <b>thanh price bên phải</b> để zoom giá.'
        if not _is_en_cmp else
        'Price unit: <b>k VND</b> · Pick timeframe <b>1D/1W/1M/3M</b> · '
        '<span style="color:#10B981">Green</span> = up, '
        '<span style="color:#EF4444">red</span> = down · '
        '<span style="color:#F59E0B">SMA 5</span> & '
        '<span style="color:#8B5CF6">SMA 20</span> overlays · '
        'Drag <b>right price scale</b> to zoom price.'
    )
    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin:-4px 0 6px;'
        f'line-height:1.5">{_cmp_hint}</div>',
        unsafe_allow_html=True,
    )

    _info_bar = render_candlestick_info_bar(df, ticker, _selected_tf, _T)
    if _info_bar:
        st.markdown(_info_bar, unsafe_allow_html=True)

    try:
        fig_cmp = chart_price_candlestick(
            df, ticker, _T,
            interval=_selected_tf,
            show_sma=_show_sma,
            show_ichimoku=_show_ichimoku,
            show_bb=_show_bb,
            show_vwap=_show_vwap,
            show_sr=_show_sr,
            show_psar=_show_psar,
        )
        _candle_config = {
            **_PLOTLY_CONFIG,
            'scrollZoom': True,
            'doubleClick': 'reset',
        }
        # key= → Streamlit persist UI state (zoom/pan) khi toggle SMA/Ichimoku
        # key CỐ ĐỊNH theo ticker (KHÔNG đổi theo timeframe) — Streamlit/Plotly
        # giữ component thay vì destroy+remount → pan/zoom mượt hơn rất nhiều.
        st.plotly_chart(
            fig_cmp,
            use_container_width=True,
            config=_candle_config,
            key=f'candlestick_chart_{ticker}',
        )
    except Exception as _e:
        st.error(f'Chart error: {_e}')


def _align_two(res_a, res_b, df):
    """Căn 2 chuỗi dự báo test theo NGÀY chung + lấy giá thực tương ứng.

    Trả (y_true, pred_a, pred_b) trên các phiên cả 2 mô hình đều có dự báo,
    hoặc None nếu < 8 phiên chung (không đủ cho kiểm định)."""
    try:
        ia = pd.to_datetime(res_a['dates_te'])
        ib = pd.to_datetime(res_b['dates_te'])
        pa = pd.Series(np.asarray(res_a['pte'], float), index=ia)
        pb = pd.Series(np.asarray(res_b['pte'], float), index=ib)
        pa = pa[~pa.index.duplicated(keep='last')]
        pb = pb[~pb.index.duplicated(keep='last')]
        j = pd.concat([pa, pb], axis=1, join='inner').dropna()
        if len(j) < 8:
            return None
        cmap = pd.Series(df['Close'].values.astype(float),
                         index=pd.to_datetime(df['Ngay']))
        cmap = cmap[~cmap.index.duplicated(keep='last')]
        y = cmap.reindex(j.index).values
        fin = np.isfinite(y)
        if fin.sum() < 8:
            return None
        return y[fin], j.iloc[:, 0].values[fin], j.iloc[:, 1].values[fin]
    except Exception:
        return None


def _render_dm_section(all_models, df, _T, is_en=False):
    """Kiểm định Diebold–Mariano: mô hình tốt nhất có vượt trội ĐÁNG KỂ không?

    So mô hình MAPE thấp nhất với từng mô hình còn lại trên phiên test chung.
    Fail-safe: thiếu mẫu/lỗi → bỏ qua section, không sập trang."""
    from data.metrics import diebold_mariano
    valid = [m for m in all_models
             if np.isfinite(m['m'].get('MAPE', float('nan')))
             and len(np.asarray(m['res'].get('pte', []))) > 0]
    if len(valid) < 2:
        return
    best = valid[0]
    rows = []
    for other in valid[1:]:
        aligned = _align_two(best['res'], other['res'], df)
        if aligned is None:
            continue
        y, fb, fo = aligned
        dm = diebold_mariano(y, fb, fo, h=1, loss='MSE')
        if not dm.get('ok'):
            continue
        # dbar<0 nghĩa best có sai số bình phương NHỎ hơn → best tốt hơn
        better = dm['dbar'] < 0
        sig = dm['p'] < 0.05
        if sig and better:
            verdict = ('Tốt hơn đáng kể' if not is_en else 'Significantly better')
            vcol = '#16A34A'
        elif sig and not better:
            verdict = ('Kém hơn đáng kể' if not is_en else 'Significantly worse')
            vcol = '#DC2626'
        else:
            verdict = ('Khác biệt không ý nghĩa' if not is_en else 'Not significant')
            vcol = _T['text_muted']
        rows.append((other['name'], dm['dm'], dm['p'], dm['n'], verdict, vcol))

    # ── Đối chứng BƯỚC NGẪU NHIÊN (random walk): dự báo nạve = giá phiên trước.
    #    Câu hỏi học thuật cốt lõi: mô hình có THỰC SỰ hơn "ngày mai = hôm nay"? ──
    try:
        cser = pd.Series(df['Close'].values.astype(float),
                         index=pd.to_datetime(df['Ngay']))
        cser = cser[~cser.index.duplicated(keep='last')]
        bidx = pd.to_datetime(best['res']['dates_te'])
        fb = pd.Series(np.asarray(best['res']['pte'], float), index=bidx)
        fb = fb[~fb.index.duplicated(keep='last')]
        naive = cser.shift(1).reindex(fb.index)
        ytrue = cser.reindex(fb.index)
        j = pd.concat([ytrue, fb, naive], axis=1).dropna()
        if len(j) >= 8:
            dmn = diebold_mariano(j.iloc[:, 0].values, j.iloc[:, 1].values,
                                  j.iloc[:, 2].values, h=1, loss='MSE')
            if dmn.get('ok'):
                better = dmn['dbar'] < 0
                sig = dmn['p'] < 0.05
                if sig and better:
                    verdict = ('Tốt hơn đáng kể' if not is_en else 'Significantly better')
                    vcol = '#16A34A'
                elif sig and not better:
                    verdict = ('Kém hơn đáng kể' if not is_en else 'Significantly worse')
                    vcol = '#DC2626'
                else:
                    verdict = ('Khác biệt không ý nghĩa' if not is_en else 'Not significant')
                    vcol = _T['text_muted']
                rows.append(('Random Walk (naïve)', dmn['dm'], dmn['p'],
                             dmn['n'], verdict, vcol))
    except Exception:
        pass

    if not rows:
        return

    st.markdown("<div style='margin:16px 0 8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Kiểm định Diebold–Mariano" if not is_en else "Diebold–Mariano test"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]}">'
        f'{"— %s có vượt trội đáng kể?" % best["name"] if not is_en else "— is %s significantly better?" % best["name"]}'
        f'</span></div>', unsafe_allow_html=True)

    _hdr = (['Đối chứng', 'DM', 'p-value', 'n phiên', 'Kết luận (α=5%)'] if not is_en
            else ['Compared model', 'DM', 'p-value', 'n obs', 'Verdict (α=5%)'])
    _tr = ''
    for nm, dm, p, n, verdict, vcol in rows:
        _pstr = '< 0.001' if p < 0.001 else f'{p:.3f}'
        _tr += (
            f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
            f'<td style="padding:8px 12px;font-weight:600">{best["name"]} vs {nm}</td>'
            f'<td style="padding:8px 12px;font-family:monospace">{dm:+.3f}</td>'
            f'<td style="padding:8px 12px;font-family:monospace">{_pstr}</td>'
            f'<td style="padding:8px 12px;color:{_T["text_secondary"]}">{n}</td>'
            f'<td style="padding:8px 12px;font-weight:700;color:{vcol}">{verdict}</td>'
            f'</tr>')
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;-webkit-overflow-scrolling:touch;'
        f'border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">'
        + ''.join(f'<th style="padding:8px 12px;text-align:left">{h}</th>' for h in _hdr)
        + f'</tr></thead><tbody>{_tr}</tbody></table></div>',
        unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:8px;line-height:1.6">'
        f'{"H₀: hai mô hình có độ chính xác bằng nhau. DM âm ⇒ %s sai số nhỏ hơn. p<0.05 ⇒ bác bỏ H₀ (khác biệt có ý nghĩa thống kê). Hàm tổn thất: sai số bình phương (MSE), tầm dự báo 1 phiên, hiệu chỉnh mẫu nhỏ HLN." % best["name"] if not is_en else "H₀: equal forecast accuracy. Negative DM ⇒ %s has lower error. p<0.05 ⇒ reject H₀ (statistically significant). Loss: squared error (MSE), 1-step horizon, HLN small-sample correction." % best["name"]}'
        f'</div>', unsafe_allow_html=True)


def _render_news_sentiment_card(ticker, _T, is_en=False):
    """Thẻ TÂM LÝ TIN TỨC — đọc RSS thị trường, chấm sentiment có trọng số.

    Fail-safe tuyệt đối: mọi lỗi (mạng/parse) → caption nhẹ, KHÔNG sập trang.
    Dữ liệu đã được warm ngầm ở trang bìa nên thường hiện tức thì.
    """
    try:
        from data.news import news_sentiment
        ns = news_sentiment(ticker)
    except Exception:
        ns = None

    if not ns or not ns.get('ok'):
        _note = (ns or {}).get('note') if ns else None
        st.markdown(
            f'<div style="font-size:11px;color:{_T["text_muted"]};'
            f'margin:0 0 14px;padding:8px 14px;background:{_T["bg_card"]};'
            f'border:1px dashed {_T["border"]};border-radius:10px">'
            f'{"News sentiment temporarily unavailable" if is_en else "Tâm lý tin tức tạm thời chưa khả dụng"}'
            f'{f" · {_note}" if _note else ""}</div>',
            unsafe_allow_html=True)
        return

    _vote = int(ns.get('vote', 0))
    _mkt  = int(ns.get('market_score', 0))
    _tks  = int(ns.get('ticker_score', 0))
    _tkn  = int(ns.get('ticker_n', 0))
    _n    = int(ns.get('n', 0))

    if _vote > 0:
        _lbl = 'Bullish' if is_en else 'Tích cực'
        _col, _bg, _arr = '#16A34A', 'rgba(22,163,74,.10)', '▲'
    elif _vote < 0:
        _lbl = 'Bearish' if is_en else 'Tiêu cực'
        _col, _bg, _arr = '#DC2626', 'rgba(220,38,38,.10)', '▼'
    else:
        _lbl = 'Neutral' if is_en else 'Trung lập'
        _col, _bg, _arr = '#D97706', 'rgba(217,119,6,.10)', '─'

    # Tin nổi bật theo mã (nếu có) để hiển thị 1 dòng ngữ cảnh
    _items = ns.get('items', [])
    _tk_item = next((i for i in _items if i.get('is_ticker')), None)
    _head = (_tk_item or (_items[0] if _items else {})).get('title', '')
    _head = (_head[:90] + '…') if len(_head) > 90 else _head
    _src  = (_tk_item or (_items[0] if _items else {})).get('source', '')

    _ctx = (f'{ticker}: {_tkn} ' + ('related headlines' if is_en else 'tin theo mã')
            if _tkn >= 1 else ('market-wide' if is_en else 'tổng quan thị trường'))
    _title = 'NEWS SENTIMENT' if is_en else 'TÂM LÝ TIN TỨC THỊ TRƯỜNG'
    _feed_txt = (f'{_n} ' + ('headlines · RSS' if is_en else 'tin · nguồn RSS'))
    _influence = ('Feeds the trading-signal vote' if is_en
                  else 'Tham gia phiếu tín hiệu giao dịch')

    # SVG icon: tờ báo (newspaper)
    _svg = (
        f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
        f'stroke="{_col}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>'
        f'<path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8z"/></svg>')

    _head_html = (
        f'<div style="font-size:11.5px;color:{_T["text_secondary"]};margin-top:8px;'
        f'line-height:1.5">“{_head}” '
        f'<span style="color:{_T["text_muted"]};font-size:10px">— {_src}</span></div>'
        if _head else '')

    st.markdown(
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-left:4px solid {_col};border-radius:12px;padding:14px 20px;'
        f'margin:0 0 16px;box-shadow:{_T["shadow_md"]}">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'flex-wrap:wrap;gap:10px">'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'{_svg}'
        f'<span style="font-size:11px;font-weight:800;color:{_T["text_secondary"]};'
        f'letter-spacing:1px">{_title}</span>'
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{_bg};color:{_col};font-weight:800;font-size:13px;'
        f'padding:4px 14px;border-radius:20px">{_arr} {_lbl}</span>'
        f'</div>'
        f'<div style="font-size:10.5px;color:{_T["text_muted"]};text-align:right">'
        f'{_feed_txt} · {_ctx}</div>'
        f'</div>'
        f'<div style="display:flex;gap:22px;flex-wrap:wrap;margin-top:10px;'
        f'font-size:12px;color:{_T["text_secondary"]}">'
        f'<span>{"Market score" if is_en else "Điểm thị trường"}: '
        f'<b style="color:{"#16A34A" if _mkt>0 else ("#DC2626" if _mkt<0 else _T["text_secondary"])}">{_mkt:+d}</b></span>'
        f'<span>{ticker} {"score" if is_en else "điểm mã"}: '
        f'<b style="color:{"#16A34A" if _tks>0 else ("#DC2626" if _tks<0 else _T["text_secondary"])}">{_tks:+d}</b></span>'
        f'<span style="color:{_T["text_muted"]}">{_influence}</span>'
        f'</div>'
        f'{_head_html}'
        f'</div>', unsafe_allow_html=True)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    col_t = CLR[ticker]

    T    = df.iloc[-1]
    ngay = str(df['Ngay'].iloc[-1])

    # ── Ichimoku summary CACHED — tránh recompute mỗi rerun ──────────────
    (_ov_code, _ov_label, _score,
     _prim_code, _trd_code, _chk_code, _fut_code,
     _close_now, _c26, _fa, _fb) = _ichi_dashboard_summary(df)

    # Share Ichimoku summary sang chatbot qua session_state để AI trả lời đúng
    st.session_state['ichimoku_summary'] = {
        'label':        _ov_label,
        'code':         _ov_code,
        'score':        int(_score),
        'primary':      _prim_code,
        'trading':      _trd_code,
        'chikou':       _chk_code,
        'future_kumo':  _fut_code,
    }

    st.markdown(
        f'<div style="background:{_T["banner_bg"]};'
        f'border-radius:14px;padding:14px 24px 12px;margin-bottom:12px;'
        f'box-shadow:{_T["shadow_lg"]}">'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
        f'<span style="font-size:20px;font-weight:800;color:{_T["banner_text"]};letter-spacing:-.3px">'
        f'{t("dash.title", ticker=ticker)}</span>'
        f'<span style="font-size:11px;background:rgba(255,255,255,.15);color:{_T["banner_subtext"]};'
        f'padding:3px 10px;border-radius:20px;font-weight:600">{ticker_sector(ticker)}</span>'
        f'</div>'
        f'<p style="color:{_T["banner_subtext"]};margin:4px 0 0;font-size:11.5px">'
        f'<span class="live-dot"></span>'
        f'<span style="color:#10B981;font-weight:700;font-size:10px;letter-spacing:1px">{t("dash.live")}</span>'
        f' &nbsp;·&nbsp; {t("dash.updated")}: <b style="color:{_T["banner_text"]}">{ngay}</b>'
        f' &nbsp;·&nbsp; {t("dash.train_test_info", tr=int(train_ratio*100), te=100-int(train_ratio*100))}'
        f' &nbsp;·&nbsp; AR({ar_order}) · MLR · ARIMA</p>'
        f'</div>', unsafe_allow_html=True)

    ret_color   = '#1B6B2F' if T['Return'] >= 0 else '#C62828'
    ret_arr     = '▲' if T['Return'] >= 0 else '▼'
    vol_ratio_v = float(T['Volume_ratio'])
    vol_color   = '#C62828' if vol_ratio_v > 2 else ('#F9A825' if vol_ratio_v > 1.5 else '#2E7D32')
    sp30_svg    = sparkline_svg(df['Close'].values[-30:] * 1000, col_t)

    _CARD_STYLE = (
        f'background:{_T["bg_card"]};border-radius:14px;padding:18px 14px;'
        f'box-shadow:{_T["shadow_md"]};border:1px solid {_T["border"]};'
        f'min-height:160px;box-sizing:border-box;'
    )
    c_hero, c_rsi, c_ma, c_vol = st.columns([4, 2, 2, 2])
    with c_hero:
        st.markdown(
            f'<div style="{_CARD_STYLE}border-top:5px solid {col_t};padding:18px 20px;">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_secondary"]};letter-spacing:.7px;'
            f'text-transform:uppercase;margin-bottom:8px">'
            f'{t("dash.latest_price")} &nbsp;·&nbsp; <b>{ngay}</b> '
            f'<span style="font-size:9px;color:#10B981;margin-left:4px">● {t("common.settled")}</span></div>'
            f'<div style="display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap">'
            f'<div style="font-size:36px;font-weight:800;color:{_T["text_primary"]};line-height:1">'
            f'{T["Close"]*1000:,.0f} <span style="font-size:16px;color:{_T["text_muted"]}">đ</span></div>'
            f'<div style="display:inline-block;font-size:14px;font-weight:700;padding:5px 14px;'
            f'border-radius:20px;color:{ret_color};background:{_T["success_bg"] if T["Return"]>=0 else _T["danger_bg"]}">'
            f'{ret_arr} {abs(T["Return"]):.2f}%</div>'
            f'</div>'
            f'<div style="font-size:9px;color:{_T["text_muted"]};margin:8px 0 4px">{t("dash.last_30")}</div>'
            f'{sp30_svg}'
            f'</div>', unsafe_allow_html=True)
    with c_rsi:
        # Màu theo chiều consensus
        if   _ov_code in ('strong_bull', 'mild_bull'):  _ichi_col = '#2E7D32'
        elif _ov_code in ('strong_bear', 'mild_bear'):  _ichi_col = '#C62828'
        else:                                            _ichi_col = '#F9A825'

        # Nhãn hiển thị — dùng i18n (signal.overall.* đã include arrow)
        _ov_title_full = t(f'signal.overall.{_ov_code}')
        _ov_arrows_map = {
            'strong_bull': '▲▲', 'mild_bull': '▲',
            'neutral':     '=',
            'mild_bear':   '▼',  'strong_bear': '▼▼',
        }
        _ov_arrow = _ov_arrows_map.get(_ov_code, '=')
        _ov_title = _ov_title_full.replace(_ov_arrow, '').strip()

        # Mini-icon cho 4 tầng
        def _mini_icon(code):
            if 'counter' in code: return '⇅'
            if any(x in code for x in ('bull', 'buy')):  return '▲'
            if any(x in code for x in ('bear', 'sell')): return '▼'
            return '─'

        _mini_p = _mini_icon(_prim_code)
        _mini_t = _mini_icon(_trd_code)
        _mini_c = _mini_icon(_chk_code)
        _mini_f = _mini_icon(_fut_code)

        _bar_n   = min(abs(_score), 5)
        _score_s = f'+{_score}' if _score > 0 else str(_score)

        # Score bar bằng SVG: 5 ô vuông nhỏ, ô nào "on" thì đổ màu
        _cell_w, _cell_h, _cell_gap = 22, 8, 4
        _bar_w = 5 * _cell_w + 4 * _cell_gap
        _cells_svg = ''
        for _i in range(5):
            _x = _i * (_cell_w + _cell_gap)
            _fill = _ichi_col if _i < _bar_n else _T['bg_elevated']
            _cells_svg += (
                f'<rect x="{_x}" y="0" width="{_cell_w}" height="{_cell_h}" '
                f'rx="2" fill="{_fill}"/>'
            )
        _bar_svg = (
            f'<svg width="{_bar_w}" height="{_cell_h}" '
            f'style="display:block;margin:4px 0">{_cells_svg}</svg>'
        )

        st.markdown(
            f'<div style="{_CARD_STYLE}border-top:5px solid {_ichi_col}">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_secondary"]};letter-spacing:.7px;'
            f'text-transform:uppercase;margin-bottom:6px">{t("dash.ichi_signal")}</div>'
            f'<div style="display:flex;align-items:baseline;gap:8px">'
            f'<div style="font-size:26px;font-weight:800;color:{_ichi_col};line-height:1">'
            f'{_ov_arrow} {_score_s}</div>'
            f'</div>'
            f'<div style="font-size:13px;font-weight:700;color:{_ichi_col};margin-top:4px">{_ov_title}</div>'
            f'<div style="font-size:10px;color:{_T["text_muted"]};margin-top:8px">Score {_score_s}/5</div>'
            f'{_bar_svg}'
            f'<div style="font-size:13px;color:{_T["text_secondary"]};margin-top:6px;letter-spacing:4px">'
            f'{_mini_p}&nbsp;{_mini_t}&nbsp;{_mini_c}&nbsp;{_mini_f}'
            f'</div>'
            f'<div style="font-size:9px;color:{_T["text_muted"]};margin-top:2px">'
            f'Trend · TK · Chikou · Future</div>'
            f'</div>', unsafe_allow_html=True)
    with c_ma:
        # ── Card BIẾN ĐỘNG 30 NGÀY (Volatility) ──────────────────────
        _ret30 = df['Return'].dropna().tail(30)
        if len(_ret30) >= 10:
            _vol_30d        = float(_ret30.std())
            _vol_annualized = _vol_30d * (252 ** 0.5)
        else:
            _vol_30d        = float('nan')
            _vol_annualized = float('nan')

        if   np.isnan(_vol_30d): _risk_col, _risk_key = '#94A3B8', 'dash.risk_na'
        elif _vol_30d < 1.5:     _risk_col, _risk_key = '#2E7D32', 'dash.risk_low'
        elif _vol_30d < 2.5:     _risk_col, _risk_key = '#F9A825', 'dash.risk_medium'
        else:                    _risk_col, _risk_key = '#C62828', 'dash.risk_high'
        _risk_label = t(_risk_key)
        _vol_str    = f'{_vol_30d:.2f}%' if not np.isnan(_vol_30d) else 'N/A'
        _ann_str    = f'{_vol_annualized:.1f}%' if not np.isnan(_vol_annualized) else 'N/A'

        st.markdown(
            f'<div style="{_CARD_STYLE}border-top:5px solid {_risk_col}">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_secondary"]};letter-spacing:.7px;'
            f'text-transform:uppercase;margin-bottom:6px">{t("dash.volatility_title")}</div>'
            f'<div style="font-size:28px;font-weight:800;color:{_risk_col};line-height:1">{_vol_str}</div>'
            f'<div style="font-size:11px;color:{_T["text_secondary"]};margin-top:10px">'
            f'{t("dash.vol_annualized")}: <b>{_ann_str}</b></div>'
            f'<div style="display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;'
            f'border-radius:12px;color:{_risk_col};'
            f'background:{_T["success_bg"] if _risk_col=="#2E7D32" else (_T["warning_bg"] if _risk_col=="#F9A825" else _T["danger_bg"])};'
            f'margin-top:8px">{t("dash.risk_label")}: {_risk_label}</div>'
            f'</div>', unsafe_allow_html=True)

    with c_vol:
        if vol_ratio_v > 2.5:   vol_label = t('dash.vol_very_high')
        elif vol_ratio_v > 1.5: vol_label = t('dash.vol_high')
        elif vol_ratio_v < 0.5: vol_label = t('dash.vol_low')
        else:                    vol_label = t('dash.vol_normal')
        st.markdown(
            f'<div style="{_CARD_STYLE}border-top:5px solid {vol_color}">'
            f'<div style="font-size:10px;font-weight:700;color:{_T["text_secondary"]};letter-spacing:.7px;'
            f'text-transform:uppercase;margin-bottom:6px">{t("dash.volume_title").upper()}</div>'
            f'<div style="font-size:28px;font-weight:800;color:{_T["text_primary"]};line-height:1">'
            f'{T["Volume"]/1e6:.2f}M</div>'
            f'<div style="display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;'
            f'border-radius:12px;color:{vol_color};'
            f'background:{_T["danger_bg"] if vol_ratio_v>2 else _T["warning_bg"] if vol_ratio_v>1.5 else _T["success_bg"]};'
            f'margin-top:14px">{vol_label}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin:18px 0 12px'></div>", unsafe_allow_html=True)

    import datetime as _dt
    _last_date = df['Ngay'].iloc[-1]
    if isinstance(_last_date, str):
        _last_date = _dt.datetime.strptime(_last_date, '%Y-%m-%d').date()
    _next_date = _last_date
    while True:
        _next_date += _dt.timedelta(days=1)
        if _next_date.weekday() < 5:
            break

    _hdr_title = t('dash.forecast_1')
    if ar_order == 1:
        _sess_desc = f'{t("dash.based_on_close")} {_last_date}'
    else:
        _first_date = df['Ngay'].iloc[-ar_order]
        if isinstance(_first_date, str):
            _first_date = _dt.datetime.strptime(_first_date, '%Y-%m-%d').date()
        _sess_desc = t('dash.based_on_close_range',
                       p=ar_order, d0=_first_date, d1=_last_date)
    _model_spec_label = t('dash.model_spec', p=ar_order)

    st.markdown(
        f'<div class="sec-hdr">{_hdr_title} '
        f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};'
        f'margin-left:8px">'
        f'<b style="color:{_T["accent"]}">{_next_date.strftime("%Y-%m-%d")}</b> '
        f'({_sess_desc})</span></div>',
        unsafe_allow_html=True)

    _badges_html  = render_param_badge(ar_order, _T)
    _timeline_svg = render_param_timeline(ar_order, _T)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;'
        f'margin:-4px 0 14px;padding:10px 16px;background:{_T["bg_card"]};'
        f'border:1px solid {_T["border"]};border-radius:10px">'
        f'<div style="flex:0 0 auto">{_badges_html}</div>'
        f'<div style="flex:0 0 auto">{_timeline_svg}</div>'
        f'<div style="flex:1;min-width:200px;font-size:11px;color:{_T["text_muted"]};'
        f'font-family:monospace;letter-spacing:0.3px">{_model_spec_label}</div>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Tính ĐỦ 7 mô hình 1 lần (cache đã warm ở app.py → tức thì) ──────
    _is_en_d = st.session_state.get('lang', 'VI') == 'EN'
    with st.spinner('Đang tổng hợp các mô hình...' if not _is_en_d
                    else 'Aggregating models...'):
        from models.advanced import run_sarima, run_ets, run_garch, run_sarimax
        from models.ml import run_gbr
        _rs = run_sarima(ticker, train_ratio, p=ar_order, date_from=date_from, date_to=date_to)
        _re = run_ets(ticker, train_ratio, p=ar_order, date_from=date_from, date_to=date_to)
        _rg = run_garch(ticker, train_ratio, p=ar_order, date_from=date_from, date_to=date_to)
        _rx = run_sarimax(ticker, train_ratio, p=ar_order, date_from=date_from, date_to=date_to)
        try:
            _rgb = run_gbr(ticker, train_ratio, p=ar_order, date_from=date_from, date_to=date_to)
        except Exception:
            _rgb = None

    def _sm(res):
        yte = np.asarray(res['yte'], float); pte = np.asarray(res['pte'], float)
        fin = np.isfinite(pte) & np.isfinite(yte)
        if fin.sum() < 3:
            return dict(MAPE=float('nan'), RMSE=float('nan'), MAE=float('nan'), R2adj=float('nan'))
        return calc_metrics(yte[fin], pte[fin], k=2)

    def _ci_lin(res):
        c = _ci95(res['yte'], res['pte']); n = float(res['next_pred'])
        return n - c, n + c

    _MCLR = {'AR': '#1565C0', 'MLR': '#6A1B9A', 'ARIMA': '#0891B2',
             'SARIMA': '#0D9488', 'Holt-Winters': '#EA580C',
             'GARCH': '#DC2626', 'SARIMAX': '#4338CA', 'GBR': '#7C3AED',
             'Ensemble': '#0F766E'}
    _raw7 = [
        (f'AR({ar_order})', 'AR',  r1, m1, _ci_lin(r1)),
        ('MLR', 'MLR',              r2, m2, _ci_lin(r2)),
        ('ARIMA', 'ARIMA',          r3, m3, (r3.get('next_lower'), r3.get('next_upper'))),
        ('SARIMA', 'SARIMA',        _rs, _sm(_rs), (_rs.get('next_lower'), _rs.get('next_upper'))),
        ('Holt-Winters', 'Holt-Winters', _re, _sm(_re), (_re.get('next_lower'), _re.get('next_upper'))),
        ('GARCH', 'GARCH',          _rg, _sm(_rg), (_rg.get('next_lower'), _rg.get('next_upper'))),
        ('SARIMAX', 'SARIMAX',      _rx, _sm(_rx), (_rx.get('next_lower'), _rx.get('next_upper'))),
    ]
    if _rgb is not None and np.isfinite(_rgb.get('next_pred', float('nan'))):
        _raw7.append(('Gradient Boosting', 'GBR', _rgb, _sm(_rgb),
                      (_rgb.get('next_lower'), _rgb.get('next_upper'))))
    _all7 = []
    for _disp, _base, _res, _mm, _ci in _raw7:
        _np = float(_res.get('next_pred', float('nan')))
        if not np.isfinite(_np):
            continue
        _all7.append(dict(name=_disp, base=_base, res=_res, m=_mm, npred=_np,
                          ci=_ci, color=_MCLR.get(_base, '#1565C0')))

    # ── MÔ HÌNH KẾT HỢP (Ensemble) — gộp tất cả theo trọng số 1/MAPE ──────
    from models.ensemble import build_ensemble
    _ens = build_ensemble(
        [{'name': d['name'], 'res': d['res'], 'mape': d['m'].get('MAPE', float('nan'))}
         for d in _all7], df)
    if _ens is not None:
        _ens_m = _sm(_ens)
        _all7.append(dict(name='FinScope Ensemble', base='Ensemble', res=_ens,
                          m=_ens_m, npred=float(_ens['next_pred']),
                          ci=(_ens.get('next_lower'), _ens.get('next_upper')),
                          color=_MCLR['Ensemble']))
    _all7.sort(key=lambda dct: dct['m'].get('MAPE', float('nan'))
               if np.isfinite(dct['m'].get('MAPE', float('nan'))) else 1e9)

    # ── BANNER DỰ BÁO KẾT HỢP (FinScope Ensemble) — nổi bật ─────────────
    if _ens is not None and np.isfinite(_ens.get('next_pred', float('nan'))):
        _en = float(_ens['next_pred']); _ecur = float(T['Close'])
        _echg = (_en - _ecur) / _ecur * 100 if _ecur else 0
        _ec = '#16A34A' if _echg >= 0 else '#FCA5A5'
        _earr = '▲' if _echg >= 0 else '▼'
        _elo, _ehi = _ens.get('next_lower'), _ens.get('next_upper')
        _ci_e = (f'[{_elo*1000:,.0f} – {_ehi*1000:,.0f}] đ'
                 if (_elo is not None and np.isfinite(_elo)) else '—')
        _emape = _ens_m.get('MAPE', float('nan'))
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0F766E 0%,#0891B2 100%);'
            f'border-radius:14px;padding:16px 24px;margin-bottom:14px;color:#fff;'
            f'box-shadow:0 4px 16px rgba(15,118,110,.35)">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">'
            f'<div>'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;opacity:.92;'
            f'display:flex;align-items:center;gap:7px">'
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
            f'<polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>'
            f'{"Dự báo Kết hợp · FinScope Ensemble" if not _is_en_d else "Combined Forecast · FinScope Ensemble"}</div>'
            f'<div style="font-size:30px;font-weight:800;line-height:1.1;margin-top:4px">'
            f'{_en*1000:,.0f} <span style="font-size:15px;opacity:.85">đ</span> '
            f'<span style="font-size:16px;color:{_ec}">{_earr} {abs(_echg):.2f}%</span></div>'
            f'</div>'
            f'<div style="text-align:right;font-size:12px;opacity:.92;line-height:1.7">'
            f'{"Gộp" if not _is_en_d else "Combines"} <b>{_ens.get("n_members","?")}</b> {"mô hình · trọng số ∝ 1/MAPE" if not _is_en_d else "models · weights ∝ 1/MAPE"}<br>'
            f'{"KTC 95%" if not _is_en_d else "95% CI"}: <b>{_ci_e}</b><br>'
            f'MAPE test: <b>{_emape:.2f}%</b></div>'
            f'</div></div>', unsafe_allow_html=True)

    # ── 3 Ô HERO = 3 MÔ HÌNH TỐT NHẤT (MAPE thấp nhất) ─────────────────
    last30  = df['Close'].values[-30:] * 1000
    _medal_lbl = [t('dash.best_badge'), t('dash.second_badge'), t('dash.third_badge')]
    _top3 = _all7[:3]
    _hcols = st.columns(len(_top3) if _top3 else 1)
    _sp_bg = 'rgba(255,255,255,0.12)' if st.session_state.get('theme_mode', 'light') == 'dark' else 'rgba(255,255,255,0.65)'
    for _i, (mcol, md) in enumerate(zip(_hcols, _top3)):
        lbl = md['name']; npred = md['npred']; mm = md['m']; col_m = md['color']
        _lo, _hi = md['ci']
        npred_d  = npred * 1000
        chg      = npred_d - T['Close'] * 1000
        pct      = chg / (T['Close'] * 1000) * 100 if T['Close'] else 0
        arr      = '▲' if chg >= 0 else '▼'
        chg_col  = '#1B6B2F' if chg >= 0 else '#C62828'
        chg_bg   = 'rgba(27,107,47,.12)' if chg >= 0 else 'rgba(198,40,40,.12)'
        rng_lo   = min(last30); rng_hi = max(last30)
        sp_svg   = sparkline_svg(last30, col_m)
        _stars   = _star(mm['MAPE']) if np.isfinite(mm.get('MAPE', float('nan'))) else ''
        if _i == 0:
            best_bd = (f'<div style="display:inline-block;margin-top:10px;'
                       f'background:linear-gradient(135deg,#F9A825 0%,#FFC107 100%);'
                       f'color:#1A2A4A;font-size:10px;font-weight:800;padding:4px 12px;'
                       f'border-radius:6px;letter-spacing:.5px;box-shadow:0 2px 8px rgba(249,168,37,0.4)">'
                       f'{_medal_lbl[0]} {_stars}</div>')
        elif _i == 1:
            best_bd = (f'<div style="display:inline-block;margin-top:10px;'
                       f'background:rgba(148,163,184,0.18);color:{_T["text_secondary"]};'
                       f'font-size:10px;font-weight:800;padding:4px 12px;border-radius:6px;letter-spacing:.5px">'
                       f'{_medal_lbl[1]} {_stars}</div>')
        else:
            best_bd = (f'<div style="display:inline-block;margin-top:10px;'
                       f'background:rgba(180,83,9,0.15);color:{_T["warning"]};'
                       f'font-size:10px;font-weight:800;padding:4px 12px;border-radius:6px;letter-spacing:.5px">'
                       f'{_medal_lbl[2]} {_stars}</div>')
        _border = f'border:2px solid {_T["warning"]};' if _i == 0 else f'border:1px solid {_T["border"]};'
        _ci_html = ''
        if _lo is not None and _hi is not None and np.isfinite(_lo) and np.isfinite(_hi):
            _ci_html = (f'<div style="font-size:10px;color:{_T["text_muted"]};margin-top:6px">'
                        f'{t("dash.ci95")}: <b style="color:{chg_col}">'
                        f'[{_lo*1000:,.0f} – {_hi*1000:,.0f}]</b></div>')
        with mcol:
            st.markdown(
                f'<div style="background:{_T["bg_card"]};border-radius:16px;padding:20px 18px;'
                f'border-top:5px solid {col_m};{_border}position:relative;overflow:hidden">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">'
                f'<div style="font-size:11px;font-weight:600;color:{_T["text_secondary"]};letter-spacing:1.2px;'
                f'text-transform:uppercase">{t("col.model")}</div>'
                f'<div style="font-size:10px;color:{_T["text_muted"]};font-weight:500">MAPE test {mm["MAPE"]:.2f}%</div>'
                f'</div>'
                f'<div style="font-size:26px;font-weight:800;color:{col_m};letter-spacing:-.5px">{lbl}</div>'
                f'<div style="font-size:34px;font-weight:800;color:{_T["text_primary"]};line-height:1;margin:10px 0 0">'
                f'{npred_d:,.0f} <span style="font-size:16px;color:{_T["text_secondary"]};font-weight:500">đ</span></div>'
                f'<div style="display:inline-block;background:{chg_bg};color:{chg_col};font-size:13px;'
                f'font-weight:700;padding:5px 14px;border-radius:20px;margin:8px 0 0">'
                f'{arr} {abs(chg):,.0f} đ ({pct:+.2f}%)</div>'
                f'<div style="margin:12px 0 0;padding:10px;background:{_sp_bg};border-radius:10px">{sp_svg}</div>'
                f'<div style="display:flex;justify-content:space-between;margin-top:8px;'
                f'font-size:10.5px;color:{_T["text_secondary"]}">'
                f'<span>{t("dash.last_30")}</span>'
                f'<span style="font-weight:600">{"Range" if _is_en_d else "Biên"}: {rng_lo:,.0f}–{rng_hi:,.0f}</span></div>'
                f'{_ci_html}{best_bd}'
                f'</div>', unsafe_allow_html=True)

    # ── Labels i18n 4 tầng Ichimoku cho AI Insight ──────────────────────
    _prim_lbl = t(f'ichi.primary.{_prim_code}')
    _trd_lbl  = t(f'ichi.trading.{_trd_code}')

    if not (np.isnan(_close_now) or np.isnan(_c26) or _c26 == 0):
        _chk_pct2 = (_close_now - _c26) / _c26 * 100.0
        _chk_lbl  = t(f'ichi.chikou.{_chk_code}', pct=f'{_chk_pct2:+.2f}')
    else:
        _chk_lbl = t('ichi.chikou.na')

    if not (np.isnan(_fa) or np.isnan(_fb)):
        _mid2     = (_fa + _fb) / 2.0
        _fut_pct2 = (_fa - _fb) / _mid2 * 100.0 if _mid2 != 0 else 0.0
        _fut_lbl  = t(f'ichi.future.{_fut_code}', pct=f'{_fut_pct2:+.2f}')
    else:
        _fut_lbl = t('ichi.future.na')

    # Dự báo best model = mô hình MAPE thấp nhất trong 7 (đầu danh sách _all7)
    _best = _all7[0] if _all7 else dict(name='ARIMA', m=m3, npred=r3['next_pred'])
    _best_model_name = _best['name']
    _best_metrics    = _best['m']
    _best_next_pred  = _best['npred']
    _best_pct        = (_best_next_pred - _close_now) / _close_now * 100.0 if _close_now else 0.0

    st.markdown(render_ai_insight(
        ticker=ticker,
        overall_code=_ov_code,
        overall_label=t(f'ichi.overall.{_ov_code}'),
        score=_score,
        primary_label=_prim_lbl,
        trading_label=_trd_lbl,
        chikou_label=_chk_lbl,
        future_label=_fut_lbl,
        best_model=_best_model_name,
        best_mape=_best_metrics['MAPE'],
        best_r2adj=_best_metrics['R2adj'],
        next_price=_best_next_pred,
        next_pct=_best_pct,
        next_date=_next_date.strftime('%Y-%m-%d'),
        T=_T,
    ), unsafe_allow_html=True)

    st.markdown("<div style='margin:8px 0 12px'></div>", unsafe_allow_html=True)

    # ── TÂM LÝ TIN TỨC THỊ TRƯỜNG (sentiment) — bổ trợ tín hiệu, fail-safe ──
    _render_news_sentiment_card(ticker, _T, _is_en_d)

    st.markdown(f'<div class="sec-hdr">{t("dash.comparison")}</div>', unsafe_allow_html=True)
    _is_en_cmp = st.session_state.get('lang', 'VI') == 'EN'

    # Chart trong fragment → toggle/timeframe đổi KHÔNG rerun KPI/forecast
    _candlestick_section(df, ticker, _T, _is_en_cmp)

    # ── DỰ BÁO NHIỀU PHIÊN TỚI (multi-step ARIMA + dải tin cậy loe rộng) ──
    _H = 10
    try:
        from models.arima import arima_future
        from charts.arima_diag import chart_future_fan
        _fr = arima_future(ticker, p=ar_order, H=_H, date_from=date_from, date_to=date_to)
    except Exception:
        _fr = None
    if _fr is not None:
        st.markdown("<div style='margin:14px 0 6px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="sec-hdr">'
            f'{f"Dự báo {_H} phiên tới" if not _is_en_cmp else f"Next {_H} sessions forecast"}'
            f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]}">'
            f'ARIMA{tuple(_fr["order"])} · {"dải tin cậy loe rộng theo thời gian" if not _is_en_cmp else "intervals widen with horizon"}</span></div>',
            unsafe_allow_html=True)
        try:
            _figf = chart_future_fan(_fr, ticker, T=_T, is_en=_is_en_cmp)
            st.plotly_chart(_figf, use_container_width=True, config={
                **_PLOTLY_CONFIG, 'toImageButtonOptions': {
                    **_PLOTLY_CONFIG['toImageButtonOptions'],
                    'filename': f'{ticker}_forecast_{_H}d'}})
            _mfin = _fr['mean'][-1]
            _chgH = (_mfin - _fr['last_close']) / _fr['last_close'] * 100 if _fr['last_close'] else 0
            _cH = _T['success'] if _chgH >= 0 else _T['danger']
            st.markdown(
                f'<div style="font-size:11.5px;color:{_T["text_muted"]};margin-top:2px">'
                f'{"Sau" if not _is_en_cmp else "After"} {_H} {"phiên" if not _is_en_cmp else "sessions"} '
                f'({_fr["future_dates"][-1]}): <b style="color:{_cH}">{_mfin*1000:,.0f} đ '
                f'({_chgH:+.2f}%)</b> · KTC 95% [{_fr["lo95"][-1]*1000:,.0f} – {_fr["hi95"][-1]*1000:,.0f}]. '
                f'{"Lưu ý: dự báo nhiều bước có độ bất định tăng nhanh." if not _is_en_cmp else "Note: multi-step uncertainty grows quickly."}'
                f'</div>', unsafe_allow_html=True)
        except Exception as _ef:
            st.caption(f'⚠ {_ef}')

    # ── DỰ BÁO ĐA MÔ HÌNH — dùng lại _all7 (đã tính + sắp xếp MAPE ở trên) ──
    _last_c = float(T['Close'])

    st.markdown("<div style='margin:12px 0 8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-hdr">'
        f'{"Dự báo đa mô hình — phiên kế tiếp" if not _is_en_d else "Multi-model next-session forecast"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]}">'
        f'({len(_all7)} {"mô hình" if not _is_en_d else "models"})</span></div>',
        unsafe_allow_html=True)
    _frows = ''
    for _md in _all7:
        _nm = _md['name']; _npd = _md['npred']; _mm = _md['m']; _lo, _hi = _md['ci']
        _chg = (_npd - _last_c) / _last_c * 100 if _last_c else 0
        _cc = _T['success'] if _chg >= 0 else _T['danger']
        _arr = '▲' if _chg >= 0 else '▼'
        _ci_s = (f'[{_lo*1000:,.0f} – {_hi*1000:,.0f}]'
                 if (_lo is not None and _hi is not None and np.isfinite(_lo) and np.isfinite(_hi))
                 else '—')
        _mp = _mm.get('MAPE', float('nan'))
        _mpc = _T['success'] if _mp < 1.5 else (_T['warning'] if _mp < 2 else _T['danger'])
        _frows += (
            f'<tr style="color:{_T["text_primary"]};border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:9px 12px;font-weight:700">{_nm}</td>'
            f'<td style="padding:9px 12px;font-weight:700">{_npd*1000:,.0f} đ</td>'
            f'<td style="padding:9px 12px;color:{_cc};font-weight:700">{_arr} {abs(_chg):.2f}%</td>'
            f'<td style="padding:9px 12px;font-size:12px;color:{_T["text_secondary"]}">{_ci_s}</td>'
            f'<td style="padding:9px 12px;color:{_mpc};font-weight:700">{_mp:.2f}%</td>'
            f'</tr>')
    _fh = (['Mô hình', 'Dự báo (đ)', 'Δ vs hiện tại', 'KTC 95% (đ)', 'MAPE test'] if not _is_en_d
           else ['Model', 'Forecast (đ)', 'Δ vs current', '95% CI (đ)', 'Test MAPE'])
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">'
        + ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _fh)
        + f'</tr></thead><tbody>{_frows}</tbody></table></div>',
        unsafe_allow_html=True)

    # ── Xếp hạng độ chính xác (toàn bộ mô hình theo MAPE test) ───────────
    st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sec-hdr">{t("dash.rank")}</div>', unsafe_allow_html=True)
    _rank_list = [(_md['name'], _md['m']) for _md in _all7
                  if np.isfinite(_md['m'].get('MAPE', float('nan')))]
    _rank_list.sort(key=lambda x: x[1]['MAPE'])
    _max_mape = max([mm['MAPE'] for _, mm in _rank_list] + [1e-9])
    _medal_html = [
        '<span style="background:#F9A825;color:#1A2A4A;font-weight:800;padding:4px 10px;border-radius:8px;font-size:12px">1ST</span>',
        '<span style="background:#94A3B8;color:#fff;font-weight:800;padding:4px 10px;border-radius:8px;font-size:12px">2ND</span>',
        '<span style="background:#CD7F32;color:#fff;font-weight:800;padding:4px 10px;border-radius:8px;font-size:12px">3RD</span>',
    ]
    _rows_html = ''
    for _r, (_mn, _mm) in enumerate(_rank_list):
        _bg = (f'background:{_T["warning_bg"]}' if _r == 0
               else (f'background:{_T["bg_elevated"]}' if _r == 1 else f'background:{_T["bg_card"]}'))
        _badge = _medal_html[_r] if _r < 3 else f'<span style="color:{_T["text_muted"]};font-weight:700">{_r+1}</span>'
        _stars_td = _star(_mm['MAPE'])
        _mape_col = _T['success'] if _mm['MAPE'] < 1.5 else (_T['warning'] if _mm['MAPE'] < 2 else _T['danger'])
        _bar_pct  = 100 - (_mm['MAPE'] / _max_mape * 75)
        _rows_html += (
            f'<tr style="{_bg};color:{_T["text_primary"]};border-top:1px solid {_T["divider"]}">'
            f'<td style="padding:10px 12px;font-size:16px">{_badge}</td>'
            f'<td style="padding:10px 12px;font-weight:700">{_mn}</td>'
            f'<td style="padding:10px 12px;color:{_mape_col};font-weight:700">'
            f'{_mm["MAPE"]:.2f}% {_stars_td}</td>'
            f'<td style="padding:10px 14px;min-width:120px">'
            f'<div style="background:{_T["border"]};border-radius:4px;height:6px;overflow:hidden">'
            f'<div style="background:{_mape_col};width:{_bar_pct:.0f}%;height:100%"></div></div></td>'
            f'<td style="padding:10px 12px">{_mm["RMSE"]:.4f}</td>'
            f'<td style="padding:10px 12px">{_mm["MAE"]:.4f}</td>'
            f'<td style="padding:10px 12px;color:{_T["success"] if _mm["R2adj"]>0.95 else _T["text_secondary"]}">'
            f'{_mm["R2adj"]:.4f}</td>'
            f'</tr>'
        )
    st.markdown(
        f'<div style="border-radius:12px;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid {_T["border"]}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
        f'<thead><tr style="background:{_T["accent"]};color:#fff">'
        f'<th style="padding:10px 12px;text-align:left">{t("col.rank")}</th>'
        f'<th style="padding:10px 12px;text-align:left">{t("col.model")}</th>'
        f'<th style="padding:10px 12px;text-align:left">MAPE</th>'
        f'<th style="padding:10px 14px;text-align:left">{"Performance" if _is_en_d else "Hiệu năng"}</th>'
        f'<th style="padding:10px 12px;text-align:left">RMSE</th>'
        f'<th style="padding:10px 12px;text-align:left">MAE</th>'
        f'<th style="padding:10px 12px;text-align:left">R²adj</th>'
        f'</tr></thead><tbody>{_rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    # ── Kiểm định Diebold–Mariano: best vs các mô hình khác ──────────────
    _render_dm_section(_all7, df, _T, _is_en_d)

"""Trang 'Giao dịch Demo' (paper trading) — sổ lệnh ảo + thống kê P&L.

Cho phép người dùng đặt lệnh MUA/BÁN ảo trên 53 mã HOSE, theo dõi vị thế,
lịch sử lệnh, lãi/lỗ thực hiện + chưa thực hiện, và thống kê hành vi giao
dịch (số lệnh, win rate, P&L trung bình…). Lưu sổ ra file để giữ qua mỗi
phiên — sổ riêng cho từng máy.
"""
import streamlit as st
import datetime as _dt

from core.constants import TICKERS, ticker_sector
from data import paper as PP
from data.fetcher import fetch_data


def _kpi_card(label, value, color, _T, sub=None):
    sub_html = (f'<div style="font-size:10px;color:{_T["text_muted"]};margin-top:3px">'
                f'{sub}</div>' if sub else '')
    return (
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-top:3px solid {color};border-radius:10px;padding:12px 14px">'
        f'<div style="font-size:10px;font-weight:700;color:{_T["text_muted"]};'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">{label}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{color};line-height:1.1">{value}</div>'
        f'{sub_html}</div>'
    )


def _get_last_close(tk: str) -> float | None:
    """Giá đóng cửa mới nhất (đ) cho mã. None nếu fetch lỗi."""
    try:
        d = fetch_data(tk)
        return float(d['Close'].iloc[-1]) * 1000.0
    except Exception:
        return None


def _conviction_bar_html(conv: float, _T) -> str:
    """Thanh conviction [-100..+100] màu đỏ-vàng-xanh, mũi tên ở vị trí conv."""
    pct = (conv + 100) / 2.0                       # 0..100 cho left%
    arrow_color = (_T['success'] if conv >= 35
                   else _T['danger'] if conv <= -35
                   else _T['warning'])
    return (
        f'<div style="position:relative;height:30px;border-radius:8px;'
        f'background:linear-gradient(90deg,#DC2626 0%,#F59E0B 50%,#16A34A 100%);'
        f'box-shadow:inset 0 1px 3px rgba(0,0,0,.15)">'
        f'<div style="position:absolute;left:{pct:.1f}%;top:-6px;transform:translateX(-50%);'
        f'background:{arrow_color};color:#fff;font-weight:800;font-size:11px;'
        f'padding:3px 8px;border-radius:6px;border:2px solid #fff;'
        f'box-shadow:0 2px 6px rgba(0,0,0,.18)">'
        f'{conv:+.0f}</div>'
        f'<div style="position:absolute;left:50%;top:0;bottom:0;width:1px;'
        f'background:rgba(255,255,255,.55)"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;'
        f'color:{_T["text_muted"]};margin-top:4px;text-transform:uppercase;letter-spacing:.5px">'
        f'<span>Bán mạnh / Strong Sell</span><span>Trung tính / Neutral</span>'
        f'<span>Mua mạnh / Strong Buy</span></div>'
    )


def _stars_html(n: int, _T) -> str:
    """Render n sao đặc tô màu vàng + (5-n) sao rỗng mờ — SVG, không emoji."""
    from ui.icons import icon as _icon
    parts = []
    for i in range(5):
        if i < n:
            parts.append(_icon('star-fill', 18, '#F59E0B'))
        else:
            parts.append(_icon('star', 18, _T['text_muted']))
    return (f'<div style="display:inline-flex;gap:3px;align-items:center;'
            f'opacity:1">{"".join(parts)}</div>')


def _pillar_chip(name_vi: str, name_en: str, p: dict, _T, is_en: bool) -> str:
    """Chip 1 trụ tín hiệu: tên · score · reason."""
    s = float(p.get('score', 0.0))
    tag = p.get('tag', 'neut')
    col = (_T['success'] if tag == 'bull' or s > 0.4 else
           _T['danger']  if tag == 'bear' or s < -0.4 else
           _T['warning'] if tag == 'wild' else
           _T['text_secondary'])
    label = name_en if is_en else name_vi
    reason = p.get('reason', '')
    return (
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-left:4px solid {col};border-radius:10px;padding:9px 12px;'
        f'margin-bottom:6px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-weight:700;font-size:12.5px;color:{_T["text_primary"]};'
        f'text-transform:uppercase;letter-spacing:.5px">{label}</span>'
        f'<span style="font-weight:800;color:{col};font-size:13px">{s:+.1f}</span>'
        f'</div>'
        f'<div style="font-size:11.5px;color:{_T["text_secondary"]};margin-top:3px;'
        f'line-height:1.5">{reason}</div></div>'
    )


def _plan_card_html(plan: dict, _T, is_en: bool, idx: int) -> str:
    """Render 1 card phương án giao dịch với entry/stop/target/qty."""
    act = plan['action']
    act_col = (_T['success'] if act == 'BUY' else
               _T['danger']  if act == 'SELL' else
               _T['text_secondary'])
    palette = ['#0F766E', '#0EA5E9', '#A855F7']
    accent = palette[idx % 3]

    def _row(lbl_vi, lbl_en, val_html):
        lbl = lbl_en if is_en else lbl_vi
        return (f'<div style="display:flex;justify-content:space-between;'
                f'padding:6px 0;border-top:1px solid {_T["divider"]}">'
                f'<span style="color:{_T["text_muted"]};font-size:11.5px">{lbl}</span>'
                f'<span style="color:{_T["text_primary"]};font-size:12.5px;'
                f'font-weight:700">{val_html}</span></div>')

    if act == 'WAIT':
        body = (
            f'<div style="color:{_T["text_secondary"]};font-size:12.5px;line-height:1.6">'
            f'{plan.get("note","")}</div>'
        )
    else:
        entry_low = plan.get('entry_low'); entry_high = plan.get('entry_high')
        entry_str = (f'{entry_low:,.0f}–{entry_high:,.0f} đ'
                     if entry_low and entry_high else f'{plan["entry_ref"]:,.0f} đ')
        sl  = plan.get('stop_loss')
        tp1 = plan.get('tp1'); tp2 = plan.get('tp2')
        rr1 = plan.get('rr_tp1', 0); rr2 = plan.get('rr_tp2', 0)
        body = (
            _row('Hành động', 'Action',
                 f'<span style="color:{act_col}">{act}</span>')
            + _row('Vùng vào (entry)', 'Entry zone', entry_str)
            + _row('Cắt lỗ (stop-loss)', 'Stop-loss',
                   f'<span style="color:{_T["danger"]}">{sl:,.0f} đ</span>'
                   if sl else '—')
            + _row('Mục tiêu 1', 'Take-profit 1',
                   f'<span style="color:{_T["success"]}">{tp1:,.0f} đ '
                   f'<span style="color:{_T["text_muted"]};font-size:10px">'
                   f'({rr1:.1f}R)</span></span>' if tp1 else '—')
            + _row('Mục tiêu 2', 'Take-profit 2',
                   f'<span style="color:{_T["success"]}">{tp2:,.0f} đ '
                   f'<span style="color:{_T["text_muted"]};font-size:10px">'
                   f'({rr2:.1f}R)</span></span>' if tp2 else '—')
            + _row('Khối lượng', 'Quantity',
                   f'{plan["qty_shares"]:,} cp · {plan["position_pct"]:.1f}% vốn')
            + _row('Rủi ro/lệnh', 'Risk/trade',
                   f'{plan["risk_pct"]:.2f}% equity')
            + _row('Khung thời gian', 'Horizon', plan['horizon'])
        )
        if plan.get('reason_chain'):
            body += (f'<div style="margin-top:8px;font-size:11px;'
                     f'color:{_T["text_secondary"]};line-height:1.6">'
                     f'<b style="color:{_T["text_muted"]}">'
                     f'{"Vì sao" if not is_en else "Why"}:</b> '
                     + ' · '.join(plan['reason_chain'][:3]) + '</div>')

    return (
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-top:4px solid {accent};border-radius:12px;padding:14px 16px;'
        f'height:100%">'
        f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:.7px;'
        f'color:{_T["text_muted"]};font-weight:700">'
        f'{"Phương án" if not is_en else "Plan"} {idx+1}</div>'
        f'<div style="font-size:17px;font-weight:800;color:{accent};margin:2px 0 10px">'
        f'{plan["name"]}</div>'
        f'{body}</div>'
    )


def _render_pro_suggestion(ticker: str, df, state: dict, stats: dict,
                            _T, is_en: bool) -> None:
    """Render tab Đề xuất chuyên gia: signal engine + 3 phương án + 1-click."""
    import streamlit as _st
    from services.signal_engine import build_signal_report
    from services.trade_planner import build_trade_plans
    from data import paper as _PP

    # Banner giới thiệu
    intro = (
        'Engine tổng hợp 8 trụ cột (Xu hướng · Ichimoku · Momentum · Khối lượng · '
        'Biến động · Hỗ trợ/Kháng cự · Mẫu hình · Cơ bản) thành điểm tin cậy '
        '[−100, +100] và đề xuất 3 phương án giao dịch — KHÔNG phải khuyến nghị '
        'đầu tư, chỉ là khung tham khảo có giải trình rõ ràng.'
        if not is_en else
        'Engine combines 8 pillars (Trend · Ichimoku · Momentum · Volume · '
        'Volatility · Support/Resistance · Pattern · Fundamentals) into a '
        'conviction score in [−100, +100] and proposes 3 trade plans — NOT '
        'investment advice, only a reasoned framework.'
    )
    _st.markdown(
        f'<div class="info-box" style="margin-bottom:12px">{intro}</div>',
        unsafe_allow_html=True)

    # Compute (cache theo (ticker, last_close, len))
    cache_key = ('_sig_report', ticker, len(df),
                 float(df['Close'].iloc[-1]) if len(df) else 0.0)
    if _st.session_state.get('_sig_cache_key') != cache_key:
        with _st.spinner('Đang phân tích đa yếu tố...' if not is_en
                         else 'Analyzing multi-factor signals...'):
            report = build_signal_report(df, ticker, include_fundamentals=True)
        _st.session_state['_sig_cache_key'] = cache_key
        _st.session_state['_sig_report']    = report
    else:
        report = _st.session_state['_sig_report']

    plans_data = build_trade_plans(
        report,
        equity_dong=float(stats['equity']),
        cash_dong=float(stats['cash']),
        lang_en=is_en,
    )

    # ── Conviction + bias header ───────────────────────────────────────
    conv = float(report['conviction'])
    bias = report['bias']
    bias_label = {
        'BUY':  ('Mua', 'Buy', _T['success']),
        'SELL': ('Bán', 'Sell', _T['danger']),
        'HOLD': ('Chờ', 'Hold', _T['warning']),
    }.get(bias, ('Chờ', 'Hold', _T['warning']))

    c_head1, c_head2 = _st.columns([3, 2])
    with c_head1:
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-radius:12px;padding:14px 18px">'
            f'<div style="font-size:11px;color:{_T["text_muted"]};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.7px">'
            f'{"Conviction score" if is_en else "Điểm tin cậy tổng hợp"}'
            f' — <b style="color:{_T["accent"]}">{ticker}</b></div>'
            f'<div style="margin-top:14px">{_conviction_bar_html(conv, _T)}</div>'
            f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:6px;'
            f'line-height:1.5">'
            f'{"<b>Điểm tin cậy</b> = Σ(score × weight) chuẩn hoá về [−100, +100] từ 8 trụ cột. ≥ +35: BUY; ≤ −35: SELL." if not is_en else "<b>Conviction</b> = Σ(score × weight) normalized to [−100, +100] over 8 pillars. ≥ +35: BUY; ≤ −35: SELL."}'
            f'</div></div>',
            unsafe_allow_html=True)
    with c_head2:
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-top:4px solid {bias_label[2]};border-radius:12px;padding:14px 18px;'
            f'text-align:center">'
            f'<div style="font-size:11px;color:{_T["text_muted"]};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.7px">'
            f'{"Khuyến nghị" if not is_en else "Suggested action"}</div>'
            f'<div style="font-size:30px;font-weight:900;color:{bias_label[2]};'
            f'margin:4px 0 2px">{bias_label[1 if is_en else 0]}</div>'
            f'{_stars_html(plans_data["stars"], _T)}'
            f'</div>',
            unsafe_allow_html=True)

    _st.markdown("<div style='margin:14px 0 6px'></div>", unsafe_allow_html=True)

    # ── 8 trụ cột chi tiết (collapsible) ───────────────────────────────
    with _st.expander(
        ('Chi tiết 8 trụ cột tín hiệu' if not is_en
         else 'Detailed 8-pillar breakdown'),
        expanded=False):
        names = [
            ('trend',      'Xu hướng',          'Trend regime'),
            ('ichimoku',   'Ichimoku',          'Ichimoku 4-tier'),
            ('momentum',   'Động lượng',        'Momentum (RSI/MACD)'),
            ('volume',     'Khối lượng',        'Volume / OBV'),
            ('volatility', 'Biến động',         'Volatility (ATR%)'),
            ('sr',         'Hỗ trợ/Kháng cự',   'Support/Resistance'),
            ('pattern',    'Mẫu hình nến',      'Candlestick pattern'),
            ('fund',       'Cơ bản (P/E·ROE)',  'Fundamentals (P/E·ROE)'),
        ]
        c_a, c_b = _st.columns(2)
        for i, (key, vi, en) in enumerate(names):
            p = report['pillars'].get(key, {})
            target = c_a if i % 2 == 0 else c_b
            target.markdown(_pillar_chip(vi, en, p, _T, is_en),
                            unsafe_allow_html=True)

    # ── 3 phương án ────────────────────────────────────────────────────
    _st.markdown(
        f'<div class="sec-hdr" style="margin-top:8px">'
        f'{"Phương án giao dịch đề xuất" if not is_en else "Suggested trade plans"} '
        f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};'
        f'margin-left:8px">'
        f'{"Mỗi phương án sizing & stop dựa trên ATR + vùng S/R + rủi ro/lệnh" if not is_en else "Each plan sized & stopped via ATR + S/R + per-trade risk"}'
        f'</span></div>',
        unsafe_allow_html=True)

    plans = plans_data['plans']
    cols = _st.columns(max(len(plans), 1))
    for i, plan in enumerate(plans):
        cols[i].markdown(_plan_card_html(plan, _T, is_en, i),
                         unsafe_allow_html=True)

    # ── Nút 1-click áp dụng ────────────────────────────────────────────
    actionable = [p for p in plans if p['action'] in ('BUY', 'SELL')
                  and p['qty_shares'] > 0]
    if actionable:
        _st.markdown("<div style='margin:12px 0 4px'></div>", unsafe_allow_html=True)
        labels = [
            (f'{p["name"]} · {p["action"]} {p["qty_shares"]:,} @ {p["entry_ref"]:,.0f} đ')
            for p in actionable]
        sel = _st.radio(
            ('Chọn phương án để đặt lệnh ngay (theo giá entry tham chiếu)'
             if not is_en else
             'Pick a plan to place the order now (at reference entry)'),
            options=list(range(len(actionable))),
            format_func=lambda i: labels[i],
            horizontal=False,
            key='_pro_pick',
        )
        col_btn1, col_btn2 = _st.columns([2, 3])
        with col_btn1:
            if _st.button(
                ('Đặt lệnh theo phương án này' if not is_en
                 else 'Place order with this plan'),
                use_container_width=True, type='primary',
                key='_pro_apply',
            ):
                chosen = actionable[sel]
                if chosen['action'] == 'BUY':
                    _, ok, msg = _PP.buy(state, ticker,
                                          int(chosen['qty_shares']),
                                          float(chosen['entry_ref']))
                else:
                    _, ok, msg = _PP.sell(state, ticker,
                                           int(chosen['qty_shares']),
                                           float(chosen['entry_ref']))
                if ok:
                    _st.success(msg)
                    _st.rerun()
                else:
                    _st.error(msg)
        with col_btn2:
            from ui.icons import icon as _icon
            _warn_svg = _icon('exclamation-triangle-fill', 13, '#D97706')
            _st.markdown(
                f'<div style="font-size:11.5px;color:{_T["text_muted"]};'
                f'line-height:1.6;padding-top:6px;display:flex;gap:6px;align-items:flex-start">'
                f'<span style="flex-shrink:0;padding-top:2px">{_warn_svg}</span>'
                f'<span>{"Lệnh đặt theo giá entry tham chiếu, chưa kèm stop-loss/take-profit tự động. Theo dõi và đóng vị thế thủ công khi giá chạm các mức." if not is_en else "The order is placed at the reference entry; stop-loss / take-profit are NOT auto-triggered. Monitor and close manually when prices hit those levels."}</span>'
                f'</div>', unsafe_allow_html=True)
    else:
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px dashed {_T["border"]};'
            f'border-radius:10px;padding:14px 18px;color:{_T["text_muted"]};'
            f'font-size:12.5px;margin-top:10px">'
            f'{"Hiện chưa có phương án khả thi (conviction yếu hoặc không đủ vốn cho size tối thiểu). Chờ tín hiệu rõ hơn hoặc nạp thêm vốn ảo." if not is_en else "No actionable plan available right now (weak conviction or insufficient cash for min size). Wait for a clearer signal or top up the virtual book."}'
            f'</div>', unsafe_allow_html=True)


def _render_journal_tab(state: dict, _T, is_en: bool) -> None:
    """Nhật ký giao dịch — gắn note + tags vào từng lệnh trong history."""
    import streamlit as _st
    from services.journal import upsert_entry, get_entry_for_trade, list_entries

    _st.markdown(
        f'<div class="info-box" style="margin-bottom:10px">'
        f'{"Ghi lại lý do vào lệnh + bài học sau khi đóng — giúp cải thiện kỷ luật giao dịch theo thời gian. Mỗi entry gắn với 1 lệnh cụ thể trong lịch sử." if not is_en else "Record entry thesis + post-trade lesson — improves trading discipline over time. Each entry attaches to a specific trade in history."}'
        f'</div>', unsafe_allow_html=True)

    history = list(reversed(state.get('history', [])))[:50]
    if not history:
        _st.info('Chưa có lệnh nào để ghi nhật ký.' if not is_en
                  else 'No trades to journal yet.')
        return

    # Selectbox lệnh
    def _label(h):
        return (f"{h['ts'][:16].replace('T',' ')} · {h['ticker']} · "
                f"{h['side']} {h['qty']:,} @ {h['price']:,.0f}đ"
                + (f" · P&L {h['realized']:+,.0f}" if h.get('realized') is not None else ''))
    options = list(range(len(history)))
    idx = _st.selectbox(
        'Chọn lệnh để ghi/sửa nhật ký' if not is_en else 'Pick a trade to journal',
        options=options, format_func=lambda i: _label(history[i]),
        key='_jr_idx')
    trade = history[idx]
    existing = get_entry_for_trade(trade) or {}

    with _st.form('_jr_form'):
        col_a, col_b = _st.columns(2)
        with col_a:
            thesis = _st.text_area(
                'Luận điểm vào lệnh' if not is_en else 'Entry thesis',
                value=existing.get('thesis', ''), height=110, max_chars=600,
                placeholder=('Vì sao bạn mở vị thế? Setup nào? Mục tiêu R-multiple?'
                              if not is_en else
                              'Why did you open the position? Setup? R target?'),
                key='_jr_thesis')
        with col_b:
            lesson = _st.text_area(
                'Bài học rút ra' if not is_en else 'Lesson learned',
                value=existing.get('lesson', ''), height=110, max_chars=600,
                placeholder=('Sau khi đóng, đúng/sai ở chỗ nào?'
                              if not is_en else 'After closing, what went right/wrong?'),
                key='_jr_lesson')
        tags_str = _st.text_input(
            'Thẻ (cách nhau bằng dấu phẩy, tối đa 8 thẻ)'
            if not is_en else 'Tags (comma-separated, max 8)',
            value=', '.join(existing.get('tags') or []),
            placeholder='breakout, earnings, oversold',
            key='_jr_tags')
        rating = _st.slider(
            'Đánh giá kỷ luật (1 thấp - 5 cao)' if not is_en
            else 'Discipline rating (1 low - 5 high)',
            min_value=0, max_value=5,
            value=int(existing.get('rating') or 0), step=1, key='_jr_rate',
            help='0 = chưa đánh giá')
        ok = _st.form_submit_button(
            'Lưu nhật ký' if not is_en else 'Save entry',
            type='primary', use_container_width=False)

    if ok:
        tags = [t.strip() for t in (tags_str or '').split(',') if t.strip()]
        upsert_entry(trade, thesis or '', lesson or '', tags,
                      rating if rating > 0 else None)
        _st.success('Đã lưu.' if not is_en else 'Saved.')

    # Render các entry đã ghi cho lệnh này
    if existing:
        _tags_html = ''.join(
            f'<span style="background:{_T["accent"]}15;color:{_T["accent"]};'
            f'border:1px solid {_T["accent"]}30;border-radius:999px;'
            f'padding:2px 10px;font-size:11px;font-weight:700;'
            f'margin-right:5px">#{tg}</span>'
            for tg in (existing.get('tags') or []))
        _st.markdown("<div style='margin:14px 0 4px'></div>", unsafe_allow_html=True)
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
            f'border-left:3px solid {_T["accent"]};border-radius:10px;'
            f'padding:12px 16px">'
            f'<div style="font-size:11px;color:{_T["text_muted"]};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">'
            f'{"Entry đã lưu cho lệnh này" if not is_en else "Saved entry for this trade"}'
            f' · cập nhật {existing.get("updated_at","")[:16].replace("T"," ")}'
            f'</div>'
            f'{_tags_html}'
            + (f'<div style="margin-top:8px;color:{_T["text_primary"]};font-size:12.5px;line-height:1.6">'
               f'<b style="color:{_T["text_muted"]}">Luận điểm:</b> {existing.get("thesis","—") or "—"}<br>'
               f'<b style="color:{_T["text_muted"]}">Bài học:</b> {existing.get("lesson","—") or "—"}'
               f'</div>'
               if (existing.get("thesis") or existing.get("lesson")) else '')
            + f'</div>', unsafe_allow_html=True)


def _render_monte_carlo_section(state: dict, stats: dict, _T, is_en: bool) -> None:
    """Section Monte Carlo — dự báo equity portfolio N ngày forward."""
    import streamlit as _st
    import numpy as _np
    import plotly.graph_objects as _go
    from services.monte_carlo import simulate
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    _st.markdown(
        f'<div class="sec-hdr">'
        f'{"Mô phỏng Monte Carlo — dự báo tài sản tương lai" if not is_en else "Monte Carlo — future equity projection"}'
        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{"Resample daily return từ equity curve lịch sử" if not is_en else "Bootstrap daily returns from equity curve history"}'
        f'</span></div>',
        unsafe_allow_html=True)

    # Cần equity_curve để lấy daily returns. Dùng lại function trong data.paper
    from data import paper as _PP
    curve = _PP.equity_curve(state)
    if len(curve) < 12:
        _st.info(
            'Cần ít nhất ~10 phiên có lệnh để mô phỏng. Hãy đặt thêm vài lệnh ảo.'
            if not is_en else
            'Need at least ~10 trading sessions to simulate. Place a few more orders.')
        return

    eq_arr = _np.array([c['equity'] for c in curve], dtype=float)
    daily_rets = _np.diff(eq_arr) / _np.maximum(eq_arr[:-1], 1.0)

    col_a, col_b, col_c, col_d = _st.columns(4)
    horizon = col_a.select_slider(
        'Khoảng dự báo' if not is_en else 'Horizon',
        options=[20, 60, 120, 252],
        value=60, format_func=lambda d: f'{d} {"phiên" if not is_en else "bars"}',
        key='_mc_h')
    n_paths = col_b.select_slider(
        'Số path mô phỏng' if not is_en else 'Number of paths',
        options=[500, 1000, 2000, 5000], value=1000,
        key='_mc_n')
    method = col_c.radio(
        'Phương pháp' if not is_en else 'Method',
        options=['bootstrap', 'parametric'], horizontal=True, key='_mc_m',
        format_func=lambda m: ('Bootstrap (phân phối thực)' if m == 'bootstrap'
                                 else 'Parametric (Gaussian)') if not is_en else
                                ('Bootstrap (empirical)' if m == 'bootstrap'
                                 else 'Parametric (Gaussian)'))
    seed = col_d.number_input(
        'Seed (tái lập)' if not is_en else 'Seed',
        min_value=0, max_value=99999, value=42, step=1, key='_mc_seed')

    # Lazy: chỉ chạy khi user bấm nút HOẶC khi đã có result cũ với cùng params.
    # Tránh chạy MC tự động mỗi rerun → mượt hơn nhiều khi user chỉ click tab.
    _params_key = (int(horizon), int(n_paths), method, int(seed),
                    float(stats['equity']), len(daily_rets))
    _cached = _st.session_state.get('_mc_result')
    _cached_key = _st.session_state.get('_mc_params_key')

    run_btn = _st.button(
        ('Chạy mô phỏng' if not is_en else 'Run simulation'),
        key='_mc_run', type='primary', use_container_width=False)

    if not run_btn and _cached_key != _params_key:
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px dashed {_T["border"]};'
            f'border-radius:10px;padding:14px 18px;color:{_T["text_muted"]};'
            f'font-size:12.5px;margin-top:10px">'
            f'{"Bấm <b>Chạy mô phỏng</b> để thực thi (1000 path ≈ 0.5s, 5000 ≈ 2s)." if not is_en else "Press <b>Run simulation</b> to execute (1000 paths ≈ 0.5s, 5000 ≈ 2s)."}'
            f'</div>', unsafe_allow_html=True)
        return

    if run_btn or _cached_key != _params_key:
        with _st.spinner('Đang mô phỏng...' if not is_en else 'Simulating...'):
            try:
                mc = simulate(daily_rets, initial_equity=float(stats['equity']),
                               horizon_days=int(horizon), n_paths=int(n_paths),
                               method=method, seed=int(seed))
            except Exception as e:
                _st.error(f'Lỗi MC: {e}'); return
        _st.session_state['_mc_result'] = mc
        _st.session_state['_mc_params_key'] = _params_key
    else:
        mc = _cached

    if mc.get('error'):
        _st.warning(mc['error']); return

    m = mc['metrics']
    # KPI strip
    def _kpi(lbl_vi, lbl_en, val, col):
        return (f'<div style="flex:1 1 150px;min-width:140px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-top:3px solid {col};'
                f'border-radius:10px;padding:10px 12px">'
                f'<div style="font-size:10px;color:{_T["text_muted"]};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:.5px">'
                f'{lbl_en if is_en else lbl_vi}</div>'
                f'<div style="font-size:15px;font-weight:800;color:{col};margin-top:3px">'
                f'{val}</div></div>')

    p_col = _T['success'] if m['prob_profit_pct'] >= 50 else _T['warning']
    var_col = _T['warning'] if m['var_95_loss_pct'] < 10 else _T['danger']

    kpi_html = ''.join([
        _kpi('Vốn hiện tại', 'Current equity',
             f'{m["initial_equity"]/1e6:,.1f}M đ', _T['accent']),
        _kpi(f'Median sau {horizon}p', f'Median after {horizon}',
             f'{m["median_final"]/1e6:,.1f}M đ', _T['text_primary']),
        _kpi('Xác suất sinh lời', 'Prob. of profit',
             f'{m["prob_profit_pct"]:.0f}%', p_col),
        _kpi('Lợi suất kỳ vọng', 'Expected return',
             f'{m["expected_return_pct"]:+.2f}%',
             _T['success'] if m['expected_return_pct'] >= 0 else _T['danger']),
        _kpi('VaR 95%', 'VaR 95%',
             f'{m["var_95_loss_pct"]:.2f}%', var_col),
        _kpi('CVaR 95%', 'CVaR 95%',
             f'{m["cvar_95_loss_pct"]:.2f}%', _T['danger']),
        _kpi('Path tốt nhất', 'Best path',
             f'{m["best_path_gain_pct"]:+.1f}%', _T['success']),
        _kpi('Path xấu nhất', 'Worst path',
             f'{m["worst_path_loss_pct"]:+.1f}%', _T['danger']),
    ])
    _st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">'
                  f'{kpi_html}</div>', unsafe_allow_html=True)

    # Chart fan
    pct = mc['percentiles']
    x_days = list(range(len(pct['p50'])))
    fig = _go.Figure()
    fig.add_trace(_go.Scatter(x=x_days, y=pct['p95'], mode='lines',
                                 line=dict(width=0), showlegend=False))
    fig.add_trace(_go.Scatter(x=x_days, y=pct['p5'], mode='lines',
                                 line=dict(width=0), fill='tonexty',
                                 fillcolor='rgba(15,118,110,0.12)',
                                 name='5%–95%'))
    fig.add_trace(_go.Scatter(x=x_days, y=pct['p75'], mode='lines',
                                 line=dict(width=0), showlegend=False))
    fig.add_trace(_go.Scatter(x=x_days, y=pct['p25'], mode='lines',
                                 line=dict(width=0), fill='tonexty',
                                 fillcolor='rgba(15,118,110,0.24)',
                                 name='25%–75%'))
    fig.add_trace(_go.Scatter(x=x_days, y=pct['p50'], mode='lines',
                                 line=dict(color='#0F766E', width=2.4),
                                 name=('Median' if is_en else 'Trung vị')))
    fig.add_hline(y=m['initial_equity'],
                   line=dict(color=_T['text_muted'], width=1, dash='dash'),
                   annotation_text=('Hiện tại' if not is_en else 'Now'),
                   annotation_position='right',
                   annotation_font=dict(size=10, color=_T['text_muted']))
    fig.update_layout(
        height=340, margin=dict(l=50, r=30, t=10, b=40),
        paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
        font=dict(family='Inter', size=11, color=_T['text_primary']),
        xaxis_title=('Phiên forward' if not is_en else 'Forward bars'),
        yaxis_title='đồng',
        legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center',
                     bgcolor='rgba(0,0,0,0)'),
        hovermode='x unified')
    _plotly_axes_style(fig, _T)
    _st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    _st.caption(
        ('Monte Carlo bootstrap mô phỏng N path equity bằng cách lấy mẫu có hoàn lại từ phân phối daily return lịch sử của sổ — giữ được fat tails và skewness thực tế. VaR 95% = lỗ tối đa với 95% confidence; CVaR (expected shortfall) = trung bình lỗ trong 5% worst case — thước đo rủi ro chặt hơn VaR.'
         if not is_en else
         'Bootstrap MC simulates N equity paths by resampling (with replacement) from your daily-return distribution — preserves real fat tails and skewness. VaR 95% = max loss at 95% confidence; CVaR = mean loss in the 5% worst paths — a stricter risk measure than VaR.'))


def _render_backtest_tab(ticker: str, df, _T, is_en: bool) -> None:
    """Tab Backtest — chạy signal engine 8 trụ trên data lịch sử của 1 mã."""
    import streamlit as _st
    import plotly.graph_objects as _go
    from services.backtest import run_backtest
    from charts.base import _PLOTLY_CONFIG, _plotly_axes_style

    _st.markdown(
        f'<div class="info-box" style="margin-bottom:10px">'
        f'{"Backtest signal engine 8 trụ trên dữ liệu lịch sử của mã đang chọn — đánh giá hiệu quả giả định nếu user đã giao dịch theo gợi ý của engine. KHÔNG sử dụng future data; bao gồm phí 0.15% + thuế bán 0.10% HOSE. So sánh với Buy & Hold." if not is_en else "Backtest the 8-pillar signal engine on the selected ticker history — measure hypothetical performance had the user traded by the engine. No look-ahead; includes 0.15% fee + 0.10% sell tax. Compared to Buy & Hold."}'
        f'</div>', unsafe_allow_html=True)

    # Tham số (5 cột, thêm rf%)
    col_a, col_b, col_c, col_d, col_e = _st.columns(5)
    with col_a:
        entry_thr = _st.slider(
            'Ngưỡng mở (entry)' if not is_en else 'Entry threshold',
            min_value=10, max_value=80, value=35, step=5,
            help='Conviction tối thiểu để mở lệnh BUY.', key='_bt_entry')
    with col_b:
        exit_thr = _st.slider(
            'Ngưỡng đóng (exit)' if not is_en else 'Exit threshold',
            min_value=10, max_value=80, value=20, step=5,
            help='Conviction âm để đóng lệnh.', key='_bt_exit')
    with col_c:
        pos_pct = _st.slider(
            '% vốn mỗi lệnh' if not is_en else '% capital per trade',
            min_value=10, max_value=100, value=30, step=10,
            key='_bt_pos') / 100.0
    with col_d:
        step = _st.select_slider(
            'Tần suất' if not is_en else 'Frequency',
            options=[1, 3, 5, 10, 20], value=5,
            format_func=lambda s: (f'{s} phiên' if not is_en else f'{s} bars'),
            help='1 = mỗi phiên (chậm). 5 = hàng tuần. 20 = hàng tháng.',
            key='_bt_step')
    with col_e:
        rf_pct = _st.number_input(
            'rf (%/năm)' if not is_en else 'rf (%/year)',
            min_value=0.0, max_value=15.0, value=4.7, step=0.1,
            help='Lãi suất phi rủi ro (4.7% = lãi gửi 12 tháng SBV). '
                 'Áp vào Sharpe + Sortino theo công thức gốc Sharpe 1966.',
            key='_bt_rf')

    _btn_col, _info_col = _st.columns([1, 3])
    with _btn_col:
        run_btn = _st.button(
            'Chạy Backtest' if not is_en else 'Run Backtest',
            key='_bt_run', type='primary', use_container_width=True)
    with _info_col:
        _st.caption(
            f'Sẽ test trên ~{max(0, len(df) - 120)} phiên (bỏ 120 phiên warmup). '
            f'Thời gian dự kiến: {max(1, (len(df) - 120) // (step or 5)) // 30}-'
            f'{max(2, (len(df) - 120) // (step or 5)) // 15} giây.'
            if not is_en else
            f'Will test ~{max(0, len(df) - 120)} bars (skip 120 warmup). '
            f'ETA: {max(1, (len(df) - 120) // (step or 5)) // 30}-'
            f'{max(2, (len(df) - 120) // (step or 5)) // 15}s.')

    if not run_btn:
        # Hiện instruction nếu chưa chạy
        _st.markdown(
            f'<div style="background:{_T["bg_card"]};border:1px dashed {_T["border"]};'
            f'border-radius:10px;padding:14px 18px;color:{_T["text_muted"]};'
            f'font-size:12.5px;margin-top:10px">'
            f'{"Bấm <b>Chạy Backtest</b> để thực thi. Engine sẽ duyệt qua từng phiên, tính conviction tại mỗi điểm và ghi nhận các lệnh giả định BUY/SELL — sau đó so sánh với chiến lược Buy & Hold cùng vốn." if not is_en else "Press <b>Run Backtest</b> to execute. The engine walks the history, computes conviction at each point and records hypothetical BUY/SELL trades — then compares to Buy & Hold with the same capital."}'
            f'</div>', unsafe_allow_html=True)
        return

    # Chạy backtest với progress bar — user thấy tiến độ thay vì spinner câm
    _pb = _st.progress(0, text='Đang chạy backtest...' if not is_en
                                else 'Running backtest...')
    def _cb(pct, done, total):
        _pb.progress(min(int(pct), 100),
                     text=(f'Backtest {done}/{total} ({pct:.0f}%)'
                            if not is_en else f'Backtest {done}/{total} ({pct:.0f}%)'))
    result = run_backtest(df, ticker,
                            entry_threshold=float(entry_thr),
                            exit_threshold=float(exit_thr),
                            position_pct=float(pos_pct),
                            step=int(step),
                            rf_annual_pct=float(rf_pct),
                            on_progress=_cb)
    _pb.empty()

    if 'error' in result:
        _st.error(result['error'])
        return

    m = result['metrics']
    # ── KPI strip ──────────────────────────────────────────────────────
    def _kpi(lbl_vi, lbl_en, val, col):
        return (f'<div style="flex:1 1 160px;min-width:150px;background:{_T["bg_card"]};'
                f'border:1px solid {_T["border"]};border-top:3px solid {col};'
                f'border-radius:10px;padding:10px 12px">'
                f'<div style="font-size:10px;color:{_T["text_muted"]};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:.5px">'
                f'{lbl_en if is_en else lbl_vi}</div>'
                f'<div style="font-size:16px;font-weight:800;color:{col};margin-top:3px">'
                f'{val}</div></div>')

    ret_col = _T['success'] if m['total_return_pct'] >= 0 else _T['danger']
    bh_col  = _T['success'] if m['buy_hold_return_pct'] >= 0 else _T['danger']
    ex_col  = _T['success'] if m['excess_vs_bh_pct'] >= 0 else _T['danger']

    # NaN-check phải trước inf — `+inf == +inf` là True nên branch '∞' bị
    # collapse (Python truthiness của ternary). Test inf trước.
    _sortino = m.get('sortino_ratio', float('nan'))
    if _sortino == float('inf'):
        _sortino_txt = '∞'
    elif _sortino != _sortino:
        _sortino_txt = 'N/A'
    else:
        _sortino_txt = f'{_sortino:+.2f}'
    _rf = m.get('rf_annual_pct', 4.7)
    kpis_html = ''.join([
        _kpi('Lợi suất tổng', 'Total return',
             f'{m["total_return_pct"]:+.2f}%', ret_col),
        _kpi('CAGR', 'CAGR', f'{m["cagr_pct"]:+.2f}%', ret_col),
        _kpi(f'Sharpe (rf={_rf:.1f}%)', f'Sharpe (rf={_rf:.1f}%)',
             f'{m["sharpe_ratio"]:+.2f}' if m['sharpe_ratio'] == m['sharpe_ratio'] else 'N/A',
             _T['accent']),
        _kpi('Sortino (ann.)', 'Sortino (ann.)', _sortino_txt, _T['accent']),
        _kpi('Max Drawdown', 'Max Drawdown',
             f'{m["max_drawdown_pct"]:.2f}%', _T['danger']),
        _kpi('Buy & Hold', 'Buy & Hold',
             f'{m["buy_hold_return_pct"]:+.2f}%', bh_col),
        _kpi('Vượt B&H', 'vs B&H',
             f'{m["excess_vs_bh_pct"]:+.2f}%', ex_col),
        _kpi('Số lệnh', 'Trades', f'{m["n_trades"]}', _T['text_primary']),
        _kpi('Win rate', 'Win rate',
             f'{m["win_rate"]:.1f}%', _T['warning']),
    ])
    _st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">'
                  f'{kpis_html}</div>', unsafe_allow_html=True)

    # ── Equity curve vs Buy & Hold ─────────────────────────────────────
    if result['equity_curve']:
        eq = result['equity_curve']
        dates = [e['date'] for e in eq]
        equity = [e['equity'] for e in eq]
        # Buy & Hold tham chiếu: equity B&H = initial × (close[t]/close[0]) trừ phí giản lược
        cl0 = eq[0]['close']
        bh_equity = [m['initial_capital'] * (e['close'] / cl0) for e in eq]

        fig = _go.Figure()
        fig.add_trace(_go.Scatter(
            x=dates, y=equity, mode='lines',
            line=dict(color='#0F766E', width=2.2),
            name=('Backtest engine' if not is_en else 'Backtest engine'),
            hovertemplate='<b>%{x}</b><br>%{y:,.0f} đ<extra></extra>'))
        fig.add_trace(_go.Scatter(
            x=dates, y=bh_equity, mode='lines',
            line=dict(color='#94A3B8', width=1.6, dash='dash'),
            name=('Buy & Hold' if not is_en else 'Buy & Hold'),
            hovertemplate='B&H %{y:,.0f} đ<extra></extra>'))
        fig.add_hline(y=m['initial_capital'],
                       line=dict(color=_T['text_muted'], width=1, dash='dot'),
                       annotation_text=('Vốn ban đầu' if not is_en else 'Initial'),
                       annotation_position='right',
                       annotation_font=dict(size=10, color=_T['text_muted']))
        fig.update_layout(
            height=360, margin=dict(l=50, r=30, t=10, b=40),
            paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
            font=dict(family='Inter', size=11, color=_T['text_primary']),
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center',
                         bgcolor='rgba(0,0,0,0)'))
        _plotly_axes_style(fig, _T)
        fig.update_yaxes(title=dict(text='đồng', font=dict(size=10, color=_T['text_muted'])))
        _st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)

    # ── Bảng lệnh ──────────────────────────────────────────────────────
    if result['trades']:
        _st.markdown(
            f'<div class="sec-hdr" style="margin-top:8px">'
            f'{"Danh sách lệnh giả định" if not is_en else "Hypothetical trades"} '
            f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
            f'{len(result["trades"])} {"lệnh" if not is_en else "trades"}'
            f'</span></div>', unsafe_allow_html=True)
        hdr = (['Vào', 'Ra', 'Giá vào', 'Giá ra', 'KL', 'Lợi suất', 'Conv vào']
                if not is_en else
                ['In', 'Out', 'Price in', 'Price out', 'Qty', 'Return', 'Conv in'])
        rows = ''
        for t in result['trades'][-50:][::-1]:
            r = t['ret_pct']
            col = _T['success'] if r > 0 else _T['danger']
            arrow = '▲' if r > 0 else '▼'
            rows += (
                f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
                f'<td style="padding:7px 10px;font-family:monospace;font-size:11px">{t["date_in"]}</td>'
                f'<td style="padding:7px 10px;font-family:monospace;font-size:11px">{t["date_out"]}</td>'
                f'<td style="padding:7px 10px">{t["price_in"]*1000:,.0f} đ</td>'
                f'<td style="padding:7px 10px">{t["price_out"]*1000:,.0f} đ</td>'
                f'<td style="padding:7px 10px">{t["qty"]:,}</td>'
                f'<td style="padding:7px 10px;color:{col};font-weight:700">{arrow} {r:+.2f}%</td>'
                f'<td style="padding:7px 10px;color:{_T["text_muted"]}">{t["conviction_in"]:+.1f}</td>'
                f'</tr>')
        th = ''.join(f'<th style="padding:8px 10px;text-align:left">{h}</th>' for h in hdr)
        _st.markdown(
            f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]};max-height:360px;overflow-y:auto">'
            f'<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
            f'<thead style="position:sticky;top:0"><tr style="background:{_T["accent"]};color:#fff">{th}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True)
    else:
        _st.info(
            'Engine không mở lệnh nào trên khoảng dữ liệu này — '
            'thử hạ ngưỡng entry hoặc tăng vùng quan sát.'
            if not is_en else
            'No trades opened — try lowering entry threshold or extending data window.')


def _render_achievements_strip(state: dict, stats: dict, _T, is_en: bool) -> None:
    """Strip 14 huy hiệu thành tựu — render bằng SVG icon, KHÔNG emoji."""
    import streamlit as _st
    from services.achievements import evaluate, summary
    from services.watchlist import get_watchlist
    from services.journal import list_entries as _list_entries
    from ui.icons import icon as _icon

    badges = evaluate(state, stats,
                       watchlist=get_watchlist(),
                       journal_entries=_list_entries())
    s = summary(badges)

    _st.markdown(
        f'<div class="sec-hdr">'
        f'{"Huy hiệu thành tựu" if not is_en else "Achievement badges"} '
        f'<span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
        f'{s["earned"]}/{s["total"]} · {s["pct"]:.0f}%</span></div>',
        unsafe_allow_html=True)

    _st.markdown(
        f'<div style="height:8px;background:{_T["bg_card"]};border-radius:999px;'
        f'overflow:hidden;border:1px solid {_T["border"]};margin:6px 0 12px">'
        f'<div style="height:100%;width:{s["pct"]:.1f}%;'
        f'background:linear-gradient(90deg,#F59E0B 0%,#0F766E 100%);'
        f'border-radius:999px"></div></div>',
        unsafe_allow_html=True)

    cells = []
    for b in badges:
        title = b['title_en'] if is_en else b['title_vi']
        desc  = b['desc_en']  if is_en else b['desc_vi']
        ic_name = b.get('icon', 'star')
        if b.get('earned'):
            border = '#0F766E'; bg_glow = 'rgba(15,118,110,0.06)'
            ic_col = '#0F766E'
            status_html = _icon('check-lg', 16, '#0F766E')
            opacity = '1'
        else:
            border = _T['border']; bg_glow = 'transparent'
            ic_col = _T['text_muted']
            status_html = ''
            opacity = '.55'

        prog_html = ''
        if b.get('progress'):
            cur, tot = b['progress']
            pct = (cur / tot * 100.0) if tot else 0.0
            prog_html = (
                f'<div style="margin-top:6px;height:5px;'
                f'background:{_T["bg_elevated"]};border-radius:999px;overflow:hidden">'
                f'<div style="height:100%;width:{pct:.0f}%;'
                f'background:{border};border-radius:999px"></div></div>'
                f'<div style="font-size:10px;color:{_T["text_muted"]};'
                f'margin-top:2px;text-align:right">{cur}/{tot}</div>')

        # Tròn nền cho icon — kích thước cố định 36×36, ic_col màu icon
        icon_chip = (
            f'<span style="display:inline-flex;align-items:center;'
            f'justify-content:center;width:36px;height:36px;border-radius:50%;'
            f'background:{ic_col}1A;color:{ic_col}">'
            f'{_icon(ic_name, 18, ic_col)}</span>')

        cells.append(
            f'<div style="flex:1 1 170px;min-width:160px;background:{bg_glow};'
            f'border:1px solid {border};border-radius:10px;padding:10px 12px;'
            f'opacity:{opacity}">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'{icon_chip}{status_html}'
            f'</div>'
            f'<div style="font-size:12.5px;font-weight:800;color:{_T["text_primary"]};'
            f'margin:6px 0 2px">{title}</div>'
            f'<div style="font-size:10.5px;color:{_T["text_secondary"]};line-height:1.5">'
            f'{desc}</div>{prog_html}</div>')

    _st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap">{"".join(cells)}</div>',
        unsafe_allow_html=True)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'
    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Giao dịch Demo" if not is_en else "Paper Trading"} — {"Sổ lệnh ảo" if not is_en else "Virtual Order Book"}</h1>'
        f'<p>{"Đặt lệnh MUA/BÁN ảo, theo dõi lãi/lỗ & thống kê — sổ lưu cục bộ, dữ liệu giá thực." if not is_en else "Place virtual BUY/SELL orders, track P&L & stats — local book, real prices."}</p>'
        f'</div>', unsafe_allow_html=True)

    state = PP.load_state()

    # Lấy giá hiện tại cho các mã đang nắm giữ (để tính unrealized + equity)
    cur_prices = {}
    for tk in list(state['positions'].keys()):
        p = _get_last_close(tk)
        if p is not None:
            cur_prices[tk] = p
    # Giá hiện tại của mã đang chọn (cho form đặt lệnh)
    last_close_sel = _get_last_close(ticker) or 0.0

    stats = PP.compute_stats(state, cur_prices)

    # ── KPI strip ───────────────────────────────────────────────────────
    _ret_col = _T['success'] if stats['total_pnl'] >= 0 else _T['danger']
    _ret_sign = '▲' if stats['total_pnl'] >= 0 else '▼'
    cols = st.columns(5)
    cols[0].markdown(_kpi_card(
        'Tiền mặt' if not is_en else 'Cash',
        f'{stats["cash"]:,.0f} đ', _T['text_primary'], _T,
        f'{"Vốn ban đầu" if not is_en else "Initial"}: {stats["initial_capital"]:,.0f}'
    ), unsafe_allow_html=True)
    cols[1].markdown(_kpi_card(
        'Giá trị nắm giữ' if not is_en else 'Holdings',
        f'{stats["holdings_value"]:,.0f} đ', _T['accent'], _T,
        f'{len(stats["positions_rows"])} {"vị thế" if not is_en else "positions"}'
    ), unsafe_allow_html=True)
    cols[2].markdown(_kpi_card(
        'Tổng tài sản' if not is_en else 'Total Equity',
        f'{stats["equity"]:,.0f} đ', '#0F766E', _T
    ), unsafe_allow_html=True)
    cols[3].markdown(_kpi_card(
        'P&L tổng' if not is_en else 'Total P&L',
        f'{_ret_sign} {stats["total_pnl"]:+,.0f} đ', _ret_col, _T,
        f'{stats["total_return_pct"]:+.2f}%'
    ), unsafe_allow_html=True)
    cols[4].markdown(_kpi_card(
        'Tỷ lệ thắng' if not is_en else 'Win Rate',
        f'{stats["win_rate"]:.0f}%', _T['warning'], _T,
        f'{stats["n_wins"]}W / {stats["n_losses"]}L · {stats["n_sells"]} {"bán" if not is_en else "sells"}'
    ), unsafe_allow_html=True)

    st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)

    # ── 7 tab: Đề xuất · Đặt lệnh · Vị thế · Lịch sử · Nhật ký · Backtest · Stats
    (tab_smart, tab_order, tab_pos, tab_hist, tab_journal,
     tab_backtest, tab_stat) = st.tabs([
        '  ' + ('Đề xuất chuyên gia' if not is_en else 'Pro Suggestion') + '  ',
        '  ' + ('Đặt lệnh' if not is_en else 'Place Order') + '  ',
        '  ' + ('Vị thế hiện tại' if not is_en else 'Current Positions') + '  ',
        '  ' + ('Lịch sử lệnh' if not is_en else 'Order History') + '  ',
        '  ' + ('Nhật ký' if not is_en else 'Journal') + '  ',
        '  ' + ('Backtest' if not is_en else 'Backtest') + '  ',
        '  ' + ('Thống kê & Huy hiệu' if not is_en else 'Stats & Badges') + '  ',
    ])

    with tab_smart:
        _render_pro_suggestion(ticker, df, state, stats, _T, is_en)

    with tab_journal:
        _render_journal_tab(state, _T, is_en)

    with tab_backtest:
        _render_backtest_tab(ticker, df, _T, is_en)

    # ── TAB 1: ĐẶT LỆNH ────────────────────────────────────────────────
    with tab_order:
        st.markdown(
            f'<div class="info-box" style="margin-bottom:10px">'
            f'{"Mã đang xem" if not is_en else "Selected ticker"}: '
            f'<b style="color:{_T["accent"]}">{ticker}</b> · '
            f'{ticker_sector(ticker)}<br>'
            f'{"Giá tham chiếu (close gần nhất)" if not is_en else "Reference price (last close)"}: '
            f'<b>{last_close_sel:,.0f} đ</b></div>',
            unsafe_allow_html=True)
        col_form, col_info = st.columns([3, 2])
        with col_form:
            with st.form('order_form', clear_on_submit=False):
                _side = st.radio(
                    'Loại lệnh' if not is_en else 'Side',
                    options=['BUY', 'SELL'], horizontal=True,
                    key='po_side',
                )
                _qty = st.number_input(
                    'Khối lượng (cổ phiếu)' if not is_en else 'Quantity (shares)',
                    min_value=1, max_value=1_000_000, value=100, step=10,
                    key='po_qty',
                )
                _px = st.number_input(
                    'Giá (đ/cp)' if not is_en else 'Price (đ/share)',
                    min_value=1.0, max_value=10_000_000.0,
                    value=float(last_close_sel) if last_close_sel else 10000.0,
                    step=100.0, format='%.0f', key='po_px',
                )
                _est = int(_qty) * float(_px)
                # Preview phí + thuế giúp user thấy chi phí thực TRƯỚC khi đặt
                _fee_rate = PP._FEE_RATE
                _tax_rate = PP._TAX_SELL
                _fee_prev = _est * _fee_rate
                _tax_prev = _est * _tax_rate if _side == 'SELL' else 0.0
                _net = _est + _fee_prev if _side == 'BUY' else _est - _fee_prev - _tax_prev
                _net_label = ('Cần trả' if _side == 'BUY' else 'Sẽ nhận') if not is_en else \
                             ('Total cost' if _side == 'BUY' else 'Net proceeds')
                _net_col = _T['danger'] if _side == 'BUY' else _T['success']
                st.markdown(
                    f'<div style="font-size:12px;color:{_T["text_muted"]};margin-top:-4px;line-height:1.6">'
                    f'{"Giá trị gốc" if not is_en else "Gross"}: '
                    f'<b style="color:{_T["text_primary"]}">{_est:,.0f} đ</b><br>'
                    f'{"Phí" if not is_en else "Fee"} 0.15%: <b>{_fee_prev:,.0f} đ</b>'
                    + (f' · {"Thuế bán" if not is_en else "Tax"} 0.10%: <b>{_tax_prev:,.0f} đ</b>' if _side == 'SELL' else '')
                    + f'<br><span style="color:{_net_col};font-weight:800">{_net_label}: {_net:,.0f} đ</span>'
                    f'</div>',
                    unsafe_allow_html=True)
                submitted = st.form_submit_button(
                    ('Đặt lệnh' if not is_en else 'Submit order'),
                    use_container_width=True, type='primary')
            if submitted:
                if _side == 'BUY':
                    state, ok, msg = PP.buy(state, ticker, int(_qty), float(_px))
                else:
                    state, ok, msg = PP.sell(state, ticker, int(_qty), float(_px))
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        with col_info:
            pos = state['positions'].get(ticker)
            if pos:
                _gap = (last_close_sel - pos['avg_price']) if last_close_sel else 0
                _gpct = (_gap / pos['avg_price'] * 100) if pos['avg_price'] else 0
                _gc = _T['success'] if _gap >= 0 else _T['danger']
                st.markdown(
                    f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
                    f'border-left:4px solid {_T["accent"]};border-radius:10px;padding:14px 18px">'
                    f'<div style="font-size:11px;font-weight:700;color:{_T["text_muted"]};'
                    f'text-transform:uppercase;letter-spacing:.5px">'
                    f'{"Vị thế hiện tại" if not is_en else "Current position"}</div>'
                    f'<div style="font-size:18px;font-weight:800;color:{_T["text_primary"]};margin-top:4px">'
                    f'{pos["qty"]:,} {ticker}</div>'
                    f'<div style="font-size:12px;color:{_T["text_secondary"]};margin-top:2px">'
                    f'{"Giá vốn TB" if not is_en else "Avg cost"}: '
                    f'<b>{pos["avg_price"]:,.0f} đ</b></div>'
                    f'<div style="font-size:12px;color:{_gc};margin-top:6px">'
                    f'{"Lãi/lỗ tạm tính" if not is_en else "Unrealized"}: '
                    f'<b>{_gap:+,.0f} đ ({_gpct:+.2f}%)</b></div>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:{_T["bg_card"]};border:1px dashed {_T["border"]};'
                    f'border-radius:10px;padding:14px 18px;color:{_T["text_muted"]};font-size:12px">'
                    f'{"Chưa có vị thế cho" if not is_en else "No position in"} '
                    f'<b style="color:{_T["text_primary"]}">{ticker}</b>.</div>',
                    unsafe_allow_html=True)

    # ── TAB 2: VỊ THẾ HIỆN TẠI ─────────────────────────────────────────
    with tab_pos:
        if not stats['positions_rows']:
            st.info('Chưa có vị thế nào.' if not is_en else 'No open positions.')
        else:
            _hdr = (['Mã', 'KL', 'Giá vốn TB', 'Giá hiện tại', 'Giá trị', 'Lãi/lỗ tạm tính']
                    if not is_en else
                    ['Ticker', 'Qty', 'Avg cost', 'Current price', 'Value', 'Unrealized P&L'])
            _rows = ''
            for r in sorted(stats['positions_rows'], key=lambda x: -x['value']):
                _c = _T['success'] if r['unrealized'] >= 0 else _T['danger']
                _arr = '▲' if r['unrealized'] >= 0 else '▼'
                _rows += (
                    f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
                    f'<td style="padding:9px 12px;font-weight:700;color:{_T["accent"]}">{r["ticker"]}</td>'
                    f'<td style="padding:9px 12px">{r["qty"]:,}</td>'
                    f'<td style="padding:9px 12px">{r["avg_price"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px">{r["cur_price"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px;font-weight:700">{r["value"]:,.0f} đ</td>'
                    f'<td style="padding:9px 12px;color:{_c};font-weight:700">'
                    f'{_arr} {r["unrealized"]:+,.0f} đ ({r["unrealized_pct"]:+.2f}%)</td>'
                    f'</tr>')
            _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
            st.markdown(
                f'<div style="border-radius:12px;overflow-x:auto;border:1px solid {_T["border"]}">'
                f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
                f'<thead><tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
                f'<tbody>{_rows}</tbody></table></div>',
                unsafe_allow_html=True)

    # ── TAB 3: LỊCH SỬ ──────────────────────────────────────────────────
    with tab_hist:
        hist = list(reversed(state.get('history', [])))
        if not hist:
            st.info('Chưa có lệnh nào.' if not is_en else 'No orders yet.')
        else:
            _hdr = (['Thời điểm', 'Mã', 'Loại', 'KL', 'Giá', 'Giá trị', 'Lãi/lỗ thực hiện']
                    if not is_en else
                    ['Time', 'Ticker', 'Side', 'Qty', 'Price', 'Value', 'Realized P&L'])
            _rows = ''
            for h in hist[:200]:        # tối đa 200 dòng gần nhất
                _sc = _T['success'] if h['side'] == 'BUY' else _T['danger']
                _rl = h.get('realized')
                if _rl is None:
                    _rl_txt, _rc = '—', _T['text_muted']
                else:
                    _rc = _T['success'] if _rl >= 0 else _T['danger']
                    _rl_txt = f'{_rl:+,.0f} đ'
                _rows += (
                    f'<tr style="border-top:1px solid {_T["divider"]};color:{_T["text_primary"]}">'
                    f'<td style="padding:8px 10px;color:{_T["text_muted"]};font-family:monospace;font-size:11px">'
                    f'{h["ts"][:16].replace("T"," ")}</td>'
                    f'<td style="padding:8px 10px;font-weight:700;color:{_T["accent"]}">{h["ticker"]}</td>'
                    f'<td style="padding:8px 10px;color:{_sc};font-weight:800">{h["side"]}</td>'
                    f'<td style="padding:8px 10px">{h["qty"]:,}</td>'
                    f'<td style="padding:8px 10px">{h["price"]:,.0f}</td>'
                    f'<td style="padding:8px 10px">{h["value"]:,.0f}</td>'
                    f'<td style="padding:8px 10px;color:{_rc};font-weight:700">{_rl_txt}</td>'
                    f'</tr>')
            _th = ''.join(f'<th style="padding:9px 12px;text-align:left">{h}</th>' for h in _hdr)
            st.markdown(
                f'<div style="border-radius:12px;overflow:hidden;max-height:480px;'
                f'overflow-y:auto;border:1px solid {_T["border"]}">'
                f'<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
                f'<thead style="position:sticky;top:0">'
                f'<tr style="background:{_T["accent"]};color:#fff">{_th}</tr></thead>'
                f'<tbody>{_rows}</tbody></table></div>',
                unsafe_allow_html=True)

    # ── TAB 4: THỐNG KÊ & RESET ────────────────────────────────────────
    with tab_stat:
        # ── Equity curve — đường tài sản theo thời gian ─────────────────
        curve = PP.equity_curve(state)
        if len(curve) >= 2:
            st.markdown(f'<div class="sec-hdr">{"Đường tài sản (Equity Curve)" if not is_en else "Equity Curve"}'
                        f' <span style="font-size:11px;font-weight:600;color:{_T["text_muted"]};margin-left:8px">'
                        f'{"Cash + giá trị nắm giữ theo thời gian — neo vào Close hằng ngày" if not is_en else "Cash + holdings value over time — anchored to daily Close"}'
                        f'</span></div>', unsafe_allow_html=True)
            try:
                import plotly.graph_objects as _go
                from charts.base import _plotly_axes_style, _PLOTLY_CONFIG
                _dates = [c['date'] for c in curve]
                _eq    = [c['equity']   for c in curve]
                _cash  = [c['cash']     for c in curve]
                _hold  = [c['holdings'] for c in curve]
                _init  = float(state.get('initial_capital', 100_000_000))
                _fig = _go.Figure()
                _fig.add_trace(_go.Scatter(
                    x=_dates, y=_eq, mode='lines+markers',
                    line=dict(color='#0F766E', width=2.4),
                    marker=dict(size=6, color='#0F766E', line=dict(color='#fff', width=1)),
                    name=('Tổng tài sản' if not is_en else 'Total Equity'),
                    fill='tozeroy', fillcolor='rgba(15,118,110,0.08)',
                    hovertemplate='<b>%{x}</b><br>%{y:,.0f} đ<extra></extra>'))
                _fig.add_trace(_go.Scatter(
                    x=_dates, y=_cash, mode='lines',
                    line=dict(color='#94A3B8', width=1.4, dash='dot'),
                    name=('Tiền mặt' if not is_en else 'Cash'),
                    hovertemplate='Cash: %{y:,.0f} đ<extra></extra>'))
                _fig.add_hline(y=_init, line=dict(color=_T['text_muted'], width=1, dash='dash'),
                               annotation_text=('Vốn ban đầu' if not is_en else 'Initial capital'),
                               annotation_position='right',
                               annotation_font=dict(size=10, color=_T['text_muted']))
                _fig.update_layout(
                    height=340, margin=dict(l=50, r=30, t=10, b=40),
                    paper_bgcolor=_T['bg_card'], plot_bgcolor=_T['bg_card'],
                    font=dict(family='Inter', size=11, color=_T['text_primary']),
                    hovermode='x unified',
                    legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center',
                                bgcolor='rgba(0,0,0,0)'))
                _plotly_axes_style(_fig, _T)
                _fig.update_yaxes(title=dict(text='đồng', font=dict(size=10, color=_T['text_muted'])))
                st.plotly_chart(_fig, use_container_width=True, config=_PLOTLY_CONFIG)
            except Exception as _e:
                st.caption(f'⚠ {_e}')
            st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)
        _detail = [
            (('Số lệnh tổng' if not is_en else 'Total trades'),       f'{stats["n_trades"]}', _T['text_primary']),
            (('Lệnh mua' if not is_en else 'Buy orders'),             f'{stats["n_buys"]}', _T['success']),
            (('Lệnh bán' if not is_en else 'Sell orders'),            f'{stats["n_sells"]}', _T['danger']),
            (('P&L thực hiện' if not is_en else 'Realized P&L'),
             f'{stats["realized_pnl"]:+,.0f} đ',
             _T['success'] if stats['realized_pnl'] >= 0 else _T['danger']),
            (('P&L chưa thực hiện' if not is_en else 'Unrealized P&L'),
             f'{stats["unrealized_pnl"]:+,.0f} đ',
             _T['success'] if stats['unrealized_pnl'] >= 0 else _T['danger']),
            (('Lãi TB / lệnh thắng' if not is_en else 'Avg win'),    f'{stats["avg_win"]:+,.0f} đ', _T['success']),
            (('Lỗ TB / lệnh thua' if not is_en else 'Avg loss'),     f'{stats["avg_loss"]:+,.0f} đ', _T['danger']),
            (('Lệnh thắng lớn nhất' if not is_en else 'Max win'),    f'{stats["max_win"]:+,.0f} đ', _T['success']),
            (('Lệnh thua nặng nhất' if not is_en else 'Max loss'),   f'{stats["max_loss"]:+,.0f} đ', _T['danger']),
            (('Max Drawdown' if not is_en else 'Max Drawdown'),
             f'{stats["max_drawdown_pct"]:.2f}%',
             _T['success'] if stats['max_drawdown_pct'] > -5 else
             (_T['warning'] if stats['max_drawdown_pct'] > -15 else _T['danger'])),
            (('Sharpe (annualized)' if not is_en else 'Sharpe (ann.)'),
             f'{stats["sharpe_ratio"]:.2f}' if stats['sharpe_ratio'] == stats['sharpe_ratio'] else 'N/A',
             _T['success'] if (stats['sharpe_ratio'] == stats['sharpe_ratio'] and stats['sharpe_ratio'] > 1)
             else (_T['warning'] if (stats['sharpe_ratio'] == stats['sharpe_ratio'] and stats['sharpe_ratio'] > 0)
                   else _T['danger'])),
            (('Phí giao dịch (cộng dồn)' if not is_en else 'Total fees'),
             f'{stats["total_fees"]:,.0f} đ', _T['text_secondary']),
            (('Thuế bán (cộng dồn)' if not is_en else 'Sell tax'),
             f'{stats["total_tax"]:,.0f} đ', _T['text_secondary']),
        ]
        _cells = ''.join(
            f'<div style="flex:1 1 180px;min-width:170px;background:{_T["bg_card"]};'
            f'border:1px solid {_T["border"]};border-top:3px solid {col};border-radius:10px;'
            f'padding:10px 12px"><div style="font-size:10px;color:{_T["text_muted"]};'
            f'text-transform:uppercase;letter-spacing:.4px">{lbl}</div>'
            f'<div style="font-size:15px;font-weight:800;color:{col};margin-top:3px">{val}</div></div>'
            for lbl, val, col in _detail)
        st.markdown(
            f'<div style="display:flex;gap:10px;flex-wrap:wrap">{_cells}</div>',
            unsafe_allow_html=True)

        # Giải thích Sharpe / MDD cho judges không quen quant
        st.caption(
            ('• <b>Sharpe (ann.)</b>: lợi suất vượt rf chia độ lệch chuẩn, hoá năm √252 — '
             '> 1 tốt, > 2 rất tốt. • <b>Max Drawdown</b>: % rớt sâu nhất từ đỉnh '
             'tới đáy equity — đo rủi ro chịu được. Càng gần 0 càng an toàn.'
             if not is_en else
             '• <b>Sharpe (ann.)</b>: excess-over-rf divided by std deviation, '
             'annualized √252 — > 1 good, > 2 great. • <b>Max Drawdown</b>: '
             '% peak-to-trough decline of equity — closer to 0 is safer.'),
            unsafe_allow_html=True)

        st.markdown("<div style='margin:18px 0 8px'></div>", unsafe_allow_html=True)
        _render_achievements_strip(state, stats, _T, is_en)

        st.markdown("<div style='margin:18px 0 8px'></div>", unsafe_allow_html=True)
        _render_monte_carlo_section(state, stats, _T, is_en)

        st.markdown("<div style='margin:18px 0 8px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="sec-hdr">{"Đặt lại sổ giao dịch" if not is_en else "Reset trading book"}</div>',
                    unsafe_allow_html=True)
        col_a, col_b = st.columns([2, 1])
        with col_a:
            new_cap = st.number_input(
                'Vốn ban đầu (đ)' if not is_en else 'Initial capital (đ)',
                min_value=1_000_000.0, max_value=10_000_000_000.0,
                value=100_000_000.0, step=10_000_000.0, format='%.0f',
                key='paper_reset_cap')
        with col_b:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button(('Reset sổ' if not is_en else 'Reset book'),
                         key='paper_reset_btn', use_container_width=True):
                PP.reset_state(float(new_cap))
                st.success(('Đã đặt lại sổ.' if not is_en else 'Book reset.'))
                st.rerun()

    st.markdown(
        f'<div style="font-size:11px;color:{_T["text_muted"]};margin-top:14px;line-height:1.6">'
        f'{"Sổ giao dịch ảo lưu cục bộ tại paper_state.json (mỗi máy 1 sổ). KHÔNG phải tài khoản chứng khoán thật — chỉ dùng để luyện tập kỷ luật giao dịch & theo dõi P&L với giá thị trường thật." if not is_en else "Virtual book stored locally in paper_state.json (one book per machine). NOT a real brokerage — for practicing trading discipline & tracking P&L against real market prices."}'
        f'</div>', unsafe_allow_html=True)

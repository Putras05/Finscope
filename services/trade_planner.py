"""Trade Planner — từ signal report dựng 3 phương án Conservative/Balanced/Aggressive.

Mỗi phương án gồm:
  • action       — BUY / SELL / WAIT (theo bias engine).
  • entry        — vùng đặt mua/bán (1 mức tham chiếu + 1 zone).
  • stop_loss    — Cắt lỗ theo ATR-multiple + bám hỗ trợ gần (nếu có).
  • take_profit  — 2 mục tiêu T1/T2 theo R-multiple (1.5R, 2.5R) hoặc bám kháng cự.
  • position_pct — % equity gợi ý (Kelly-lite × hệ số phương án).
  • qty_shares   — Số CP tương ứng (lô 10), ĐÃ clamp theo cash & rule rủi ro.
  • horizon      — Khoảng thời gian dự kiến nắm giữ.
  • conviction_label — Chip nhãn tin cậy 1-5 sao.
  • reason_chain — list bullet lý do hợp nhất từ signal engine.

Triết lý:
  Conservative: nhỏ size, stop chặt, mục tiêu khiêm tốn — phù hợp người mới
    hoặc khi conviction thấp/biên độ rộng.
  Balanced:     size vừa, stop ATR-2, mục tiêu 2R — cân bằng tiêu chuẩn.
  Aggressive:   size lớn hơn, stop rộng hơn để tránh "shake out", mục tiêu 3R.
    CHỈ nên dùng khi conviction cao + ATR% thấp.

Áp dụng quy tắc rủi ro chuẩn:
  Conservative max risk per trade = 0.5% equity
  Balanced     max risk per trade = 1.0% equity
  Aggressive   max risk per trade = 1.5% equity (cap 2%).
"""
from __future__ import annotations
import math
from typing import Optional
from services.risk import position_size_by_risk, position_size_cap_by_cash


_PLAN_PRESETS = [
    # name_vi, name_en, atr_stop_mult, tp1_R, tp2_R, risk_pct, horizon_vi, horizon_en
    ('Thận trọng',  'Conservative', 1.5, 1.0, 1.8, 0.50, '1–2 tuần',  '1–2 weeks'),
    ('Cân bằng',    'Balanced',     2.0, 1.5, 2.5, 1.00, '2–4 tuần',  '2–4 weeks'),
    ('Tích cực',    'Aggressive',   2.8, 2.0, 3.5, 1.50, '4–8 tuần',  '4–8 weeks'),
]


def _stars(conviction_abs: float) -> int:
    """Quy đổi |conviction| (0..100) → 1..5 sao."""
    if conviction_abs >= 75: return 5
    if conviction_abs >= 55: return 4
    if conviction_abs >= 35: return 3
    if conviction_abs >= 15: return 2
    return 1


def _round_price_dong(p_dong: float, side: str = 'round') -> float:
    """Làm tròn giá ĐỒNG theo bước giá HOSE đơn giản (10đ/50đ/100đ tùy mệnh giá).

    side='floor' cho stop-buy (mua không vượt), 'ceil' cho stop-sell-stop.
    """
    if p_dong < 10_000:
        step = 10.0
    elif p_dong < 50_000:
        step = 50.0
    else:
        step = 100.0
    if side == 'floor':
        return math.floor(p_dong / step) * step
    if side == 'ceil':
        return math.ceil(p_dong / step) * step
    return round(p_dong / step) * step


def build_trade_plans(report: dict,
                      equity_dong: float,
                      cash_dong: float,
                      lang_en: bool = False) -> dict:
    """Tạo 3 phương án từ signal report.

    Tham số:
      report      — output của services.signal_engine.build_signal_report().
      equity_dong — tổng tài sản hiện tại (cash + holdings) — base sizing.
      cash_dong   — tiền mặt còn → clamp số CP.

    Trả dict:
      {
        'action_overall', 'conviction', 'stars',
        'plans': [3 dict như mô tả ở docstring module],
        'context': {atr, atr_pct, last_price_dong, ...}
      }
    """
    bias = report.get('bias', 'HOLD')
    conviction = float(report.get('conviction', 0.0))
    stars = _stars(abs(conviction))
    last_close = float(report.get('last_price', 0.0))        # nghìn đồng (đơn vị data)
    atr = float(report.get('atr', 0.0))                       # nghìn đồng

    # Chuyển sang đồng (×1000) cho mọi giá hiển thị / sizing
    last_dong = last_close * 1000.0
    atr_dong  = atr * 1000.0

    plans = []
    pillars = report.get('pillars', {})
    sr = pillars.get('sr', {}).get('details', {})
    near_res = sr.get('near_res')   # nghìn đồng hoặc None
    near_sup = sr.get('near_sup')

    if bias == 'HOLD' or last_dong <= 0 or atr_dong <= 0:
        # Không đề xuất giao dịch — chỉ trả WAIT plan duy nhất
        return {
            'action_overall': 'WAIT',
            'conviction': conviction, 'stars': stars,
            'plans': [{
                'name': 'Chưa giao dịch' if not lang_en else 'Stand by',
                'action': 'WAIT',
                'entry_ref': last_dong, 'entry_low': None, 'entry_high': None,
                'stop_loss': None,
                'tp1': None, 'tp2': None,
                'position_pct': 0.0, 'qty_shares': 0,
                'risk_pct': 0.0,
                'horizon': '—',
                'reason_chain': (report.get('reasons_positive', [])
                                 + report.get('reasons_negative', []))[:6],
                'note': (
                    'Conviction chưa đủ mạnh để mở lệnh; chờ tín hiệu rõ hơn.'
                    if not lang_en else
                    'Conviction is not strong enough; wait for clearer signal.'
                ),
            }],
            'context': {'atr_dong': atr_dong, 'atr_pct': report.get('atr_pct'),
                        'last_price_dong': last_dong,
                        'near_res': (near_res * 1000.0) if near_res else None,
                        'near_sup': (near_sup * 1000.0) if near_sup else None},
        }

    is_long = (bias == 'BUY')

    # Trần cứng cho rủi ro mỗi lệnh — bất kể conviction cao bao nhiêu, không
    # vượt 2% equity (chuẩn quản trị rủi ro retail) để honor lời hứa trong
    # docstring (Conservative ≤ 0.5%, Balanced ≤ 1.0%, Aggressive ≤ 2.0%).
    _HARD_RISK_CAP_PCT = 2.0
    # Trần cho %cash trên từng plan — Conservative chỉ được vào tối đa 30%
    # cash 1 mã, không bao giờ all-in.
    _CASH_CAPS = {'Thận trọng': 30.0, 'Cân bằng': 50.0, 'Tích cực': 70.0,
                   'Conservative': 30.0, 'Balanced': 50.0, 'Aggressive': 70.0}

    for name_vi, name_en, atr_mult, tp1_R, tp2_R, risk_pct, hz_vi, hz_en in _PLAN_PRESETS:
        # Tăng cấp aggressive theo conviction: conviction càng cao, càng dám
        # mở rộng risk_pct trong preset đó (±30%) — nhưng KHÔNG bao giờ vượt cap.
        conv_boost = max(0.7, min(1.3, abs(conviction) / 60.0))
        eff_risk_pct = min(risk_pct * conv_boost, _HARD_RISK_CAP_PCT)

        if is_long:
            # Entry = giá tham chiếu hôm nay; zone ±0.4×ATR cho linh hoạt
            entry_ref = last_dong
            entry_low = _round_price_dong(last_dong - 0.4 * atr_dong, 'floor')
            entry_high = _round_price_dong(last_dong + 0.4 * atr_dong, 'ceil')

            # Stop: max( entry - atr_mult×ATR, hỗ trợ gần - 0.3×ATR )
            stop_atr = last_dong - atr_mult * atr_dong
            stop_sup = ((near_sup * 1000.0) - 0.3 * atr_dong) if near_sup else None
            stop_loss = max(stop_atr, stop_sup) if stop_sup else stop_atr
            stop_loss = _round_price_dong(stop_loss, 'floor')
            stop_loss = max(stop_loss, 100.0)        # không âm

            risk_per_share = entry_ref - stop_loss
            if risk_per_share <= 0:
                continue

            # TP theo R-multiple, sau đó nâng lên kháng cự gần nếu thấp hơn TP1
            tp1 = entry_ref + tp1_R * risk_per_share
            tp2 = entry_ref + tp2_R * risk_per_share
            if near_res:
                near_res_dong = near_res * 1000.0
                if near_res_dong > entry_ref and near_res_dong < tp1:
                    # Kháng cự sát → hạ TP1 về dưới kháng cự 1 tick
                    tp1 = _round_price_dong(near_res_dong - 0.2 * atr_dong, 'floor')
            tp1 = _round_price_dong(tp1, 'round')
            tp2 = _round_price_dong(tp2, 'round')

        else:  # SELL bias — gợi ý đóng/giảm vị thế, KHÔNG short (không có short trên Paper)
            entry_ref = last_dong
            entry_low = _round_price_dong(last_dong - 0.4 * atr_dong, 'floor')
            entry_high = _round_price_dong(last_dong + 0.4 * atr_dong, 'ceil')
            # "Stop" cho lệnh bán = ngưỡng nếu giá phục hồi trên kháng cự thì hủy bán
            stop_atr = last_dong + atr_mult * atr_dong
            stop_res = ((near_res * 1000.0) + 0.3 * atr_dong) if near_res else None
            stop_loss = min(stop_atr, stop_res) if stop_res else stop_atr
            stop_loss = _round_price_dong(stop_loss, 'ceil')
            risk_per_share = stop_loss - entry_ref
            if risk_per_share <= 0:
                continue
            tp1 = entry_ref - tp1_R * risk_per_share
            tp2 = entry_ref - tp2_R * risk_per_share
            if near_sup:
                near_sup_dong = near_sup * 1000.0
                if near_sup_dong < entry_ref and near_sup_dong > tp1:
                    tp1 = _round_price_dong(near_sup_dong + 0.2 * atr_dong, 'ceil')
            tp1 = _round_price_dong(tp1, 'round')
            tp2 = _round_price_dong(tp2, 'round')

        qty_risk = position_size_by_risk(equity_dong, entry_ref, stop_loss, eff_risk_pct)
        # Cap %cash theo plan — Conservative tối đa 30%, Balanced 50%, Aggressive 70%.
        _cash_cap_pct = _CASH_CAPS.get(name_vi, _CASH_CAPS.get(name_en, 100.0))
        qty_cash = position_size_cap_by_cash(cash_dong, entry_ref,
                                             max_pct_of_cash=_cash_cap_pct)
        qty_final = min(qty_risk, qty_cash) if is_long else qty_risk
        # % equity sẽ phân bổ
        alloc_dong = qty_final * entry_ref
        position_pct = (alloc_dong / equity_dong * 100.0) if equity_dong > 0 else 0.0

        plan = {
            'name': name_vi if not lang_en else name_en,
            'action': 'BUY' if is_long else 'SELL',
            'entry_ref': float(entry_ref),
            'entry_low': float(entry_low),
            'entry_high': float(entry_high),
            'stop_loss': float(stop_loss),
            'tp1': float(tp1),
            'tp2': float(tp2),
            'position_pct': float(position_pct),
            'qty_shares': int(qty_final),
            'risk_pct': float(eff_risk_pct),
            'horizon': hz_vi if not lang_en else hz_en,
            'reason_chain': (report.get('reasons_positive', [])
                             if is_long else
                             report.get('reasons_negative', []))[:5],
            'rr_tp1': tp1_R, 'rr_tp2': tp2_R,
            'atr_mult': atr_mult,
        }
        plans.append(plan)

    return {
        'action_overall': bias,
        'conviction': conviction,
        'stars': stars,
        'plans': plans,
        'context': {'atr_dong': atr_dong, 'atr_pct': report.get('atr_pct'),
                    'last_price_dong': last_dong,
                    'near_res': (near_res * 1000.0) if near_res else None,
                    'near_sup': (near_sup * 1000.0) if near_sup else None},
    }

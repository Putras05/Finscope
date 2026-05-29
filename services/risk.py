"""Công cụ quản trị rủi ro cho engine giao dịch FinScope.

Tách riêng khỏi signal_engine và trade_planner để dễ test:
  • atr_series — Average True Range (Wilder 1978) — đơn vị giá nghìn-đồng.
  • position_size_by_risk — sizing chuẩn: risk-per-trade % × equity / |entry-stop|.
  • kelly_fraction — Kelly-lite (1/2 Kelly) từ win-rate + payoff ratio.
  • r_multiple — đo lợi nhuận theo bội số rủi ro (R = |entry - stop|).

THAM KHẢO:
  Wilder, J. W. (1978). New Concepts in Technical Trading Systems.
  Thorp, E. (1969). Optimal Gambling Systems for Favorable Games.
  Van Tharp (2008). Trade Your Way to Financial Freedom (R-multiple).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


# ── ATR (Average True Range) — Wilder 1978 ──────────────────────────────
def atr_series(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    """Trả mảng ATR cùng độ dài df (đơn vị giá nghìn-đồng như toàn app).

    TR = max(H-L, |H-Cprev|, |L-Cprev|); ATR = RMA(TR, n) (Wilder smoothing).
    """
    H = df['High'].astype(float)
    L = df['Low'].astype(float)
    C = df['Close'].astype(float)
    prev_c = C.shift(1)
    tr = pd.concat([(H - L), (H - prev_c).abs(), (L - prev_c).abs()],
                   axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean().values


def last_atr(df: pd.DataFrame, n: int = 14) -> float:
    """ATR phiên cuối (nghìn đồng). 0.0 nếu chưa đủ dữ liệu."""
    a = atr_series(df, n)
    if len(a) == 0:
        return 0.0
    v = a[-1]
    return float(v) if v == v else 0.0           # NaN-safe


# ── Position sizing chuẩn (fixed-fractional risk) ───────────────────────
def position_size_by_risk(equity_dong: float,
                          entry_dong: float,
                          stop_dong: float,
                          risk_pct: float) -> int:
    """Số cổ phiếu tối đa được phép mua sao cho lỗ nếu chạm stop ≤
    `risk_pct`% tài sản. Trả số nguyên (làm tròn về lô 10 cho HOSE retail).

    Tham số đơn vị ĐỒNG (cả equity và giá). risk_pct dạng phần trăm (1.0 = 1%).
    """
    if equity_dong <= 0 or risk_pct <= 0:
        return 0
    risk_per_share = abs(float(entry_dong) - float(stop_dong))
    if risk_per_share <= 0:
        return 0
    raw_qty = (equity_dong * risk_pct / 100.0) / risk_per_share
    qty = int(raw_qty // 10) * 10                 # lô tối thiểu HOSE = 10 cp
    return max(qty, 0)


def position_size_cap_by_cash(cash_dong: float,
                              entry_dong: float,
                              max_pct_of_cash: float = 100.0,
                              fee_rate: float = 0.0015) -> int:
    """Trần số CP có thể mua bằng tiền mặt (gồm phí). Dùng để CLAMP kết quả
    position_size_by_risk khỏi vượt khả năng tài chính.
    """
    if cash_dong <= 0 or entry_dong <= 0:
        return 0
    budget = cash_dong * (max_pct_of_cash / 100.0)
    qty = int((budget / (entry_dong * (1 + fee_rate))) // 10) * 10
    return max(qty, 0)


# ── Kelly criterion (Kelly 1956) — full + fractional + growth rate ──────
def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float,
                   safety: float = 0.5) -> float:
    """Kelly fraction = W - (1 - W) / R, với R = avg_win / |avg_loss|.

    Trả tỉ lệ vốn nên đặt vào lệnh hiện tại (0..1). Áp safety=0.5 (1/2 Kelly)
    để giảm phương sai — practice phổ biến trong quant trading (Thorp 1969).

    win_rate: 0..1 (KHÔNG phải %).

    THAM KHẢO:
      Kelly, J. L. (1956). A new interpretation of information rate.
        Bell System Technical Journal, 35(4), 917-926.
      Thorp, E. O. (1969). Optimal gambling systems for favorable games.
        Rev. of the International Statistical Institute, 37(3).
    """
    if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss >= 0:
        return 0.0
    R = avg_win / abs(avg_loss)
    if R <= 0:
        return 0.0
    k = win_rate - (1 - win_rate) / R
    return max(0.0, min(1.0, k * safety))


def kelly_full_report(win_rate: float, avg_win: float, avg_loss: float) -> dict:
    """Báo cáo đầy đủ Kelly: full / 1/2 / 1/4 fraction + edge + payoff +
    expected log-growth g* (Kelly 1956).

    g(f) = W·log(1 + f·b) + (1-W)·log(1 - f), với b = avg_win / |avg_loss|.
    g* tại f* (full Kelly) là tốc độ tăng trưởng kỳ vọng log-vốn dài hạn.

    Trả {kelly_full, kelly_half, kelly_quarter, edge, payoff_ratio,
         expected_log_growth, all_in_disaster_risk_pct}.

    Lưu ý: kelly_full có thể > 1 (theo công thức nguyên gốc) khi edge rất
    lớn — clamp về [0, 1] cho long-only no-leverage.
    """
    import math
    if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss >= 0:
        return {'kelly_full': 0.0, 'kelly_half': 0.0, 'kelly_quarter': 0.0,
                'edge': 0.0, 'payoff_ratio': 0.0,
                'expected_log_growth': 0.0,
                'all_in_disaster_risk_pct': 0.0,
                'error': 'Cần win_rate ∈ (0,1) và avg_win > 0 > avg_loss.'}
    W = float(win_rate)
    b = avg_win / abs(avg_loss)
    f_full = W - (1 - W) / b
    f_full = max(0.0, min(1.0, f_full))
    # Edge = W·b - (1-W) (expected gain per unit bet)
    edge = W * b - (1 - W)
    # Growth rate ở fractional Kelly
    def _g(f):
        if f <= 0 or f >= 1:
            return float('-inf') if f >= 1 else 0.0
        return W * math.log(1 + f * b) + (1 - W) * math.log(1 - f)
    return {
        'kelly_full':    float(f_full),
        'kelly_half':    float(f_full * 0.5),
        'kelly_quarter': float(f_full * 0.25),
        'edge':          float(edge),
        'payoff_ratio':  float(b),
        'expected_log_growth': float(_g(f_full)),
        'all_in_disaster_risk_pct': float((1 - W) * 100),    # P(lose all on full bet)
    }


def gaussian_kelly(mu_daily: float, sigma_daily: float,
                    rf_daily: float = 0.0) -> float:
    """Continuous-time Kelly cho phân phối lợi suất Gaussian (Thorp 1969):
        f* = (μ - r_f) / σ²

    Dùng khi không có win/loss rời rạc mà có chuỗi return liên tục.
    Trả tỉ lệ vốn tối ưu để max log-growth (clamp về [0, 1]).
    """
    if sigma_daily <= 0:
        return 0.0
    f = (mu_daily - rf_daily) / (sigma_daily ** 2)
    return max(0.0, min(1.0, f))


# ── R-multiple ──────────────────────────────────────────────────────────
def r_multiple(entry: float, exit_px: float, stop: float) -> float:
    """Lợi nhuận theo bội số rủi ro R = |entry − stop|. Quy ước long-only:
    R dương khi exit_px > entry, âm khi ngược lại.
    """
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    return float((exit_px - entry) / risk)

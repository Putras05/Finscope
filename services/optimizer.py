"""Portfolio Optimizer — Markowitz Mean-Variance (1952) + biên hiệu quả.

Bài toán Markowitz:
    min  w' Σ w
    s.t. w' μ  = R_target        (lợi suất kỳ vọng)
         w' 1  = 1                (tổng trọng số = 1)
         w_i  >= 0                (long-only — không bán khống)

Trong đó:
    μ — vector lợi suất kỳ vọng (mean của daily returns × 252).
    Σ — ma trận hiệp phương sai daily returns × 252 (annualized).

Thuật toán:
  • Closed-form (analytical) cho 2 cực biên: min-variance portfolio (MVP) và
    max-Sharpe portfolio (tangency).
  • Biên hiệu quả: grid R_target ∈ [R_min, R_max] → giải QP với scipy.optimize.

API:
  optimize(returns_df)      → dict các portfolio đặc biệt
  efficient_frontier(...)   → list (vol, ret, weights) cho chart

THAM KHẢO:
  Markowitz, H. (1952). Portfolio Selection. The J. of Finance, 7(1).
  Tobin, J. (1958). Liquidity Preference as Behavior Towards Risk.
  Sharpe, W. F. (1966). Mutual Fund Performance.

KHÔNG cần scipy nếu đầu vào ≤ 10 mã — ta dùng matrix inverse closed-form
cho min-var và max-Sharpe. Frontier dùng grid solver thuần numpy.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional


# Hash fingerprint hợp nhất ở core/cache.py (v55) — single source of truth.
from core.cache import returns_fingerprint as _returns_fingerprint


def _annualize(returns_df: pd.DataFrame) -> tuple:
    """Trả (mu_annual, sigma_annual) từ daily returns (% hoặc ratio).

    Đầu vào: DataFrame index=date, columns=ticker, value=daily return (%).
    """
    # Quy chuẩn về tỉ lệ (ratio) nếu giá trị > 5 (% scale)
    if returns_df.abs().median().median() > 1.0:
        r = returns_df / 100.0       # % -> ratio
    else:
        r = returns_df
    r = r.dropna()
    if len(r) < 30:
        raise ValueError(f'Cần ≥ 30 phiên có đủ dữ liệu (hiện {len(r)}).')
    mu = r.mean().values * 252.0
    cov = r.cov().values * 252.0
    return mu, cov, list(r.columns)


def _project_simplex(v: np.ndarray) -> np.ndarray:
    """Chiếu vector v lên simplex {w >= 0, sum(w) = 1} — closed-form O(n log n).

    Tham khảo: Wang & Carreira-Perpiñán (2013), Projection onto the
    probability simplex.
    """
    n = len(v)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    rho = np.where(u - cssv / np.arange(1, n + 1) > 0)[0]
    if len(rho) == 0:
        return np.ones(n) / n
    rho = rho[-1]
    theta = cssv[rho] / float(rho + 1)
    return np.maximum(v - theta, 0.0)


def _min_variance(cov: np.ndarray) -> np.ndarray:
    """Minimum-variance portfolio: w* ∝ Σ⁻¹ · 1, chuẩn hoá sum=1.

    Sau đó chiếu lên simplex để bảo đảm long-only.
    """
    n = cov.shape[0]
    ones = np.ones(n)
    try:
        inv = np.linalg.pinv(cov)
        w = inv @ ones
        w = w / w.sum()
    except Exception:
        w = ones / n
    return _project_simplex(w)


def _max_sharpe(mu: np.ndarray, cov: np.ndarray,
                  rf: float = 0.0) -> np.ndarray:
    """Tangency portfolio: w* ∝ Σ⁻¹ (μ - rf·1), chuẩn hoá sum=1.

    BUG cũ: chia trực tiếp w/w.sum() khi w.sum() âm hoặc gần 0 sẽ FLIP dấu
    toàn bộ trọng số → simplex projection snap MÃ THUA về 100%. Repro:
    μ=[+0.05, -0.05], cov=I → w=[0.05,-0.05], sum=0 → equal-weight (OK)
    nhưng μ=[+0.05, -0.10] → w.sum() < 0 → flip → 100% mã thua.

    Fix: nếu sum gần 0 → fallback equal-weight; nếu sum < 0 → fallback
    grid-search trên efficient frontier chọn argmax Sharpe.
    """
    n = len(mu)
    excess = mu - rf
    try:
        inv = np.linalg.pinv(cov)
        w = inv @ excess
        s = float(w.sum())
        if abs(s) < 1e-8:
            return _project_simplex(np.ones(n) / n)
        if s > 0:
            return _project_simplex(w / s)
        # s < 0 — closed-form không áp dụng (excess return / cov pathological).
        # Grid-search Sharpe trên simplex: trên efficient frontier targets.
        r_min = max(mu.min(), 0.0)
        r_max = mu.max()
        if r_max <= r_min:
            return _project_simplex(np.ones(n) / n)
        best_w, best_sh = None, -np.inf
        for r_t in np.linspace(r_min, r_max, 40):
            wi = _solve_frontier_point(mu, cov, r_t)
            ret = float(wi @ mu)
            vol = float(np.sqrt(max(wi @ cov @ wi, 0.0)))
            if vol <= 0:
                continue
            sh = (ret - rf) / vol
            if sh > best_sh:
                best_sh, best_w = sh, wi
        return best_w if best_w is not None else _project_simplex(np.ones(n) / n)
    except Exception:
        return _project_simplex(np.ones(n) / n)


def _portfolio_stats(w: np.ndarray, mu: np.ndarray, cov: np.ndarray,
                     rf: float = 0.0) -> dict:
    ret = float(w @ mu)
    var = float(w @ cov @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    sharpe = float((ret - rf) / vol) if vol > 0 else float('nan')
    return {'expected_return': ret, 'volatility': vol, 'sharpe': sharpe,
            'weights': w.tolist()}


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: _returns_fingerprint})
def optimize(returns_df: pd.DataFrame, rf: float = 0.0) -> dict:
    """Trả 3 portfolio kinh điển: equal weight, min-variance, max-Sharpe.

    Tất cả đơn vị return/volatility annualized (×252). rf = risk-free rate
    annual (mặc định 0 — đơn giản hoá).
    """
    mu, cov, tickers = _annualize(returns_df)
    n = len(tickers)

    eq = np.ones(n) / n
    mv = _min_variance(cov)
    ms = _max_sharpe(mu, cov, rf)

    return {
        'tickers': tickers,
        'rf': rf,
        'equal_weight': {**_portfolio_stats(eq, mu, cov, rf), 'name': 'Equal Weight'},
        'min_variance': {**_portfolio_stats(mv, mu, cov, rf), 'name': 'Minimum Variance'},
        'max_sharpe':   {**_portfolio_stats(ms, mu, cov, rf), 'name': 'Tangency (Max Sharpe)'},
        'mu_annual': mu.tolist(),
        'cov_annual': cov.tolist(),
    }


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: _returns_fingerprint})
def efficient_frontier(returns_df: pd.DataFrame, n_points: int = 40,
                        rf: float = 0.0) -> dict:
    """Tính biên hiệu quả: với mỗi R_target ∈ [R_min, R_max], tìm w min-var.

    Dùng penalty method thuần numpy (KHÔNG cần scipy):
      Tối thiểu hoá  w' Σ w + λ₁ (w' μ - R_t)² + λ₂ (sum(w) - 1)²
    với projected gradient descent + chiếu simplex mỗi bước.

    Phương pháp đơn giản nhưng đủ chính xác cho 2-10 mã (use-case Portfolio
    page giới hạn 6 mã).
    """
    mu, cov, tickers = _annualize(returns_df)
    n = len(tickers)

    r_min = max(mu.min(), 0.0)
    r_max = mu.max()
    if r_max <= r_min:
        return {'tickers': tickers, 'points': [], 'rf': rf}

    targets = np.linspace(r_min, r_max, n_points)
    pts = []
    for r_t in targets:
        w = _solve_frontier_point(mu, cov, r_t)
        s = _portfolio_stats(w, mu, cov, rf)
        s['target_return'] = float(r_t)
        pts.append(s)

    return {'tickers': tickers, 'points': pts, 'rf': rf,
            'mu_annual': mu.tolist(),
            'cov_annual': cov.tolist()}


def _solve_frontier_point(mu: np.ndarray, cov: np.ndarray,
                            r_target: float,
                            n_iter: int = 600,
                            lr: float = 1e-3,
                            lambda_r: float = 2_000.0) -> np.ndarray:
    """Projected gradient descent đơn giản cho 1 điểm biên hiệu quả.

    Mục tiêu: min w'Σw + λ_r (w'μ - r_target)² s.t. w ∈ simplex.
    """
    n = len(mu)
    w = np.ones(n) / n        # khởi tạo equal-weight
    for _ in range(n_iter):
        grad = 2 * cov @ w + 2 * lambda_r * (w @ mu - r_target) * mu
        w = w - lr * grad
        w = _project_simplex(w)
    return w

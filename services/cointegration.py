"""Cointegration test (Engle-Granger 2-step 1987) + Pairs trading framework.

Bài toán:
  2 chuỗi giá X_t, Y_t cùng I(1) (không dừng, có unit root). Nếu tồn tại
  β sao cho Y_t - β·X_t = u_t là I(0) (dừng) → X và Y đồng tích hợp
  (cointegrated). Khi đó spread u_t mean-reverting → pairs trading.

Engle-Granger 2-step:
  Bước 1: Hồi quy OLS Y_t = α + β·X_t + u_t
  Bước 2: Test u_t có unit root không bằng ADF.
          H₀: u_t có unit root (KHÔNG cointegrated)
          Reject H₀ với p < 0.05 → cointegrated → có thể pairs-trade.

Z-score của spread:
  z_t = (u_t - mean(u)) / std(u)
  |z| > 2 → spread lệch >2σ → tín hiệu mean-reversion.

API:
  test_pair(price_a, price_b)        — Engle-Granger trên 1 cặp
  pair_matrix(prices_dict)           — ma trận p-value cho mọi cặp C(n,2)
  spread_zscore(price_a, price_b, b) — chuỗi z-score của spread

THAM KHẢO:
  Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error
    correction. Econometrica, 55(2). [Nobel 2003]
  Vidyamurthy, G. (2004). Pairs Trading: Quantitative methods and analysis.
  Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators
    for autoregressive time series with a unit root. JASA, 74.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional


# Hash fingerprint hợp nhất ở core/cache.py (v55) — single source of truth.
from core.cache import returns_fingerprint as _fingerprint


def test_pair(price_a: np.ndarray, price_b: np.ndarray) -> dict:
    """Engle-Granger test cho cặp (A, B). Trả:
      {beta_ols, alpha_ols, coint_t_stat, coint_p_value, adf_stat, adf_p,
       n_obs, is_cointegrated, current_z}
    """
    from statsmodels.tsa.stattools import coint, adfuller

    a = np.asarray(price_a, dtype=float)
    b = np.asarray(price_b, dtype=float)
    n = min(len(a), len(b))
    if n < 60:
        return {'beta_ols': float('nan'), 'coint_p_value': float('nan'),
                'is_cointegrated': False, 'n_obs': n,
                'error': f'Cần ≥ 60 phiên (hiện {n}).'}
    a, b = a[-n:], b[-n:]

    # OLS step 1: a = α + β·b + u
    n_obs = n
    b_mean = b.mean()
    a_mean = a.mean()
    cov_ab = float(np.mean((a - a_mean) * (b - b_mean)))
    var_b  = float(np.mean((b - b_mean) ** 2))
    if var_b <= 0:
        return {'beta_ols': float('nan'), 'coint_p_value': float('nan'),
                'is_cointegrated': False, 'n_obs': n,
                'error': 'Var(B) = 0.'}
    beta = cov_ab / var_b
    alpha = a_mean - beta * b_mean
    spread = a - (alpha + beta * b)

    # statsmodels coint test (uses Engle-Granger MacKinnon critical values)
    try:
        coint_t, coint_p, _ = coint(a, b)
    except Exception as e:
        coint_t, coint_p = float('nan'), float('nan')

    # ADF on residual spread (independent confirmation)
    try:
        adf_result = adfuller(spread, autolag='AIC')
        adf_stat, adf_p = float(adf_result[0]), float(adf_result[1])
    except Exception:
        adf_stat, adf_p = float('nan'), float('nan')

    # Current spread z-score
    sp_mean = float(spread.mean())
    sp_std = float(spread.std(ddof=1))
    current_z = float((spread[-1] - sp_mean) / sp_std) if sp_std > 0 else 0.0

    return {
        'beta_ols': float(beta),
        'alpha_ols': float(alpha),
        'coint_t_stat': float(coint_t) if coint_t == coint_t else float('nan'),
        'coint_p_value': float(coint_p) if coint_p == coint_p else float('nan'),
        'adf_stat': adf_stat,
        'adf_p': adf_p,
        'spread_mean': sp_mean,
        'spread_std': sp_std,
        'current_z': current_z,
        'n_obs': int(n_obs),
        'is_cointegrated': bool(coint_p == coint_p and coint_p < 0.05),
    }


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: _fingerprint})
def pair_matrix(prices_df: pd.DataFrame) -> dict:
    """Tính ma trận p-value cointegration cho mọi cặp C(n, 2).

    prices_df: index=date, columns=ticker, values=close price (raw).

    Trả {tickers, p_matrix (n×n, diag=1), pairs_significant (list dict đã
    sort theo p-value asc — cặp cointegrated nhất xếp đầu)}.
    """
    cols = list(prices_df.columns)
    n = len(cols)
    if n < 2:
        return {'tickers': cols, 'p_matrix': [], 'pairs_significant': []}
    p_mat = np.ones((n, n))
    pairs = []
    df = prices_df.dropna()
    for i in range(n):
        for j in range(i + 1, n):
            r = test_pair(df[cols[i]].values, df[cols[j]].values)
            p = r.get('coint_p_value', 1.0)
            if p != p:
                p = 1.0
            p_mat[i, j] = p_mat[j, i] = float(p)
            pairs.append({
                'a': cols[i], 'b': cols[j],
                'p_value': float(p),
                'beta': r.get('beta_ols'),
                'current_z': r.get('current_z'),
                'is_cointegrated': r.get('is_cointegrated', False),
            })
    pairs = sorted(pairs, key=lambda x: x['p_value'])
    return {'tickers': cols, 'p_matrix': p_mat.tolist(),
            'pairs_significant': pairs}


def spread_zscore(price_a: np.ndarray, price_b: np.ndarray,
                   beta: Optional[float] = None,
                   window: Optional[int] = None) -> dict:
    """Trả spread = A - β·B + (chuỗi z-score) — input cho chart pairs trading.

    Nếu beta=None tự fit OLS. window=None thì z-score rolling toàn bộ; nếu
    có window → rolling N phiên (mean/std cuộn).
    """
    a = np.asarray(price_a, dtype=float)
    b = np.asarray(price_b, dtype=float)
    n = min(len(a), len(b))
    if n < 30:
        return {'spread': np.array([]), 'z': np.array([])}
    a, b = a[-n:], b[-n:]
    if beta is None:
        b_mean, a_mean = b.mean(), a.mean()
        var_b = float(np.mean((b - b_mean) ** 2))
        beta = (float(np.mean((a - a_mean) * (b - b_mean))) / var_b) if var_b > 0 else 1.0
    spread = a - beta * b
    if window:
        s = pd.Series(spread)
        z = ((s - s.rolling(window).mean()) /
             s.rolling(window).std(ddof=1)).values
    else:
        sp_mean = spread.mean()
        sp_std = spread.std(ddof=1)
        z = (spread - sp_mean) / sp_std if sp_std > 0 else np.zeros_like(spread)
    return {'spread': spread, 'z': z, 'beta': float(beta)}

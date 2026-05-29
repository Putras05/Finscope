"""Monte Carlo projection — dự báo equity portfolio N ngày forward bằng
mô phỏng ngẫu nhiên dựa trên phân phối daily return lịch sử.

Hai phương pháp:
  • Bootstrap (mặc định) — resample (có hoàn lại) daily return từ dữ liệu
    lịch sử user → giữ phân phối thực nghiệm gồm fat tails.
  • GBM parametric (Geometric Brownian Motion, Boyle 1977) — fit μ, σ trên
    LOG returns, mô phỏng:
        log(S_t/S_{t-1}) ~ N((μ - σ²/2)·Δt, σ²·Δt)
    Áp dụng Itô correction (μ - σ²/2) — đảm bảo E[S_T] = S_0·exp(μ·T)
    đúng theo lý thuyết. Nếu mô phỏng r_t = N(μ, σ²) rồi cumprod(1+r) thì
    bias dương cỡ σ²/2 · T (với σ=2%/d, T=60d → +1.2%).

Đầu ra:
  • Mảng equity[n_paths, n_days+1] (path đầu = vốn ban đầu).
  • Percentile bands: p5, p25, median, p75, p95.
  • Probability of profit (P(equity_T > initial)).
  • VaR và CVaR 95% — loss tối đa với 95% confidence.

THAM KHẢO:
  Boyle, P. P. (1977). Options: A Monte Carlo Approach. J. of Financial Economics.
  Itô, K. (1944). Stochastic integral. Proc. Imperial Academy, Tokyo.
  Jorion, P. (2007). Value at Risk (3rd ed.).
"""
from __future__ import annotations
import numpy as np
from typing import Optional


def simulate(daily_returns: np.ndarray,
              initial_equity: float,
              horizon_days: int = 60,
              n_paths: int = 1000,
              method: str = 'bootstrap',
              seed: Optional[int] = None) -> dict:
    """Chạy Monte Carlo simulation.

    daily_returns: mảng tỉ lệ (KHÔNG phải %), ví dụ [0.012, -0.005, ...].
    method: 'bootstrap' (resample lịch sử) hoặc 'parametric' (Gaussian GBM).
    """
    if method not in ('bootstrap', 'parametric'):
        raise ValueError("method phải là 'bootstrap' hoặc 'parametric'")
    if initial_equity <= 0 or horizon_days <= 0 or n_paths <= 0:
        return {'paths': np.array([]), 'percentiles': {}, 'metrics': {}}
    rng = np.random.default_rng(seed)
    rets = np.asarray(daily_returns, dtype=float)
    rets = rets[np.isfinite(rets)]
    if len(rets) < 10:
        return {'paths': np.array([]), 'percentiles': {}, 'metrics': {},
                'error': 'Cần ≥ 10 phiên có return.'}

    if method == 'bootstrap':
        idx = rng.integers(0, len(rets), size=(n_paths, horizon_days))
        path_rets = rets[idx]
        # Equity = initial * Π(1 + r_t) cumulative
        cum = np.cumprod(1.0 + path_rets, axis=1)
        paths = np.hstack([np.ones((n_paths, 1)), cum]) * initial_equity
    else:
        # GBM parametric (Boyle 1977 + Itô correction) — fit μ, σ trên LOG
        # returns; mô phỏng log r ~ N((μ - σ²/2), σ²) để E[S_T] = S_0·exp(μT)
        # đúng theo Itô. Đây là chuẩn risk-neutral pricing.
        # GUARD: r <= -1 (wipeout/delisting/junk) → log1p(-1) = -inf →
        # mu_log NaN → toàn path NaN. Clip về -0.9999 + filter finite.
        rets_g = np.clip(rets, -0.9999, None)
        log_rets = np.log1p(rets_g)
        log_rets = log_rets[np.isfinite(log_rets)]
        if len(log_rets) < 10:
            return {'paths': np.array([]), 'percentiles': {}, 'metrics': {},
                    'error': 'GBM cần ≥ 10 phiên log-return hữu hạn.'}
        mu_log = float(np.mean(log_rets))
        sd_log = float(np.std(log_rets, ddof=1))
        drift = mu_log - 0.5 * sd_log ** 2          # Itô correction
        z = rng.normal(0.0, 1.0, size=(n_paths, horizon_days))
        log_path = drift + sd_log * z                # log-return per step
        cum_log = np.cumsum(log_path, axis=1)
        paths = np.hstack([np.zeros((n_paths, 1)), cum_log])
        paths = initial_equity * np.exp(paths)
        path_rets = np.expm1(log_path)                # cho compatible final stats

    final = paths[:, -1]
    pct_change_final = (final - initial_equity) / initial_equity * 100.0
    p5, p25, p50, p75, p95 = np.percentile(paths, [5, 25, 50, 75, 95], axis=0)
    prob_profit = float((final > initial_equity).mean() * 100.0)
    # VaR 95% — return THƯỜNG biểu diễn dưới dạng số dương (mức loss)
    var_95_loss_pct = float(-np.percentile(pct_change_final, 5))
    # CVaR (expected shortfall) — trung bình loss trong 5% worst case
    losses = pct_change_final[pct_change_final < -var_95_loss_pct] if var_95_loss_pct > 0 else \
              pct_change_final[pct_change_final < 0]
    cvar_95_loss_pct = float(-losses.mean()) if len(losses) else 0.0

    return {
        'paths': paths,            # (n_paths, horizon+1)
        'percentiles': {
            'p5': p5.tolist(), 'p25': p25.tolist(),
            'p50': p50.tolist(), 'p75': p75.tolist(),
            'p95': p95.tolist(),
        },
        'metrics': {
            'initial_equity': float(initial_equity),
            'horizon_days': int(horizon_days),
            'n_paths': int(n_paths),
            'method': method,
            'expected_final': float(np.mean(final)),
            'median_final': float(p50[-1]),
            'p5_final': float(p5[-1]),
            'p95_final': float(p95[-1]),
            'expected_return_pct': float(pct_change_final.mean()),
            'median_return_pct': float(np.median(pct_change_final)),
            'prob_profit_pct': prob_profit,
            'var_95_loss_pct': var_95_loss_pct,
            'cvar_95_loss_pct': cvar_95_loss_pct,
            'worst_path_loss_pct': float(pct_change_final.min()),
            'best_path_gain_pct': float(pct_change_final.max()),
        },
    }

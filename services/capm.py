"""CAPM — Capital Asset Pricing Model (Sharpe 1964, Lintner 1965, Treynor 1962).

Mô hình:
    E[R_i] - r_f = β_i · (E[R_m] - r_f)

Trong đó:
  • R_i — daily return cổ phiếu i
  • R_m — daily return chỉ số benchmark (VN-Index)
  • r_f — risk-free rate (lãi suất tiền gửi 12 tháng SBV ~4.7%/năm)
  • β_i = Cov(R_i, R_m) / Var(R_m)
  • α_i = E[R_i] - r_f - β_i · (E[R_m] - r_f)  (Jensen 1968)

β > 1: cổ phiếu nhạy hơn thị trường (chuyển động mạnh hơn)
β = 1: đồng pha thị trường
β < 1: defensive
β < 0: ngược chiều thị trường (rất hiếm)

α > 0: cổ phiếu vượt CAPM expectation (outperform)
α < 0: underperform

API:
  fetch_vnindex(start, end)         — lấy daily close VNINDEX qua vnstock
  align_returns(stock_df, vnindex_df) — căn theo ngày chung, tính returns
  compute_beta(r_stock, r_market, rf=0.0) — OLS β + α + R² + t-stat + p-value
  capm_table(tickers, rf, ...)      — bảng beta/alpha cho nhiều mã

THAM KHẢO:
  Sharpe, W. F. (1964). Capital asset prices. J. of Finance, 19(3).
  Lintner, J. (1965). The valuation of risk assets. RES, 47(1).
  Treynor, J. L. (1962). Toward a theory of market value of risky assets.
  Jensen, M. C. (1968). The performance of mutual funds 1945-1964. J. Finance.
"""
from __future__ import annotations
import contextlib
import io
import datetime as _dt
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_vnindex(start: str = '2016-01-01',
                  end: Optional[str] = None) -> pd.DataFrame:
    """Fetch daily close VN-Index qua vnstock VCI. Cache 6h.

    Trả DataFrame cột Ngay (date), Close (giá đóng cửa index).
    """
    from data._clients import vn_stock, throttle
    if end is None:
        end = _dt.date.today().isoformat()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        throttle()
        v = vn_stock('VNINDEX', 'VCI')
        df = v.quote.history(start=start, end=end, interval='1D')
    df = df.rename(columns={'time': 'Ngay', 'close': 'Close'})
    df['Ngay'] = pd.to_datetime(df['Ngay']).dt.date
    df = df.sort_values('Ngay').reset_index(drop=True)
    df['Return'] = df['Close'].pct_change()
    return df[['Ngay', 'Close', 'Return']]


def align_returns(stock_df: pd.DataFrame,
                   index_df: pd.DataFrame) -> tuple:
    """Inner join stock_df + index_df theo Ngay; trả (r_stock, r_market) — 2
    Series numpy aligned + dropped na.
    """
    if 'Return' not in stock_df.columns:
        stock_df = stock_df.copy()
        stock_df['Return'] = stock_df['Close'].pct_change()
    a = stock_df[['Ngay', 'Return']].rename(columns={'Return': 'rs'})
    b = index_df[['Ngay', 'Return']].rename(columns={'Return': 'rm'})
    j = pd.merge(a, b, on='Ngay').dropna()
    return j['rs'].values.astype(float), j['rm'].values.astype(float)


def compute_beta(r_stock: np.ndarray, r_market: np.ndarray,
                  rf_daily: float = 0.0) -> dict:
    """OLS hồi quy excess return cổ phiếu lên excess return thị trường:
        (R_i - rf) = α + β · (R_m - rf) + ε

    Trả {beta, alpha, alpha_annual_pct, r_squared, t_beta, p_beta, n_obs}.
    Sai số chuẩn dạng homoscedastic OLS (chưa robust). Nếu cần HAC dùng
    statsmodels.OLS().fit(cov_type='HAC') — overkill cho UI.
    """
    n = min(len(r_stock), len(r_market))
    if n < 30:
        return {'beta': float('nan'), 'alpha': float('nan'),
                'alpha_annual_pct': float('nan'),
                'r_squared': float('nan'),
                't_beta': float('nan'), 'p_beta': float('nan'),
                'n_obs': n, 'error': f'Cần ≥ 30 phiên overlap (hiện {n}).'}
    r_stock = r_stock[:n]
    r_market = r_market[:n]

    excess_s = r_stock - rf_daily
    excess_m = r_market - rf_daily
    x_mean = excess_m.mean()
    y_mean = excess_s.mean()
    cov_xy = float(np.mean((excess_m - x_mean) * (excess_s - y_mean)))
    var_x  = float(np.mean((excess_m - x_mean) ** 2))
    if var_x <= 0:
        return {'beta': float('nan'), 'alpha': float('nan'),
                'r_squared': float('nan'),
                't_beta': float('nan'), 'p_beta': float('nan'),
                'n_obs': n, 'error': 'Var(market) = 0.'}
    beta = cov_xy / var_x
    alpha = y_mean - beta * x_mean

    # R² + t-stat
    resid = excess_s - (alpha + beta * excess_m)
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((excess_s - y_mean) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # OLS std error of beta: σ_ε / √(Σ(x - x̄)²)
    sigma_e = float(np.sqrt(ss_res / max(n - 2, 1)))
    se_beta = sigma_e / np.sqrt(((excess_m - x_mean) ** 2).sum())
    t_beta = beta / se_beta if se_beta > 0 else float('nan')
    # p-value 2-tailed: dùng SURVIVAL FUNCTION (sf = 1 - cdf) thay vì
    # `1 - cdf` để giữ precision khi |t| > 8 (n lớn dễ xảy ra). Trước đây
    # underflow về 0.0 — Khoa Toán-Thống kê sẽ flag.
    try:
        from scipy.stats import t as _t
        p_beta = float(2 * _t.sf(abs(t_beta), df=n - 2))
    except Exception:
        # normal approx: erfc(x/√2) = 2(1 - Φ(x)) → 2-tailed p
        from math import erfc, sqrt
        p_beta = float(erfc(abs(t_beta) / sqrt(2)))

    return {
        'beta': float(beta),
        'alpha': float(alpha),
        'alpha_annual_pct': float(alpha * 252 * 100),    # hoá năm
        'r_squared': float(r2),
        't_beta': float(t_beta),
        'p_beta': float(p_beta),
        'n_obs': int(n),
    }


def capm_table(stock_data: dict, index_df: pd.DataFrame,
                rf_annual_pct: float = 4.7) -> list:
    """Tính CAPM cho nhiều mã. stock_data = {ticker: stock_df (có cột Close+Ngay)}.

    Trả list dict sắp xếp theo alpha desc — outperform xếp đầu.
    """
    rf_daily = (rf_annual_pct / 100.0) / 252.0
    rows = []
    for tk, sdf in stock_data.items():
        r_s, r_m = align_returns(sdf, index_df)
        res = compute_beta(r_s, r_m, rf_daily=rf_daily)
        res['ticker'] = tk
        rows.append(res)
    # Sort: alpha_annual_pct desc (mã outperform đứng đầu).
    # BUG cũ: `... or -999` xử lý 0.0 như falsy (đẩy lên đầu),
    # và NaN làm key undefined order. Dùng key tường minh.
    def _alpha_key(r):
        a = r.get('alpha_annual_pct')
        if a is None or a != a:    # NaN check
            return float('inf')    # xếp xuống cuối
        return -float(a)
    rows = sorted(rows, key=_alpha_key)
    return rows

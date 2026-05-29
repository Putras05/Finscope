"""PCA — Principal Component Analysis (Pearson 1901, Hotelling 1933) trên
ma trận hiệp phương sai/tương quan daily returns của portfolio.

Mục đích:
  • Diễn giải các "yếu tố ẩn" (latent factors) chi phối nhiều cổ phiếu
    cùng lúc — đặc biệt hữu ích khi rổ mã có correlation cao.
  • PC1 thường gần với "thị trường chung" (market factor); PC2/PC3 có
    thể là sector / size / momentum factor.
  • Variance explained cho biết bao nhiêu thông tin nén được vào k component
    đầu — basis cho dimensionality reduction.

Thuật toán (closed-form, numpy only):
  1. Chuẩn hoá returns matrix R về z-score (mean 0, std 1) theo từng mã.
  2. Tính correlation matrix C = (1/n) Z'Z.
  3. Eigendecomp C = V Λ V' qua numpy.linalg.eigh (symmetric).
  4. Sort eigenvalues desc, trả top k.

API:
  pca_decompose(returns_df) → eigenvalues, var_explained, loadings, scores

THAM KHẢO:
  Pearson, K. (1901). On lines and planes of closest fit. Philosophical Magazine.
  Hotelling, H. (1933). Analysis of a complex of statistical variables into
    principal components. J. of Educational Psychology, 24.
  Jolliffe, I. T. (2002). Principal Component Analysis (2nd ed.). Springer.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st


# Hash fingerprint hợp nhất ở core/cache.py (v55) — single source of truth.
from core.cache import returns_fingerprint as _fingerprint


@st.cache_data(ttl=900, show_spinner=False,
                 hash_funcs={pd.DataFrame: _fingerprint})
def pca_decompose(returns_df: pd.DataFrame,
                   use_corr: bool = True) -> dict:
    """Phân rã PCA trên returns_df (index=date, cols=ticker, values=daily return).

    use_corr=True (mặc định) — dùng ma trận tương quan (standardize trước),
    use_corr=False — dùng ma trận hiệp phương sai thô.

    Trả dict:
      tickers, n_obs, n_components
      eigenvalues          — mảng giá trị riêng đã sort desc (Λ)
      var_explained        — Λ_i / Σ Λ — tỷ trọng phương sai mỗi PC
      cum_var_explained    — cumulative sum
      loadings             — V (k × k), cột i = PC_i, hàng j = mã j
      scores               — Z @ V (n × k), điểm portfolio trên không gian PC
      pc1_pc2_loadings     — list (ticker, l1, l2) cho biplot 2D
    """
    rets = returns_df.dropna()
    if len(rets) < 30 or rets.shape[1] < 2:
        raise ValueError(f'PCA cần ≥ 30 phiên và ≥ 2 mã (hiện {rets.shape}).')
    # Quy chuẩn về tỉ lệ (ratio) nếu giá trị > 1 (% scale)
    if rets.abs().median().median() > 1.0:
        rets = rets / 100.0

    cols = list(rets.columns)
    X = rets.values
    n, k = X.shape

    # Standardize
    mu = X.mean(axis=0)
    sd = X.std(axis=0, ddof=1)
    sd_safe = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd_safe

    if use_corr:
        M = (Z.T @ Z) / (n - 1)              # correlation matrix
    else:
        Xc = X - mu
        M = (Xc.T @ Xc) / (n - 1)            # covariance matrix

    # eigh trên symmetric — eigenvalues ascending
    eig_vals, eig_vecs = np.linalg.eigh(M)
    # Sort descending
    order = np.argsort(eig_vals)[::-1]
    eig_vals = eig_vals[order]
    eig_vecs = eig_vecs[:, order]

    total = float(eig_vals.sum())
    var_exp = eig_vals / total if total > 0 else np.zeros_like(eig_vals)
    cum_var = np.cumsum(var_exp)

    # Project Z lên k component đầu
    scores = Z @ eig_vecs

    # Biplot 2D: loading PC1 vs PC2 cho từng mã
    pc1_pc2 = []
    if k >= 2:
        for i, tk in enumerate(cols):
            pc1_pc2.append({'ticker': tk,
                             'loading_pc1': float(eig_vecs[i, 0]),
                             'loading_pc2': float(eig_vecs[i, 1])})

    return {
        'tickers': cols,
        'n_obs': int(n),
        'n_components': int(k),
        'eigenvalues': eig_vals.tolist(),
        'var_explained': var_exp.tolist(),
        'cum_var_explained': cum_var.tolist(),
        'loadings': eig_vecs.tolist(),       # (k, k)
        'scores': scores.tolist(),           # (n, k)
        'pc1_pc2_loadings': pc1_pc2,
        'method': 'correlation' if use_corr else 'covariance',
    }

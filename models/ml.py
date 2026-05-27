"""Mô hình HỌC MÁY cây tăng cường (Gradient Boosting) cho FinScope.

GBR(p): học phi tuyến trên 6 đặc trưng kỹ thuật × p lag để dự báo lợi suất
phiên kế tiếp, rồi quy về giá. Thường là top performer cho dữ liệu dạng bảng.
Trả về dict cùng shape AR/MLR/ARIMA (ytr/ptr/yte/pte/dates/next_pred + CI).
"""
import numpy as np
import streamlit as st

from data.fetcher import fetch_data

_FEATS = ['Return', 'Volume_ratio', 'Range_ratio', 'MA5_ratio', 'MA20_ratio', 'RSI14']
_Z95 = 1.959963985
_Z80 = 1.281551566


@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_gbr(ticker: str, train_ratio: float, p: int = 1,
            date_from=None, date_to=None) -> dict:
    """Gradient Boosting Regressor — dự báo lợi suất phiên kế tiếp.

    Đặc trưng: 6 chỉ báo kỹ thuật × p lag. Target: R_{t+1}=100·(Y_{t+1}/Y_t−1).
    Phục hồi giá: Ŷ_{t+1}=Y_t·(1+R̂/100). CI 80/95 từ ±z·σ(sai số test).
    """
    from sklearn.ensemble import GradientBoostingRegressor

    df = fetch_data(ticker, date_from, date_to)
    N = len(df)
    close = df['Close'].values.astype(float)
    raw = df[_FEATS].values.astype(float)
    dates_full = df['Ngay'].values

    num = N - p
    if num < 30:
        raise ValueError(f'Not enough data: N={N}, p={p}')

    cols = [raw[p - 1 - k: p - 1 - k + num, :] for k in range(p)]
    X_full = np.hstack(cols)
    close_t = close[p - 1: p - 1 + num]
    close_t1 = close[p: p + num]
    Y_ret = 100.0 * (close_t1 / close_t - 1.0)

    mask = ~(np.isnan(X_full).any(axis=1) | np.isnan(Y_ret))
    X_full, Y_ret = X_full[mask], Y_ret[mask]
    close_t, close_t1 = close_t[mask], close_t1[mask]
    if len(X_full) < 30:
        raise ValueError('Not enough valid samples')

    nt_adj = max(10, min(int(N * train_ratio) - p, len(X_full) - 10))
    Xtr, Ytr_ret = X_full[:nt_adj], Y_ret[:nt_adj]
    Xte = X_full[nt_adj:]
    ctr, cte = close_t[:nt_adj], close_t[nt_adj:]

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42).fit(Xtr, Ytr_ret)

    ptr = ctr * (1 + model.predict(Xtr) / 100.0)
    pte = cte * (1 + model.predict(Xte) / 100.0)
    ytr = close_t1[:nt_adj]
    yte = close_t1[nt_adj:]

    # Dự báo phiên kế tiếp
    x_next = np.concatenate([raw[N - 1 - k, :] for k in range(p)]).reshape(1, -1)
    ret_next = float(model.predict(x_next)[0])
    next_pred = float(close[-1] * (1 + ret_next / 100.0))

    sigma = float(np.std(yte - pte)) if len(yte) > 1 else float(np.std(ytr - ptr))

    # Độ quan trọng đặc trưng (gộp theo lag)
    imp_raw = model.feature_importances_
    imp = {f: float(imp_raw[[i + len(_FEATS) * k for k in range(p)]].sum())
           for i, f in enumerate(_FEATS)}

    dates_all = dates_full[p:p + (N - p)][mask]
    return dict(
        name='Gradient Boosting', engine='sklearn GradientBoosting', ok=True,
        params=f'GBR · 200 cây · depth 3 · 6 đặc trưng × {p} lag',
        summary=f'Gradient Boosting · {6*p} đặc trưng',
        importances=imp, p=int(p), nt=nt_adj,
        ytr=ytr, ptr=ptr, yte=yte, pte=pte,
        dates_tr=dates_all[:nt_adj], dates_te=dates_all[nt_adj:],
        next_pred=next_pred, ret_pred=ret_next,
        next_lower=next_pred - _Z95 * sigma, next_upper=next_pred + _Z95 * sigma,
        next_lower80=next_pred - _Z80 * sigma, next_upper80=next_pred + _Z80 * sigma,
        pte_lower=pte - _Z95 * sigma, pte_upper=pte + _Z95 * sigma,
        pte_lower80=pte - _Z80 * sigma, pte_upper80=pte + _Z80 * sigma,
        close_full=close, dates_full=dates_full,
    )

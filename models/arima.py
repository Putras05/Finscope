"""ARIMA(p,d,q) — mô hình chuỗi thời gian Box-Jenkins (thay thế CART).

Khác với AR/MLR (hồi quy tuyến tính thủ công bằng numpy), ARIMA dùng
``statsmodels`` để ước lượng hợp lý cực đại (MLE) và cung cấp **khoảng dự báo**
(prediction interval) giải tích — nền tảng cho chức năng "Khoảng tin cậy".

Trả về cùng cấu trúc dict với các model khác (ytr/ptr/yte/pte/dates/next_pred…)
để tương thích với toàn bộ chart & page, đồng thời bổ sung các khóa riêng cho
ARIMA: order, aic, bic, resid, fitted, các dải CI cho test + phiên kế tiếp.
"""
import warnings
import numpy as np
import streamlit as st

from data.fetcher import fetch_data

warnings.filterwarnings('ignore')

# Trần bậc AR khi auto-chọn order — ARIMA bậc quá cao vừa chậm vừa overfit.
# Tham số p từ sidebar chỉ dùng làm "trần tìm kiếm", không ép cứng.
_P_CEIL = 4
_Q_CEIL = 2


def _choose_d(y: np.ndarray, d_max: int = 2) -> int:
    """Chọn bậc sai phân d bằng kiểm định ADF (Augmented Dickey-Fuller).

    Sai phân tới khi chuỗi dừng (p-value < 0.05) hoặc chạm d_max.
    Giá cổ phiếu hầu như luôn cho d=1.
    """
    try:
        from statsmodels.tsa.stattools import adfuller
    except Exception:
        return 1
    s = np.asarray(y, dtype=float)
    for d in range(d_max + 1):
        if len(s) < 10:
            return d
        try:
            pval = adfuller(s, autolag='AIC')[1]
        except Exception:
            return min(d + 1, d_max)
        if pval < 0.05:
            return d
        s = np.diff(s)
    return d_max


def _auto_order(y: np.ndarray, p_ceil: int, q_ceil: int):
    """Tìm (p,d,q) tối ưu theo AIC trên lưới nhỏ. Trả về (order, fitted_results).

    d cố định theo ADF; p,q quét lưới. Bỏ qua (0,d,0) vô nghĩa.
    """
    from statsmodels.tsa.arima.model import ARIMA

    d = _choose_d(y)
    best = None  # (aic, order, results)
    for p in range(0, p_ceil + 1):
        for q in range(0, q_ceil + 1):
            if p == 0 and q == 0:
                continue
            try:
                res = ARIMA(
                    y, order=(p, d, q),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                ).fit(method_kwargs={'warn_convergence': False})
                aic = float(res.aic)
                if not np.isfinite(aic):
                    continue
                if best is None or aic < best[0]:
                    best = (aic, (p, d, q), res)
            except Exception:
                continue
    return best


def _np_ar_fallback(y, nt, p, dates):
    """Dự phòng khi statsmodels không khả dụng: AR(p) bằng numpy lstsq + CI từ
    sai số dự báo (giống thông lệ AR/MLR). Bảo đảm app vẫn chạy."""
    p = max(1, min(int(p), 5))
    N = len(y)
    num = N - p
    X = np.column_stack([y[p - 1 - k: p - 1 - k + num] for k in range(p)])
    Y = y[p: p + num]
    Xd = np.column_stack([X, np.ones(len(X))])
    beta, *_ = np.linalg.lstsq(Xd, Y, rcond=None)
    fitted = Xd @ beta
    nt_s = max(10, min(nt - p, num - 10))
    ytr, ptr = Y[:nt_s], fitted[:nt_s]
    yte, pte = Y[nt_s:], fitted[nt_s:]
    sigma = float(np.std(yte - pte)) if len(yte) > 1 else float(np.std(Y - fitted))
    z95, z80 = 1.959963985, 1.281551566
    x_next = y[N - 1: N - 1 - p: -1]
    next_pred = float(beta[:p] @ x_next + beta[p])
    d_all = np.asarray(dates)
    d_s = d_all[p: p + num]
    return dict(
        order=(p, 0, 0), aic=float('nan'), bic=float('nan'),
        resid=(Y - fitted), fitted=fitted,
        nt=nt_s, p=p,
        ytr=ytr, ptr=ptr, yte=yte, pte=pte,
        dates_tr=d_s[:nt_s], dates_te=d_s[nt_s:],
        pte_lower=pte - z95 * sigma, pte_upper=pte + z95 * sigma,
        pte_lower80=pte - z80 * sigma, pte_upper80=pte + z80 * sigma,
        next_pred=next_pred,
        next_lower=next_pred - z95 * sigma, next_upper=next_pred + z95 * sigma,
        next_lower80=next_pred - z80 * sigma, next_upper80=next_pred + z80 * sigma,
        ljungbox_p=float('nan'), sigma2=sigma ** 2,
        close_full=np.asarray(y, dtype=float), dates_full=d_all,
        engine='numpy-AR (fallback)',
    )


@st.cache_data(ttl=1800, show_spinner=False)
def run_arima(ticker: str, train_ratio: float, p: int = 1,
              date_from=None, date_to=None) -> dict:
    """ARIMA(p,d,q) dự báo 1 phiên kế tiếp trên giá đóng cửa.

    - order tự chọn theo AIC (d theo ADF; p,q quét lưới, p làm trần tìm kiếm).
    - Dự báo test = 1-bước-tới (dynamic=False) → so sánh công bằng với AR/MLR.
    - Khoảng dự báo 95% & 80% lấy trực tiếp từ phân phối hậu nghiệm của ARIMA.
    """
    if p < 1:
        raise ValueError(f'p must be >= 1, got p={p}')

    df = fetch_data(ticker, date_from, date_to)
    N = len(df)
    y = df['Close'].values.astype(float)
    dates_full = df['Ngay'].values
    nt = int(N * train_ratio)
    nt = max(20, min(nt, N - 10))  # đảm bảo đủ train & test

    try:
        from statsmodels.tsa.arima.model import ARIMA  # noqa: F401
    except Exception:
        return _np_ar_fallback(y, nt, p, dates_full)

    ytr_raw = y[:nt]
    yte_raw = y[nt:]

    p_ceil = min(max(int(p), 1), _P_CEIL)
    best = _auto_order(ytr_raw, p_ceil, _Q_CEIL)
    if best is None:
        return _np_ar_fallback(y, nt, p, dates_full)

    _, order, res = best

    # ── Dự báo 1-bước-tới trên test: append toàn bộ test (không refit) rồi
    #    lấy prediction dynamic=False (mỗi điểm dùng giá trị thực quá khứ). ──
    try:
        res_full = res.append(yte_raw, refit=False)
    except Exception:
        # Một số phiên bản statsmodels cần .extend cho mô hình không exog
        res_full = res.extend(yte_raw)

    # Test forecasts + CI
    pred_te = res_full.get_prediction(start=nt, end=N - 1, dynamic=False)
    pte = np.asarray(pred_te.predicted_mean, dtype=float)
    ci95 = np.asarray(pred_te.conf_int(alpha=0.05), dtype=float)
    ci80 = np.asarray(pred_te.conf_int(alpha=0.20), dtype=float)
    pte_lower, pte_upper = ci95[:, 0], ci95[:, 1]
    pte_lower80, pte_upper80 = ci80[:, 0], ci80[:, 1]

    # In-sample (train) fitted 1-bước-tới
    pred_tr = res_full.get_prediction(start=0, end=nt - 1, dynamic=False)
    ptr_all = np.asarray(pred_tr.predicted_mean, dtype=float)

    # Loại bỏ điểm đầu không xác định (do sai phân/khởi tạo)
    d_order = order[1]
    warm = max(d_order, order[0], 1)
    ytr = ytr_raw[warm:]
    ptr = ptr_all[warm:]
    finite = np.isfinite(ptr)
    ytr, ptr = ytr[finite], ptr[finite]

    # ── Dự báo phiên kế tiếp (out-of-sample, h=1) + CI ──
    fc = res_full.get_forecast(steps=1)
    next_pred = float(np.asarray(fc.predicted_mean, dtype=float)[0])
    nci95 = np.asarray(fc.conf_int(alpha=0.05), dtype=float)[0]
    nci80 = np.asarray(fc.conf_int(alpha=0.20), dtype=float)[0]

    # Chẩn đoán phần dư: Ljung-Box (kiểm tra tự tương quan phần dư)
    resid = np.asarray(res.resid, dtype=float)
    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox
        lb = acorr_ljungbox(resid[warm:], lags=[10], return_df=True)
        ljungbox_p = float(lb['lb_pvalue'].iloc[0])
    except Exception:
        ljungbox_p = float('nan')

    dates_tr_all = dates_full[:nt]
    dates_tr = dates_tr_all[warm:][finite]
    dates_te = dates_full[nt:]

    return dict(
        order=order,
        aic=float(res.aic),
        bic=float(res.bic),
        resid=resid,
        fitted=ptr_all,
        nt=nt,
        p=int(p),
        ytr=ytr, ptr=ptr,
        yte=yte_raw, pte=pte,
        dates_tr=dates_tr, dates_te=dates_te,
        pte_lower=pte_lower, pte_upper=pte_upper,
        pte_lower80=pte_lower80, pte_upper80=pte_upper80,
        next_pred=next_pred,
        next_lower=float(nci95[0]), next_upper=float(nci95[1]),
        next_lower80=float(nci80[0]), next_upper80=float(nci80[1]),
        ljungbox_p=ljungbox_p,
        sigma2=float(getattr(res, 'mse', np.var(resid))),
        close_full=y, dates_full=dates_full,
        engine='statsmodels ARIMA',
    )

"""Bộ mô hình thống kê nâng cao cho chức năng "Khoảng tin cậy".

Bốn họ mô hình, mỗi mô hình trả về dict có CẤU TRÚC THỐNG NHẤT để trang
"Mô hình Nâng cao" vẽ fan chart + bảng CI đồng bộ:

    SARIMA   — ARIMA có thành phần mùa vụ (chu kỳ tuần giao dịch s=5)
    ETS/HW   — Exponential Smoothing (Holt-Winters, statespace ETSModel)
    GARCH    — AR(1) mean + GARCH(1,1) volatility (dự báo biến động & CI giá)
    SARIMAX  — ARIMA + biến ngoại sinh (Volume, Range)

Shape thống nhất (giá đơn vị nghìn đồng, như toàn app):
    name, engine, params, summary,
    yte, pte, dates_te, nt,
    pte_lower/upper (95%), pte_lower80/upper80 (80%),
    next_pred, next_lower/upper (95%), next_lower80/upper80 (80%),
    close_full, dates_full, + khóa riêng (aic, bic, ljungbox_p, vol_next…)
"""
import warnings
import numpy as np
import streamlit as st

from data.fetcher import fetch_data

warnings.filterwarnings('ignore')

_Z95 = 1.959963985
_Z80 = 1.281551566
_SEASON = 5  # tuần giao dịch HOSE: 5 phiên


def _split(ticker, train_ratio, date_from, date_to):
    df = fetch_data(ticker, date_from, date_to)
    N = len(df)
    y = df['Close'].values.astype(float)
    dates = df['Ngay'].values
    nt = max(30, min(int(N * train_ratio), N - 10))
    return df, N, y, dates, nt


def _params_dict(res) -> dict:
    """Trích tham số ước lượng thành dict {tên: giá trị}, chịu được cả
    pandas Series (arch/statsmodels input pandas) lẫn numpy ndarray
    (SARIMAX fit từ numpy → dùng res.param_names)."""
    p = getattr(res, 'params', None)
    if p is None:
        return {}
    names = list(getattr(res, 'param_names', []) or [])
    try:
        vals = np.asarray(getattr(p, 'values', p), dtype=float).ravel()
    except Exception:
        vals = None
    # Ưu tiên param_names (tên mô tả: smoothing_level, ar.L1...) khi khớp độ dài.
    if names and vals is not None and len(names) == len(vals):
        return {str(n): float(v) for n, v in zip(names, vals)}
    if hasattr(p, 'items'):  # pandas Series (vd. arch — index đã là tên)
        try:
            return {str(k): float(v) for k, v in p.items()}
        except Exception:
            pass
    return {}


def _ci_from_sigma(point, sigma):
    """Fallback CI khi mô hình không cho khoảng giải tích trực tiếp."""
    point = np.asarray(point, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    return (point - _Z95 * sigma, point + _Z95 * sigma,
            point - _Z80 * sigma, point + _Z80 * sigma)


def _empty_like(name, engine, y, dates, nt, msg):
    """Dict hợp lệ tối thiểu khi mô hình lỗi/không khả dụng — page không vỡ."""
    yte = y[nt:]
    pte = np.full_like(yte, np.nan, dtype=float)
    nanrow = np.full_like(yte, np.nan, dtype=float)
    return dict(
        name=name, engine=engine, params='—', summary=msg, ok=False,
        yte=yte, pte=pte, dates_te=dates[nt:], nt=nt,
        pte_lower=nanrow, pte_upper=nanrow,
        pte_lower80=nanrow, pte_upper80=nanrow,
        next_pred=float('nan'),
        next_lower=float('nan'), next_upper=float('nan'),
        next_lower80=float('nan'), next_upper80=float('nan'),
        close_full=np.asarray(y, dtype=float), dates_full=dates,
    )


# ════════════════════════════════════════════════════════════════════════════
#  SARIMA
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_sarima(ticker: str, train_ratio: float, p: int = 1,
               date_from=None, date_to=None) -> dict:
    df, N, y, dates, nt = _split(ticker, train_ratio, date_from, date_to)
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from statsmodels.tsa.arima.model import ARIMA  # noqa: F401
    except Exception:
        return _empty_like('SARIMA', 'statsmodels SARIMAX', y, dates, nt,
                           'statsmodels chưa được cài đặt.')
    ytr = y[:nt]; yte = y[nt:]
    pc = min(max(int(p), 1), 2)
    order = (pc, 1, 1)
    seasonal_order = (1, 0, 1, _SEASON)
    try:
        res = SARIMAX(ytr, order=order, seasonal_order=seasonal_order,
                      enforce_stationarity=False, enforce_invertibility=False
                      ).fit(disp=False)
        try:
            res_full = res.append(yte, refit=False)
        except Exception:
            res_full = res.extend(yte)
        pred = res_full.get_prediction(start=nt, end=N - 1, dynamic=False)
        pte = np.asarray(pred.predicted_mean, dtype=float)
        c95 = np.asarray(pred.conf_int(alpha=0.05), dtype=float)
        c80 = np.asarray(pred.conf_int(alpha=0.20), dtype=float)
        fc = res_full.get_forecast(steps=1)
        npred = float(np.asarray(fc.predicted_mean, dtype=float)[0])
        n95 = np.asarray(fc.conf_int(alpha=0.05), dtype=float)[0]
        n80 = np.asarray(fc.conf_int(alpha=0.20), dtype=float)[0]
        _coef = _params_dict(res)
        return dict(
            name='SARIMA', engine='statsmodels SARIMAX', ok=True,
            params=f'order={order} · seasonal={seasonal_order}',
            summary=f'SARIMA{order}×{seasonal_order} · AIC={res.aic:.1f}',
            aic=float(res.aic), bic=float(res.bic), coef=_coef,
            order=order, seasonal_order=seasonal_order,
            yte=yte, pte=pte, dates_te=dates[nt:], nt=nt,
            pte_lower=c95[:, 0], pte_upper=c95[:, 1],
            pte_lower80=c80[:, 0], pte_upper80=c80[:, 1],
            next_pred=npred,
            next_lower=float(n95[0]), next_upper=float(n95[1]),
            next_lower80=float(n80[0]), next_upper80=float(n80[1]),
            close_full=y, dates_full=dates,
        )
    except Exception as e:
        return _empty_like('SARIMA', 'statsmodels SARIMAX', y, dates, nt,
                           f'Lỗi fit SARIMA: {str(e)[:120]}')


# ════════════════════════════════════════════════════════════════════════════
#  Holt-Winters / ETS (Exponential Smoothing — statespace)
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_ets(ticker: str, train_ratio: float, p: int = 1,
            date_from=None, date_to=None) -> dict:
    import pandas as pd
    df, N, y, dates, nt = _split(ticker, train_ratio, date_from, date_to)
    try:
        from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    except Exception:
        return _empty_like('Holt-Winters (ETS)', 'statsmodels ETSModel',
                           y, dates, nt, 'statsmodels chưa được cài đặt.')
    yte = y[nt:]
    try:
        # ETSModel yêu cầu input pandas Series (cần .index cho get_prediction).
        ys = pd.Series(y)
        _kw = dict(error='add', trend='add', damped_trend=True, seasonal=None)
        # Ước lượng tham số CHỈ trên train → tránh rò rỉ dữ liệu test.
        res_tr = ETSModel(ys.iloc[:nt], **_kw).fit(disp=False)
        # Áp tham số train lên toàn chuỗi (smooth, KHÔNG refit) để lấy dự báo
        # 1-bước-tới trên test dùng giá trị thực quá khứ.
        res_full = ETSModel(ys, **_kw).smooth(res_tr.params)

        sf = res_full.get_prediction(start=nt, end=N - 1).summary_frame(alpha=0.05)
        sf80 = res_full.get_prediction(start=nt, end=N - 1).summary_frame(alpha=0.20)
        pte = sf['mean'].to_numpy(dtype=float)
        lo95, hi95 = sf['pi_lower'].to_numpy(float), sf['pi_upper'].to_numpy(float)
        lo80, hi80 = sf80['pi_lower'].to_numpy(float), sf80['pi_upper'].to_numpy(float)

        sfn = res_full.get_prediction(start=N, end=N).summary_frame(alpha=0.05)
        sfn80 = res_full.get_prediction(start=N, end=N).summary_frame(alpha=0.20)
        npred = float(sfn['mean'].iloc[0])
        nlo95, nhi95 = float(sfn['pi_lower'].iloc[0]), float(sfn['pi_upper'].iloc[0])
        nlo80, nhi80 = float(sfn80['pi_lower'].iloc[0]), float(sfn80['pi_upper'].iloc[0])

        _coef = _params_dict(res_tr)
        return dict(
            name='Holt-Winters (ETS)', engine='statsmodels ETSModel', ok=True,
            params='error=add · trend=add · damped',
            summary=f'ETS(A,Ad,N) · AIC={res_tr.aic:.1f}',
            aic=float(res_tr.aic), bic=float(res_tr.bic), coef=_coef,
            yte=yte, pte=pte, dates_te=dates[nt:], nt=nt,
            pte_lower=lo95, pte_upper=hi95,
            pte_lower80=lo80, pte_upper80=hi80,
            next_pred=npred,
            next_lower=nlo95, next_upper=nhi95,
            next_lower80=nlo80, next_upper80=nhi80,
            close_full=y, dates_full=dates,
        )
    except Exception as e:
        return _empty_like('Holt-Winters (ETS)', 'statsmodels ETSModel',
                           y, dates, nt, f'Lỗi fit ETS: {str(e)[:120]}')


# ════════════════════════════════════════════════════════════════════════════
#  GARCH — AR(1) mean + GARCH(1,1) volatility
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_garch(ticker: str, train_ratio: float, p: int = 1,
              date_from=None, date_to=None) -> dict:
    df, N, y, dates, nt = _split(ticker, train_ratio, date_from, date_to)
    # Lợi suất % theo phiên
    ret = 100.0 * (y[1:] / y[:-1] - 1.0)
    ret = np.concatenate([[0.0], ret])
    try:
        from arch import arch_model
    except Exception:
        # Fallback: EWMA volatility + AR(1) mean thủ công
        return _garch_ewma_fallback(y, ret, dates, nt)
    try:
        # ret_arr[j] (j=0..N-2) = lợi suất tại chỉ số giá j+1. Fit AR(1)-GARCH
        # trên train, cố định tham số rồi forecast 1-bước-tới analytic.
        ret_arr = ret[1:]                  # độ dài N-1
        m = N - nt
        am = arch_model(ret_arr[:nt - 1], mean='AR', lags=1, vol='GARCH',
                        p=1, o=0, q=1, dist='normal', rescale=False)
        res = am.fit(disp='off', show_warning=False)
        am_full = arch_model(ret_arr, mean='AR', lags=1, vol='GARCH',
                             p=1, o=0, q=1, dist='normal', rescale=False)
        fixed = am_full.fix(res.params)

        # start=nt-2 → các origin j=nt-2..N-2 (m+1 hàng): m hàng đầu dự báo
        # giá test y[nt..N-1]; hàng cuối là phiên kế tiếp (out-of-sample).
        fc = fixed.forecast(horizon=1, start=nt - 2, reindex=False)
        mean_all = np.asarray(fc.mean.values, dtype=float).ravel()
        sig_all = np.sqrt(np.maximum(
            np.asarray(fc.variance.values, dtype=float).ravel(), 1e-12))

        mean_fc, sig_fc = mean_all[:m], sig_all[:m]
        mn, sn = float(mean_all[-1]), float(sig_all[-1])

        # Lợi suất → giá: P̂_t = P_{t-1}·(1 + r̂_t/100)
        prev_close = y[nt - 1:N - 1]
        pte = prev_close * (1.0 + mean_fc / 100.0)
        lo95 = prev_close * (1.0 + (mean_fc - _Z95 * sig_fc) / 100.0)
        hi95 = prev_close * (1.0 + (mean_fc + _Z95 * sig_fc) / 100.0)
        lo80 = prev_close * (1.0 + (mean_fc - _Z80 * sig_fc) / 100.0)
        hi80 = prev_close * (1.0 + (mean_fc + _Z80 * sig_fc) / 100.0)

        # Phiên kế tiếp
        last = y[-1]
        npred = last * (1.0 + mn / 100.0)
        nlo95 = last * (1.0 + (mn - _Z95 * sn) / 100.0)
        nhi95 = last * (1.0 + (mn + _Z95 * sn) / 100.0)
        nlo80 = last * (1.0 + (mn - _Z80 * sn) / 100.0)
        nhi80 = last * (1.0 + (mn + _Z80 * sn) / 100.0)

        _coef = _params_dict(res)
        return dict(
            name='GARCH', engine='arch · AR(1)+GARCH(1,1)', ok=True,
            params='mean=AR(1) · vol=GARCH(1,1) · dist=Normal',
            summary=f'AR(1)-GARCH(1,1) · σ phiên tới ≈ {sn:.2f}%',
            coef=_coef,
            yte=y[nt:], pte=pte, dates_te=dates[nt:], nt=nt,
            pte_lower=lo95, pte_upper=hi95,
            pte_lower80=lo80, pte_upper80=hi80,
            next_pred=npred,
            next_lower=nlo95, next_upper=nhi95,
            next_lower80=nlo80, next_upper80=nhi80,
            vol_test=sig_fc, vol_next=sn,
            close_full=y, dates_full=dates,
        )
    except Exception as e:
        return _empty_like('GARCH', 'arch', y, dates, nt,
                           f'Lỗi fit GARCH: {str(e)[:120]}')


def _garch_ewma_fallback(y, ret, dates, nt):
    """Khi thiếu thư viện `arch`: ước lượng biến động bằng EWMA (RiskMetrics
    λ=0.94) + dự báo điểm bằng random-walk (giá hôm trước)."""
    N = len(y)
    lam = 0.94
    var = np.zeros(N)
    var[1] = ret[1] ** 2 if N > 1 else 1.0
    for t in range(2, N):
        var[t] = lam * var[t - 1] + (1 - lam) * ret[t - 1] ** 2
    sig = np.sqrt(np.maximum(var, 1e-12))
    prev_close = y[nt - 1:N - 1]
    sig_te = sig[nt:N]
    pte = prev_close.copy()
    lo95 = prev_close * (1 - _Z95 * sig_te / 100.0)
    hi95 = prev_close * (1 + _Z95 * sig_te / 100.0)
    lo80 = prev_close * (1 - _Z80 * sig_te / 100.0)
    hi80 = prev_close * (1 + _Z80 * sig_te / 100.0)
    sn = float(sig[-1])
    last = y[-1]
    return dict(
        name='GARCH', engine='EWMA λ=0.94 (fallback)', ok=True,
        params='RiskMetrics EWMA · λ=0.94',
        summary=f'EWMA volatility · σ phiên tới ≈ {sn:.2f}%',
        yte=y[nt:], pte=pte, dates_te=dates[nt:], nt=nt,
        pte_lower=lo95, pte_upper=hi95, pte_lower80=lo80, pte_upper80=hi80,
        next_pred=last,
        next_lower=last * (1 - _Z95 * sn / 100), next_upper=last * (1 + _Z95 * sn / 100),
        next_lower80=last * (1 - _Z80 * sn / 100), next_upper80=last * (1 + _Z80 * sn / 100),
        vol_test=sig_te, vol_next=sn,
        close_full=y, dates_full=dates,
    )


# ════════════════════════════════════════════════════════════════════════════
#  SARIMAX — ARIMA + biến ngoại sinh (Volume, Range)
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_sarimax(ticker: str, train_ratio: float, p: int = 1,
                date_from=None, date_to=None) -> dict:
    df, N, y, dates, nt = _split(ticker, train_ratio, date_from, date_to)
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception:
        return _empty_like('SARIMAX', 'statsmodels SARIMAX', y, dates, nt,
                           'statsmodels chưa được cài đặt.')
    # Biến ngoại sinh: Volume (triệu cp) + Range (biên độ). Lấy log-volume cho ổn định.
    try:
        vol = df['Volume'].values.astype(float)
        rng = df['Range'].values.astype(float)
        exog = np.column_stack([np.log1p(vol), rng])
        # Thay NaN bằng trung bình cột
        for j in range(exog.shape[1]):
            col = exog[:, j]
            col[~np.isfinite(col)] = np.nanmean(col[np.isfinite(col)])
    except Exception:
        return _empty_like('SARIMAX', 'statsmodels SARIMAX', y, dates, nt,
                           'Thiếu cột Volume/Range.')
    pc = min(max(int(p), 1), 2)
    order = (pc, 1, 1)
    ytr, yte = y[:nt], y[nt:]
    extr, exte = exog[:nt], exog[nt:]
    try:
        res = SARIMAX(ytr, exog=extr, order=order,
                      enforce_stationarity=False, enforce_invertibility=False
                      ).fit(disp=False)
        try:
            res_full = res.append(yte, exog=exte, refit=False)
        except Exception:
            res_full = res.extend(yte, exog=exte)
        pred = res_full.get_prediction(start=nt, end=N - 1, dynamic=False)
        pte = np.asarray(pred.predicted_mean, dtype=float)
        c95 = np.asarray(pred.conf_int(alpha=0.05), dtype=float)
        c80 = np.asarray(pred.conf_int(alpha=0.20), dtype=float)
        # Phiên kế tiếp: dùng exog cuối cùng (persistence)
        exog_next = exog[-1:].copy()
        fc = res_full.get_forecast(steps=1, exog=exog_next)
        npred = float(np.asarray(fc.predicted_mean, dtype=float)[0])
        n95 = np.asarray(fc.conf_int(alpha=0.05), dtype=float)[0]
        n80 = np.asarray(fc.conf_int(alpha=0.20), dtype=float)[0]
        _coef = _params_dict(res)
        return dict(
            name='SARIMAX', engine='statsmodels SARIMAX', ok=True,
            params=f'order={order} · exog=[log(Volume), Range]',
            summary=f'SARIMAX{order} + Volume,Range · AIC={res.aic:.1f}',
            aic=float(res.aic), bic=float(res.bic), order=order, coef=_coef,
            yte=yte, pte=pte, dates_te=dates[nt:], nt=nt,
            pte_lower=c95[:, 0], pte_upper=c95[:, 1],
            pte_lower80=c80[:, 0], pte_upper80=c80[:, 1],
            next_pred=npred,
            next_lower=float(n95[0]), next_upper=float(n95[1]),
            next_lower80=float(n80[0]), next_upper80=float(n80[1]),
            close_full=y, dates_full=dates,
        )
    except Exception as e:
        return _empty_like('SARIMAX', 'statsmodels SARIMAX', y, dates, nt,
                           f'Lỗi fit SARIMAX: {str(e)[:120]}')

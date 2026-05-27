"""Mô hình HỌC SÂU cho FinScope — LSTM (Keras) dự báo giá phiên kế tiếp.

Triết lý "deploy-safe + demo-rich":
  • Ưu tiên LSTM (TensorFlow/Keras) — chuẩn deep learning cho chuỗi thời gian.
  • Nếu TensorFlow không khả dụng (vd. Streamlit Cloud RAM thấp) → tự động
    fallback sang sklearn MLPRegressor (mạng nơ-ron nhẹ) → app KHÔNG vỡ.

Trả về dict CÙNG SHAPE với models/advanced.py để trang "Mô hình Nâng cao"
vẽ fan chart + bảng CI đồng bộ. Khoảng tin cậy từ ±z·σ(sai số test).
"""
import os
import warnings
import numpy as np
import streamlit as st

from data.fetcher import fetch_data

warnings.filterwarnings('ignore')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')   # tắt log TF ồn ào

_Z95 = 1.959963985
_Z80 = 1.281551566
_WIN = 10        # lookback — số phiên quá khứ làm input
_SEED = 42


def _build_windows(scaled, W):
    """Tạo (X, target) cho dự báo 1-bước-tới: X[i]=scaled[i-W:i], y=scaled[i]."""
    X, Y, idx = [], [], []
    for i in range(W, len(scaled)):
        X.append(scaled[i - W:i]); Y.append(scaled[i]); idx.append(i)
    return np.asarray(X, dtype=float), np.asarray(Y, dtype=float), np.asarray(idx)


def _empty(name, y, dates, nt, msg):
    yte = y[nt:]; nan = np.full_like(yte, np.nan, dtype=float)
    return dict(name=name, engine='—', ok=False, params='—', summary=msg,
                yte=yte, pte=nan.copy(), dates_te=dates[nt:], nt=nt,
                pte_lower=nan.copy(), pte_upper=nan.copy(),
                pte_lower80=nan.copy(), pte_upper80=nan.copy(),
                next_pred=float('nan'), next_lower=float('nan'), next_upper=float('nan'),
                next_lower80=float('nan'), next_upper80=float('nan'),
                close_full=np.asarray(y, float), dates_full=dates)


def _fit_keras_lstm(Xtr, Ytr, Xte, x_next):
    """LSTM 1 lớp (Keras). Trả (pred_test, pred_next) ở scale chuẩn hoá."""
    import random
    random.seed(_SEED); np.random.seed(_SEED)
    import tensorflow as tf
    tf.random.set_seed(_SEED)
    try:
        tf.config.threading.set_intra_op_parallelism_threads(2)
    except Exception:
        pass
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Input
    from tensorflow.keras.callbacks import EarlyStopping

    model = Sequential([Input(shape=(Xtr.shape[1], 1)),
                        LSTM(32), Dense(1)])
    model.compile(optimizer='adam', loss='mse')
    es = EarlyStopping(patience=5, restore_best_weights=True, monitor='loss')
    model.fit(Xtr[..., None], Ytr, epochs=30, batch_size=64,
              verbose=0, callbacks=[es])
    pte = model.predict(Xte[..., None], verbose=0).ravel()
    nxt = float(model.predict(x_next[None, ..., None], verbose=0).ravel()[0])
    return pte, nxt, 'TensorFlow/Keras LSTM(32)'


def _fit_mlp(Xtr, Ytr, Xte, x_next):
    """Fallback: sklearn MLPRegressor (mạng nơ-ron nhẹ)."""
    from sklearn.neural_network import MLPRegressor
    m = MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu',
                     max_iter=600, random_state=_SEED, early_stopping=True,
                     n_iter_no_change=12)
    m.fit(Xtr, Ytr)
    pte = m.predict(Xte)
    nxt = float(m.predict(x_next[None, :])[0])
    return pte, nxt, 'sklearn MLP(64,32)'


@st.cache_data(ttl=21600, show_spinner=False, persist="disk")
def run_lstm(ticker: str, train_ratio: float, p: int = 1,
             date_from=None, date_to=None) -> dict:
    """LSTM dự báo giá đóng cửa phiên kế tiếp (1-bước-tới).

    Cửa sổ trượt W=10 phiên (chuẩn hoá theo train). Dự báo test dùng cửa sổ
    GIÁ TRỊ THỰC quá khứ (không đệ quy) → so sánh công bằng với mô hình khác.
    Khoảng tin cậy 80%/95% từ ±z·σ(sai số test).
    """
    df = fetch_data(ticker, date_from, date_to)
    N = len(df)
    y = df['Close'].values.astype(float)
    dates = df['Ngay'].values
    W = _WIN
    nt = max(W + 30, min(int(N * train_ratio), N - 10))
    if N < W + 50:
        return _empty('Deep Learning (LSTM)', y, dates, nt, 'Không đủ dữ liệu cho LSTM.')

    # Học trên KHÔNG GIAN LỢI SUẤT (stationary) rồi quy về giá: P̂_t = P_{t-1}·(1+r̂_t)
    # → dự báo neo vào giá phiên trước, sát ngưỡng biến động, cạnh tranh hơn.
    ret = np.zeros(N)
    ret[1:] = y[1:] / y[:-1] - 1.0                  # ret[i] = lợi suất tại chỉ số i
    mu = float(np.mean(ret[1:nt])); sd = float(np.std(ret[1:nt])) or 1e-6
    scaled = (ret - mu) / sd

    # X[k] = scaled[i-W:i], target = scaled[i] (lợi suất phiên i), i = W..N-1
    X, Yt, idx = _build_windows(scaled, W)
    tr_mask = idx < nt
    te_mask = idx >= nt
    Xtr, Ytr = X[tr_mask], Yt[tr_mask]
    Xte = X[te_mask]
    te_target_idx = idx[te_mask]                    # vị trí giá test được dự báo
    x_next = scaled[N - W:N]                         # cửa sổ cuối → dự báo lợi suất phiên N

    if len(Xtr) < 30 or len(Xte) < 3:
        return _empty('Deep Learning (LSTM)', y, dates, nt, 'Không đủ mẫu train/test.')

    try:
        try:
            pte_s, nxt_s, engine = _fit_keras_lstm(Xtr, Ytr, Xte, x_next)
        except Exception:
            pte_s, nxt_s, engine = _fit_mlp(Xtr, Ytr, Xte, x_next)
    except Exception as e:
        return _empty('Deep Learning (LSTM)', y, dates, nt, f'Lỗi train: {str(e)[:120]}')

    # Giải chuẩn hoá lợi suất → giá (neo vào giá phiên trước thực tế)
    ret_te = pte_s * sd + mu
    prev_close_te = y[te_target_idx - 1]
    pte = prev_close_te * (1.0 + ret_te)
    ret_next = nxt_s * sd + mu
    next_pred = float(y[-1] * (1.0 + ret_next))
    yte = y[te_target_idx]

    sigma = float(np.std(yte - pte)) if len(yte) > 1 else float(sd)
    pte_lower, pte_upper = pte - _Z95 * sigma, pte + _Z95 * sigma
    pte_lower80, pte_upper80 = pte - _Z80 * sigma, pte + _Z80 * sigma

    is_lstm = 'LSTM' in engine
    return dict(
        name='Deep Learning (LSTM)' if is_lstm else 'Neural Net (MLP)',
        engine=engine, ok=True,
        params=f'lookback W={W} · {"LSTM(32)" if is_lstm else "MLP(64,32)"}',
        summary=(f'{"LSTM" if is_lstm else "MLP"} · cửa sổ {W} phiên · '
                 f'chuẩn hoá z-score'),
        yte=yte, pte=pte, dates_te=dates[te_target_idx], nt=nt,
        pte_lower=pte_lower, pte_upper=pte_upper,
        pte_lower80=pte_lower80, pte_upper80=pte_upper80,
        next_pred=next_pred,
        next_lower=next_pred - _Z95 * sigma, next_upper=next_pred + _Z95 * sigma,
        next_lower80=next_pred - _Z80 * sigma, next_upper80=next_pred + _Z80 * sigma,
        close_full=y, dates_full=dates,
        coef={'window_W': float(W), 'train_mean': mu, 'train_std': sd,
              'resid_sigma': sigma},
    )

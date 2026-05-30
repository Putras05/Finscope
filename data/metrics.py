import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error


def calc_metrics(ytrue, ypred, k: int = 1) -> dict:
    ytrue, ypred = np.array(ytrue), np.array(ypred)
    rmse  = np.sqrt(mean_squared_error(ytrue, ypred))
    mae   = mean_absolute_error(ytrue, ypred)
    mask  = ytrue != 0
    # v58 — guard zero-size mask (mọi ytrue=0): tránh "zero-size array
    # to reduction" crash khi mã có dữ liệu bất thường.
    mape  = (np.mean(np.abs((ytrue[mask] - ypred[mask]) / ytrue[mask])) * 100
             if mask.any() else float('nan'))
    ssr   = np.sum((ytrue - ypred) ** 2)
    sst   = np.sum((ytrue - np.mean(ytrue)) ** 2)
    r2    = 1 - ssr / sst if sst else 0
    n     = len(ytrue)
    r2adj = 1 - (1 - r2) * (n - 1) / (n - k - 1) if n > k + 1 else r2
    return dict(MAPE=mape, RMSE=rmse, MAE=mae, R2adj=r2adj)


def calc_r2(ytrue, ypred) -> float:
    ytrue, ypred = np.array(ytrue), np.array(ypred)
    ssr = np.sum((ytrue - ypred) ** 2)
    sst = np.sum((ytrue - np.mean(ytrue)) ** 2)
    return 1 - ssr / sst if sst else 0


def _ci95(ytrue, ypred) -> float:
    return 1.96 * float(np.std(np.array(ytrue) - np.array(ypred)))


def _star(mape: float) -> str:
    if mape < 1.0: return '★★★'
    if mape < 2.0: return '★★'
    if mape < 3.0: return '★'
    return ''


def diebold_mariano(y, f1, f2, h: int = 1, loss: str = 'MSE') -> dict:
    """Kiểm định Diebold–Mariano: dự báo f1 có chính xác hơn f2 không?

    H0: hai dự báo có độ chính xác kỳ vọng BẰNG nhau (không khác biệt).
    Thống kê DM âm  → f1 sai số NHỎ hơn f2 (f1 tốt hơn); dương → ngược lại.
    Áp dụng hiệu chỉnh mẫu nhỏ Harvey–Leybourne–Newbold (1997) + phân phối t.

    Tham số:
      y, f1, f2 : giá thực và 2 chuỗi dự báo (đã căn theo cùng mốc thời gian).
      h         : tầm dự báo (1-bước = 1) → bậc tự tương quan sai số tối đa h−1.
      loss      : 'MSE' (sai số bình phương) hoặc 'MAE' (sai số tuyệt đối).

    Trả: {ok, dm, p, n, dbar, loss}. ok=False nếu không đủ mẫu/biến thiên 0.
    """
    y  = np.asarray(y,  dtype=float)
    f1 = np.asarray(f1, dtype=float)
    f2 = np.asarray(f2, dtype=float)
    m = np.isfinite(y) & np.isfinite(f1) & np.isfinite(f2)
    y, f1, f2 = y[m], f1[m], f2[m]
    n = len(y)
    if n < 8:
        return {'ok': False, 'n': n}

    e1, e2 = y - f1, y - f2
    if loss == 'MAE':
        d = np.abs(e1) - np.abs(e2)
    else:                                        # MSE (mặc định)
        d = e1 ** 2 - e2 ** 2
    dbar = float(np.mean(d))

    # Phương sai dài hạn: gamma0 + 2·Σ gamma_k (k = 1..h−1) — sai số h-bước
    # tự tương quan tới bậc h−1. Với h=1 ⇒ chỉ còn gamma0.
    dc = d - dbar
    gamma0 = float(np.mean(dc ** 2))
    var = gamma0
    for k in range(1, h):
        if k < n:
            var += 2.0 * float(np.mean(dc[k:] * dc[:-k]))
    var_dbar = var / n
    if var_dbar <= 0:
        return {'ok': False, 'n': n}

    dm = dbar / np.sqrt(var_dbar)
    # Hiệu chỉnh mẫu nhỏ HLN + dùng phân phối Student-t (n−1 bậc tự do)
    corr = np.sqrt(max((n + 1 - 2 * h + h * (h - 1) / n) / n, 1e-9))
    dm_hln = dm * corr
    try:
        from scipy import stats as _sps
        p = float(2.0 * _sps.t.cdf(-abs(dm_hln), df=n - 1))
    except Exception:
        # Fallback: xấp xỉ chuẩn nếu thiếu scipy
        from math import erfc, sqrt
        p = float(erfc(abs(dm_hln) / sqrt(2.0)))
    return {'ok': True, 'dm': float(dm_hln), 'p': p, 'n': n,
            'dbar': dbar, 'loss': loss}

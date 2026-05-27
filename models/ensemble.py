"""Mô hình KẾT HỢP (Ensemble) — gộp dự báo của nhiều mô hình.

Trọng số nghịch-MAPE: mô hình càng chính xác (MAPE thấp) → trọng số càng lớn.
Đây là kỹ thuật chuẩn (forecast combination, Bates & Granger 1969) giúp dự báo
ỔN ĐỊNH & chính xác hơn mọi mô hình đơn lẻ. Căn các chuỗi test theo NGÀY rồi
lấy trung bình có trọng số trên các ngày có ≥2 mô hình.
"""
import numpy as np
import pandas as pd

_Z95 = 1.959963985
_Z80 = 1.281551566


def build_ensemble(members, df, is_en=False):
    """members: list dict {'name', 'res' (dict model), 'mape' (test MAPE)}.

    Trả dict cùng shape các model khác (yte/pte/dates_te/next_pred/CI + weights)
    hoặc None nếu < 2 thành viên hợp lệ.
    """
    valid = [m for m in members
             if np.isfinite(m.get('mape', np.nan))
             and np.isfinite(m['res'].get('next_pred', np.nan))]
    if len(valid) < 2:
        return None

    w = np.array([1.0 / (m['mape'] + 0.1) for m in valid], dtype=float)
    w = w / w.sum()
    weights = {m['name']: float(wi) for m, wi in zip(valid, w)}

    next_pred = float(sum(wi * float(m['res']['next_pred']) for wi, m in zip(w, valid)))

    # ── Căn chuỗi test theo ngày ──────────────────────────────────────
    cols = []
    for m in valid:
        idx = pd.to_datetime(m['res']['dates_te'])
        s = pd.Series(np.asarray(m['res']['pte'], dtype=float), index=idx)
        s = s[~s.index.duplicated(keep='last')]
        cols.append(s)
    mat = pd.concat(cols, axis=1)              # (T ngày × M mô hình)
    vals = mat.values
    present = ~np.isnan(vals)
    wrow = present * w[None, :]
    wsum = wrow.sum(axis=1)
    keep = wsum > 0
    ens = (np.nansum(np.where(present, vals * w[None, :], 0.0), axis=1)[keep]
           / wsum[keep])
    dates_keep = mat.index[keep]

    # Giá thực theo ngày
    cmap = pd.Series(df['Close'].values.astype(float),
                     index=pd.to_datetime(df['Ngay']))
    cmap = cmap[~cmap.index.duplicated(keep='last')]
    yte = cmap.reindex(dates_keep).values
    fin = np.isfinite(yte) & np.isfinite(ens)
    ens, yte, dates_keep = ens[fin], yte[fin], dates_keep[fin]
    if len(ens) < 3:
        return None

    sigma = float(np.std(yte - ens))
    dates_te = np.array([d.date() for d in dates_keep])

    # nt cho biểu đồ lịch sử
    dfull = pd.to_datetime(df['Ngay'])
    try:
        nt = int(np.where(dfull == dates_keep[0])[0][0])
    except Exception:
        nt = int(len(df) * 0.8)

    return dict(
        name='FinScope Ensemble', engine='Kết hợp nghịch-MAPE', ok=True,
        params='Trung bình có trọng số ∝ 1/MAPE',
        summary=f'Kết hợp {len(valid)} mô hình (trọng số ∝ 1/MAPE)',
        weights=weights, n_members=len(valid),
        yte=yte, pte=ens, dates_te=dates_te, nt=nt,
        pte_lower=ens - _Z95 * sigma, pte_upper=ens + _Z95 * sigma,
        pte_lower80=ens - _Z80 * sigma, pte_upper80=ens + _Z80 * sigma,
        next_pred=next_pred,
        next_lower=next_pred - _Z95 * sigma, next_upper=next_pred + _Z95 * sigma,
        next_lower80=next_pred - _Z80 * sigma, next_upper80=next_pred + _Z80 * sigma,
        close_full=df['Close'].values.astype(float),
        dates_full=df['Ngay'].values,
    )

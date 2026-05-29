"""Price alert engine — cảnh báo khi giá chạm mức người dùng đặt.

Lưu mỗi user 1 file `user_data/alerts/{uid}.json`, schema:

  {
    "items": [
      {"id": "a_xxx", "ticker": "FPT", "kind": "above"|"below",
       "price_dong": 145000.0, "note": "..." (optional),
       "created_at": "ISO", "triggered_at": null | "ISO"}
    ]
  }

Quy ước: price_dong tính bằng ĐỒNG (đã ×1000 từ Close gốc) cho khớp với
UI Paper Trading. `check_triggered(state, current_prices)` chạy mỗi rerun
để mark alert đã chạm; chỉ trigger 1 lần / alert (không spam).
"""
from __future__ import annotations
import datetime as _dt
import json
import os
import secrets
from pathlib import Path
from typing import Optional

import streamlit as st

_DIR = Path(__file__).resolve().parent.parent / 'user_data' / 'alerts'


def _file_for(uid: Optional[str]) -> Path:
    if uid is None:
        try:
            from auth.session import user_id as _uid
            uid = _uid()
        except Exception:
            uid = 'guest'
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return _DIR / f'{uid or "guest"}.json'


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec='seconds')


def _load(uid: Optional[str]) -> dict:
    fp = _file_for(uid)
    if not fp.exists():
        return {'items': []}
    try:
        with fp.open('r', encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, dict) and 'items' in d:
            return d
    except Exception:
        pass
    return {'items': []}


def _save(state: dict, uid: Optional[str]) -> None:
    fp = _file_for(uid)
    tmp = fp.with_suffix('.json.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, fp)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def add_alert(ticker: str, kind: str, price_dong: float,
              note: str = '', uid: Optional[str] = None) -> dict:
    """Tạo alert mới. kind ∈ {'above','below'}.

    Trả về dict alert vừa tạo (kèm id).
    """
    if kind not in ('above', 'below'):
        raise ValueError("kind phải là 'above' hoặc 'below'")
    if price_dong <= 0:
        raise ValueError('price phải > 0')
    state = _load(uid)
    rec = {
        'id': 'a_' + secrets.token_hex(5),
        'ticker': str(ticker).upper().strip(),
        'kind': kind,
        'price_dong': float(price_dong),
        'note': (note or '').strip()[:120],
        'created_at': _now(),
        'triggered_at': None,
    }
    state['items'].append(rec)
    _save(state, uid)
    return rec


def remove_alert(alert_id: str, uid: Optional[str] = None) -> bool:
    state = _load(uid)
    n0 = len(state['items'])
    state['items'] = [x for x in state['items'] if x.get('id') != alert_id]
    _save(state, uid)
    return len(state['items']) < n0


def list_alerts(uid: Optional[str] = None,
                only_active: bool = False) -> list:
    items = _load(uid).get('items', [])
    if only_active:
        items = [a for a in items if a.get('triggered_at') is None]
    return list(items)


def check_triggered(current_prices_dong: dict,
                    uid: Optional[str] = None) -> list:
    """Quét toàn bộ alert vs giá hiện tại; mark triggered nếu chạm.

    current_prices_dong: {ticker: price_in_DONG}.
    Trả list các alert vừa-mới triggered (chưa có triggered_at trước đây).
    """
    state = _load(uid)
    just_triggered = []
    changed = False
    for a in state['items']:
        if a.get('triggered_at'):
            continue
        cur = current_prices_dong.get(a['ticker'])
        if cur is None:
            continue
        cur = float(cur)
        kind = a.get('kind')
        target = float(a.get('price_dong', 0))
        if (kind == 'above' and cur >= target) or \
           (kind == 'below' and cur <= target):
            a['triggered_at'] = _now()
            a['triggered_at_price'] = cur
            just_triggered.append(dict(a))
            changed = True
    if changed:
        _save(state, uid)
    return just_triggered


def count_active(uid: Optional[str] = None) -> int:
    return sum(1 for a in _load(uid).get('items', [])
               if not a.get('triggered_at'))


def count_unread_triggered(uid: Optional[str] = None) -> int:
    """Đếm alert đã trigger và CHƯA bị xoá — coi như chưa đọc."""
    return sum(1 for a in _load(uid).get('items', [])
               if a.get('triggered_at'))


@st.cache_data(show_spinner=False)
def _counts_cached(uid: Optional[str], _mtime: float) -> tuple[int, int]:
    """Cache theo (uid, mtime). Khi file thay đổi → mtime đổi → cache miss."""
    items = _load(uid).get('items', [])
    active    = sum(1 for a in items if not a.get('triggered_at'))
    triggered = sum(1 for a in items if a.get('triggered_at'))
    return active, triggered


def counts(uid: Optional[str] = None) -> tuple[int, int]:
    """Trả (active, triggered). Cache theo file mtime → topbar render mỗi
    rerun chỉ tốn 1 lần os.stat() (~0.05ms) thay vì đọc + parse JSON.
    """
    fp = _file_for(uid)
    try:
        mtime = fp.stat().st_mtime if fp.exists() else 0.0
    except OSError:
        mtime = 0.0
    return _counts_cached(uid, mtime)


def clear_triggered(uid: Optional[str] = None) -> int:
    """Xoá toàn bộ alert đã trigger. Trả số đã xoá."""
    state = _load(uid)
    n0 = len(state['items'])
    state['items'] = [a for a in state['items'] if not a.get('triggered_at')]
    _save(state, uid)
    return n0 - len(state['items'])

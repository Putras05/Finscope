"""Watchlist (danh mục mã yêu thích) per-user.

Lưu tại `user_data/watchlist/{uid}.json` dưới dạng list mã ticker (string).
Guest dùng chung 1 file `user_data/watchlist/guest.json` để không mất khi
reload.

API:
  get_watchlist(uid=None)        — list các mã (đã chuẩn hoá uppercase, sort)
  toggle(ticker, uid=None)       — bật/tắt 1 mã; trả True nếu sau khi gọi mã có trong list
  add(ticker, uid=None)          — thêm; idempotent
  remove(ticker, uid=None)       — xoá
  clear(uid=None)                — xoá toàn bộ
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional

import streamlit as st

_DIR = Path(__file__).resolve().parent.parent / 'user_data' / 'watchlist'


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


def _load(uid: Optional[str]) -> list:
    fp = _file_for(uid)
    if not fp.exists():
        return []
    try:
        with fp.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return sorted({str(x).upper() for x in data if str(x).strip()})
    except Exception:
        pass
    return []


def _save(items: list, uid: Optional[str]) -> None:
    fp = _file_for(uid)
    tmp = fp.with_suffix('.json.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(sorted(set(items)), f, ensure_ascii=False, indent=2)
        os.replace(tmp, fp)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


@st.cache_data(show_spinner=False)
def _watchlist_cached(uid: Optional[str], _mtime: float) -> list:
    return _load(uid)


def get_watchlist(uid: Optional[str] = None) -> list:
    """Cache theo (uid, mtime) — topbar render mỗi rerun chỉ os.stat() 1 lần."""
    fp = _file_for(uid)
    try:
        mtime = fp.stat().st_mtime if fp.exists() else 0.0
    except OSError:
        mtime = 0.0
    return _watchlist_cached(uid, mtime)


def add(ticker: str, uid: Optional[str] = None) -> list:
    if not ticker:
        return _load(uid)
    items = set(_load(uid))
    items.add(ticker.upper())
    res = sorted(items)
    _save(res, uid)
    return res


def remove(ticker: str, uid: Optional[str] = None) -> list:
    items = set(_load(uid))
    items.discard((ticker or '').upper())
    res = sorted(items)
    _save(res, uid)
    return res


def toggle(ticker: str, uid: Optional[str] = None) -> bool:
    """Bật/tắt 1 mã. Trả True nếu sau khi gọi mã có trong watchlist."""
    if not ticker:
        return False
    tk = ticker.upper()
    items = set(_load(uid))
    if tk in items:
        items.discard(tk); _save(sorted(items), uid); return False
    items.add(tk); _save(sorted(items), uid); return True


def clear(uid: Optional[str] = None) -> None:
    _save([], uid)


def is_watching(ticker: str, uid: Optional[str] = None) -> bool:
    return (ticker or '').upper() in set(_load(uid))


def get_watchlist_and_check(ticker: str, uid: Optional[str] = None) -> tuple[list, bool]:
    """Trả (list mã, is_watching) trong 1 lần đọc file — dùng cho topbar
    coalesce (get_watchlist + is_watching trước đây đọc file 2 lần)."""
    items = _load(uid)
    return items, (ticker or '').upper() in set(items)

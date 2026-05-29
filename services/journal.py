"""Trade journal — sổ ghi chú giao dịch per-user (notes + tags + lesson).

Lưu tại `user_data/journal/{uid}.json`. Mỗi entry liên kết tới 1 lệnh
trong sổ Paper Trading qua trade_id (ISO timestamp + ticker + side).

Schema:
  {"entries": [
    {"id": "j_xxxx", "trade_ts": "ISO", "ticker": "FPT", "side": "BUY",
     "qty": 100, "price": 140000.0,
     "thesis": "...",  # lý do vào lệnh
     "lesson": "...",  # bài học sau khi đóng
     "tags": ["breakout","earnings"],
     "rating": 1..5 | null,   # tự đánh giá kỷ luật
     "updated_at": "ISO"}
  ]}
"""
from __future__ import annotations
import datetime as _dt
import json
import os
import secrets
from pathlib import Path
from typing import Optional

_DIR = Path(__file__).resolve().parent.parent / 'user_data' / 'journal'


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
        return {'entries': []}
    try:
        with fp.open('r', encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, dict) and 'entries' in d:
            return d
    except Exception:
        pass
    return {'entries': []}


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


def _trade_key(trade: dict) -> str:
    """Khoá ổn định cho 1 lệnh = ts + ticker + side + qty + price."""
    return (f"{trade.get('ts','')}|{trade.get('ticker','')}|"
            f"{trade.get('side','')}|{trade.get('qty','')}|"
            f"{trade.get('price','')}")


def get_entry_for_trade(trade: dict, uid: Optional[str] = None) -> Optional[dict]:
    """Tìm note đã ghi cho 1 lệnh cụ thể (theo trade key)."""
    key = _trade_key(trade)
    for e in _load(uid).get('entries', []):
        if e.get('trade_key') == key:
            return e
    return None


def upsert_entry(trade: dict, thesis: str = '', lesson: str = '',
                 tags: Optional[list] = None,
                 rating: Optional[int] = None,
                 uid: Optional[str] = None) -> dict:
    """Tạo hoặc cập nhật entry. Đồng nhất qua trade_key.

    Tham số `trade` lấy nguyên record từ state['history'] của paper.
    """
    state = _load(uid)
    key = _trade_key(trade)
    found = None
    for e in state['entries']:
        if e.get('trade_key') == key:
            found = e; break
    if found is None:
        found = {
            'id': 'j_' + secrets.token_hex(5),
            'trade_key': key,
            'trade_ts': trade.get('ts'),
            'ticker': trade.get('ticker'),
            'side': trade.get('side'),
            'qty': trade.get('qty'),
            'price': trade.get('price'),
        }
        state['entries'].append(found)
    found['thesis']     = (thesis or '').strip()[:600]
    found['lesson']     = (lesson or '').strip()[:600]
    found['tags']       = [str(t).strip()[:24] for t in (tags or []) if str(t).strip()][:8]
    found['rating']     = int(rating) if rating in (1, 2, 3, 4, 5) else None
    found['updated_at'] = _now()
    _save(state, uid)
    return found


def list_entries(uid: Optional[str] = None) -> list:
    return list(_load(uid).get('entries', []))


def delete_entry(entry_id: str, uid: Optional[str] = None) -> bool:
    state = _load(uid)
    n0 = len(state['entries'])
    state['entries'] = [e for e in state['entries'] if e.get('id') != entry_id]
    _save(state, uid)
    return len(state['entries']) < n0


def stats(uid: Optional[str] = None) -> dict:
    """Tổng hợp đếm theo tag + rating phân phối."""
    entries = list_entries(uid)
    tag_count = {}
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for e in entries:
        for t in (e.get('tags') or []):
            tag_count[t] = tag_count.get(t, 0) + 1
        r = e.get('rating')
        if r in rating_dist:
            rating_dist[r] += 1
    return {
        'n_entries': len(entries),
        'tag_count': dict(sorted(tag_count.items(),
                                   key=lambda kv: -kv[1])),
        'rating_dist': rating_dist,
        'avg_rating': (sum(k * v for k, v in rating_dist.items())
                       / max(sum(rating_dist.values()), 1))
                      if any(rating_dist.values()) else None,
    }

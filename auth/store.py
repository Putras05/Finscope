"""User store dùng JSON file đơn giản — DB demo, không phải production.

Schema mỗi record:
    {
      id: "u_xxxxxxxxxxxx",       # 12 hex chars, ổn định
      username: "...",            # 3-32, [a-z0-9._-], lowercase
      display_name: "...",        # tự do, max 64
      email: "...|null",          # optional
      password_hash: "pbkdf2_sha256$...",
      created_at: "ISO datetime",
      last_seen: "ISO datetime",
      role: "user" | "admin",     # admin = thấy panel /admin (chưa dùng)
    }

File mặc định: `<app_root>/user_data/users.json`. Ghi atomically qua temp +
os.replace để không vỡ giữa chừng nếu app bị kill.
"""
from __future__ import annotations
import datetime as _dt
import json
import os
import re
import secrets
import threading
from pathlib import Path
from typing import Optional

from auth.passwords import hash_password, verify_password


_USER_DIR = Path(__file__).resolve().parent.parent / 'user_data'
_USERS_FILE = _USER_DIR / 'users.json'
_LOCK = threading.Lock()

_USERNAME_RE = re.compile(r'^[a-z0-9._-]{3,32}$')
_EMAIL_RE    = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec='seconds')


def _ensure_dir() -> None:
    try:
        _USER_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _load_all() -> list:
    _ensure_dir()
    if not _USERS_FILE.exists():
        return []
    try:
        with _USERS_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_all(users: list) -> None:
    _ensure_dir()
    tmp = _USERS_FILE.with_suffix('.json.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _USERS_FILE)
    except Exception:
        # best-effort: nếu ghi thất bại, không sập app
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def _new_user_id() -> str:
    return 'u_' + secrets.token_hex(6)


# ── API ─────────────────────────────────────────────────────────────────
def list_users() -> list:
    """Trả về list bản ghi (KHÔNG kèm password_hash)."""
    with _LOCK:
        return [{k: v for k, v in u.items() if k != 'password_hash'}
                for u in _load_all()]


def find_user(username: str) -> Optional[dict]:
    """Tìm theo username (lowercase). Trả dict gốc (gồm password_hash) hoặc None."""
    if not isinstance(username, str):
        return None
    u_norm = username.strip().lower()
    with _LOCK:
        for u in _load_all():
            if u.get('username', '').lower() == u_norm:
                return u
    return None


def create_user(username: str, password: str,
                display_name: str = '',
                email: Optional[str] = None) -> tuple[bool, str, Optional[dict]]:
    """Tạo user mới. Trả (ok, message, user_record_no_hash).

    Validate:
      • username: 3-32, [a-z0-9._-]; chuẩn hoá lowercase; unique.
      • password: tối thiểu 6 ký tự.
      • email (nếu có): regex đơn giản.
    """
    if not isinstance(username, str) or not _USERNAME_RE.match(username.strip().lower()):
        return False, ('Tên đăng nhập 3–32 ký tự, chỉ chữ thường, số và . _ -'), None
    if not isinstance(password, str) or len(password) < 6 or len(password) > 512:
        return False, 'Mật khẩu 6–512 ký tự.', None
    if email is not None and email.strip() and not _EMAIL_RE.match(email.strip()):
        return False, 'Email không hợp lệ.', None

    u_norm = username.strip().lower()
    with _LOCK:
        users = _load_all()
        if any(u.get('username', '').lower() == u_norm for u in users):
            return False, 'Tên đăng nhập đã tồn tại.', None
        rec = {
            'id': _new_user_id(),
            'username': u_norm,
            'display_name': (display_name or username).strip()[:64],
            'email': (email or '').strip() or None,
            'password_hash': hash_password(password),
            'created_at': _now(),
            'last_seen':  _now(),
            'role': 'user',
        }
        users.append(rec)
        _save_all(users)
    rec_pub = {k: v for k, v in rec.items() if k != 'password_hash'}
    return True, 'Tạo tài khoản thành công.', rec_pub


def verify_credentials(username: str, password: str) -> tuple[bool, str, Optional[dict]]:
    """Kiểm tra username + password. Trả (ok, msg, user_record_no_hash)."""
    u = find_user(username)
    if not u:
        return False, 'Tài khoản không tồn tại.', None
    if not verify_password(password, u.get('password_hash', '')):
        return False, 'Mật khẩu không đúng.', None
    rec_pub = {k: v for k, v in u.items() if k != 'password_hash'}
    return True, 'Đăng nhập thành công.', rec_pub


def change_password(user_id_: str, old_password: str,
                    new_password: str) -> tuple[bool, str]:
    """Đổi mật khẩu: verify old → update hash. Trả (ok, msg)."""
    if not isinstance(new_password, str) or len(new_password) < 6:
        return False, 'Mật khẩu mới tối thiểu 6 ký tự.'
    with _LOCK:
        users = _load_all()
        rec = next((u for u in users if u.get('id') == user_id_), None)
        if not rec:
            return False, 'Không tìm thấy tài khoản.'
        if not verify_password(old_password, rec.get('password_hash', '')):
            return False, 'Mật khẩu hiện tại không đúng.'
        rec['password_hash'] = hash_password(new_password)
        rec['last_seen'] = _now()
        _save_all(users)
    return True, 'Đã đổi mật khẩu.'


def update_profile(user_id_: str,
                   display_name: Optional[str] = None,
                   email: Optional[str] = None) -> tuple[bool, str]:
    """Cập nhật tên hiển thị / email. Email rỗng → set None.

    Trả (ok, msg). Không cho phép sửa username (định danh đăng nhập).
    """
    with _LOCK:
        users = _load_all()
        rec = next((u for u in users if u.get('id') == user_id_), None)
        if not rec:
            return False, 'Không tìm thấy tài khoản.'
        if display_name is not None:
            dn = display_name.strip()[:64]
            if not dn:
                return False, 'Tên hiển thị không được rỗng.'
            rec['display_name'] = dn
        if email is not None:
            e = email.strip()
            if e and not _EMAIL_RE.match(e):
                return False, 'Email không hợp lệ.'
            rec['email'] = e or None
        rec['last_seen'] = _now()
        _save_all(users)
    return True, 'Đã cập nhật hồ sơ.'


def delete_user(user_id_: str, password: str) -> tuple[bool, str]:
    """Xoá vĩnh viễn tài khoản (yêu cầu password để xác nhận).

    LƯU Ý: không xoá file paper/watchlist/journal/alerts — chỉ user bản
    thân có thể yêu cầu xoá thêm; ở đây giữ lại để audit/restore nếu cần.
    """
    if not isinstance(password, str):
        return False, 'Cần nhập mật khẩu để xác nhận.'
    with _LOCK:
        users = _load_all()
        rec = next((u for u in users if u.get('id') == user_id_), None)
        if not rec:
            return False, 'Không tìm thấy tài khoản.'
        if not verify_password(password, rec.get('password_hash', '')):
            return False, 'Mật khẩu không đúng.'
        users = [u for u in users if u.get('id') != user_id_]
        _save_all(users)
    return True, 'Đã xoá tài khoản.'


def update_last_seen(user_id_: str) -> None:
    """Cập nhật mốc last_seen cho user — best-effort."""
    if not user_id_:
        return
    with _LOCK:
        users = _load_all()
        changed = False
        for u in users:
            if u.get('id') == user_id_:
                u['last_seen'] = _now()
                changed = True
                break
        if changed:
            _save_all(users)

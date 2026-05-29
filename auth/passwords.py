"""Băm mật khẩu PBKDF2-HMAC-SHA256 — stdlib only.

Dùng `hashlib.pbkdf2_hmac` (Python 3.4+) với 200,000 vòng lặp — đủ chậm để
chống brute-force offline trong ngữ cảnh demo, vẫn nhanh trên CPU thường.

Định dạng hash lưu xuống file:
    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

Tương thích với Django pre-2.0 (cùng scheme) — dễ port nếu sau này nâng cấp.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets


_ALGO = 'pbkdf2_sha256'
_ITERATIONS = 200_000
_SALT_BYTES = 16
_DKLEN = 32


def hash_password(password: str) -> str:
    """Hash plaintext → string '$'-delimited (an toàn lưu cleartext JSON)."""
    if not isinstance(password, str) or len(password) == 0:
        raise ValueError('password phải là chuỗi không rỗng')
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt,
                              _ITERATIONS, dklen=_DKLEN)
    return f'{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}'


def verify_password(password: str, stored: str) -> bool:
    """So sánh constant-time: trả True nếu khớp. Mọi lỗi parse → False."""
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    try:
        algo, iters_str, salt_hex, hash_hex = stored.split('$')
        if algo != _ALGO:
            return False
        iters = int(iters_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except Exception:
        return False
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt,
                              iters, dklen=len(expected))
    return hmac.compare_digest(dk, expected)

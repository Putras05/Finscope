"""Quản lý session người dùng qua streamlit session_state.

3 trạng thái:
  • anonymous: chưa làm gì (chưa qua splash) → splash sẽ block.
  • guest:     bấm "Dùng thử khách" → user_id = 'guest'.
  • user:      đã login/register → user_id = 'u_xxxx...'.

Mỗi user (kể cả guest) có sổ Paper Trading riêng tại
`user_data/paper/{user_id}.json` để không đè lên nhau.
"""
from __future__ import annotations
from typing import Optional


_KEY_USER = '_auth_user'         # dict đầy đủ hoặc None
_KEY_GUEST = '_auth_is_guest'    # bool


def _ss():
    import streamlit as st
    return st.session_state


def current_user() -> Optional[dict]:
    """Bản ghi user hiện tại (không hash). None nếu chưa login & chưa guest."""
    return _ss().get(_KEY_USER)


def is_authenticated() -> bool:
    """True khi đã login thật (không phải guest)."""
    u = current_user()
    return bool(u) and not _ss().get(_KEY_GUEST, False)


def is_guest() -> bool:
    return bool(_ss().get(_KEY_GUEST, False))


def user_id() -> str:
    """ID dùng để mở sổ Paper / watchlist. 'guest' khi chưa login."""
    u = current_user()
    if not u:
        return 'guest'
    return u.get('id') or 'guest'


def login_user(user_record: dict) -> None:
    """Set session sang trạng thái logged-in. `user_record` KHÔNG kèm password_hash."""
    _ss()[_KEY_USER] = user_record
    _ss()[_KEY_GUEST] = False
    # Reset PRO cache cũ để engine tính lại theo equity sổ mới
    _ss().pop('_sig_report', None)
    _ss().pop('_sig_cache_key', None)


def login_as_guest() -> None:
    _ss()[_KEY_USER] = {'id': 'guest', 'username': 'guest',
                        'display_name': 'Khách', 'role': 'guest'}
    _ss()[_KEY_GUEST] = True


def logout_user() -> None:
    """Đăng xuất — xoá user khỏi session_state, KHÔNG xoá file paper."""
    for k in (_KEY_USER, _KEY_GUEST):
        _ss().pop(k, None)
    # Clear cache có liên quan user (nếu có)
    for k in list(_ss().keys()):
        if k.startswith('_sig_'):
            _ss().pop(k, None)
    # Đẩy về splash
    _ss().pop('_splash_done', None)

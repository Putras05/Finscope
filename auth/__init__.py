"""Module xác thực người dùng cho FinScope.

Tách rời thành 3 file:
  • passwords — băm mật khẩu PBKDF2-HMAC-SHA256 (stdlib, không thêm dep).
  • store     — đọc/ghi `users.json` (best-effort, lock đơn giản qua file).
  • session   — wrapper Streamlit session_state cho login/logout/current_user.

Mục đích: thêm chế độ "tài khoản cá nhân" cho ứng dụng demo — sổ Paper
Trading riêng, watchlist riêng, không phải global. Có chế độ KHÁCH để
ban giám khảo / người mới chạy thử nhanh không cần đăng ký.

KHÔNG dùng cho hệ thống thật — chỉ là demo có hash mật khẩu chuẩn.
"""
from auth.session import (
    current_user, is_authenticated, is_guest, user_id,
    login_user, logout_user, login_as_guest,
)
from auth.store import (
    create_user, find_user, verify_credentials, list_users, update_last_seen,
)

__all__ = [
    'current_user', 'is_authenticated', 'is_guest', 'user_id',
    'login_user', 'logout_user', 'login_as_guest',
    'create_user', 'find_user', 'verify_credentials', 'list_users',
    'update_last_seen',
]

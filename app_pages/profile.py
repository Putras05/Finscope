"""Trang Hồ sơ cá nhân — settings + export + delete account.

Yêu cầu user đã login thật (không phải guest); nếu guest sẽ hiện banner
mời đăng ký.
"""
import datetime as _dt
import io
import json
import zipfile
from pathlib import Path

import streamlit as st

from auth.session import (current_user, is_guest, is_authenticated,
                            logout_user, login_user)
from auth.store import (change_password, update_profile, delete_user,
                          find_user)


def _section_header(title_vi: str, title_en: str, _T, is_en: bool,
                     subtitle_vi: str = '', subtitle_en: str = ''):
    sub = (subtitle_en if is_en else subtitle_vi)
    sub_html = (f'<span style="font-size:11px;font-weight:600;'
                f'color:{_T["text_muted"]};margin-left:8px">{sub}</span>'
                if sub else '')
    st.markdown(
        f'<div class="sec-hdr" style="margin-top:8px">'
        f'{title_en if is_en else title_vi}{sub_html}</div>',
        unsafe_allow_html=True)


def _build_export_zip(uid: str) -> bytes:
    """Đóng gói toàn bộ dữ liệu user (paper + watchlist + journal + alerts)
    thành 1 file zip để download. KHÔNG kèm password_hash.
    """
    buf = io.BytesIO()
    root = Path(__file__).resolve().parent.parent / 'user_data'
    paths = [
        root / 'paper' / f'{uid}.json',
        root / 'watchlist' / f'{uid}.json',
        root / 'journal' / f'{uid}.json',
        root / 'alerts' / f'{uid}.json',
    ]
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            if p.exists():
                z.writestr(f'{p.parent.name}/{p.name}', p.read_bytes())
        # Thêm metadata user (public fields)
        u = current_user() or {}
        pub = {k: v for k, v in u.items() if k != 'password_hash'}
        z.writestr('account.json',
                    json.dumps(pub, ensure_ascii=False, indent=2))
        z.writestr('README.txt',
                    'FinScope — Export tài khoản\n'
                    f'Ngày xuất: {_dt.datetime.now().isoformat(timespec="seconds")}\n\n'
                    'Cấu trúc:\n'
                    '  account.json     — thông tin tài khoản (không kèm mật khẩu)\n'
                    '  paper/...        — sổ giao dịch ảo\n'
                    '  watchlist/...    — danh mục mã yêu thích\n'
                    '  journal/...      — nhật ký giao dịch\n'
                    '  alerts/...       — cảnh báo giá\n')
    return buf.getvalue()


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'

    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Hồ sơ cá nhân" if not is_en else "Account Profile"}</h1>'
        f'<p>{"Quản lý tài khoản, đổi mật khẩu, xuất hoặc xoá dữ liệu của bạn." if not is_en else "Manage your account, change password, export or delete your data."}</p>'
        f'</div>', unsafe_allow_html=True)

    if is_guest() or not is_authenticated():
        # Banner CTA + 4 preview card mô tả lợi ích khi đăng ký
        from ui.icons import icon as _icon
        _cta_msg = ('Bạn đang ở chế độ KHÁCH — sổ Paper Trading dùng chung file '
                    'cục bộ với mọi user Khách trên máy này, watchlist không '
                    'được lưu riêng. Đăng ký 1 tài khoản để có:'
                    if not is_en else
                    'You are in GUEST mode — Paper Trading book is shared and '
                    'watchlist is not private. Register an account to unlock:')
        st.markdown(
            f'<div style="background:{_T["warning_bg"]};'
            f'border:2px solid {_T["warning"]};border-radius:14px;padding:18px 24px;'
            f'margin:14px 0;color:{_T["warning"]};font-size:13.5px;line-height:1.7">'
            f'<div style="font-size:15px;font-weight:800;margin-bottom:6px">'
            f'{"Chế độ Khách" if not is_en else "Guest Mode"}</div>'
            f'<span style="color:{_T["text_primary"]}">{_cta_msg}</span></div>',
            unsafe_allow_html=True)

        # 4 feature preview card
        previews = [
            ('briefcase-fill', '#0F766E',
             'Sổ Paper Trading riêng' if not is_en else 'Private Paper Book',
             'Mỗi tài khoản 1 sổ giao dịch độc lập với lịch sử lệnh, vị thế, P&L riêng — không ai khác xem được.'
             if not is_en else
             'A separate trading book per account with private order history, positions and P&L.'),
            ('star-fill', '#F59E0B',
             'Danh sách yêu thích' if not is_en else 'Personal Watchlist',
             'Đánh dấu các mã quan tâm bằng 1 click ở topbar; chọn nhanh từ dropdown ngành "Yêu thích".'
             if not is_en else
             'Star tickers from the topbar; filter to them with the "Watchlist" sector option.'),
            ('bell', '#DC2626',
             'Cảnh báo giá cá nhân' if not is_en else 'Private Price Alerts',
             'Đặt mục tiêu giá above/below cho mỗi mã; chuông topbar hiện badge khi giá chạm.'
             if not is_en else
             'Set above/below price targets per ticker; topbar bell badges when triggered.'),
            ('journal-text', '#A855F7',
             'Nhật ký giao dịch' if not is_en else 'Trade Journal',
             'Ghi luận điểm vào lệnh + bài học rút ra cho từng giao dịch; mở khoá huy hiệu thành tựu.'
             if not is_en else
             'Log entry thesis + post-trade lessons; unlock achievement badges.'),
        ]
        cols = st.columns(2)
        for i, (ic_name, color, title, desc) in enumerate(previews):
            with cols[i % 2]:
                st.markdown(
                    f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
                    f'border-left:4px solid {color};border-radius:10px;padding:14px 18px;'
                    f'margin-bottom:10px">'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                    f'<span style="width:32px;height:32px;border-radius:50%;'
                    f'background:{color}1A;display:inline-flex;align-items:center;'
                    f'justify-content:center">{_icon(ic_name, 16, color)}</span>'
                    f'<span style="font-size:14px;font-weight:800;color:{_T["text_primary"]}">{title}</span>'
                    f'</div>'
                    f'<div style="font-size:12.5px;color:{_T["text_secondary"]};line-height:1.65">'
                    f'{desc}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin:14px 0 6px'></div>", unsafe_allow_html=True)
        if st.button(('Đăng xuất để đăng ký / đăng nhập' if not is_en
                      else 'Sign out to register / log in'),
                      key='_prof_go_login', type='primary',
                      use_container_width=False):
            logout_user()
            st.rerun()
        return

    u = current_user() or {}
    uid = u.get('id', '')

    # ── KPI card thông tin tài khoản ─────────────────────────────────
    _name = u.get('display_name') or u.get('username') or '—'
    _email = u.get('email') or '—'
    _created = (u.get('created_at') or '—')[:10]
    _last = (u.get('last_seen') or '—')[:19].replace('T', ' ')
    _initial = (_name[:1] or '?').upper()

    st.markdown(
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-left:5px solid {_T["accent"]};border-radius:14px;'
        f'padding:18px 22px;margin:12px 0 18px;display:flex;gap:18px;'
        f'align-items:center;flex-wrap:wrap">'
        f'<div style="width:64px;height:64px;border-radius:50%;'
        f'background:linear-gradient(135deg,{_T["accent"]} 0%,#1E40AF 100%);'
        f'color:#fff;display:flex;align-items:center;justify-content:center;'
        f'font-size:30px;font-weight:800">{_initial}</div>'
        f'<div style="flex:1;min-width:240px">'
        f'<div style="font-size:18px;font-weight:800;color:{_T["text_primary"]};'
        f'margin-bottom:2px">{_name}</div>'
        f'<div style="font-size:12px;color:{_T["text_secondary"]};line-height:1.7">'
        f'<b>{"Tên đăng nhập" if not is_en else "Username"}:</b> '
        f'<span style="font-family:monospace">{u.get("username","—")}</span> · '
        f'<b>Email:</b> {_email}<br>'
        f'<b>{"Ngày tạo" if not is_en else "Created"}:</b> {_created} · '
        f'<b>{"Hoạt động gần nhất" if not is_en else "Last seen"}:</b> {_last}<br>'
        f'<b>ID:</b> <span style="font-family:monospace;font-size:11px">{uid}</span>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    tab_info, tab_pw, tab_export, tab_danger = st.tabs([
        '  ' + ('Hồ sơ' if not is_en else 'Profile') + '  ',
        '  ' + ('Đổi mật khẩu' if not is_en else 'Change Password') + '  ',
        '  ' + ('Xuất dữ liệu' if not is_en else 'Export Data') + '  ',
        '  ' + ('Vùng nguy hiểm' if not is_en else 'Danger Zone') + '  ',
    ])

    # ── Tab 1: Hồ sơ — sửa display name + email ─────────────────────
    with tab_info:
        with st.form('_prof_form'):
            new_name = st.text_input(
                'Tên hiển thị' if not is_en else 'Display name',
                value=u.get('display_name', ''), key='_prof_name', max_chars=64)
            new_email = st.text_input(
                'Email (tuỳ chọn)' if not is_en else 'Email (optional)',
                value=u.get('email') or '', key='_prof_email')
            ok = st.form_submit_button(
                'Lưu thay đổi' if not is_en else 'Save changes',
                type='primary', use_container_width=False)
        if ok:
            ok2, msg = update_profile(uid, display_name=new_name, email=new_email)
            if ok2:
                # Cập nhật session user
                u2 = find_user(u.get('username', ''))
                if u2:
                    rec_pub = {k: v for k, v in u2.items() if k != 'password_hash'}
                    login_user(rec_pub)
                st.success(msg); st.rerun()
            else:
                st.error(msg)

    # ── Tab 2: Đổi mật khẩu ─────────────────────────────────────────
    with tab_pw:
        with st.form('_prof_pw'):
            old = st.text_input(
                'Mật khẩu hiện tại' if not is_en else 'Current password',
                type='password', key='_prof_pw_old')
            new1 = st.text_input(
                'Mật khẩu mới' if not is_en else 'New password',
                type='password', key='_prof_pw_n1',
                help='Tối thiểu 6 ký tự')
            new2 = st.text_input(
                'Nhập lại mật khẩu mới' if not is_en else 'Confirm new password',
                type='password', key='_prof_pw_n2')
            ok = st.form_submit_button(
                'Đổi mật khẩu' if not is_en else 'Change password',
                type='primary')
        if ok:
            if (new1 or '') != (new2 or ''):
                st.error('Hai lần nhập mật khẩu mới không khớp.'
                          if not is_en else 'New passwords do not match.')
            else:
                ok2, msg = change_password(uid, old or '', new1 or '')
                if ok2:
                    st.success(msg)
                else:
                    st.error(msg)

    # ── Tab 3: Xuất dữ liệu ─────────────────────────────────────────
    with tab_export:
        st.markdown(
            f'<div style="font-size:13px;color:{_T["text_secondary"]};line-height:1.7">'
            f'{"Tải về 1 file ZIP gồm tất cả dữ liệu của bạn: sổ Paper Trading, danh mục yêu thích, nhật ký giao dịch, cảnh báo giá. Không kèm mật khẩu." if not is_en else "Download a ZIP containing all your data: paper book, watchlist, journal, alerts. Password is NOT included."}'
            f'</div>', unsafe_allow_html=True)
        try:
            _zip = _build_export_zip(uid)
            _fname = f'finscope_{u.get("username","user")}_{_dt.date.today().isoformat()}.zip'
            st.markdown("<div style='margin:12px 0'></div>", unsafe_allow_html=True)
            st.download_button(
                ('Tải dữ liệu (ZIP)' if not is_en else 'Download data (ZIP)'),
                data=_zip, file_name=_fname, mime='application/zip',
                key='_prof_dl', use_container_width=False, type='primary')
            st.caption(f'{len(_zip)/1024:.1f} KB')
        except Exception as e:
            st.error(f'Lỗi đóng gói: {e}')

    # ── Tab 4: Vùng nguy hiểm ───────────────────────────────────────
    with tab_danger:
        from ui.icons import icon as _icon
        _warn = _icon('exclamation-triangle-fill', 18, _T['danger'])
        st.markdown(
            f'<div style="background:{_T["danger_bg"]};border:2px solid {_T["danger"]};'
            f'border-radius:12px;padding:18px 22px;color:{_T["danger"]};font-size:13px;'
            f'line-height:1.7">'
            f'<div style="display:flex;gap:10px;align-items:flex-start">'
            f'<span style="flex-shrink:0;padding-top:1px">{_warn}</span>'
            f'<div><b>{"Xoá tài khoản — không hoàn tác." if not is_en else "Delete account — irreversible."}</b><br>'
            f'<span style="color:{_T["text_primary"]}">'
            f'{"Tài khoản sẽ bị xoá khỏi danh sách đăng nhập. Sổ Paper Trading, watchlist, nhật ký, cảnh báo của bạn vẫn được giữ trên ổ đĩa (để có thể khôi phục nếu cần) nhưng không truy cập được nữa." if not is_en else "Account will be removed from login. Your paper book, watchlist, journal, alerts remain on disk for recovery but are no longer accessible."}'
            f'</span></div></div></div>',
            unsafe_allow_html=True)
        with st.form('_prof_del'):
            confirm_pw = st.text_input(
                'Nhập mật khẩu để xác nhận' if not is_en else 'Enter password to confirm',
                type='password', key='_prof_del_pw')
            confirm_text = st.text_input(
                'Gõ XOA-TAI-KHOAN để chắc chắn' if not is_en else 'Type DELETE to confirm',
                key='_prof_del_text')
            ok = st.form_submit_button(
                'Xoá vĩnh viễn tài khoản' if not is_en else 'Delete account permanently')
        if ok:
            magic = 'XOA-TAI-KHOAN' if not is_en else 'DELETE'
            if (confirm_text or '').strip().upper() != magic.upper():
                st.error(
                    (f'Gõ chính xác "{magic}" để xác nhận.' if not is_en
                     else f'Type exactly "{magic}" to confirm.'))
            else:
                ok2, msg = delete_user(uid, confirm_pw or '')
                if ok2:
                    st.success(msg)
                    logout_user()
                    st.rerun()
                else:
                    st.error(msg)

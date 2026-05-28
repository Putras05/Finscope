"""Logo thương hiệu FinScope — SVG tự vẽ, KHÔNG dùng emoji/icon ngoài.

Concept v2 (redesign): MONOGRAM "F" + MŨI TÊN VỌT LÊN.
  • Chữ "F" trắng đậm hình học (spine dọc + 2 stroke ngang) — chữ cái đầu
    của "FinScope" và "Finance"; cấu trúc 90° tạo cảm giác chắc chắn,
    kỹ thuật, đáng tin.
  • Mũi tên vàng (#FACC15) bứt lên từ đỉnh chữ F → trỗi cao bên phải:
    đọc ngay ra "thị trường đang lên", thay vì hình kính lúp chung chung.
  • 3 chấm mini bar-chart dưới đáy = nhịp dữ liệu (data heartbeat),
    thêm chiều sâu cho mark khi nhìn ở size lớn.
  • Gradient #1E40AF → #0891B2 → #0F766E giữ bảng màu chủ đạo của app.

Hai biến thể:
  • mark_gradient(size): huy hiệu bo góc nền gradient (splash, favicon).
  • mark_mono(size, color): bản nét đơn sắc trong suốt (topbar bên chữ).
"""

_GRAD_ID = 'finscope_grad'


def mark_gradient(size: int = 56, rid: str = _GRAD_ID) -> str:
    """Huy hiệu FinScope nền gradient bo góc — splash / nơi nổi bật.

    rid: id gradient (đặt KHÁC nhau nếu render nhiều bản trên cùng 1 trang)."""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 64 64' fill='none' "
        f"xmlns='http://www.w3.org/2000/svg' role='img' aria-label='FinScope'>"
        f"<defs>"
        f"<linearGradient id='{rid}' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='#1E40AF'/>"
        f"<stop offset='0.55' stop-color='#0891B2'/>"
        f"<stop offset='1' stop-color='#0F766E'/>"
        f"</linearGradient>"
        f"<linearGradient id='{rid}_arrow' x1='0' y1='1' x2='1' y2='0'>"
        f"<stop offset='0' stop-color='#FACC15'/>"
        f"<stop offset='1' stop-color='#FDE68A'/>"
        f"</linearGradient>"
        f"</defs>"
        # NỀN huy hiệu — gradient bo góc 16px
        f"<rect x='2' y='2' width='60' height='60' rx='16' fill='url(#{rid})'/>"
        # SHEEN nhẹ phía trên (highlight subtle, không lóa)
        f"<rect x='2' y='2' width='60' height='30' rx='16' "
        f"fill='rgba(255,255,255,0.08)'/>"
        # MONOGRAM F — chữ F hình học trắng đậm
        # spine dọc (cột chính của F)
        f"<rect x='14' y='14' width='8' height='36' rx='2' fill='#FFFFFF'/>"
        # stroke trên (cánh trên của F) — dài 18px
        f"<rect x='14' y='14' width='22' height='8' rx='2' fill='#FFFFFF'/>"
        # stroke giữa (cánh giữa của F) — ngắn hơn 4px
        f"<rect x='14' y='28' width='16' height='7' rx='2' fill='#FFFFFF'/>"
        # MŨI TÊN VÀNG vọt lên từ đỉnh F sang góc phải-trên
        # thân mũi tên (đường chéo lên)
        f"<path d='M36 22 L52 8' stroke='url(#{rid}_arrow)' stroke-width='4' "
        f"stroke-linecap='round' fill='none'/>"
        # đầu mũi tên (cánh trên + cánh dưới)
        f"<path d='M44 8 L52 8 L52 16' stroke='url(#{rid}_arrow)' stroke-width='4' "
        f"stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
        # 3 chấm mini bar-chart dưới đáy (data heartbeat) — chỉ hiện ở size lớn
        f"<rect x='34' y='44' width='4' height='6'  rx='1' fill='rgba(255,255,255,0.55)'/>"
        f"<rect x='41' y='40' width='4' height='10' rx='1' fill='rgba(255,255,255,0.70)'/>"
        f"<rect x='48' y='36' width='4' height='14' rx='1' fill='#FFFFFF'/>"
        f"</svg>"
    )


def mark_mono(size: int = 24, color: str = '#1E40AF',
              accent: str = '#F59E0B') -> str:
    """Bản nét đơn sắc — chèn cạnh chữ FinScope ở topbar.

    color: màu chữ F chính. accent: màu mũi tên vọt lên (gold)."""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"xmlns='http://www.w3.org/2000/svg' role='img' aria-label='FinScope'>"
        # MONOGRAM F (filled rectangles)
        # spine dọc
        f"<rect x='4' y='3' width='3' height='17' rx='0.5' fill='{color}'/>"
        # stroke trên
        f"<rect x='4' y='3' width='10' height='3' rx='0.5' fill='{color}'/>"
        # stroke giữa
        f"<rect x='4' y='10' width='7' height='2.5' rx='0.5' fill='{color}'/>"
        # MŨI TÊN vàng (accent) — vọt từ đỉnh F lên góc phải-trên
        f"<path d='M14 6 L20 1.5' stroke='{accent}' stroke-width='2' "
        f"stroke-linecap='round' fill='none'/>"
        f"<path d='M16.5 1.5 L20 1.5 L20 5' stroke='{accent}' stroke-width='2' "
        f"stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
        f"</svg>"
    )

"""Logo thương hiệu FinScope — SVG tự vẽ, KHÔNG dùng emoji/icon ngoài.

Ý nghĩa thiết kế:
  • "Scope" = thấu kính / ống ngắm → vòng tròn kính lúp + tay cầm dưới-phải.
  • "Fin" (tài chính) → bên trong thấu kính là 3 cây nến + đường xu hướng
    BỨT LÊN xuyên khỏi vành kính → "soi đúng cơ hội thị trường đang lên".
  • Gradient xanh dương → cyan → teal: trùng bảng màu chủ đạo của app
    (#1E40AF / #0891B2 / #0F766E) → nhận diện đồng bộ toàn giao diện.

Hai biến thể:
  • mark_gradient(size): huy hiệu bo góc nền gradient (splash / favicon).
  • mark_mono(size, color): bản nét đơn sắc trong suốt (chèn cạnh chữ ở topbar).
"""

_GRAD_ID = 'finscope_grad'


def mark_gradient(size: int = 56, rid: str = _GRAD_ID) -> str:
    """Huy hiệu FinScope nền gradient bo góc — dùng cho splash / nơi nổi bật.

    rid: id gradient (đặt KHÁC nhau nếu render nhiều bản trên cùng 1 trang để
    tránh trùng id trong DOM)."""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 64 64' fill='none' "
        f"xmlns='http://www.w3.org/2000/svg' role='img' aria-label='FinScope'>"
        f"<defs>"
        f"<linearGradient id='{rid}' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='#1E40AF'/>"
        f"<stop offset='0.55' stop-color='#0891B2'/>"
        f"<stop offset='1' stop-color='#0F766E'/>"
        f"</linearGradient>"
        f"</defs>"
        # nền huy hiệu bo góc
        f"<rect x='2' y='2' width='60' height='60' rx='16' fill='url(#{rid})'/>"
        # tay cầm kính lúp (dưới-phải) — vẽ TRƯỚC để vành kính đè lên gốc
        f"<line x1='42.5' y1='40.5' x2='52' y2='50' stroke='#FFFFFF' "
        f"stroke-width='5' stroke-linecap='round'/>"
        # vành thấu kính (scope)
        f"<circle cx='28' cy='27' r='17.5' fill='rgba(255,255,255,0.10)' "
        f"stroke='#FFFFFF' stroke-width='3'/>"
        # 3 cây nến trong kính (thân trắng, tăng dần)
        f"<g stroke='#FFFFFF' stroke-linecap='round'>"
        f"<line x1='21' y1='20' x2='21' y2='36' stroke-width='1.6'/>"
        f"<rect x='18.6' y='27' width='4.8' height='8' rx='1' fill='#FFFFFF' stroke='none'/>"
        f"<line x1='28' y1='17' x2='28' y2='34' stroke-width='1.6'/>"
        f"<rect x='25.6' y='23' width='4.8' height='8' rx='1' fill='#FFFFFF' stroke='none'/>"
        f"<line x1='35' y1='14' x2='35' y2='31' stroke-width='1.6'/>"
        f"<rect x='32.6' y='19' width='4.8' height='8' rx='1' fill='#FFFFFF' stroke='none'/>"
        f"</g>"
        # đường xu hướng bứt lên xuyên vành kính (mũi tên)
        f"<path d='M16 33 L24 28 L31 23 L41 13' fill='none' stroke='#FACC15' "
        f"stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/>"
        f"<path d='M35.5 13 L41 13 L41 18.5' fill='none' stroke='#FACC15' "
        f"stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/>"
        f"</svg>"
    )


def mark_mono(size: int = 24, color: str = '#1E40AF') -> str:
    """Bản nét đơn sắc, nền trong suốt — chèn cạnh chữ FinScope ở topbar."""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"stroke='{color}' stroke-width='2' stroke-linecap='round' "
        f"stroke-linejoin='round' role='img' aria-label='FinScope'>"
        # vành kính
        f"<circle cx='10' cy='10' r='7'/>"
        # tay cầm
        f"<line x1='15.2' y1='15.2' x2='21' y2='21'/>"
        # đường xu hướng đi lên trong kính
        f"<path d='M6.5 12.5 L9 10 L11 11.5 L14 7.5'/>"
        f"<path d='M12.4 7.5 L14 7.5 L14 9.1'/>"
        f"</svg>"
    )

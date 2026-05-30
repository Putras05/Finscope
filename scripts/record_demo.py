"""Tự động quay video demo FinScope bằng Playwright.

Cài 1 lần:
    pip install playwright
    playwright install chromium

Chạy:
    python scripts/record_demo.py

Output: scripts/finscope_demo.webm (sau đó dùng FFmpeg để convert mp4
nếu cần — VLC/most players đã đọc .webm trực tiếp).

Kịch bản:
    1. Mở Login → click Khách
    2. Dashboard FPT (chờ chart render)
    3. Thị trường (snapshot)
    4. Cơ bản (financial)
    5. Chi tiết (8 mô hình tab)
    6. Nâng cao (fan chart)
    7. Chiến lược (signal engine)
    8. Tín hiệu (11 indicators)
    9. Danh mục (Markowitz/CAPM/PCA)
    10. Paper (giao dịch demo)
    11. Cơ sở Toán (LaTeX formulas)
    Tổng: ~5-7 phút.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

URL = 'https://finscope-bfz4abyb4tq6fhg6rd3gkx.streamlit.app/'
OUT_DIR = Path(__file__).resolve().parent
VIEWPORT = {'width': 1440, 'height': 900}


# Sequence: (nav_label_substring, wait_seconds_after_click)
SEQUENCE = [
    ('Dashboard',    8),   # KPI + candlestick + forecast
    ('Thị trường',   10),  # 53-ticker snapshot heatmap
    ('Cơ bản',       8),   # fundamental ratios
    ('Chi tiết',     12),  # 9 tabs models — give time
    ('Nâng cao',     10),  # fan chart 7 tabs
    ('Chiến lược',   8),   # signal engine
    ('Tín hiệu',     8),   # 11 indicators
    ('Danh mục',     12),  # Markowitz + CAPM + PCA + Cointegration
    ('Paper',        10),  # paper trading
    ('Cơ sở Toán',   8),   # LaTeX formulas
]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: playwright chưa cài. Chạy:\n'
              '  pip install playwright\n'
              '  playwright install chromium')
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True để chạy nền
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(OUT_DIR),
            record_video_size=VIEWPORT,
            locale='vi-VN',
        )
        page = context.new_page()

        print(f'[1/12] Mở {URL}')
        page.goto(URL, wait_until='networkidle', timeout=60_000)
        time.sleep(3)

        # Login as guest — click tab "Dùng thử (Khách)" rồi nút "VÀO NHANH..."
        print('[2/12] Login chế độ Khách')
        try:
            page.get_by_text('Dùng thử', exact=False).first.click(timeout=10_000)
            time.sleep(1)
            page.get_by_text('VÀO NHANH', exact=False).first.click(timeout=10_000)
        except Exception as e:
            print(f'   ⚠ Không click được Khách: {e}')
        time.sleep(15)  # đợi splash xong

        for i, (label, wait_s) in enumerate(SEQUENCE, start=3):
            print(f'[{i}/12] Click {label!r} (chờ {wait_s}s)')
            try:
                # Streamlit option_menu render label thành text trong span/p
                page.get_by_text(label, exact=False).first.click(timeout=10_000)
            except Exception as e:
                print(f'   ⚠ Skip {label}: {e}')
            time.sleep(wait_s)
            # Scroll xuống nửa trang để show thêm nội dung
            page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
            time.sleep(2)
            page.evaluate('window.scrollTo(0, 0)')
            time.sleep(1)

        print('[12/12] Logout')
        try:
            page.get_by_text('Đăng xuất', exact=False).first.click(timeout=5_000)
        except Exception:
            pass
        time.sleep(2)

        # Đóng context để flush video ra file
        context.close()
        browser.close()

    # Tìm file video mới nhất
    videos = sorted(OUT_DIR.glob('*.webm'), key=lambda p: p.stat().st_mtime, reverse=True)
    if videos:
        v = videos[0]
        # Rename cho gọn
        target = OUT_DIR / 'finscope_demo.webm'
        if target.exists():
            target.unlink()
        v.rename(target)
        size_mb = target.stat().st_size / 1024 / 1024
        print(f'\n✅ Done: {target} ({size_mb:.1f} MB)')
        print('   Convert sang mp4 (tùy chọn):')
        print(f'   ffmpeg -i {target.name} -c:v libx264 -preset slow -crf 23 finscope_demo.mp4')
    else:
        print('⚠ Không tìm thấy file video — playwright record_video chưa flush?')


if __name__ == '__main__':
    main()

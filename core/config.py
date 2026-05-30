PAGE_TITLE  = "FinScope · Dự báo Chứng khoán HOSE"
PAGE_ICON   = "📈"
LAYOUT      = "wide"
SIDEBAR_STATE = "collapsed"  # sidebar không dùng — điều hướng + tham số ở topbar main area
DATA_START  = "2012-01-01"
DATA_END    = "2030-12-31"
DATA_SOURCE = "KBS"
CACHE_TTL   = 86400  # 24 giờ. v56: tăng từ 6h → 24h. HOSE chỉ chốt giá
                       # 1 lần/ngày 14:45; cache 24h ≈ session boundary.


def is_streamlit_cloud() -> bool:
    """Detect runtime đang chạy trên Streamlit Community Cloud.

    Filesystem trên Cloud là ephemeral — container reset khi redeploy /
    idle 7 ngày / hạ tầng nâng cấp → users.json + paper_state + watchlist
    mất hết. UI cần hiện banner cảnh báo + khuyến nghị dùng chế độ Khách
    cho ban giám khảo demo nhanh.

    Detection heuristic (Streamlit Cloud convention):
      - __file__ chứa `/mount/src/` (folder mặc định mount source)
      - HOSTNAME env var dạng `streamlit-...`
    """
    import os
    from pathlib import Path
    try:
        if '/mount/src/' in str(Path(__file__).resolve()):
            return True
    except Exception:
        pass
    if 'streamlit' in (os.environ.get('HOSTNAME', '') or '').lower():
        return True
    return False

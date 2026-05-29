PAGE_TITLE  = "FinScope · Dự báo Chứng khoán HOSE"
PAGE_ICON   = "📈"
LAYOUT      = "wide"
SIDEBAR_STATE = "collapsed"  # sidebar không dùng — điều hướng + tham số ở topbar main area
DATA_START  = "2012-01-01"
DATA_END    = "2030-12-31"
DATA_SOURCE = "KBS"
CACHE_TTL   = 86400  # 24 giờ. v56: tăng từ 6h → 24h. HOSE chỉ chốt giá
                       # 1 lần/ngày 14:45; cache 24h ≈ session boundary.

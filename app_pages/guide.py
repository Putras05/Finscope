import streamlit as st


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    _is_en = st.session_state.get('lang', 'VI') == 'EN'
    # _T param từ caller — KHÔNG override bằng theme() (mất theme override nếu caller pass)

    st.markdown(f"""
<div style="background:{_T['banner_bg']};border-radius:14px;padding:24px 32px;
            margin-bottom:24px;border:1px solid {_T['border']}">
  <div style="display:flex;align-items:center;gap:16px">
    <div style="width:52px;height:52px;border-radius:12px;
                background:linear-gradient(135deg,#1E40AF,#3B82F6);
                display:flex;align-items:center;justify-content:center;flex-shrink:0">
      <svg width="26" height="26" viewBox="0 0 16 16" fill="#FFFFFF"><path d="M8.5 2.687c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783"/></svg>
    </div>
    <div>
      <div style="font-size:22px;font-weight:800;color:{_T['banner_text']};line-height:1.2">
        {'User Guide' if _is_en else 'Hướng dẫn Sử dụng'}
      </div>
      <div style="font-size:13px;color:{_T['banner_subtext']};margin-top:4px">
        {'FinScope · Multi-model Stock Analysis & Forecasting'
         if _is_en else
         'FinScope · Phân tích & Dự báo Chứng khoán Đa mô hình'}
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    _SVGS = {
        'speedometer2': '<path d="M8 4a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0zm3.5.5a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1zm-7 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1zm11 0a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0zM4.354 8.646a.5.5 0 1 0-.708.708.5.5 0 0 0 .708-.708zm7.996-5.039a.5.5 0 1 0-.708.707.5.5 0 0 0 .708-.707zm-9.29 9.29a.5.5 0 1 0 .707-.708.5.5 0 0 0-.707.708zM8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8z"/><path d="M8 7.5a.5.5 0 0 0-.354.854l.5.5a.5.5 0 0 0 .707 0l4-4a.5.5 0 0 0-.707-.707L8.5 7.793l-.146-.146A.5.5 0 0 0 8 7.5z"/>',
        'graph-up-arrow': '<path fill-rule="evenodd" d="M0 0h1v15h15v1H0zm10 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V4.9l-3.613 4.417a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61L13.445 4H10.5a.5.5 0 0 1-.5-.5z"/>',
        'clock-history':  '<path d="M8.515 1.019A7 7 0 0 0 8 1V0a8 8 0 0 1 .589.022zm2.004.45a7 7 0 0 0-.985-.299l.219-.976q.576.129 1.126.342zm1.37.71a7 7 0 0 0-.831-.556l.51-.857q.48.27.92.598zm1.658 1.545a7 7 0 0 0-.653-.796l.724-.69q.406.429.747.91zm.744 1.352a7 7 0 0 0-.394-.952l.893-.45a8 8 0 0 1 .45 1.088zm.53 2.507a7 7 0 0 0-.1-1.025l.985-.17q.1.58.116 1.17zm-.131 1.538q.05-.254.081-.51l.993.123a8 8 0 0 1-.23 1.155zm-.952 2.379q.276-.436.486-.908l.914.405q-.24.54-.555 1.038zm-1.243 1.81q.183-.183.35-.378l.758.653a8 8 0 0 1-.401.432zM8 1a7 7 0 1 0 4.95 11.95l.707.707A8.001 8.001 0 1 1 8 0z"/><path d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5z"/>',
        'activity':       '<path fill-rule="evenodd" d="M6 2a.5.5 0 0 1 .47.33L10 12.036l1.53-4.208A.5.5 0 0 1 12 7.5h3.5a.5.5 0 0 1 0 1h-3.15l-1.88 5.17a.5.5 0 0 1-.94 0L6 3.964 4.47 8.171A.5.5 0 0 1 4 8.5H.5a.5.5 0 0 1 0-1h3.15l1.88-5.17A.5.5 0 0 1 6 2z"/>',
        'briefcase':      '<path d="M6.5 1A1.5 1.5 0 0 0 5 2.5V3H1.5A1.5 1.5 0 0 0 0 4.5v8A1.5 1.5 0 0 0 1.5 14h13a1.5 1.5 0 0 0 1.5-1.5v-8A1.5 1.5 0 0 0 14.5 3H11v-.5A1.5 1.5 0 0 0 9.5 1zm0 1h3a.5.5 0 0 1 .5.5V3H6v-.5a.5.5 0 0 1 .5-.5zm1.886 6.914L15 7.151V12.5a.5.5 0 0 1-.5.5h-13a.5.5 0 0 1-.5-.5V7.15l6.614 1.764a1.5 1.5 0 0 0 .772 0zM1.5 4h13a.5.5 0 0 1 .5.5v1.616L8.129 7.948a.5.5 0 0 1-.258 0L1 6.116V4.5a.5.5 0 0 1 .5-.5z"/>',
        'sliders':        '<path d="M11.5 2a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM9.05 3a2.5 2.5 0 0 1 4.9 0H16v1h-2.05a2.5 2.5 0 0 1-4.9 0H0V3zm-4.55 4a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM2.05 8a2.5 2.5 0 0 1 4.9 0H16v1H6.95a2.5 2.5 0 0 1-4.9 0H0V8zm9.45 4a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm-2.45 1a2.5 2.5 0 0 1 4.9 0H16v1h-2.05a2.5 2.5 0 0 1-4.9 0H0v-1z"/>',
        'info-circle-fill':'<path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>',
        'bezier2':        '<path fill-rule="evenodd" d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01q.21.236.393.5H7.5a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1A1.5 1.5 0 0 1 5 7v-.5H2.5A1.5 1.5 0 0 1 1 5zM2.5 2a.5.5 0 0 0-.5.5v2a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-2a.5.5 0 0 0-.5-.5zm5.5 4.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5zM2.5 11a.5.5 0 0 0-.5.5v2a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-2a.5.5 0 0 0-.5-.5zM1 11.5A1.5 1.5 0 0 1 2.5 10h1A1.5 1.5 0 0 1 5 11.5h4.134a1 1 0 1 1 0 1h-2.01q.21.236.393.5H7.5a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1A1.5 1.5 0 0 1 5 16v-.5H2.5A1.5 1.5 0 0 1 1 14z"/>',
    }

    def _ic(name: str, color: str, size: int = 18) -> str:
        body = _SVGS.get(name, '<circle cx="8" cy="8" r="6"/>')
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
                f'fill="{color}" xmlns="http://www.w3.org/2000/svg">{body}</svg>')

    def _guide_card(icon_name: str, title: str, color: str, body_html: str):
        icon_svg = _ic(icon_name, color, 18)
        st.markdown(f"""
<div style="background:{_T['bg_card']};border:1px solid {_T['border']};
            border-radius:12px;padding:20px 24px;margin-bottom:16px;
            border-left:4px solid {color}">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
    <div style="width:38px;height:38px;border-radius:9px;background:{color}28;
                display:flex;align-items:center;justify-content:center;flex-shrink:0">
      {icon_svg}
    </div>
    <div style="font-size:15px;font-weight:700;color:{_T['text_primary']}">{title}</div>
  </div>
  <div style="color:{_T['text_primary']};font-size:13px;line-height:1.75">
    {body_html}
  </div>
</div>
""", unsafe_allow_html=True)

    _SVGS['newspaper'] = '<path d="M0 2.5A1.5 1.5 0 0 1 1.5 1h11A1.5 1.5 0 0 1 14 2.5v10.528c0 .3-.05.654-.238.972h.738a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 1 1 0v9a1.5 1.5 0 0 1-1.5 1.5H1.497A1.497 1.497 0 0 1 0 13.5zM12 14c.37 0 .654-.211.853-.441.092-.106.147-.279.147-.531V2.5a.5.5 0 0 0-.5-.5h-11a.5.5 0 0 0-.5.5v11c0 .278.223.5.497.5z"/><path d="M2 3h10v2H2zm0 3h4v3H2zm0 4h4v1H2zm0 2h4v1H2zm5-6h2v1H7zm3 0h2v1h-2zM7 8h2v1H7zm3 0h2v1h-2zm-3 2h2v1H7zm3 0h2v1h-2zm-3 2h2v1H7zm3 0h2v1h-2z"/>'

    _IC_DASH = 'speedometer2'
    _IC_ANA  = 'graph-up-arrow'
    _IC_ADV  = 'bezier2'
    _IC_HIST = 'clock-history'
    _IC_SIG  = 'activity'
    _IC_PORT = 'briefcase'
    _IC_SET  = 'sliders'

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        _guide_card(_IC_DASH, 'Dashboard Tổng quan' if not _is_en else 'Overview Dashboard',
                    '#3B82F6', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Cung cấp cái nhìn nhanh về mã đang chọn (danh sách VN30): giá, KPI, dự báo đa mô hình, tín hiệu kỹ thuật.'
 if not _is_en else 'Quick snapshot of the selected VN30 ticker: price, KPIs, multi-model forecast, technical signals.'}<br><br>

<b style="color:{_T['text_primary']}">{'Các thông tin hiển thị:' if not _is_en else 'Information displayed:'}</b><br>
{'• Giá đóng cửa hiện tại + KPI biến động/khối lượng/tín hiệu Ichimoku<br>'
 '• Banner <b>Dự báo Kết hợp (FinScope Ensemble)</b> + 3 card <b>TOP-3 mô hình tốt nhất theo MAPE</b> (động, không cố định)<br>'
 '• Thẻ <b>Tâm lý tin tức</b> (đọc hiểu) + AI Insight: Ichimoku 4 tầng + dự báo phiên tới<br>'
 '• <b>Biểu đồ nến TradingView-style</b>: khung 1D/1W/1M/3M, toggle SMA 5/20 & Ichimoku, info bar O/H/L/C, volume<br>'
 '• Dự báo nhiều phiên (fan chart) + bảng đa mô hình + <b>kiểm định Diebold–Mariano</b> + xếp hạng MAPE'
 if not _is_en else
 '• Current close price + volatility/volume/Ichimoku KPIs<br>'
 '• <b>Combined Forecast (FinScope Ensemble)</b> banner + 3 cards = <b>TOP-3 models by MAPE</b> (dynamic, not fixed)<br>'
 '• <b>News sentiment</b> card + AI Insight: Ichimoku 4-tier signal + next-session forecast<br>'
 '• <b>TradingView-style candlestick</b>: 1D/1W/1M/3M, toggle SMA 5/20 & Ichimoku, OHLC info bar, volume<br>'
 '• Multi-step fan chart + multi-model table + <b>Diebold–Mariano test</b> + MAPE ranking'}
""")

        _guide_card('graph-up-arrow', 'Tổng quan Thị trường' if not _is_en else 'Market Overview',
                    '#0F766E', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Bức tranh TỔNG cả thị trường (53 mã HOSE) — snapshot mỗi 5 phút trong phiên: ai tăng, ai giảm, ngành nào dẫn dắt, dòng tiền chảy về đâu.'
 if not _is_en else 'WHOLE-market snapshot (53 HOSE tickers) refreshed every 5 min: who is up, who is down, which sectors lead, where the money flows.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• 6 KPI top: số mã tăng / giảm / đứng · Δ% trung bình · <b>vốn hóa tổng</b> · GTGD hôm nay<br>'
 '• <b>Top 5 tăng giá</b> / <b>Top 5 giảm giá</b> (2 cột song song)<br>'
 '• Bảng <b>tổng quan 31 ngành</b>: số mã · Δ% TB · advancers/decliners · vốn hóa · GTGD<br>'
 '• <b>Heatmap 53 mã</b>: cards sắp theo vốn hóa, màu nền theo % thay đổi<br>'
 '• Bảng dữ liệu đầy đủ + tải CSV'
 if not _is_en else
 '• 6 top KPIs: advancers / decliners / unchanged · avg Δ% · <b>total market cap</b> · today turnover<br>'
 '• <b>Top 5 gainers</b> / <b>Top 5 losers</b> (side-by-side)<br>'
 '• <b>31-sector overview</b>: # tickers · avg Δ% · advancers/decliners · mcap · turnover<br>'
 '• <b>53-ticker heatmap</b>: cards sorted by mcap, colored by %change<br>'
 '• Full data table + CSV download'}
""")

        _guide_card(_IC_HIST, 'Lịch sử & Dữ liệu' if not _is_en else 'History & Data',
                    '#F59E0B', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Xem dữ liệu lịch sử và thống kê mô tả.'
 if not _is_en else 'Browse historical data and descriptive statistics.'}<br><br>

<b style="color:{_T['text_primary']}">{'Cách sử dụng:' if not _is_en else 'How to use:'}</b><br>
{'• Chọn khoảng thời gian bằng bộ lọc <b>Từ</b> / <b>Đến</b> trên thanh điều khiển<br>'
 '• Biểu đồ giá lịch sử tương tác (zoom/pan/download)<br>'
 '• Phân phối Return hàng ngày so với phân phối Chuẩn<br>'
 '• Bảng dữ liệu OHLCV đầy đủ có thể tải xuống'
 if not _is_en else
 '• Select date range using <b>From</b> / <b>To</b> filters on the top bar<br>'
 '• Interactive historical price chart (zoom/pan/download)<br>'
 '• Daily Return distribution vs. Normal distribution<br>'
 '• Full OHLCV data table downloadable'}
""")

        _guide_card(_IC_PORT, 'Danh mục Đầu tư' if not _is_en else 'Investment Portfolio',
                    '#10B981', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'So sánh hiệu quả dự báo và rủi ro của <b>2–6 cổ phiếu</b> tuỳ chọn.'
 if not _is_en else 'Compare forecast performance and risk across <b>2–6 selectable stocks</b>.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• Card dự báo phiên tới mỗi mã (AR · MLR · ARIMA + <b>FinScope Ensemble</b>)<br>'
 '• Biểu đồ hiệu suất chuẩn hóa (Base = 100) — so sánh tương đối<br>'
 '• Bảng MAPE · RMSE · MAE · R²adj cho 4 mô hình × mỗi mã (đánh dấu mô hình tốt nhất)<br>'
 '• Thống kê Return (mean/std/min/max/up_days) cho mỗi mã'
 if not _is_en else
 '• Per-ticker next-session forecast cards (AR · MLR · ARIMA + <b>FinScope Ensemble</b>)<br>'
 '• Normalized performance chart (Base = 100) — relative comparison<br>'
 '• MAPE · RMSE · MAE · R²adj table for 4 models × each ticker (best model marked)<br>'
 '• Return stats (mean/std/min/max/up_days) per ticker'}
""")

        _guide_card(_IC_PORT, 'Giao dịch Demo (Paper Trading)' if not _is_en else 'Paper Trading',
                    '#F59E0B', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Tập giao dịch ảo với giá thị trường THẬT để theo dõi lãi/lỗ + thống kê hành vi (win rate, lệnh trung bình…). Sổ lệnh lưu cục bộ vào paper_state.json — KHÔNG phải tài khoản chứng khoán thật.'
 if not _is_en else 'Practice trading with REAL market prices, track P&L + behavior stats (win rate, avg trade…). Book stored locally in paper_state.json — NOT a real brokerage account.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• 5 KPI: <b>Tiền mặt · Giá trị nắm giữ · Tổng tài sản · P&L tổng · Tỉ lệ thắng</b><br>'
 '• Tab <b>Đặt lệnh</b>: chọn MUA/BÁN, KL, giá (mặc định = close gần nhất); preview tổng giá trị<br>'
 '• Tab <b>Vị thế hiện tại</b>: bảng KL · giá vốn TB · giá hiện tại · lãi/lỗ tạm tính<br>'
 '• Tab <b>Lịch sử lệnh</b>: log đầy đủ + realized P&L mỗi lệnh bán<br>'
 '• Tab <b>Thống kê & Reset</b>: avg win/loss · max win/loss · n_wins/n_losses + tuỳ chọn vốn ban đầu reset<br>'
 '• Vốn mặc định: <b>100 triệu đồng</b>. Bình quân gia quyền khi mua thêm, realized P&L tính theo avg cost'
 if not _is_en else
 '• 5 KPIs: <b>Cash · Holdings · Total Equity · Total P&L · Win Rate</b><br>'
 '• <b>Place Order</b> tab: pick BUY/SELL, qty, price (default = last close); total value preview<br>'
 '• <b>Current Positions</b> tab: qty · avg cost · current price · unrealized P&L<br>'
 '• <b>Order History</b> tab: full log + realized P&L per sell<br>'
 '• <b>Stats & Reset</b> tab: avg win/loss · max win/loss · n_wins/n_losses + custom-capital reset<br>'
 '• Default capital: <b>100M đồng</b>. Weighted-average cost basis on buys, realized P&L vs avg cost on sells'}
""")

        _guide_card('newspaper', 'Tin tức & Đọc hiểu' if not _is_en else 'News & AI Reading',
                    '#0891B2', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Đọc tin RSS thị trường (CafeF · VnExpress · Vietstock) và <b>đọc hiểu</b> bằng AI để bổ trợ tín hiệu — không dùng để dự báo giá.'
 if not _is_en else 'Read market RSS news (CafeF · VnExpress · Vietstock) and <b>comprehend</b> it with AI to augment the signal — not for price forecasting.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• Thẻ tâm lý <b>thị trường</b> & <b>theo mã</b> (từ điển tài chính tiếng Việt, có trọng số + ưu tiên tin mới)<br>'
 '• Nhận diện <b>chủ đề</b> mỗi tin (KQKD · cổ tức · M&A · pháp lý · vĩ mô · khối ngoại...) + gom nhóm <b>Chủ đề nổi bật</b><br>'
 '• Tùy chọn <b>Đọc hiểu bằng AI học sâu (PhoBERT)</b> — cảm xúc bằng Transformer tiếng Việt, hiển thị song song từ điển để đối chiếu<br>'
 '• Cảm xúc tin tham gia <b>phiếu tín hiệu</b> ở trang Chiến lược Giao dịch'
 if not _is_en else
 '• <b>Market</b> & <b>per-ticker</b> sentiment cards (weighted Vietnamese finance lexicon + recency)<br>'
 '• <b>Aspect</b> tags per headline (earnings · dividend · M&A · legal · macro · foreign flows...) + <b>theme clustering</b><br>'
 '• Optional <b>deep-learning AI reading (PhoBERT)</b> — Vietnamese Transformer sentiment shown side-by-side with the lexicon<br>'
 '• News sentiment feeds the <b>signal vote</b> on the Trading Strategy page'}
""")

    with col_g2:
        _guide_card(_IC_ANA, 'Phân tích Chi tiết' if not _is_en else 'Detailed Analysis',
                    '#8B5CF6', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Xem chi tiết các mô hình dự báo phiên kế tiếp — mỗi tab có phương trình, bảng tham số ước lượng, hiệu năng Train/Test, biểu đồ & khoảng tin cậy.'
 if not _is_en else 'Detailed view of each next-session forecasting model — each tab shows the equation, estimated-parameter table, Train/Test performance, charts & confidence interval.'}<br><br>

<b style="color:{_T['text_primary']}">{'9 tab (8 mô hình + Kết hợp):' if not _is_en else '9 tabs (8 models + Ensemble):'}</b><br>
{(f'• <b>AR(p)</b> — Tự hồi quy bậc p (Box-Jenkins), {ar_order+1} hệ số.<br>'
  f'• <b>MLR(p)</b> — Hồi quy đa biến Close + Volume + Range × p lag.<br>'
  f'• <b>ARIMA(p,d,q)</b> — Box-Jenkins tổng quát, order tự chọn theo AIC + chẩn đoán ACF/PACF.<br>'
  f'• <b>SARIMA</b> — ARIMA có mùa vụ (chu kỳ tuần s=5).<br>'
  f'• <b>Holt-Winters (ETS)</b> — San mũ có xu thế giảm dần (damped).<br>'
  f'• <b>GARCH</b> — AR(1) + GARCH(1,1): mô hình biến động có điều kiện.<br>'
  f'• <b>SARIMAX</b> — ARIMA + biến ngoại sinh log(Volume) & Range.<br>'
  f'• <b>Gradient Boosting</b> — học máy phi tuyến (cây) dự báo lợi suất → giá.<br>'
  f'• <b>FinScope Ensemble</b> — kết hợp các mô hình theo trọng số nghịch-MAPE.')
 if not _is_en else
 (f'• <b>AR(p)</b> — Autoregressive order p (Box-Jenkins), {ar_order+1} coefficients.<br>'
  f'• <b>MLR(p)</b> — Multiple linear regression on Close + Volume + Range × p lags.<br>'
  f'• <b>ARIMA(p,d,q)</b> — General Box-Jenkins, AIC-selected order + ACF/PACF diagnostics.<br>'
  f'• <b>SARIMA</b> — seasonal ARIMA (weekly period s=5).<br>'
  f'• <b>Holt-Winters (ETS)</b> — exponential smoothing with damped trend.<br>'
  f'• <b>GARCH</b> — AR(1) + GARCH(1,1) conditional-volatility model.<br>'
  f'• <b>SARIMAX</b> — ARIMA + exogenous log(Volume) & Range.<br>'
  f'• <b>Gradient Boosting</b> — nonlinear ML (trees) predicting return → price.<br>'
  f'• <b>FinScope Ensemble</b> — inverse-MAPE weighted combination of models.')
}<br><br>

<b style="color:{_T['text_primary']}">{'Biểu đồ hiển thị:' if not _is_en else 'Charts shown:'}</b><br>
{'• Lịch sử giá với vùng Train/Test được tô màu<br>'
 '• Kết quả dự báo: đường thực tế vs. dự báo theo thời gian<br>'
 '• Scatter thực tế vs. dự báo (R² = 1 là lý tưởng)<br>'
 '• Phương trình mô hình + bảng tham số ước lượng<br>'
 '• Chẩn đoán ARIMA: ACF/PACF + phần dư + Q-Q + fan chart khoảng tin cậy'
 if not _is_en else
 '• Price history with Train/Test regions highlighted<br>'
 '• Forecast results: actual vs. forecast time series<br>'
 '• Actual vs. forecast scatter (ideal R² = 1)<br>'
 '• Model equation + estimated parameter table<br>'
 '• ARIMA diagnostics: ACF/PACF + residuals + Q-Q + CI fan chart'}
""")

        _guide_card(_IC_ADV, 'Phân tích Cơ bản' if not _is_en else 'Fundamental Analysis',
                    '#7C3AED', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Phân tích báo cáo tài chính + các tỷ số tài chính (P/E, P/B, ROE, ROA, EPS, biên LN, D/E) — số liệu THẬT 4 quý gần nhất, không phải demo.'
 if not _is_en else 'Financial statement + ratio analysis (P/E, P/B, ROE, ROA, EPS, margins, D/E) — REAL data from the last 4 quarters, not demo.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• 7 KPI top: <b>P/E · P/B · EPS · ROE · ROA · Vốn hóa · D/E</b> — tự tính từ income + balance + giá thị trường (KHÔNG dùng endpoint ratio() bị paywalled trong vnstock)<br>'
 '• Bảng <b>Kết quả kinh doanh 4 quý</b>: doanh thu · LN gộp · LN trước/sau thuế · EPS — kèm bar chart Doanh thu/LN<br>'
 '• Bảng <b>Cân đối kế toán 4 quý</b>: tổng tài sản · vốn CSH · nợ ngắn/dài hạn · tiền<br>'
 '• 6 card <b>Biên LN & Tăng trưởng</b>: biên gộp/ròng · Δ QoQ doanh thu/LN · TTM revenue/income<br>'
 '• <b>Hỗ trợ cả NGÂN HÀNG</b>: BCTC bank khác DN thường → map riêng tự nhận diện'
 if not _is_en else
 '• 7 top KPIs: <b>P/E · P/B · EPS · ROE · ROA · Mcap · D/E</b> — self-computed from income + balance + market price (NOT using paywalled vnstock ratio() endpoint)<br>'
 '• <b>4-quarter income statement</b>: revenue · gross/operating/pretax/net profit · EPS — with Revenue/NI bar chart<br>'
 '• <b>4-quarter balance sheet</b>: assets · equity · short/long-term debt · cash<br>'
 '• 6 <b>Margins & Growth</b> cards: gross/net margin · QoQ revenue/NI · TTM revenue/income<br>'
 '• <b>Bank statements supported</b>: bank financials differ from corporates — separate auto-detected map'}
""")

        _guide_card(_IC_ADV, 'Mô hình Nâng cao' if not _is_en else 'Advanced Models',
                    '#0891B2', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Mở rộng sang bộ mô hình thống kê chuyên sâu và chức năng Khoảng tin cậy cho dự báo phiên kế tiếp.'
 if not _is_en else 'Extend to a suite of advanced statistical models plus a Confidence-Interval feature for the next-session forecast.'}<br><br>

<b style="color:{_T['text_primary']}">{'Mô hình nâng cao (thống kê · ML · kết hợp):' if not _is_en else 'Advanced models (statistical · ML · ensemble):'}</b><br>
{'• <b>SARIMA</b> — ARIMA có thành phần mùa vụ (chu kỳ tuần giao dịch s=5)<br>'
 '• <b>Holt-Winters (ETS)</b> — San mũ có xu thế giảm dần (damped trend)<br>'
 '• <b>GARCH</b> — AR(1) + GARCH(1,1): mô hình biến động có điều kiện<br>'
 '• <b>SARIMAX</b> — ARIMA + biến ngoại sinh log(Volume) & Range<br>'
 '• <b>Gradient Boosting</b> — học máy phi tuyến (cây quyết định)<br>'
 '• <b>FinScope Ensemble</b> — kết hợp tất cả theo trọng số nghịch-MAPE'
 if not _is_en else
 '• <b>SARIMA</b> — ARIMA with a seasonal component (trading-week s=5)<br>'
 '• <b>Holt-Winters (ETS)</b> — exponential smoothing with damped trend<br>'
 '• <b>GARCH</b> — AR(1) + GARCH(1,1): conditional-volatility model<br>'
 '• <b>SARIMAX</b> — ARIMA + exogenous log(Volume) & Range<br>'
 '• <b>Gradient Boosting</b> — nonlinear ML (decision trees)<br>'
 '• <b>FinScope Ensemble</b> — inverse-MAPE weighted combination'}<br><br>

<b style="color:{_T['text_primary']}">{'Chức năng Khoảng tin cậy:' if not _is_en else 'Confidence-Interval feature:'}</b><br>
{'• Bảng so sánh dự báo phiên tới + KTC 80%/95% cho mọi mô hình<br>'
 '• Fan chart từng mô hình: dải tin cậy 80%/95% quanh dự báo<br>'
 '• Biểu đồ biến động có điều kiện (GARCH) + xếp hạng độ chính xác MAPE'
 if not _is_en else
 '• Comparison table of next-session forecast + 80%/95% CI for all models<br>'
 '• Per-model fan charts: 80%/95% bands around the forecast<br>'
 '• Conditional volatility chart (GARCH) + MAPE accuracy ranking'}
""")

        _guide_card(_IC_SIG, 'Chiến lược Giao dịch' if not _is_en else 'Trading Strategy',
                    '#0891B2', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Kết hợp <b>phân tích kỹ thuật</b> (Ichimoku, RSI, MACD, Bollinger, MA cross) với <b>đồng thuận dự báo</b> của các mô hình → tín hiệu MUA/BÁN/GIỮ kèm điểm vào lệnh.'
 if not _is_en else 'Combine <b>technical analysis</b> (Ichimoku, RSI, MACD, Bollinger, MA cross) with the <b>forecast consensus</b> of the models → a BUY/SELL/HOLD signal with an entry plan.'}<br><br>

<b style="color:{_T['text_primary']}">{'Nội dung:' if not _is_en else 'Content:'}</b><br>
{'• Bảng điểm 9 phiếu: MA50 · MA5/20 · MACD · RSI · Bollinger · Ichimoku · <b>mẫu hình nến</b> · đồng thuận dự báo · <b>tâm lý tin tức</b><br>'
 '• Khuyến nghị MUA/BÁN/GIỮ với điểm <b>vào lệnh</b>, <b>cắt lỗ (SL)</b>, <b>chốt lời (TP)</b> theo ATR<br>'
 '• <b>Phân tích Kỹ thuật nâng cao</b>: Hỗ trợ/Kháng cự · Fibonacci · Kênh xu hướng · Sóng (ZigZag) · Pivot Points · mẫu hình nến<br>'
 '• <b>Backtest</b> chiến lược (đã trừ phí giao dịch ~0,3% khứ hồi): số lệnh, tỉ lệ thắng, Sharpe, lợi nhuận tích lũy'
 if not _is_en else
 '• 9-vote score: MA50 · MA5/20 · MACD · RSI · Bollinger · Ichimoku · <b>candlestick patterns</b> · forecast consensus · <b>news sentiment</b><br>'
 '• BUY/SELL/HOLD recommendation with <b>entry</b>, <b>stop-loss (SL)</b>, <b>take-profit (TP)</b> via ATR<br>'
 '• <b>Advanced technical analysis</b>: Support/Resistance · Fibonacci · Trend channel · Waves (ZigZag) · Pivot Points · candlestick patterns<br>'
 '• Strategy <b>backtest</b> (net of ~0.3% round-trip fees): trades, win rate, Sharpe, cumulative return'}
""")

        _guide_card(_IC_SIG, 'Tín hiệu & Cảnh báo' if not _is_en else 'Signals & Alerts',
                    '#EF4444', f"""
<b style="color:{_T['text_primary']}">{'Mục đích:' if not _is_en else 'Purpose:'}</b>
{'Phân tích xu hướng theo hệ thống Ichimoku Kinko Hyo (Hosoda 1969).'
 if not _is_en else 'Trend analysis using the Ichimoku Kinko Hyo system (Hosoda 1969).'}<br><br>

<b style="color:{_T['text_primary']}">{'Hệ thống 4 tầng + điểm đồng thuận (±5):' if not _is_en else '4-tier system + consensus score (±5):'}</b><br>
{'• <b>Tầng 1 — Xu hướng chính:</b> giá vs. Kumo (mây) → ±1 điểm<br>'
 '• <b>Tầng 2 — TK Cross:</b> Tenkan/Kijun cắt nhau + vị trí vs. Kumo → ±2/±1/0<br>'
 '• <b>Tầng 3 — Chikou Span:</b> đường trễ 26 phiên vs. giá quá khứ → ±1 điểm<br>'
 '• <b>Tầng 4 — Kumo tương lai:</b> hình dạng mây dự báo 26 phiên tới → ±1 điểm<br><br>'
 '• Score <b>+4/+5</b>: <span style="color:#4ADE80">Tăng mạnh</span> · '
 '<b>+2/+3</b>: <span style="color:#86EFAC">Tăng nhẹ</span> · '
 '<b>0/±1</b>: <span style="color:#94A3B8">Trung tính</span><br>'
 '• Score <b>−2/−3</b>: <span style="color:#FCA5A5">Giảm nhẹ</span> · '
 '<b>−4/−5</b>: <span style="color:#F87171">Giảm mạnh</span><br>'
 '• <b>Lưu ý:</b> Chỉ mang tính tham khảo học thuật, không phải lời khuyên đầu tư'
 if not _is_en else
 '• <b>Tier 1 — Primary trend:</b> price vs. Kumo (cloud) → ±1 point<br>'
 '• <b>Tier 2 — TK Cross:</b> Tenkan/Kijun crossover + position vs. Kumo → ±2/±1/0<br>'
 '• <b>Tier 3 — Chikou Span:</b> lagging line (−26) vs. past price → ±1 point<br>'
 '• <b>Tier 4 — Future Kumo:</b> projected cloud shape 26 sessions ahead → ±1 point<br><br>'
 '• Score <b>+4/+5</b>: <span style="color:#4ADE80">Strong bull</span> · '
 '<b>+2/+3</b>: <span style="color:#86EFAC">Mild bull</span> · '
 '<b>0/±1</b>: <span style="color:#94A3B8">Neutral</span><br>'
 '• Score <b>−2/−3</b>: <span style="color:#FCA5A5">Mild bear</span> · '
 '<b>−4/−5</b>: <span style="color:#F87171">Strong bear</span><br>'
 '• <b>Note:</b> For academic reference only, not investment advice'}
""")

        _guide_card(_IC_SET, 'Thanh điều khiển (Topbar)' if not _is_en else 'Topbar Controls',
                    '#64748B', f"""
<b style="color:{_T['text_primary']}">{'Điều hướng trang:' if not _is_en else 'Page navigation:'}</b><br>
{'• <b>Menu 12 trang</b> trên thanh ngang đầu trang: Dashboard · <b>Tổng quan TT</b> · <b>Phân tích Cơ bản</b> · Phân tích Chi tiết · Mô hình Nâng cao · Chiến lược · Tin tức · Tín hiệu · Lịch sử · Danh mục · <b>Giao dịch Demo</b> · Hướng dẫn<br>'
 '• Bấm vào tên trang để chuyển qua lại — trạng thái mô hình được giữ nguyên (không train lại)'
 if not _is_en else
 '• <b>12-page menu</b> on the top bar: Dashboard · <b>Market</b> · <b>Fundamental</b> · Analysis · Advanced Models · Strategy · News · Signals · History · Portfolio · <b>Paper Trading</b> · Guide<br>'
 '• Click a page name to switch — trained model state persists (no retraining)'}<br><br>

<b style="color:{_T['text_primary']}">{'Chọn mã (2 bước):' if not _is_en else 'Ticker selection (2-step):'}</b><br>
{'• <b>Bước 1 — Ngành:</b> chọn ngành (Ngân hàng / Bất động sản / Chứng khoán / ...) — số mã hiện sau tên ngành<br>'
 '• <b>Bước 2 — Mã:</b> chọn mã trong ngành đã chọn. Chọn "Tất cả ngành" để xem toàn bộ 53 mã'
 if not _is_en else
 '• <b>Step 1 — Sector:</b> pick sector (Banking / Real Estate / Securities / ...) — number of tickers shown after sector name<br>'
 '• <b>Step 2 — Ticker:</b> pick ticker within selected sector. Choose "All sectors" to see all 53'}<br><br>

<b style="color:{_T['text_primary']}">{'Tham số mô hình:' if not _is_en else 'Model parameters:'}</b><br>
{'• <b>Mã giao dịch:</b> chọn trong <b>53 mã HOSE</b> (VN30 + nhiều mã thanh khoản cao: FPT, HPG, VCB, PNJ, GMD, DGC, ...) — gom theo 31 ngành<br>'
 '• <b>Tỉ lệ Huấn luyện:</b> 70–90% — tỉ lệ dữ liệu dùng để train mô hình (còn lại để test)<br>'
 '• <b>Độ trễ (p):</b> số phiên quá khứ làm input cho AR/MLR; với ARIMA dùng làm trần bậc AR khi tự chọn order. Mặc định p=1; tăng 3–5 để thử. Quy tắc an toàn: p ≤ √n<br>'
 '• <b>Khoảng thời gian:</b> lọc dữ liệu lịch sử theo ngày <b>Từ</b> / <b>Đến</b> (định dạng YYYY/MM/DD)'
 if not _is_en else
 '• <b>Ticker:</b> pick from <b>53 HOSE symbols</b> (VN30 + many liquid names: FPT, HPG, VCB, PNJ, GMD, DGC, ...) — grouped by 31 sectors<br>'
 '• <b>Train Ratio:</b> 70–90% — proportion of data used for training (remainder for testing)<br>'
 '• <b>Lag Order (p):</b> past sessions as input for AR/MLR; for ARIMA it caps the AR order during auto-selection. Default p=1; try 3–5. Safety: p ≤ √n<br>'
 '• <b>Date Range:</b> filter historical data by <b>From</b> / <b>To</b> (format YYYY/MM/DD)'}<br><br>

<b style="color:{_T['text_primary']}">{'Hành động & cài đặt:' if not _is_en else 'Actions & settings:'}</b><br>
{'• <b>Cập nhật dữ liệu</b> (nút trên cùng): xoá cache + tải lại dữ liệu mới nhất từ nguồn<br>'
 '• <b>Dark / Light</b>: chuyển đổi chế độ giao diện sáng / tối (mọi biểu đồ + card đổi theo)<br>'
 '• <b>VI / EN</b>: chuyển đổi ngôn ngữ Tiếng Việt / English (toàn bộ giao diện đổi theo)'
 if not _is_en else
 '• <b>Refresh data</b> (top button): clears cache + reloads latest data from source<br>'
 '• <b>Dark / Light</b>: toggle dark / light interface mode (all charts + cards follow)<br>'
 '• <b>VI / EN</b>: switch Vietnamese / English (entire interface follows)'}
""")

    st.markdown(f"""
<div style="background:{_T['bg_elevated']};border:1px solid {_T['border']};
            border-radius:12px;padding:20px 24px;margin-top:4px">
  <div style="font-size:14px;font-weight:700;color:{_T['text_primary']};margin-bottom:14px;
              display:flex;align-items:center;gap:8px">
    {_ic('info-circle-fill', _T['accent'], 17)}
    {'Chỉ số đánh giá mô hình' if not _is_en else 'Model Evaluation Metrics'}
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
    {''.join([
      f'<div style="background:{_T["bg_card"]};border-radius:8px;padding:12px 14px;'
      f'border:1px solid {_T["border"]}">'
      f'<div style="font-size:13px;font-weight:800;color:{c};margin-bottom:4px">{nm}</div>'
      f'<div style="font-size:11.5px;color:{_T["text_primary"]};line-height:1.5">{desc}</div>'
      f'</div>'
      for nm, c, desc in [
          ('MAPE', '#3B82F6',
           ('Sai số phần trăm tuyệt đối trung bình.<br><b>Mục tiêu:</b> &lt; 2%'
            if not _is_en else
            'Mean Absolute Percentage Error.<br><b>Target:</b> &lt; 2%')),
          ('RMSE', '#8B5CF6',
           ('Sai số bình phương trung bình gốc.<br><b>Đơn vị:</b> nghìn VNĐ'
            if not _is_en else
            'Root Mean Square Error.<br><b>Unit:</b> thousand VND')),
          ('MAE', '#F59E0B',
           ('Sai số tuyệt đối trung bình.<br><b>Đơn vị:</b> nghìn VNĐ'
            if not _is_en else
            'Mean Absolute Error.<br><b>Unit:</b> thousand VND')),
          ('R²adj', '#10B981',
           ('Hệ số xác định hiệu chỉnh.<br><b>Tốt nhất:</b> gần 1.0'
            if not _is_en else
            'Adjusted coefficient of determination.<br><b>Best:</b> close to 1.0')),
      ]
    ])}
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div style="text-align:center;margin-top:20px;padding:14px;
            color:{_T['text_muted']};font-size:11px">
  {'FinScope · Hệ thống phân tích & dự báo chứng khoán đa mô hình · Không phải lời khuyên đầu tư'
   if not _is_en else
   'FinScope · Multi-model stock analysis & forecasting system · Not investment advice'}
</div>
""", unsafe_allow_html=True)

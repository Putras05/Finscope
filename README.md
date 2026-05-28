# FinScope — Phân tích & Dự báo Chứng khoán Đa mô hình

> Nền tảng phân tích kỹ thuật + dự báo + đọc hiểu tin tức cho HOSE.

Ứng dụng Streamlit phân tích & dự báo giá cổ phiếu **HOSE** bằng **8 mô hình
thống kê/học máy + mô hình Kết hợp**, kèm **khoảng tin cậy**, **kiểm định
thống kê**, bộ **phân tích kỹ thuật** đầy đủ và **đọc hiểu tin tức bằng AI**.

**Nhóm tác giả:** Nguyễn Thành Danh (C2300014) · Trần Huỳnh Nhã Trúc

## Tính năng (12 trang)

- **Dashboard** — giá, KPI, banner Dự báo Kết hợp, TOP-3 mô hình tốt nhất (theo MAPE), thẻ tâm lý tin tức, dự báo nhiều phiên + **kiểm định Diebold–Mariano**.
- **Tổng quan Thị trường** — snapshot 53 mã HOSE: heatmap, sector overview 31 ngành, top movers, vốn hóa, GTGD (cache 5'). 
- **Phân tích Cơ bản** — báo cáo tài chính 4 quý + tỷ số TỰ TÍNH (P/E, P/B, ROE, ROA, EPS, biên LN, D/E) cho cả DN thường lẫn ngân hàng.
- **Phân tích Chi tiết** — 9 tab: 8 mô hình + FinScope Ensemble, mỗi tab có phương trình/tham số, chẩn đoán (ACF/PACF, phần dư, Q-Q), fan chart khoảng tin cậy.
- **Mô hình Nâng cao** — SARIMA · Holt-Winters/ETS · GARCH · SARIMAX · Gradient Boosting · Ensemble + khoảng tin cậy 80%/95%.
- **Chiến lược Giao dịch** — 12 phiếu (MA50/MA5-20/MACD/RSI/Bollinger/Stochastic/ADX/OBV/Ichimoku/mẫu nến/dự báo/tin tức) → MUA/BÁN/GIỮ + SL/TP (ATR) + backtest **có phí giao dịch**; **Phân tích kỹ thuật**: Hỗ trợ/Kháng cự · Fibonacci · Kênh xu hướng · Sóng (ZigZag) · Pivot · mẫu hình nến · VWAP · Parabolic SAR.
- **Tin tức & Đọc hiểu** — RSS (CafeF/VnExpress/Vietstock) + **AI học sâu PhoBERT** chạy ngầm (fallback từ điển) + nhận diện chủ đề + gom nhóm.
- **Tín hiệu & Cảnh báo** — alerts dashboard 11 chỉ báo + biểu đồ kỹ thuật tổng hợp + 4 tab nhóm (Xu hướng/Động lượng/Biến động/Khối lượng) + Ichimoku chuyên sâu.
- **Lịch sử & Dữ liệu** · **Danh mục Đầu tư** (Ensemble 4 mô hình × n mã) · **Giao dịch Demo** (paper trading P&L) · **Hướng dẫn**.
- Song ngữ VI/EN · Sáng/Tối · **53 mã HOSE** (VN30 + nhiều mã thanh khoản cao) · **chọn 2 bước: ngành → mã**.

## Mô hình

| Nhóm | Mô hình |
|------|---------|
| Tuyến tính | AR(p), MLR(p) |
| Box-Jenkins | ARIMA(p,d,q), SARIMA, SARIMAX |
| San mũ | Holt-Winters / ETS |
| Biến động | GARCH(1,1) |
| Học máy | Gradient Boosting |
| Kết hợp | FinScope Ensemble (trọng số ∝ 1/MAPE) |

Bậc ARIMA tự chọn theo AIC (d theo ADF). Khoảng dự báo giải tích cho mô hình
thống kê. So sánh mô hình bằng **kiểm định Diebold–Mariano** (kèm benchmark
Random Walk). Học sâu (PhoBERT) dùng cho **đọc hiểu tin tức**, không dự báo giá.

## Chạy cục bộ

```bash
pip install -r requirements.txt
streamlit run app.py
```

Yêu cầu Python 3.11. Dữ liệu lấy realtime từ **vnstock** (HOSE). Lưu ý: nguồn
miễn phí giới hạn ~20 request/phút — đổi mã quá nhanh có thể bị tạm giới hạn
(app đã xử lý: hiện thông báo & chờ ~60s).

## Deploy lên Streamlit Community Cloud

Xem [DEPLOY.md](DEPLOY.md) để biết các bước chi tiết.

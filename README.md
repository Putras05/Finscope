# Dự Báo Giá Cổ Phiếu — Cuộc thi Ứng dụng AI 2026

Ứng dụng Streamlit phân tích & dự báo giá cổ phiếu **VN30 (HOSE)** bằng nhiều
mô hình thống kê + công cụ kỹ thuật, kèm **khoảng tin cậy** và **chiến lược giao dịch**.

**Nhóm tác giả:** Nguyễn Thành Danh (C2300014) · Trần Huỳnh Nhã Trúc

## Tính năng

- **Dashboard** — giá, KPI, dự báo phiên kế tiếp của **7 mô hình** + bảng xếp hạng độ chính xác.
- **Phân tích Chi tiết** — AR, MLR, ARIMA: phương trình/hệ số, chẩn đoán (ACF/PACF, phần dư, Q-Q), fan chart khoảng tin cậy.
- **Mô hình Nâng cao** — SARIMA · Holt-Winters/ETS · GARCH · SARIMAX + khoảng tin cậy 80%/95%.
- **Chiến lược Giao dịch** — kết hợp Ichimoku, RSI, MACD, Bollinger, MA cross + đồng thuận dự báo → MUA/BÁN/GIỮ + điểm vào lệnh, SL/TP (ATR) + backtest.
- **Tín hiệu Ichimoku** · **Lịch sử & Dữ liệu** · **Danh mục Đầu tư** (so sánh nhiều mã) · **Hướng dẫn**.
- Song ngữ VI/EN · Sáng/Tối · ~29 mã VN30 (chọn mã tuỳ ý).

## Mô hình

| Nhóm | Mô hình |
|------|---------|
| Tuyến tính | AR(p), MLR(p) |
| Box-Jenkins | ARIMA(p,d,q), SARIMA, SARIMAX |
| San mũ | Holt-Winters / ETS |
| Biến động | GARCH(1,1) |

Bậc ARIMA tự chọn theo AIC (d theo ADF). Khoảng dự báo giải tích cho mô hình thống kê.

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

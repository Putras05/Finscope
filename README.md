# FinScope — Phân tích & Dự báo Chứng khoán Đa mô hình

> Nền tảng phân tích kỹ thuật + dự báo + đọc hiểu tin tức + tối ưu danh mục
> + giao dịch ảo cho HOSE.

Ứng dụng Streamlit phân tích & dự báo giá cổ phiếu **HOSE** bằng **8 mô hình
thống kê / học máy + Ensemble**, kèm **khoảng tin cậy**, **kiểm định
Diebold–Mariano**, bộ **phân tích kỹ thuật**, **engine tín hiệu 8 trụ**,
**lý thuyết danh mục Markowitz**, **Monte Carlo**, **CAPM**, **PCA**,
**Cointegration**, và **đọc hiểu tin tức bằng AI**.

**Nhóm tác giả:** Nguyễn Thành Danh (C2300014) · Trần Huỳnh Nhã Trúc
(C2300189) · Khoa Toán – Thống kê, Trường Đại học Tôn Đức Thắng.

## Tính năng (14 trang chính)

### 📊 Phân tích & Dự báo
- **Dashboard Tổng quan** — giá, KPI, banner Dự báo Ensemble, TOP-3 mô
  hình tốt nhất theo MAPE, thẻ tâm lý tin tức, dự báo nhiều phiên +
  **kiểm định Diebold–Mariano** (kèm Random Walk benchmark).
- **Tổng quan Thị trường** — snapshot 53 mã HOSE: heatmap, sector
  overview 31 ngành, top movers, vốn hóa, GTGD (cache 5').
- **Phân tích Cơ bản** — báo cáo tài chính 4 quý + 7 tỷ số tự tính
  (P/E, P/B, ROE, ROA, EPS, biên LN, D/E) cho cả DN thường lẫn ngân hàng.
- **Phân tích Chi tiết** — 9 tab: 8 mô hình + Ensemble, mỗi tab có
  phương trình, tham số, chẩn đoán (ACF/PACF, phần dư, Q-Q), fan chart
  khoảng tin cậy 80%/95%.
- **Mô hình Nâng cao** — SARIMA · Holt-Winters/ETS · GARCH(1,1) · SARIMAX
  · Gradient Boosting · Ensemble với khoảng tin cậy.

### 💹 Chiến lược & Tín hiệu
- **Chiến lược Giao dịch** — 12 phiếu chỉ báo (MA/MACD/RSI/Bollinger/
  Stochastic/ADX/OBV/Ichimoku/mẫu nến/dự báo/tin tức) → MUA/BÁN/GIỮ +
  điểm vào, SL, TP theo ATR + backtest có phí giao dịch.
- **Tín hiệu & Cảnh báo** — alerts dashboard 11 chỉ báo + biểu đồ kỹ
  thuật tổng hợp + Ichimoku 4 tầng chi tiết + **cảnh báo giá cá nhân
  (price alerts)** per-user.
- **Tin tức Thị trường** — RSS (CafeF/VnExpress/Vietstock) + **AI học
  sâu PhoBERT** chạy ngầm (fallback từ điển) + nhận diện chủ đề.

### 💼 Danh mục & Giao dịch ảo
- **Danh mục Đầu tư** — so sánh 2-6 mã + Ensemble dự báo +
  **Markowitz Mean-Variance (1952)** với biên hiệu quả + 3 portfolio
  (Equal/Min-Var/Max Sharpe) + **CAPM Beta/Alpha vs VN-Index** với SML
  chart + **PCA** scree + biplot + **Engle-Granger Cointegration**
  test pairs trading.
- **Giao dịch Demo (Paper Trading)** — 7 tab: Đề xuất chuyên gia
  (signal engine 8 trụ → conviction [-100,+100] + 3 phương án giao
  dịch), Đặt lệnh, Vị thế, Lịch sử, Nhật ký, **Backtest engine**
  walk-forward với Sharpe (rf), Sortino, Buy & Hold benchmark, Thống
  kê + 14 huy hiệu thành tựu + **Monte Carlo** projection (bootstrap
  + GBM với Itô correction) + VaR/CVaR 95%.

### 📐 Toán học & Tài khoản
- **Cơ sở Toán học** — trang LaTeX showcase ~25 công thức (AR/MLR/
  ARIMA/SARIMA/ETS/GARCH/SARIMAX/GBR + Markowitz + CAPM + PCA +
  Sharpe/MDD/VaR/CVaR/Kelly + GBM + Diebold-Mariano +
  Engle-Granger) kèm trích dẫn APA 7th.
- **Hồ sơ cá nhân** — đăng nhập / đăng ký (PBKDF2 hash) + đổi mật
  khẩu + xuất dữ liệu ZIP + xoá tài khoản.
- **Hướng dẫn Sử dụng** — quy ước tham số, ý nghĩa từng chỉ số, FAQ.

### 🛠 Hệ thống
- **Song ngữ VI/EN** · **Sáng/Tối** · 53 mã HOSE (VN30 + thanh khoản cao)
- **Chọn 2 bước**: ngành → mã (31 ngành)
- **Auth PBKDF2** 200k vòng · per-user paper book / watchlist / alerts
  / journal · 14 trang chức năng.

## Bộ công cụ Toán-Thống kê

| Phương pháp | File | Công thức ngắn | Trích dẫn |
|---|---|---|---|
| AR(p) | models/ar.py | y_t = c + Σφᵢy_{t-i} + ε | Box & Jenkins 1970 |
| MLR(k) | models/mlr.py | y = Xβ + ε; β̂ = (X'X)⁻¹X'y | Wooldridge 2019 |
| ARIMA(p,d,q) | models/arima.py | ∇^d y_t = c + ARMA | Box-Jenkins 1976 |
| SARIMA | models/advanced.py | ARIMA × (P,D,Q)_s | Box-Jenkins-Reinsel 1994 |
| Holt-Winters ETS | models/advanced.py | level + trend + seasonal | Holt 1957, Winters 1960 |
| GARCH(1,1) | models/advanced.py | σ²_t = ω + αε² + βσ² | Bollerslev 1986 |
| SARIMAX | models/advanced.py | SARIMA + β'x_t | Durbin-Koopman 2012 |
| Gradient Boosting | models/ml.py | F_M = Σν·h_m | Friedman 2001 |
| FinScope Ensemble | models/ensemble.py | w_i ∝ 1/(MAPE_i + 0.1) | Stock-Watson 2004 |
| **Diebold-Mariano + HLN** | data/metrics.py | DM = d̄/√(V̂/n) | DM 1995, HLN 1997 |
| **Ichimoku Kinko Hyo** | data/ichimoku.py | 5 đường + Kumo 9-26-52 | Hosoda 1969 |
| **Markowitz Mean-Variance** | services/optimizer.py | min w'Σw s.t. w'μ=R, w≥0 | Markowitz 1952 |
| **Tangency / Max Sharpe** | services/optimizer.py | w* ∝ Σ⁻¹(μ-rf) | Sharpe 1966 |
| **Efficient Frontier (PGD)** | services/optimizer.py | projected gradient + simplex | Wang & Carreira-Perpiñán 2013 |
| **CAPM Beta/Alpha** | services/capm.py | E[R]−rf = β(E[Rm]−rf) | Sharpe 1964, Lintner 1965 |
| **PCA** | services/pca.py | C = VΛV' eigendecomp | Pearson 1901, Hotelling 1933 |
| **Engle-Granger Cointegration** | services/cointegration.py | OLS + ADF on residual | Engle-Granger 1987 (Nobel 2003) |
| **Sharpe Ratio** | services/backtest.py | (E[R]−rf)/σ × √252 | Sharpe 1966 |
| **Sortino Ratio** | services/backtest.py | (E[R]−rf)/σ_down × √252 | Sortino & Price 1994 |
| **Maximum Drawdown** | data/paper.py | min(E_t / max_{s≤t} E_s − 1) | Magdon-Ismail 2004 |
| **VaR / CVaR 95%** | services/monte_carlo.py | F⁻¹(α); E[R\|R≤F⁻¹] | Jorion 2007 |
| **Kelly Criterion (full + g\*)** | services/risk.py | f* = W − (1−W)/b | Kelly 1956 |
| **ATR** | services/risk.py | RMA(TR, 14) Wilder | Wilder 1978 |
| **Monte Carlo + GBM Itô** | services/monte_carlo.py | log r ~ N((μ−σ²/2), σ²) | Boyle 1977, Itô 1944 |

## Kiến trúc

```
app.py                       — entry point
app_pages/  (14 trang)       — dashboard, market, fundamental, analysis,
                               advanced, strategy, news, signals, history,
                               portfolio, paper, math, profile, guide
data/                        — fetcher, market, fundamental, news, news_ai,
                               ichimoku, technicals (cache rộng), metrics, paper
models/  (8 mô hình)         — ar, mlr, arima, advanced (SARIMA/ETS/GARCH/
                               SARIMAX), ml (GBR), ensemble
charts/                      — base, comparison, technicals, ichimoku,
                               arima_diag, portfolio, price (Plotly)
services/  (13 dịch vụ)      — risk, signal_engine (8 trụ), trade_planner
                               (3 phương án), watchlist, alerts, journal,
                               achievements, backtest, optimizer (Markowitz),
                               monte_carlo, capm, pca, cointegration
auth/                        — passwords (PBKDF2), store, session
ui/                          — topbar, css, js, logo, components, icons (SVG)
core/                        — config, constants, themes, i18n, preload,
                               references (38+ APA), validate
```

## Chạy cục bộ

```bash
pip install -r requirements.txt
streamlit run app.py
```

Yêu cầu **Python 3.11**. Dữ liệu lấy realtime từ **vnstock** (HOSE). Lưu ý
nguồn miễn phí giới hạn ~20 request/phút — đổi mã quá nhanh có thể bị tạm
giới hạn (app đã xử lý: hiện thông báo & chờ ~60s).

Lần đầu mở: splash 25-30s + warm thread chạy nền pre-cache 8 mô hình cho mã
mặc định (FPT, MWG, MSN) + VN-Index + Ichimoku + technicals + signal
engine + market snapshot. Sau đó **chuyển tab <1 giây**.

## Deploy

Xem [DEPLOY.md](DEPLOY.md) để biết các bước deploy lên Streamlit Community
Cloud.

## Tài liệu

- [CHANGELOG.md](CHANGELOG.md) — lịch sử thay đổi từ v40 đến v53 (kèm
  benchmarks, audit findings, fixes).
- `Mo_ta_san_pham.pdf` — mô tả sản phẩm theo quy chế Hội thi Toán học
  sinh viên TDTU 2025–2026.
- `Nhat_ky_su_dung_AI.pdf` — phụ lục nhật ký sử dụng AI hỗ trợ lập trình.

## Tham khảo

App cite đầy đủ trong code docstrings và trang **Cơ sở Toán học**.
Khoảng 38 references APA 7th tập trung trong [core/references.py](core/references.py).
Một số highlight:

- Markowitz, H. (1952). Portfolio selection. *J. of Finance, 7*(1).
- Sharpe, W. F. (1964). Capital asset prices. *J. of Finance, 19*(3).
- Engle, R. F., & Granger, C. W. J. (1987). Co-integration. *Econometrica,
  55*(2). [**Nobel 2003**]
- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy.
  *J. of Business & Economic Statistics, 13*(3).
- Hosoda, G. (1969). *Ichimoku Kinko Hyo*. Tokyo.
- Box, G. E. P., & Jenkins, G. M. (1976). *Time Series Analysis*. Holden-Day.
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles
  and Practice* (3rd ed.). OTexts.

## Bản quyền & Tuyên bố

**Mục đích học tập** — sản phẩm hỗ trợ phân tích & dự báo phục vụ học
thuật, **KHÔNG phải khuyến nghị đầu tư**. Người dùng tự chịu trách nhiệm
với mọi quyết định giao dịch.

"""Trang "Cơ sở Toán học" — showcase tất cả công thức + tham khảo APA.

Mục tiêu: judges Khoa Toán-Thống kê có thể xem trực tiếp công thức + nguồn
mà KHÔNG cần đọc code. Dùng st.latex() cho công thức, citation APA cuối
mỗi block. KHÔNG có compute — chỉ render.
"""
import streamlit as st


def _block(_T, title_vi: str, title_en: str, latex: str | list,
            desc_vi: str = '', desc_en: str = '',
            references: list[str] = None, color: str = '#1E40AF',
            is_en: bool = False) -> None:
    """Render 1 block công thức: header + LaTeX + description + references."""
    title = title_en if is_en else title_vi
    desc = desc_en if is_en else desc_vi
    st.markdown(
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-left:4px solid {color};border-radius:10px;'
        f'padding:14px 18px;margin-bottom:14px">'
        f'<div style="font-size:14px;font-weight:800;color:{color};'
        f'margin-bottom:8px">{title}</div>',
        unsafe_allow_html=True)
    if isinstance(latex, str):
        st.latex(latex)
    else:
        for eq in latex:
            st.latex(eq)
    if desc:
        # v58 — Tăng visibility: font 12.5 → 13.5, color text_secondary →
        # text_primary, thêm padding + bg subtle để tách khỏi References.
        st.markdown(
            f'<div style="font-size:13.5px;color:{_T["text_primary"]};'
            f'line-height:1.65;margin-top:6px;padding:8px 10px;'
            f'background:{_T["bg_elevated"]};border-radius:6px">{desc}</div>',
            unsafe_allow_html=True)
    if references:
        _ref_lbl = 'References:' if is_en else 'Tham khảo:'
        refs_html = '<br>'.join(
            f'<span style="color:{_T["text_muted"]}">{r}</span>'
            for r in references)
        st.markdown(
            f'<div style="font-size:11px;font-style:italic;'
            f'color:{_T["text_muted"]};line-height:1.6;margin-top:8px;'
            f'padding-top:6px;border-top:1px dashed {_T["border"]}">'
            f'<b>{_ref_lbl}</b><br>{refs_html}</div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render(ticker, train_ratio, date_from, date_to, df, r1, r2, r3, m1, m2, m3, _T,
           ar_order=1):
    is_en = st.session_state.get('lang', 'VI') == 'EN'

    st.markdown(
        f'<div class="page-header">'
        f'<h1>{"Cơ sở Toán học" if not is_en else "Mathematical Foundations"}</h1>'
        f'<p>{"Tổng hợp các công thức và mô hình thống kê - tài chính sử dụng trong FinScope, kèm trích dẫn APA gốc." if not is_en else "All mathematical formulas and statistical models used in FinScope, with original APA citations."}</p>'
        f'</div>', unsafe_allow_html=True)

    # ── Tabs cấp 1 — chia theo 5 nhóm chủ đề ─────────────────────────
    tab_fc, tab_tech, tab_port, tab_risk, tab_test = st.tabs([
        '  ' + ('Dự báo chuỗi thời gian' if not is_en else 'Forecasting') + '  ',
        '  ' + ('Phân tích Kỹ thuật' if not is_en else 'Technical Analysis') + '  ',
        '  ' + ('Lý thuyết Danh mục' if not is_en else 'Portfolio Theory') + '  ',
        '  ' + ('Quản trị Rủi ro' if not is_en else 'Risk Management') + '  ',
        '  ' + ('Kiểm định Thống kê' if not is_en else 'Statistical Tests') + '  ',
    ])

    # ═══════════════════════════════════════════════════════════════
    #  TAB 1 — DỰ BÁO CHUỖI THỜI GIAN
    # ═══════════════════════════════════════════════════════════════
    with tab_fc:
        st.markdown(
            f'<div class="info-box" style="margin-bottom:12px">'
            f'{"8 mô hình dự báo + 1 ensemble theo trọng số nghịch đảo MAPE." if not is_en else "8 forecasting models + 1 ensemble weighted by inverse MAPE."}'
            f'</div>', unsafe_allow_html=True)

        _block(_T, 'AR(p) — Autoregressive', 'AR(p) — Autoregressive',
                r'y_t = c + \sum_{i=1}^{p} \phi_i \cdot y_{t-i} + \varepsilon_t',
                'Hồi quy tuyến tính giá hiện tại lên p giá trị quá khứ. Tham số φᵢ ước lượng bằng OLS hoặc Yule-Walker.',
                'Linear regression of current price on p past values. Parameters φᵢ estimated by OLS or Yule-Walker.',
                ['Box, G. E. P., & Jenkins, G. M. (1970). Time Series Analysis: Forecasting and Control. Holden-Day.'],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'MLR — Multiple Linear Regression', 'MLR — Multiple Linear Regression',
                r'y_t = \beta_0 + \sum_{j=1}^{k} \beta_j \cdot x_{j,t} + \varepsilon_t',
                'Hồi quy bội với k = 3p biến độc lập (Close, Volume, Range lag 1..p). Ước lượng bằng OLS giảm thiểu RSS.',
                'Multiple regression with k = 3p predictors (Close, Volume, Range lag 1..p). OLS estimation minimizes RSS.',
                ['Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning (2nd ed.). Springer.'],
                color='#8B5CF6', is_en=is_en)

        _block(_T, 'ARIMA(p, d, q)', 'ARIMA(p, d, q)',
                [r'\nabla^d y_t = c + \sum_{i=1}^{p} \phi_i \nabla^d y_{t-i} + \sum_{j=1}^{q} \theta_j \varepsilon_{t-j} + \varepsilon_t',
                 r'\text{where } \nabla y_t = y_t - y_{t-1}'],
                'Tổng quát hơn AR — kết hợp sai phân bậc d (loại trend) + thành phần trung bình trượt MA(q). Order (p,d,q) chọn qua AIC/BIC.',
                'Generalization of AR — combining d-th order differencing (detrend) + moving average MA(q). Order (p,d,q) selected via AIC/BIC.',
                ['Box, G. E. P., & Jenkins, G. M. (1970). Time Series Analysis. Holden-Day.',
                 'Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.'],
                color='#0EA5E9', is_en=is_en)

        _block(_T, 'SARIMA — Seasonal ARIMA', 'SARIMA — Seasonal ARIMA',
                r'\text{ARIMA}(p, d, q) \times (P, D, Q)_s',
                'Mở rộng ARIMA với chu kỳ mùa vụ s (5 phiên/tuần với HOSE). Đảm bảo dữ liệu sau dual-differencing là dừng.',
                'Extension of ARIMA with seasonality period s (5 sessions/week for HOSE).',
                ['Box, Jenkins & Reinsel (1994). Time Series Analysis (3rd ed.). Prentice Hall.'],
                color='#10B981', is_en=is_en)

        _block(_T, 'Holt-Winters ETS (Exponential Smoothing)',
                'Holt-Winters ETS (Exponential Smoothing)',
                [r'\ell_t = \alpha \cdot y_t + (1 - \alpha)(\ell_{t-1} + b_{t-1})',
                 r'b_t = \beta(\ell_t - \ell_{t-1}) + (1 - \beta) b_{t-1}',
                 r's_t = \gamma(y_t - \ell_{t-1}) + (1 - \gamma) s_{t-m}'],
                'Phân rã chuỗi thành 3 thành phần: level ℓ, trend $b$, seasonal s. Ba tham số làm mượt α, β, γ ước lượng tối thiểu hoá SSE.',
                'Decomposition into level ℓ, trend $b$, seasonal s. Three smoothing parameters α, β, γ minimize SSE.',
                ['Holt, C. C. (1957). Forecasting trends and seasonals by exponentially weighted moving averages. ONR Memo 52.',
                 'Winters, P. R. (1960). Forecasting sales by exponentially weighted moving averages. Management Science, 6(3).'],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'GARCH(1, 1) — Generalized Autoregressive Conditional Heteroscedasticity',
                'GARCH(1, 1)',
                [r'r_t = \mu + \varepsilon_t, \quad \varepsilon_t = \sigma_t z_t, \quad z_t \sim N(0, 1)',
                 r'\sigma_t^2 = \omega + \alpha \varepsilon_{t-1}^2 + \beta \sigma_{t-1}^2'],
                'Mô hình hoá phương sai có điều kiện (volatility clustering). Điều kiện dừng: α + β < 1.',
                'Models conditional variance (volatility clustering). Stationarity: α + β < 1.',
                ['Engle, R. F. (1982). Autoregressive conditional heteroscedasticity. Econometrica, 50(4). [Nobel 2003]',
                 'Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. J. of Econometrics, 31(3).'],
                color='#EF4444', is_en=is_en)

        _block(_T, 'SARIMAX — SARIMA with eXogenous regressors',
                'SARIMAX',
                r'\text{SARIMA}(p, d, q)(P, D, Q)_s + \boldsymbol{\beta}^\top \mathbf{x}_t',
                'Bổ sung biến ngoại sinh xₜ (ví dụ: volume, sentiment) vào SARIMA — cho phép giải thích thêm bằng features.',
                'Adds exogenous regressors xₜ (e.g., volume, sentiment) to SARIMA.',
                ['Durbin, J., & Koopman, S. J. (2012). Time Series Analysis by State Space Methods (2nd ed.). Oxford UP.'],
                color='#A855F7', is_en=is_en)

        _block(_T, 'Gradient Boosting Regression (GBR)',
                'Gradient Boosting Regression (GBR)',
                [r'F_M(\mathbf{x}) = \sum_{m=1}^{M} \nu \cdot h_m(\mathbf{x})',
                 r'h_m = \arg\min_h \sum_i L(y_i, F_{m-1}(\mathbf{x}_i) + h(\mathbf{x}_i))'],
                'Ensemble cây quyết định, mỗi cây hₘ fit residual của ensemble trước. ν — learning rate.',
                'Ensemble of decision trees; each tree hₘ fits residual of previous ensemble. ν — learning rate.',
                ['Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics, 29(5).'],
                color='#EC4899', is_en=is_en)

        _block(_T, 'FinScope Ensemble (inverse-MAPE weighted)',
                'FinScope Ensemble (inverse-MAPE weighted)',
                r'\hat{y}_t^{\,\text{ens}} = \frac{\sum_{i} w_i \cdot \hat{y}_t^{(i)}}{\sum_i w_i}, \quad w_i = \frac{1}{\text{MAPE}_i + 0.1}',
                'Gộp K mô hình theo trọng số nghịch đảo MAPE — mô hình tốt hơn có trọng số cao hơn. Hằng số 0.1 tránh chia 0.',
                'Combines K models with weights inversely proportional to MAPE. Constant 0.1 avoids division by 0.',
                ['Stock, J. H., & Watson, M. W. (2004). Combination forecasts of output growth. J. of Forecasting, 23.'],
                color='#0F766E', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 2 — PHÂN TÍCH KỸ THUẬT
    # ═══════════════════════════════════════════════════════════════
    with tab_tech:
        _block(_T, 'Ichimoku Kinko Hyo — Một cái nhìn thoáng', 'Ichimoku Kinko Hyo',
                [r'\text{Tenkan} = \frac{\max H_9 + \min L_9}{2}',
                 r'\text{Kijun} = \frac{\max H_{26} + \min L_{26}}{2}',
                 r'\text{Senkou A} = \frac{\text{Tenkan} + \text{Kijun}}{2} \quad (\text{shifted } +26)',
                 r'\text{Senkou B} = \frac{\max H_{52} + \min L_{52}}{2} \quad (\text{shifted } +26)',
                 r'\text{Chikou} = C_t \quad (\text{shifted } -26)'],
                'Hệ thống đa thành phần Hosoda 1969 — 5 đường + mây Kumo. Chuẩn anti-leak: Chikou shifted backward chỉ dùng để VẼ, không làm feature tại t.',
                "Hosoda 1969 multi-component system — 5 lines + Kumo cloud. Anti-leak: Chikou shifted backward used only for plotting, not as feature at t.",
                ['Hosoda, G. (1969). Ichimoku Kinko Hyo (一目均衡表).',
                 'Gurrib, I. (2016). Optimization of the Ichimoku Kinko Hyo trading system. Int. J. of Monetary Economics & Finance.'],
                color='#0F766E', is_en=is_en)

        _block(_T, 'RSI(14) — Relative Strength Index', 'RSI(14)',
                [r'\text{RS} = \frac{\text{Avg Gain}_{14}}{\text{Avg Loss}_{14}}',
                 r'\text{RSI} = 100 - \frac{100}{1 + \text{RS}}'],
                'Oscillator [0,100] đo lực mua/bán 14 phiên. RSI > 70 quá mua, < 30 quá bán.',
                'Oscillator [0,100] measuring 14-bar buying/selling pressure. > 70 overbought, < 30 oversold.',
                ['Wilder, J. W. (1978). New Concepts in Technical Trading Systems. Trend Research.'],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'ATR(n) — Average True Range', 'ATR(n)',
                [r'\text{TR}_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)',
                 r'\text{ATR}_t = \frac{(n-1) \cdot \text{ATR}_{t-1} + \text{TR}_t}{n} \quad (\text{Wilder smoothing})'],
                'Đo biến động giá. Dùng để set stop-loss ATR × k (k=1.5–3 tùy phương án).',
                'Measures price volatility. Used for stop-loss ATR × k.',
                ['Wilder, J. W. (1978). New Concepts in Technical Trading Systems. Trend Research.'],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'MACD — Moving Average Convergence Divergence',
                'MACD',
                [r'\text{MACD} = \text{EMA}_{12}(C) - \text{EMA}_{26}(C)',
                 r'\text{Signal} = \text{EMA}_9(\text{MACD})',
                 r'\text{Histogram} = \text{MACD} - \text{Signal}'],
                'Cross MACD lên Signal = bull; cross xuống = bear. Histogram đo độ phân kỳ.',
                'MACD crossing above Signal = bull; below = bear.',
                ['Appel, G. (1979). The Moving Average Convergence-Divergence Trading Method.'],
                color='#8B5CF6', is_en=is_en)

        _block(_T, 'Stochastic Oscillator (%K, %D)',
                'Stochastic Oscillator (%K, %D)',
                [r'\%K = \frac{C_t - L_n}{H_n - L_n} \times 100',
                 r'\%D = \text{SMA}_3(\%K)'],
                '%K > 80 quá mua, < 20 quá bán. Cross %K lên %D = bull.',
                '%K > 80 overbought, < 20 oversold.',
                ['Lane, G. (1957). Stochastic Oscillator. Investment Educators.'],
                color='#10B981', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 3 — LÝ THUYẾT DANH MỤC
    # ═══════════════════════════════════════════════════════════════
    with tab_port:
        _block(_T, 'Markowitz Mean-Variance Optimization (1952)',
                'Markowitz Mean-Variance Optimization (1952)',
                [r'\min_{\mathbf{w}} \, \mathbf{w}^\top \boldsymbol{\Sigma} \mathbf{w}',
                 r'\text{s.t.} \quad \mathbf{w}^\top \boldsymbol{\mu} = R_{\text{target}}, \quad \mathbf{w}^\top \mathbf{1} = 1, \quad \mathbf{w} \geq \mathbf{0}'],
                'Bài toán QP tìm trọng số **w** tối thiểu hoá phương sai với lợi suất kỳ vọng cho trước. Long-only constraint **w** ≥ 0 giải bằng projected gradient descent + chiếu simplex.',
                'QP problem finding weights **w** minimizing variance given target return. Long-only via projected gradient + simplex projection.',
                ['Markowitz, H. (1952). Portfolio selection. The J. of Finance, 7(1).',
                 'Tobin, J. (1958). Liquidity preference as behavior towards risk. RES, 25.',
                 'Wang, W. & Carreira-Perpiñán, M. Á. (2013). Projection onto the probability simplex. arXiv:1309.1541.'],
                color='#1E40AF', is_en=is_en)

        _block(_T, 'Tangency Portfolio (Max Sharpe)', 'Tangency Portfolio (Max Sharpe)',
                r'\mathbf{w}^* \propto \boldsymbol{\Sigma}^{-1} (\boldsymbol{\mu} - r_f \cdot \mathbf{1})',
                'Closed-form tangency portfolio — điểm trên biên hiệu quả có Sharpe ratio cực đại, tiếp xúc đường thị trường vốn (CML).',
                'Closed-form tangency — point on efficient frontier with maximum Sharpe ratio, tangent to Capital Market Line.',
                ['Sharpe, W. F. (1966). Mutual fund performance. J. of Business, 39.',
                 'Merton, R. C. (1972). An analytic derivation of the efficient portfolio frontier. JFQA, 7(4).'],
                color='#A855F7', is_en=is_en)

        _block(_T, 'CAPM — Capital Asset Pricing Model', 'CAPM',
                [r'E[R_i] - r_f = \beta_i \cdot (E[R_m] - r_f)',
                 r'\beta_i = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}',
                 r'\alpha_i = E[R_i] - r_f - \beta_i (E[R_m] - r_f) \quad (\text{Jensen 1968})'],
                'Quan hệ tuyến tính giữa lợi suất kỳ vọng và rủi ro hệ thống β. α > 0 = vượt CAPM (outperform). FinScope hồi quy OLS trên VN-Index.',
                'Linear relationship between expected return and systematic risk β. α > 0 = outperform CAPM.',
                ['Sharpe, W. F. (1964). Capital asset prices. J. of Finance, 19(3).',
                 'Lintner, J. (1965). The valuation of risk assets. RES, 47(1).',
                 'Jensen, M. C. (1968). The performance of mutual funds 1945-1964. J. of Finance, 23(2).'],
                color='#0EA5E9', is_en=is_en)

        _block(_T, 'PCA — Principal Component Analysis', 'PCA',
                [r'\boldsymbol{\Sigma} = \mathbf{V} \boldsymbol{\Lambda} \mathbf{V}^\top \quad (\text{eigendecomposition})',
                 r'\text{Var explained}_i = \lambda_i \,/\, \sum_j \lambda_j'],
                'Phân rã ma trận hiệp phương sai (hoặc tương quan) thành các thành phần chính — PC1 thường gần "market factor", PC2/PC3 sector/size factor.',
                'Decomposition of covariance/correlation matrix into principal components — PC1 typically captures the market factor.',
                ['Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. Philosophical Magazine, 2(11).',
                 'Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. J. of Educational Psychology, 24.',
                 'Jolliffe, I. T. (2002). Principal Component Analysis (2nd ed.). Springer.'],
                color='#EC4899', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 4 — QUẢN TRỊ RỦI RO
    # ═══════════════════════════════════════════════════════════════
    with tab_risk:
        _block(_T, 'Sharpe Ratio (annualized)', 'Sharpe Ratio (annualized)',
                r'\text{Sharpe} = \frac{E[R_p] - r_f}{\sigma_p} \cdot \sqrt{252}',
                'Lợi suất vượt rf chia độ lệch chuẩn, hoá năm √252. > 1 tốt, > 2 rất tốt.',
                'Excess return over rf divided by std deviation, annualized.',
                ['Sharpe, W. F. (1966). Mutual fund performance. J. of Business, 39.',
                 'Sharpe, W. F. (1994). The Sharpe ratio. J. of Portfolio Management.'],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'Maximum Drawdown', 'Maximum Drawdown',
                r'\text{MDD} = \min_t \frac{E_t - \max_{s \leq t} E_s}{\max_{s \leq t} E_s}',
                'Rớt sâu nhất từ đỉnh equity đến đáy sau đó — đo "đau" tối đa user phải chịu.',
                'Largest peak-to-trough decline of equity.',
                ['Magdon-Ismail, M., & Atiya, A. F. (2004). Maximum drawdown. Risk Magazine, 17(10).'],
                color='#EF4444', is_en=is_en)

        _block(_T, 'VaR và CVaR (Expected Shortfall)', 'VaR and CVaR',
                [r'\text{VaR}_\alpha = -F_R^{-1}(\alpha) \quad (\alpha = 0.05 \text{ cho 95\% confidence})',
                 r'\text{CVaR}_\alpha = -E[R \mid R \leq F_R^{-1}(\alpha)]'],
                'VaR 95% = lỗ tối đa với 95% xác suất; CVaR = trung bình lỗ trong 5% trường hợp xấu nhất (chặt hơn VaR — coherent risk measure).',
                'VaR 95% = max loss at 95% confidence; CVaR = mean loss in worst 5% (stricter than VaR, coherent).',
                ['Jorion, P. (2007). Value at Risk: The New Benchmark (3rd ed.). McGraw-Hill.',
                 'Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. J. of Risk, 2(3).'],
                color='#DC2626', is_en=is_en)

        _block(_T, 'Kelly Criterion (1956)', 'Kelly Criterion (1956)',
                [r'f^* = W - \frac{1 - W}{b}, \quad b = \frac{\text{avg win}}{|\text{avg loss}|}',
                 r'g(f) = W \log(1 + fb) + (1 - W) \log(1 - f) \quad (\text{expected log-growth})'],
                'Tỷ lệ vốn tối ưu f* tối đa hoá kỳ vọng log-tăng trưởng. Thực tế dùng 1/2 hoặc 1/4 Kelly để giảm phương sai (Thorp 1969).',
                'Optimal bet size f* maximizing expected log-growth.',
                ['Kelly, J. L. (1956). A new interpretation of information rate. Bell System Technical Journal, 35(4).',
                 'Thorp, E. O. (1969). Optimal gambling systems for favorable games. Rev. of the Intl. Statistical Inst., 37(3).'],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'Monte Carlo + GBM (Itô correction)',
                'Monte Carlo + GBM (Itô correction)',
                [r'd \ln S_t = \left(\mu - \frac{\sigma^2}{2}\right) dt + \sigma \, dW_t',
                 r'\ln(S_t / S_{t-1}) \sim N\left((\mu - \sigma^2/2) \Delta t, \, \sigma^2 \Delta t\right)'],
                'Mô phỏng Geometric Brownian Motion. Itô correction $\\mu - \\sigma^2/2$ đảm bảo $E[S_T] = S_0 e^{\\mu T}$. Bootstrap = resample lịch sử thay vì giả định Gaussian.',
                'Geometric Brownian Motion simulation. Itô drift correction ensures $E[S_T] = S_0 e^{\\mu T}$.',
                ['Boyle, P. P. (1977). Options: A Monte Carlo approach. J. of Financial Economics, 4(3).',
                 'Itô, K. (1944). Stochastic integral. Proc. Imperial Academy, Tokyo, 20(8).'],
                color='#10B981', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 5 — KIỂM ĐỊNH THỐNG KÊ
    # ═══════════════════════════════════════════════════════════════
    with tab_test:
        _block(_T, 'Diebold-Mariano Test (1995) + HLN Correction',
                'Diebold-Mariano Test (1995) + HLN Correction',
                [r'd_t = L(e_{1,t}) - L(e_{2,t}), \quad \bar{d} = \frac{1}{n} \sum d_t',
                 r'\text{DM} = \frac{\bar{d}}{\sqrt{\hat{V}(\bar{d})/n}} \to N(0, 1)',
                 r'\text{DM}^* = \text{DM} \cdot \sqrt{\frac{n + 1 - 2h + h(h-1)/n}{n}} \quad (\text{Harvey-Leybourne-Newbold 1997})'],
                'So sánh độ chính xác 2 mô hình dự báo. H₀: 2 mô hình tương đương. HLN correction bù mẫu nhỏ.',
                'Compares forecast accuracy of 2 models. H₀: both equivalent. HLN correction for small samples.',
                ['Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. J. of Business & Economic Statistics, 13(3).',
                 'Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction MSE. Int. J. of Forecasting, 13.'],
                color='#1E40AF', is_en=is_en)

        _block(_T, 'Engle-Granger 2-step Cointegration',
                'Engle-Granger 2-step Cointegration',
                [r'\text{Step 1: } Y_t = \alpha + \beta X_t + u_t \quad (\text{OLS})',
                 r'\text{Step 2 (ADF on } u_t\text{): } \Delta u_t = \rho u_{t-1} + \sum_{i=1}^{p} \gamma_i \Delta u_{t-i} + \varepsilon_t',
                 r'H_0: \rho = 0 \quad (\text{unit root: NOT cointegrated})'],
                'Test 2 chuỗi giá I(1) có đồng tích hợp không — spread mean-reverting → pairs trading.',
                'Tests if two I(1) price series are cointegrated — spread mean-reverts → pairs trading.',
                ['Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction. Econometrica, 55(2). [Nobel 2003]',
                 'Dickey, D. A., & Fuller, W. A. (1979). Distribution of estimators for autoregressive time series with unit root. JASA, 74.',
                 'Vidyamurthy, G. (2004). Pairs Trading: Quantitative methods and analysis. Wiley.'],
                color='#A855F7', is_en=is_en)

        _block(_T, 'MAPE, RMSE, MAE, R²adj — Forecast Metrics',
                'MAPE, RMSE, MAE, R²adj — Forecast Metrics',
                [r'\text{MAPE} = \frac{100}{n} \sum_t \left|\frac{y_t - \hat{y}_t}{y_t}\right| \%',
                 r'\text{RMSE} = \sqrt{\frac{1}{n} \sum_t (y_t - \hat{y}_t)^2}',
                 r'R^2_{\text{adj}} = 1 - (1 - R^2) \cdot \frac{n - 1}{n - k - 1}'],
                'Đánh giá mô hình: MAPE thấp tốt (< 2% xuất sắc); R²adj phạt số tham số $k$ (tránh overfitting).',
                'Model evaluation: lower MAPE is better; R²adj penalizes parameter count $k$.',
                ['Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. Int. J. of Forecasting, 22(4).'],
                color='#10B981', is_en=is_en)

    st.markdown(
        f'<div style="text-align:center;margin-top:20px;padding:14px;'
        f'color:{_T["text_muted"]};font-size:11px">'
        f'{"FinScope · Tài liệu tham khảo APA · Không phải lời khuyên đầu tư" if not is_en else "FinScope · APA references · Not investment advice"}'
        f'</div>', unsafe_allow_html=True)

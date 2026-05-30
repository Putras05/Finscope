"""Trang "Cơ sở Toán học" — showcase tất cả công thức + tham khảo APA.

Mục tiêu: judges Khoa Toán-Thống kê có thể xem trực tiếp công thức + nguồn
mà KHÔNG cần đọc code. Dùng st.latex() cho công thức, citation APA cuối
mỗi block. KHÔNG có compute — chỉ render.
"""
import streamlit as st


def _block(_T, title_vi: str, title_en: str, latex: str | list,
            desc_vi: str = '', desc_en: str = '',
            components: list[tuple] = None,
            references: list[str] = None, color: str = '#1E40AF',
            is_en: bool = False) -> None:
    """Render 1 block công thức với đầy đủ thành phần:
      - HEADER chip (title + border-left màu)
      - FORMULA st.latex
      - DESCRIPTION ngắn (Ý tưởng)
      - COMPONENTS table (mỗi ký hiệu trong công thức → giải thích)
      - REFERENCES list (bullet)

    components: list of (latex_symbol_str, explanation_vi, explanation_en)
                hoặc (latex_symbol_str, explanation_vi) (EN = VI)
    """
    title = title_en if is_en else title_vi
    desc = desc_en if is_en else desc_vi

    # 1. HEADER — line-height 1.5 + padding rõ để text không clip
    st.markdown(
        f'<div style="font-size:16px;font-weight:800;color:{color};'
        f'margin:24px 0 10px;padding:8px 0 8px 14px;'
        f'border-left:4px solid {color};line-height:1.5">{title}</div>',
        unsafe_allow_html=True)

    # 2. FORMULA st.latex (rộng full-width với centering từ Streamlit native)
    if isinstance(latex, str):
        st.latex(latex)
    else:
        for eq in latex:
            st.latex(eq)

    # 3. CONTENT CARD: desc + components + references trong 1 div đóng đầy đủ
    parts = [
        f'<div style="background:{_T["bg_card"]};border:1px solid {_T["border"]};'
        f'border-radius:8px;padding:14px 18px;margin-bottom:24px;'
        f'overflow:hidden;word-wrap:break-word">'
    ]
    if desc:
        _lbl_idea = 'Ý tưởng:' if not is_en else 'Idea:'
        parts.append(
            f'<div style="font-size:14px;color:{_T["text_primary"]};'
            f'line-height:1.7;margin-bottom:12px">'
            f'<b style="color:{color}">{_lbl_idea}</b> {desc}</div>'
        )
    if components:
        _lbl_comp = 'Diễn giải từng thành phần:' if not is_en else 'Components:'
        # v58 — design: alternating row bg + symbol badge có nền nhẹ + centered
        comp_rows = []
        for i, c in enumerate(components):
            if len(c) >= 3:
                sym, exp_vi, exp_en = c[0], c[1], c[2]
            else:
                sym, exp_vi = c[0], c[1]
                exp_en = exp_vi
            exp = exp_en if is_en else exp_vi
            _row_bg = _T['bg_elevated'] if i % 2 == 0 else 'transparent'
            comp_rows.append(
                f'<tr style="background:{_row_bg}">'
                f'<td style="padding:8px 14px 8px 10px;vertical-align:top;'
                f'white-space:nowrap;font-family:Consolas,monospace;'
                f'color:{color};font-weight:700;font-size:13.5px;'
                f'border-right:1px solid {_T["border"]};'
                f'min-width:80px;text-align:center">{sym}</td>'
                f'<td style="padding:8px 12px;color:{_T["text_primary"]};'
                f'line-height:1.6;font-size:13.5px">{exp}</td></tr>'
            )
        parts.append(
            f'<div style="padding-top:12px;border-top:1px solid {_T["border"]};'
            f'margin-top:6px">'
            f'<div style="font-weight:700;color:{color};margin-bottom:8px;'
            f'font-size:13px;text-transform:uppercase;letter-spacing:.6px">'
            f'{_lbl_comp}</div>'
            f'<table style="width:100%;font-size:13px;border-collapse:collapse;'
            f'border:1px solid {_T["border"]};border-radius:6px;overflow:hidden">'
            f'{"".join(comp_rows)}</table></div>'
        )
    if references:
        _ref_lbl = 'Tài liệu tham khảo:' if not is_en else 'References:'
        refs_html = ''.join(
            f'<div style="margin:4px 0 4px 18px;text-indent:-18px">• {r}</div>'
            for r in references)
        parts.append(
            f'<div style="font-size:12.5px;'
            f'color:{_T["text_secondary"]};line-height:1.55;'
            f'padding-top:10px;border-top:1px solid {_T["border"]};'
            f'margin-top:12px">'
            f'<div style="font-weight:700;color:{color};margin-bottom:5px">'
            f'{_ref_lbl}</div>{refs_html}</div>'
        )
    parts.append('</div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


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
                'Giá trị hiện tại được giải thích bởi p giá trị quá khứ kề nhau.',
                'Current value explained by p preceding values.',
                components=[
                    ('y_t',         'Giá trị (giá đóng cửa hoặc log-return) tại phiên t',
                                     'Value (close price or log-return) at session t'),
                    ('c',           'Hằng số chặn (intercept)',
                                     'Intercept constant'),
                    ('φ_i',         'Hệ số tự hồi quy bậc i (i = 1, …, p)',
                                     'Autoregressive coefficient of order i'),
                    ('ε_t',         'Nhiễu trắng, kỳ vọng 0, phương sai σ²',
                                     'White noise, mean 0, variance σ²'),
                    ('p',           'Bậc tự hồi quy, chọn theo AIC hoặc PACF',
                                     'AR order, selected via AIC or PACF'),
                ],
                references=[
                    'Box, G. E. P., & Jenkins, G. M. (1970). Time Series Analysis: Forecasting and Control. Holden-Day.',
                    'Akaike, H. (1974). A new look at the statistical model identification. IEEE Trans. Automatic Control, 19(6).',
                ],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'MLR — Multiple Linear Regression', 'MLR — Multiple Linear Regression',
                r'y_t = \beta_0 + \sum_{j=1}^{k} \beta_j \cdot x_{j,t} + \varepsilon_t',
                'Hồi quy tuyến tính bội với k biến ngoại sinh trễ (k = 3p: Close, Volume, Range lag 1..p).',
                'Multiple linear regression with k lagged exogenous predictors.',
                components=[
                    ('y_t',         'Biến phụ thuộc (giá hoặc lợi suất)',
                                     'Dependent variable (price or return)'),
                    ('β_0',         'Hệ số chặn (intercept)',
                                     'Intercept'),
                    ('β_j',         'Hệ số hồi quy của biến độc lập thứ j',
                                     'Coefficient of j-th independent variable'),
                    ('x_{j,t}',     'Biến ngoại sinh thứ j tại phiên t (close, volume, range trễ)',
                                     'j-th exogenous variable at session t'),
                    ('ε_t',         'Sai số ngẫu nhiên N(0, σ²) iid',
                                     'Random error N(0, σ²) iid'),
                ],
                references=[
                    'Greene, W. H. (2018). Econometric Analysis (8th ed.). Pearson.',
                    'Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning (2nd ed.). Springer.',
                ],
                color='#8B5CF6', is_en=is_en)

        _block(_T, 'ARIMA(p, d, q) — Autoregressive Integrated Moving Average',
                'ARIMA(p, d, q)',
                r'\Phi(L)\,(1-L)^{d}\, y_t = \Theta(L)\, \varepsilon_t',
                'Kết hợp tự hồi quy bậc p, sai phân bậc d (loại trend), trung bình trượt bậc q.',
                'Combines AR(p), differencing of order d (detrend), and MA(q).',
                components=[
                    ('L',           'Toán tử trễ (lag operator): L·y_t = y_{t-1}',
                                     'Lag operator: L·y_t = y_{t-1}'),
                    ('Φ(L)',        '1 − φ_1·L − ⋯ − φ_p·L^p — đa thức AR bậc p',
                                     '1 − φ_1·L − ⋯ − φ_p·L^p — AR polynomial of order p'),
                    ('Θ(L)',        '1 + θ_1·L + ⋯ + θ_q·L^q — đa thức MA bậc q',
                                     '1 + θ_1·L + ⋯ + θ_q·L^q — MA polynomial of order q'),
                    ('(1−L)^d',     'Toán tử sai phân bậc d, biến chuỗi không dừng thành dừng',
                                     'Differencing operator of order d'),
                    ('ε_t',         'Nhiễu trắng',
                                     'White noise'),
                ],
                references=[
                    'Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2008). Time Series Analysis (4th ed.). Wiley.',
                    'Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.',
                ],
                color='#0EA5E9', is_en=is_en)

        _block(_T, 'SARIMA — Seasonal ARIMA', 'SARIMA — Seasonal ARIMA',
                r'\Phi_P(L^s)\,\phi_p(L)\,(1-L)^d (1-L^s)^D y_t = \Theta_Q(L^s)\,\theta_q(L)\,\varepsilon_t',
                'Mở rộng ARIMA với chu kỳ mùa vụ s (5 phiên/tuần với HOSE). Đảm bảo dữ liệu sau dual-differencing là dừng.',
                'Extension of ARIMA with seasonality period s (5 sessions/week for HOSE).',
                components=[
                    ('(p, d, q)',   'Bậc AR / sai phân / MA của thành phần không mùa vụ.',
                                     'Non-seasonal AR / differencing / MA orders.'),
                    ('(P, D, Q)',   'Bậc AR / sai phân / MA của thành phần mùa vụ.',
                                     'Seasonal AR / differencing / MA orders.'),
                    ('s',           'Chu kỳ mùa vụ — HOSE dùng s=5 (1 tuần giao dịch).',
                                     'Seasonal period — HOSE uses s=5 (one trading week).'),
                    ('L',           'Toán tử trễ: L·yₜ = yₜ₋₁.',
                                     'Lag operator: L·yₜ = yₜ₋₁.'),
                    ('(1−L^s)^D',   'Sai phân mùa vụ bậc D — loại lặp lại theo chu kỳ s.',
                                     'Seasonal differencing of order D.'),
                ],
                references=[
                    'Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2008). Time Series Analysis (4th ed.). Wiley.',
                ],
                color='#10B981', is_en=is_en)

        _block(_T, 'Holt-Winters ETS (Exponential Smoothing)',
                'Holt-Winters ETS (Exponential Smoothing)',
                [r'\ell_t = \alpha (y_t - s_{t-m}) + (1 - \alpha)(\ell_{t-1} + b_{t-1})',
                 r'b_t = \beta(\ell_t - \ell_{t-1}) + (1 - \beta) b_{t-1}',
                 r's_t = \gamma(y_t - \ell_{t-1} - b_{t-1}) + (1 - \gamma) s_{t-m}'],
                'Phân rã chuỗi thành 3 thành phần: level ℓ, trend b, seasonal s. Ba tham số làm mượt α, β, γ ước lượng tối thiểu hoá SSE.',
                'Decomposition into level ℓ, trend b, seasonal s. Three smoothing parameters minimize SSE.',
                components=[
                    ('ℓ_t', 'Mức (level) tại t — giá trị "trung tâm" hiện tại.',
                            'Level at t — current baseline value.'),
                    ('b_t', 'Xu hướng (trend) tại t — tốc độ thay đổi mức.',
                            'Trend slope at t.'),
                    ('s_t', 'Thành phần mùa vụ tại t (chu kỳ m).',
                            'Seasonal component at t (period m).'),
                    ('α',   'Hệ số làm mượt level, 0 < α < 1.',
                            'Level smoothing parameter, 0 < α < 1.'),
                    ('β',   'Hệ số làm mượt trend.',
                            'Trend smoothing parameter.'),
                    ('γ',   'Hệ số làm mượt seasonal.',
                            'Seasonal smoothing parameter.'),
                    ('m',   'Độ dài chu kỳ mùa vụ (m=5 cho 1 tuần HOSE).',
                            'Seasonal period length.'),
                ],
                references=[
                    'Holt, C. C. (1957). Forecasting trends and seasonals by exponentially weighted moving averages. ONR Memo 52.',
                    'Winters, P. R. (1960). Forecasting sales by exponentially weighted moving averages. Management Science, 6(3).',
                ],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'GARCH(1, 1) — Generalized Autoregressive Conditional Heteroscedasticity',
                'GARCH(1, 1)',
                [r'r_t = \mu + \varepsilon_t, \quad \varepsilon_t = \sigma_t z_t, \quad z_t \sim N(0, 1)',
                 r'\sigma_t^2 = \omega + \alpha \varepsilon_{t-1}^2 + \beta \sigma_{t-1}^2'],
                'Mô hình hoá phương sai có điều kiện (volatility clustering). Điều kiện dừng: α + β < 1.',
                'Models conditional variance. Stationarity: α + β < 1.',
                components=[
                    ('r_t',     'Lợi suất tại t (log-return).',
                                'Return at t (log-return).'),
                    ('μ',       'Lợi suất trung bình (drift).',
                                'Mean return (drift).'),
                    ('ε_t',     'Sai số (shock) tại t = σₜ·zₜ.',
                                'Shock at t = σₜ·zₜ.'),
                    ('σ_t²',    'Phương sai có điều kiện tại t — đại lượng cần mô hình hoá.',
                                'Conditional variance at t.'),
                    ('ω',       'Hằng số > 0 — variance dài hạn.',
                                'Constant > 0 — long-run variance.'),
                    ('α',       'Hệ số ARCH — tác động shock quá khứ.',
                                'ARCH coefficient — past shock impact.'),
                    ('β',       'Hệ số GARCH — quán tính variance.',
                                'GARCH coefficient — variance persistence.'),
                ],
                references=[
                    'Engle, R. F. (1982). Autoregressive conditional heteroscedasticity. Econometrica, 50(4). [Nobel 2003]',
                    'Bollerslev, T. (1986). Generalized ARCH. J. of Econometrics, 31(3).',
                ],
                color='#EF4444', is_en=is_en)

        _block(_T, 'SARIMAX — SARIMA with eXogenous regressors',
                'SARIMAX',
                r'\Phi_P(L^s)\phi_p(L)(1-L)^d(1-L^s)^D \big(y_t - \boldsymbol{\beta}^\top \mathbf{x}_t\big) = \Theta_Q(L^s)\theta_q(L)\varepsilon_t',
                'Bổ sung biến ngoại sinh xₜ (ví dụ: volume, sentiment) vào SARIMA — cho phép giải thích thêm bằng features.',
                'Adds exogenous regressors xₜ (e.g., volume, sentiment) to SARIMA.',
                components=[
                    ('y_t',     'Giá trị quan sát tại t.',
                                'Observed value at t.'),
                    ('x_t',     'Vector biến ngoại sinh tại t (volume, sentiment, …).',
                                'Exogenous regressor vector at t.'),
                    ('β',       'Vector hệ số hồi quy của biến ngoại sinh.',
                                'Regression coefficient vector.'),
                    ('ε_t',     'Nhiễu trắng phần SARIMA.',
                                'White noise of the SARIMA part.'),
                    ('(p,d,q)(P,D,Q)_s', 'Các bậc SARIMA — xem block SARIMA phía trên.',
                                          'SARIMA orders — see SARIMA block above.'),
                ],
                references=[
                    'Durbin, J., & Koopman, S. J. (2012). Time Series Analysis by State Space Methods (2nd ed.). Oxford UP.',
                ],
                color='#A855F7', is_en=is_en)

        _block(_T, 'Gradient Boosting Regression (GBR)',
                'Gradient Boosting Regression (GBR)',
                [r'F_M(\mathbf{x}) = F_0(\mathbf{x}) + \sum_{m=1}^{M} \nu \cdot h_m(\mathbf{x})',
                 r'r_{i,m} = -\left.\frac{\partial L(y_i, F(\mathbf{x}_i))}{\partial F(\mathbf{x}_i)}\right|_{F = F_{m-1}}'],
                'Ensemble cây quyết định, mỗi cây hₘ fit pseudo-residual của ensemble trước. ν — learning rate.',
                'Ensemble of decision trees; each tree hₘ fits the pseudo-residual.',
                components=[
                    ('F_M',     'Mô hình ensemble cuối cùng sau M vòng boosting.',
                                'Final ensemble model after M boosting rounds.'),
                    ('F_0',     'Mô hình khởi tạo (thường là hằng số = mean(y)).',
                                'Initial model (usually constant = mean(y)).'),
                    ('h_m',     'Cây quyết định bậc m (weak learner).',
                                'm-th decision tree (weak learner).'),
                    ('ν',       'Tốc độ học (learning rate), 0 < ν ≤ 1.',
                                'Learning rate, 0 < ν ≤ 1.'),
                    ('M',       'Số vòng boosting (số cây).',
                                'Number of boosting rounds.'),
                    ('r_{i,m}', 'Pseudo-residual của mẫu i ở vòng m.',
                                'Pseudo-residual of sample i at round m.'),
                    ('L',       'Hàm mất mát (squared loss cho hồi quy).',
                                'Loss function (squared loss for regression).'),
                ],
                references=[
                    'Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics, 29(5).',
                ],
                color='#EC4899', is_en=is_en)

        _block(_T, 'FinScope Ensemble (inverse-MAPE weighted)',
                'FinScope Ensemble (inverse-MAPE weighted)',
                # v58.3 — widehat + capital Y + \,\, để superscript ens
                # không dính sát mũ; mathrm thay text cho thẳng đứng đều.
                r'\widehat{Y}^{\,\mathrm{ens}}_{t} \;=\; '
                r'\frac{\displaystyle\sum_{i=1}^{K} w_{i} \cdot \widehat{Y}^{(i)}_{t}}'
                r'{\displaystyle\sum_{i=1}^{K} w_{i}}, \qquad '
                r'w_{i} \;=\; \frac{1}{\mathrm{MAPE}_{i} + \delta}',
                'Gộp K mô hình theo trọng số nghịch đảo MAPE — mô hình tốt hơn có trọng số cao hơn. Hằng số δ = 0.1 tránh chia 0.',
                'Combines K models with weights inversely proportional to MAPE.',
                components=[
                    ('ŷ_t^(ens)',   'Dự báo ensemble tại t.',
                                     'Ensemble forecast at t.'),
                    ('ŷ_t^(i)',     'Dự báo của mô hình thứ i tại t.',
                                     'Forecast of i-th model at t.'),
                    ('w_i',         'Trọng số mô hình thứ i — tỉ lệ nghịch với MAPE.',
                                     'Weight of i-th model — inverse of MAPE.'),
                    ('MAPE_i',      'Sai số phần trăm trung bình của mô hình i trên tập validation.',
                                     'Mean absolute percentage error of model i on validation.'),
                    ('K',           'Số mô hình thành phần trong ensemble.',
                                     'Number of component models.'),
                    ('δ',           'Hằng số làm mượt = 0.1 — tránh chia cho 0 khi MAPE → 0.',
                                     'Smoothing constant = 0.1 — avoids division by 0.'),
                ],
                references=[
                    'Stock, J. H., & Watson, M. W. (2004). Combination forecasts of output growth. J. of Forecasting, 23.',
                ],
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
                'Hosoda 1969 multi-component system — 5 lines + Kumo cloud. Anti-leak: Chikou used only for plotting.',
                components=[
                    ('Tenkan',  'Conversion Line — trung bình max/min 9 phiên gần nhất.',
                                'Conversion line — midpoint of 9-period high/low.'),
                    ('Kijun',   'Base Line — trung bình max/min 26 phiên.',
                                'Base line — midpoint of 26-period high/low.'),
                    ('Senkou A','Leading Span A — (Tenkan+Kijun)/2, vẽ tới trước 26 phiên.',
                                'Leading Span A — plotted 26 periods ahead.'),
                    ('Senkou B','Leading Span B — midpoint 52 phiên, vẽ tới trước 26.',
                                'Leading Span B — 52-period midpoint, plotted ahead 26.'),
                    ('Chikou',  'Lagging Span — giá đóng cửa Cₜ vẽ lùi 26 phiên.',
                                'Lagging Span — close shifted back 26 periods.'),
                    ('Kumo',    'Mây giữa Senkou A và B — vùng hỗ trợ/kháng cự động.',
                                'Cloud between Senkou A and B — dynamic S/R zone.'),
                ],
                references=[
                    'Hosoda, G. (1969). Ichimoku Kinko Hyo (一目均衡表).',
                    'Gurrib, I. (2016). Optimization of the Ichimoku Kinko Hyo trading system. Int. J. of Monetary Economics & Finance.',
                ],
                color='#0F766E', is_en=is_en)

        _block(_T, 'RSI(14) — Relative Strength Index', 'RSI(14)',
                [r'\text{RS} = \frac{\text{Avg Gain}_{14}}{\text{Avg Loss}_{14}}',
                 r'\text{RSI} = 100 - \frac{100}{1 + \text{RS}}'],
                'Oscillator [0,100] đo lực mua/bán 14 phiên. RSI > 70 quá mua, < 30 quá bán.',
                'Oscillator [0,100] measuring 14-bar buying/selling pressure.',
                components=[
                    ('Avg Gain₁₄', 'Trung bình các thay đổi DƯƠNG trong 14 phiên (Wilder smoothing).',
                                   '14-period average of positive price changes.'),
                    ('Avg Loss₁₄', 'Trung bình các thay đổi ÂM trong 14 phiên (giá trị tuyệt đối).',
                                   '14-period average of negative price changes (absolute).'),
                    ('RS',         'Tỷ số sức mạnh = Avg Gain / Avg Loss.',
                                   'Relative strength = Avg Gain / Avg Loss.'),
                    ('RSI',        'Chỉ số 0–100; > 70 quá mua, < 30 quá bán.',
                                   '0–100 index; > 70 overbought, < 30 oversold.'),
                ],
                references=[
                    'Wilder, J. W. (1978). New Concepts in Technical Trading Systems. Trend Research.',
                ],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'ATR(n) — Average True Range', 'ATR(n)',
                [r'\text{TR}_t = \max\big(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|\big)',
                 r'\text{ATR}_t = \frac{(n-1) \cdot \text{ATR}_{t-1} + \text{TR}_t}{n}'],
                'Đo biến động giá. Dùng để set stop-loss ATR × k (k=1.5–3 tùy phương án).',
                'Measures price volatility. Used for ATR × k stop-loss.',
                components=[
                    ('H_t, L_t, C_t', 'Giá cao nhất / thấp nhất / đóng cửa tại phiên t.',
                                      'High / Low / Close at session t.'),
                    ('TR_t',          'True Range — biên độ "thật" đã tính gap qua đêm.',
                                      'True Range — accounts for overnight gap.'),
                    ('ATR_t',         'Trung bình True Range theo công thức Wilder.',
                                      'Wilder-smoothed average of True Range.'),
                    ('n',             'Cửa sổ làm mượt, thường n=14.',
                                      'Smoothing window, typically n=14.'),
                ],
                references=[
                    'Wilder, J. W. (1978). New Concepts in Technical Trading Systems. Trend Research.',
                ],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'MACD — Moving Average Convergence Divergence',
                'MACD',
                [r'\text{MACD}_t = \text{EMA}_{12}(C_t) - \text{EMA}_{26}(C_t)',
                 r'\text{Signal}_t = \text{EMA}_9(\text{MACD}_t)',
                 r'\text{Histogram}_t = \text{MACD}_t - \text{Signal}_t'],
                'Cross MACD lên Signal = bull; cross xuống = bear. Histogram đo độ phân kỳ.',
                'MACD crossing above Signal = bull; below = bear.',
                components=[
                    ('C_t',         'Giá đóng cửa tại t.',
                                    'Close price at t.'),
                    ('EMA_n',       'Trung bình động hàm mũ với chu kỳ n; trọng số α = 2/(n+1).',
                                    'Exponential moving average; weight α = 2/(n+1).'),
                    ('MACD_t',      'Hiệu EMA ngắn (12) trừ EMA dài (26).',
                                    'Short EMA (12) minus long EMA (26).'),
                    ('Signal_t',    'EMA(9) của MACD — đường tín hiệu.',
                                    'EMA(9) of MACD — signal line.'),
                    ('Histogram_t', 'MACD − Signal; đổi dấu = giao cắt.',
                                    'MACD − Signal; sign change = crossover.'),
                ],
                references=[
                    'Appel, G. (1979). The Moving Average Convergence-Divergence Trading Method.',
                ],
                color='#8B5CF6', is_en=is_en)

        _block(_T, 'Stochastic Oscillator (%K, %D)',
                'Stochastic Oscillator (%K, %D)',
                [r'\%K_t = \frac{C_t - \min L_n}{\max H_n - \min L_n} \times 100',
                 r'\%D_t = \text{SMA}_3(\%K_t)'],
                '%K > 80 quá mua, < 20 quá bán. Cross %K lên %D = bull.',
                '%K > 80 overbought, < 20 oversold.',
                components=[
                    ('C_t',          'Giá đóng cửa tại t.',
                                     'Close at t.'),
                    ('min L_n',      'Giá thấp nhất trong n phiên gần nhất (mặc định n=14).',
                                     'Lowest low over last n bars (default n=14).'),
                    ('max H_n',      'Giá cao nhất trong n phiên gần nhất.',
                                     'Highest high over last n bars.'),
                    ('%K',           'Vị trí tương đối của close trong range — 0..100.',
                                     'Position of close within range — 0..100.'),
                    ('%D',           'SMA 3 phiên của %K — đường tín hiệu chậm.',
                                     '3-bar SMA of %K — slow signal line.'),
                ],
                references=[
                    'Lane, G. (1957). Stochastic Oscillator. Investment Educators.',
                ],
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
                'QP problem minimizing variance given target return. Long-only via projected gradient.',
                components=[
                    ('w',           'Vector trọng số danh mục (kích thước N tài sản).',
                                    'Portfolio weight vector (size N assets).'),
                    ('μ',           'Vector lợi suất kỳ vọng của N tài sản.',
                                    'Expected return vector of N assets.'),
                    ('Σ',           'Ma trận hiệp phương sai lợi suất (N×N), đối xứng PSD.',
                                    'Return covariance matrix (N×N), symmetric PSD.'),
                    ('R_target',    'Lợi suất mục tiêu — di chuyển sẽ vẽ ra biên hiệu quả.',
                                    'Target return — varying it traces the efficient frontier.'),
                    ('w^T·1 = 1',   'Ràng buộc ngân sách: tổng trọng số = 100%.',
                                    'Budget constraint: weights sum to 100%.'),
                    ('w ≥ 0',       'Long-only — không cho phép bán khống.',
                                    'Long-only — no short-selling.'),
                ],
                references=[
                    'Markowitz, H. (1952). Portfolio selection. The J. of Finance, 7(1).',
                    'Tobin, J. (1958). Liquidity preference as behavior towards risk. RES, 25.',
                    'Wang, W. & Carreira-Perpiñán, M. Á. (2013). Projection onto the probability simplex. arXiv:1309.1541.',
                ],
                color='#1E40AF', is_en=is_en)

        _block(_T, 'Tangency Portfolio (Max Sharpe)', 'Tangency Portfolio (Max Sharpe)',
                r'\mathbf{w}^* = \frac{\boldsymbol{\Sigma}^{-1} (\boldsymbol{\mu} - r_f \cdot \mathbf{1})}{\mathbf{1}^\top \boldsymbol{\Sigma}^{-1} (\boldsymbol{\mu} - r_f \cdot \mathbf{1})}',
                'Closed-form tangency portfolio — điểm trên biên hiệu quả có Sharpe ratio cực đại, tiếp xúc đường thị trường vốn (CML).',
                'Closed-form tangency — point on efficient frontier with maximum Sharpe ratio.',
                components=[
                    ('w*',          'Trọng số danh mục tiếp tuyến (tối đa Sharpe).',
                                    'Tangency portfolio weights (max Sharpe).'),
                    ('Σ⁻¹',         'Ma trận hiệp phương sai nghịch đảo.',
                                    'Inverse covariance matrix.'),
                    ('μ',           'Vector lợi suất kỳ vọng.',
                                    'Expected return vector.'),
                    ('r_f',         'Lãi suất phi rủi ro (annualized).',
                                    'Risk-free rate (annualized).'),
                    ('μ − r_f·1',   'Vector lợi suất vượt rf (excess return).',
                                    'Excess return vector over rf.'),
                    ('1',           'Vector toàn số 1 cùng kích thước với μ.',
                                    'All-ones vector matching μ.'),
                ],
                references=[
                    'Sharpe, W. F. (1966). Mutual fund performance. J. of Business, 39.',
                    'Merton, R. C. (1972). An analytic derivation of the efficient portfolio frontier. JFQA, 7(4).',
                ],
                color='#A855F7', is_en=is_en)

        _block(_T, 'CAPM — Capital Asset Pricing Model', 'CAPM',
                [r'E[R_i] - r_f = \beta_i \cdot (E[R_m] - r_f)',
                 r'\beta_i = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}',
                 r'\alpha_i = E[R_i] - r_f - \beta_i (E[R_m] - r_f) \quad (\text{Jensen 1968})'],
                'Quan hệ tuyến tính giữa lợi suất kỳ vọng và rủi ro hệ thống β. α > 0 = vượt CAPM (outperform). FinScope hồi quy OLS trên VN-Index.',
                'Linear relationship between expected return and systematic risk β.',
                components=[
                    ('R_i',         'Lợi suất tài sản i.',
                                    'Asset i return.'),
                    ('R_m',         'Lợi suất danh mục thị trường (FinScope dùng VN-Index).',
                                    'Market portfolio return (FinScope uses VN-Index).'),
                    ('r_f',         'Lãi suất phi rủi ro.',
                                    'Risk-free rate.'),
                    ('β_i',         'Hệ số rủi ro hệ thống — độ nhạy của Rᵢ với Rₘ.',
                                    'Systematic risk — sensitivity of Rᵢ to Rₘ.'),
                    ('α_i',         'Jensen alpha — phần "vượt CAPM" không giải thích bởi β.',
                                    "Jensen's alpha — excess return not explained by β."),
                    ('Cov(R_i, R_m)', 'Hiệp phương sai giữa lợi suất tài sản và thị trường.',
                                       'Covariance between asset and market returns.'),
                    ('Var(R_m)',    'Phương sai lợi suất thị trường.',
                                    'Variance of market return.'),
                ],
                references=[
                    'Sharpe, W. F. (1964). Capital asset prices. J. of Finance, 19(3).',
                    'Lintner, J. (1965). The valuation of risk assets. RES, 47(1).',
                    'Jensen, M. C. (1968). The performance of mutual funds 1945-1964. J. of Finance, 23(2).',
                ],
                color='#0EA5E9', is_en=is_en)

        _block(_T, 'PCA — Principal Component Analysis', 'PCA',
                [r'\boldsymbol{\Sigma} = \mathbf{V} \boldsymbol{\Lambda} \mathbf{V}^\top \quad (\text{eigendecomposition})',
                 r'\text{Var explained}_i = \lambda_i \,/\, \sum_j \lambda_j'],
                'Phân rã ma trận hiệp phương sai (hoặc tương quan) thành các thành phần chính — PC1 thường gần "market factor", PC2/PC3 sector/size factor.',
                'Decomposition of covariance/correlation matrix into principal components.',
                components=[
                    ('Σ',           'Ma trận hiệp phương sai (hoặc tương quan) của N tài sản.',
                                    'Covariance (or correlation) matrix of N assets.'),
                    ('V',           'Ma trận cột chứa các vector riêng (principal components).',
                                    'Matrix of eigenvectors (principal components) in columns.'),
                    ('Λ',           'Ma trận chéo các trị riêng λ₁ ≥ λ₂ ≥ … ≥ λ_N ≥ 0.',
                                    'Diagonal matrix of eigenvalues λ₁ ≥ … ≥ λ_N ≥ 0.'),
                    ('λ_i',         'Trị riêng thứ i — phương sai giải thích bởi PCᵢ.',
                                    'i-th eigenvalue — variance explained by PCᵢ.'),
                    ('Var expl_i',  'Tỷ lệ phương sai giải thích bởi thành phần chính thứ i.',
                                    'Variance share explained by i-th component.'),
                ],
                references=[
                    'Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. Philosophical Magazine, 2(11).',
                    'Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. J. of Educational Psychology, 24.',
                    'Jolliffe, I. T. (2002). Principal Component Analysis (2nd ed.). Springer.',
                ],
                color='#EC4899', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 4 — QUẢN TRỊ RỦI RO
    # ═══════════════════════════════════════════════════════════════
    with tab_risk:
        _block(_T, 'Sharpe Ratio (annualized)', 'Sharpe Ratio (annualized)',
                r'\text{Sharpe} = \frac{E[R_p] - r_f}{\sigma_p} \cdot \sqrt{252}',
                'Lợi suất vượt rf chia độ lệch chuẩn, hoá năm √252. > 1 tốt, > 2 rất tốt.',
                'Excess return over rf divided by std deviation, annualized.',
                components=[
                    ('E[R_p]',      'Lợi suất kỳ vọng (trung bình) của danh mục p.',
                                    'Expected (mean) return of portfolio p.'),
                    ('r_f',         'Lãi suất phi rủi ro (annualized).',
                                    'Risk-free rate (annualized).'),
                    ('σ_p',         'Độ lệch chuẩn lợi suất danh mục (theo bước thời gian).',
                                    'Standard deviation of portfolio return.'),
                    ('√252',        'Hệ số hoá năm — giả định 252 phiên/năm cho cổ phiếu.',
                                    'Annualization factor — assumes 252 trading days/year.'),
                ],
                references=[
                    'Sharpe, W. F. (1966). Mutual fund performance. J. of Business, 39.',
                    'Sharpe, W. F. (1994). The Sharpe ratio. J. of Portfolio Management.',
                ],
                color='#3B82F6', is_en=is_en)

        _block(_T, 'Maximum Drawdown', 'Maximum Drawdown',
                r'\text{MDD} = \min_t \frac{E_t - \max_{s \leq t} E_s}{\max_{s \leq t} E_s}',
                'Rớt sâu nhất từ đỉnh equity đến đáy sau đó — đo "đau" tối đa user phải chịu.',
                'Largest peak-to-trough decline of equity.',
                components=[
                    ('E_t',                  'Giá trị equity (NAV) của danh mục tại t.',
                                              'Portfolio equity (NAV) at t.'),
                    ('max_{s ≤ t} E_s',      'Đỉnh equity lịch sử tính đến phiên t.',
                                              'Running peak of equity up to t.'),
                    ('(E_t − peak)/peak',    'Drawdown tại t — luôn ≤ 0.',
                                              'Drawdown at t — always ≤ 0.'),
                    ('MDD',                  'Drawdown âm nhất qua toàn lịch sử backtest.',
                                              'Most negative drawdown over backtest history.'),
                ],
                references=[
                    'Magdon-Ismail, M., & Atiya, A. F. (2004). Maximum drawdown. Risk Magazine, 17(10).',
                ],
                color='#EF4444', is_en=is_en)

        _block(_T, 'VaR và CVaR (Expected Shortfall)', 'VaR and CVaR',
                [r'\text{VaR}_\alpha = -F_R^{-1}(\alpha) \quad (\alpha = 0.05 \text{ cho 95\% confidence})',
                 r'\text{CVaR}_\alpha = -E[R \mid R \leq F_R^{-1}(\alpha)]'],
                'VaR 95% = lỗ tối đa với 95% xác suất; CVaR = trung bình lỗ trong 5% trường hợp xấu nhất (chặt hơn VaR — coherent risk measure).',
                'VaR 95% = max loss at 95% confidence; CVaR = mean loss in worst 5%.',
                components=[
                    ('R',           'Biến lợi suất danh mục (random variable).',
                                    'Portfolio return random variable.'),
                    ('α',           'Mức ý nghĩa — α = 0.05 ↔ tin cậy 95%.',
                                    'Significance level — α = 0.05 ↔ 95% confidence.'),
                    ('F_R⁻¹(α)',    'Phân vị α của phân phối R (quantile function).',
                                    'α-quantile of R distribution.'),
                    ('VaR_α',       'Lỗ tối đa kỳ vọng với xác suất 1−α (giá trị dương).',
                                    'Worst loss at confidence 1−α (positive value).'),
                    ('CVaR_α',      'Trung bình lỗ trong vùng đuôi xấu (≤ phân vị α).',
                                    'Average loss within tail beyond α-quantile.'),
                ],
                references=[
                    'Jorion, P. (2007). Value at Risk: The New Benchmark (3rd ed.). McGraw-Hill.',
                    'Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. J. of Risk, 2(3).',
                ],
                color='#DC2626', is_en=is_en)

        _block(_T, 'Kelly Criterion (1956)', 'Kelly Criterion (1956)',
                [r'f^* = W - \frac{1 - W}{b}, \quad b = \frac{\text{avg win}}{|\text{avg loss}|}',
                 r'g(f) = W \log(1 + fb) + (1 - W) \log(1 - f) \quad (\text{expected log-growth})'],
                'Tỷ lệ vốn tối ưu f* tối đa hoá kỳ vọng log-tăng trưởng. Thực tế dùng 1/2 hoặc 1/4 Kelly để giảm phương sai (Thorp 1969).',
                'Optimal bet size f* maximizing expected log-growth.',
                components=[
                    ('f*',          'Tỷ lệ vốn tối ưu mỗi lệnh (fraction of equity).',
                                    'Optimal fraction of equity per bet.'),
                    ('W',           'Xác suất thắng (win rate) ước lượng từ lịch sử.',
                                    'Win rate estimated from history.'),
                    ('b',           'Tỉ lệ payoff = lãi trung bình / lỗ trung bình (tuyệt đối).',
                                    'Payoff ratio = avg win / |avg loss|.'),
                    ('g(f)',        'Kỳ vọng log-tăng trưởng vốn — Kelly tối đa hoá hàm này.',
                                    'Expected log-growth of capital — maximized by Kelly.'),
                    ('½ / ¼ Kelly', 'Thực hành: dùng nửa hoặc một phần tư f* để giảm phương sai.',
                                    'Practice: use half/quarter f* to reduce variance.'),
                ],
                references=[
                    'Kelly, J. L. (1956). A new interpretation of information rate. Bell System Technical Journal, 35(4).',
                    'Thorp, E. O. (1969). Optimal gambling systems for favorable games. Rev. of the Intl. Statistical Inst., 37(3).',
                ],
                color='#F59E0B', is_en=is_en)

        _block(_T, 'Monte Carlo + GBM (Itô correction)',
                'Monte Carlo + GBM (Itô correction)',
                [r'd \ln S_t = \left(\mu - \frac{\sigma^2}{2}\right) dt + \sigma \, dW_t',
                 r'\ln(S_t / S_{t-1}) \sim N\left((\mu - \sigma^2/2) \Delta t, \, \sigma^2 \Delta t\right)'],
                'Mô phỏng Geometric Brownian Motion. Itô correction μ − σ²/2 đảm bảo E[S_T] = S₀·e^(μT). Bootstrap = resample lịch sử thay vì giả định Gaussian.',
                'Geometric Brownian Motion simulation with Itô drift correction.',
                components=[
                    ('S_t',         'Giá tài sản tại thời điểm t.',
                                    'Asset price at time t.'),
                    ('μ',           'Drift — kỳ vọng lợi suất tức thời (annualized).',
                                    'Drift — instantaneous expected return.'),
                    ('σ',           'Volatility — độ lệch chuẩn lợi suất (annualized).',
                                    'Volatility — standard deviation of returns.'),
                    ('μ − σ²/2',    'Itô correction — đảm bảo E[S_T] = S₀·e^{μT}.',
                                    'Itô correction — ensures E[S_T] = S₀·e^{μT}.'),
                    ('dW_t',        'Vi phân chuyển động Brown chuẩn — dW_t ~ N(0, dt).',
                                    'Standard Brownian increment — dW_t ~ N(0, dt).'),
                    ('Δt',          'Bước thời gian rời rạc (ví dụ 1/252 cho 1 phiên).',
                                    'Discrete time step (e.g., 1/252 for one trading day).'),
                ],
                references=[
                    'Boyle, P. P. (1977). Options: A Monte Carlo approach. J. of Financial Economics, 4(3).',
                    'Itô, K. (1944). Stochastic integral. Proc. Imperial Academy, Tokyo, 20(8).',
                ],
                color='#10B981', is_en=is_en)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 5 — KIỂM ĐỊNH THỐNG KÊ
    # ═══════════════════════════════════════════════════════════════
    with tab_test:
        _block(_T, 'Diebold-Mariano Test (1995) + HLN Correction',
                'Diebold-Mariano Test (1995) + HLN Correction',
                [r'd_t = L(e_{1,t}) - L(e_{2,t}), \quad \bar{d} = \frac{1}{n} \sum_{t=1}^{n} d_t',
                 r'\text{DM} = \frac{\bar{d}}{\sqrt{\hat{V}(\bar{d})/n}} \;\to\; N(0, 1)',
                 r'\text{DM}^* = \text{DM} \cdot \sqrt{\frac{n + 1 - 2h + h(h-1)/n}{n}}'],
                'So sánh độ chính xác 2 mô hình dự báo. H₀: 2 mô hình tương đương. HLN correction bù mẫu nhỏ.',
                'Compares forecast accuracy of 2 models. H₀: equivalent.',
                components=[
                    ('e_{i,t}',     'Sai số dự báo của mô hình i tại t (i = 1, 2).',
                                    'Forecast error of model i at t.'),
                    ('L(·)',        'Hàm mất mát (thường là squared error e²).',
                                    'Loss function (usually squared error).'),
                    ('d_t',         'Chênh lệch loss giữa 2 mô hình tại t.',
                                    'Loss differential at t.'),
                    ('d̄',           'Trung bình mẫu của d_t.',
                                    'Sample mean of d_t.'),
                    ('V̂(d̄)',        'Phương sai dài hạn của d̄ (Newey-West HAC).',
                                    'Long-run variance of d̄ (Newey-West HAC).'),
                    ('h',            'Tầm dự báo (forecast horizon).',
                                    'Forecast horizon.'),
                    ('DM*',          'Thống kê DM hiệu chỉnh Harvey-Leybourne-Newbold.',
                                     'HLN-corrected DM statistic.'),
                ],
                references=[
                    'Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. J. of Business & Economic Statistics, 13(3).',
                    'Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction MSE. Int. J. of Forecasting, 13.',
                ],
                color='#1E40AF', is_en=is_en)

        _block(_T, 'Engle-Granger 2-step Cointegration',
                'Engle-Granger 2-step Cointegration',
                [r'\text{Step 1: } Y_t = \alpha + \beta X_t + u_t \quad (\text{OLS})',
                 r'\text{Step 2 (ADF on } u_t\text{): } \Delta u_t = \rho \, u_{t-1} + \sum_{i=1}^{p} \gamma_i \Delta u_{t-i} + \varepsilon_t',
                 r'H_0: \rho = 0 \quad (\text{unit root: NOT cointegrated})'],
                'Test 2 chuỗi giá I(1) có đồng tích hợp không — spread mean-reverting → pairs trading.',
                'Tests if two I(1) price series are cointegrated.',
                components=[
                    ('Y_t, X_t',    'Cặp chuỗi giá I(1) cần kiểm tra cointegration.',
                                    'Pair of I(1) price series under test.'),
                    ('α, β',        'Hệ số chặn và hệ số hồi quy OLS bước 1 (cointegrating vector).',
                                    'OLS intercept and slope (cointegrating vector).'),
                    ('u_t',         'Phần dư (spread) — đối tượng kiểm định ADF.',
                                    'Residual (spread) — tested by ADF.'),
                    ('Δu_t',        'Sai phân bậc 1 của phần dư.',
                                    'First difference of residual.'),
                    ('ρ',           'Hệ số mức (level) trong ADF. ρ < 0 đáng kể ⇒ stationary.',
                                    'Level coefficient in ADF. Significant ρ < 0 ⇒ stationary.'),
                    ('p, γ_i',      'Bậc trễ và hệ số tự hồi quy phần sai phân (loại bỏ tự tương quan).',
                                    'Lag order and AR coefficients in differenced part.'),
                    ('H_0',         'Giả thuyết "có unit root" → KHÔNG cointegrated.',
                                    "Null 'has unit root' → NOT cointegrated."),
                ],
                references=[
                    'Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction. Econometrica, 55(2). [Nobel 2003]',
                    'Dickey, D. A., & Fuller, W. A. (1979). Distribution of estimators for AR time series with unit root. JASA, 74.',
                    'Vidyamurthy, G. (2004). Pairs Trading: Quantitative methods and analysis. Wiley.',
                ],
                color='#A855F7', is_en=is_en)

        _block(_T, 'MAPE, RMSE, MAE, R²adj — Forecast Metrics',
                'MAPE, RMSE, MAE, R²adj — Forecast Metrics',
                [r'\text{MAPE} = \frac{100}{n} \sum_{t=1}^{n} \left|\frac{y_t - \hat{y}_t}{y_t}\right| \%',
                 r'\text{RMSE} = \sqrt{\frac{1}{n} \sum_{t=1}^{n} (y_t - \hat{y}_t)^2}, \quad \text{MAE} = \frac{1}{n} \sum_{t=1}^{n} |y_t - \hat{y}_t|',
                 r'R^2_{\text{adj}} = 1 - (1 - R^2) \cdot \frac{n - 1}{n - k - 1}'],
                'Đánh giá mô hình: MAPE thấp tốt (< 2% xuất sắc); R²adj phạt số tham số k (tránh overfitting).',
                'Model evaluation metrics; R²adj penalizes parameter count k.',
                components=[
                    ('y_t',         'Giá trị thực tại t.',
                                    'Actual value at t.'),
                    ('ŷ_t',         'Giá trị dự báo tại t.',
                                    'Forecast value at t.'),
                    ('n',           'Số quan sát trong tập kiểm tra.',
                                    'Number of test observations.'),
                    ('MAPE',        'Sai số phần trăm tuyệt đối trung bình (đơn vị %).',
                                    'Mean absolute percentage error (%).'),
                    ('RMSE',        'Căn của trung bình bình phương sai số (cùng đơn vị y).',
                                    'Root mean squared error (same unit as y).'),
                    ('MAE',         'Sai số tuyệt đối trung bình.',
                                    'Mean absolute error.'),
                    ('R²',          'Tỷ lệ phương sai giải thích.',
                                    'Proportion of variance explained.'),
                    ('k',           'Số tham số hồi quy (cho R²adj phạt overfitting).',
                                    'Number of regressors (R²adj penalizes overfitting).'),
                ],
                references=[
                    'Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. Int. J. of Forecasting, 22(4).',
                ],
                color='#10B981', is_en=is_en)

    st.markdown(
        f'<div style="text-align:center;margin-top:20px;padding:14px;'
        f'color:{_T["text_muted"]};font-size:11px">'
        f'{"FinScope · Tài liệu tham khảo APA · Không phải lời khuyên đầu tư" if not is_en else "FinScope · APA references · Not investment advice"}'
        f'</div>', unsafe_allow_html=True)

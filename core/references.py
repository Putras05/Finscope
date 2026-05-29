"""Academic references database cho chatbot — APA 7th, song ngữ VI/EN."""

REFERENCES = {
    'box_jenkins_1976': {
        'apa': 'Box, G. E. P., & Jenkins, G. M. (1976). *Time Series Analysis: Forecasting and Control*. San Francisco: Holden-Day.',
        'topic': ['ar', 'autoregressive', 'arima', 'time_series'],
        'note_vi': 'Tài liệu kinh điển về mô hình AR, MA, ARIMA.',
        'note_en': 'Classical reference for AR, MA, ARIMA models.',
    },
    'hamilton_1994': {
        'apa': 'Hamilton, J. D. (1994). *Time Series Analysis*. Princeton, NJ: Princeton University Press.',
        'topic': ['ar', 'time_series', 'econometrics'],
        'note_vi': 'Giáo trình cao học về time series analysis.',
        'note_en': 'Graduate-level time series textbook.',
    },
    'hyndman_2021_metrics': {
        'apa': 'Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). Melbourne: OTexts. https://otexts.com/fpp3/',
        'topic': ['mape', 'metrics', 'forecasting', 'evaluation'],
        'note_vi': 'Sách mở trực tuyến, chuẩn đánh giá dự báo.',
        'note_en': 'Open online textbook, forecast evaluation standard.',
    },
    'wooldridge_2019': {
        'apa': 'Wooldridge, J. M. (2019). *Introductory Econometrics: A Modern Approach* (7th ed.). Boston: Cengage Learning.',
        'topic': ['mlr', 'multiple_regression', 'ols', 'econometrics'],
        'note_vi': 'Giáo trình kinh tế lượng căn bản về MLR, OLS.',
        'note_en': 'Standard undergraduate econometrics textbook.',
    },
    'greene_2018': {
        'apa': 'Greene, W. H. (2018). *Econometric Analysis* (8th ed.). New York: Pearson.',
        'topic': ['mlr', 'econometrics', 'distributed_lag'],
        'note_vi': 'Tham khảo nâng cao về kinh tế lượng và Distributed Lag.',
        'note_en': 'Advanced econometrics reference.',
    },
    'box_jenkins_2015': {
        'apa': 'Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015). *Time Series Analysis: Forecasting and Control* (5th ed.). Hoboken, NJ: Wiley.',
        'topic': ['arima', 'sarima', 'box_jenkins', 'time_series'],
        'note_vi': 'Công trình nền tảng về ARIMA/SARIMA (phương pháp Box-Jenkins).',
        'note_en': 'Foundational work on ARIMA/SARIMA (the Box-Jenkins methodology).',
    },
    'hyndman_2021_ets': {
        'apa': 'Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). Melbourne: OTexts.',
        'topic': ['arima', 'ets', 'holt_winters', 'forecasting', 'time_series', 'mape'],
        'note_vi': 'Tham khảo chính về dự báo chuỗi thời gian: ARIMA, ETS/Holt-Winters, khoảng dự báo, MAPE.',
        'note_en': 'Main time-series forecasting reference: ARIMA, ETS/Holt-Winters, prediction intervals, MAPE.',
    },
    'bollerslev_1986': {
        'apa': 'Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics, 31*(3), 307–327.',
        'topic': ['garch', 'volatility', 'time_series'],
        'note_vi': 'Công trình gốc giới thiệu mô hình GARCH (biến động có điều kiện).',
        'note_en': 'Original work introducing the GARCH conditional-volatility model.',
    },
    'hosoda_1969': {
        'apa': 'Hosoda, G. (1969). *Ichimoku Kinko Hyo* [一目均衡表]. Tokyo: Keizai Henshuukai. (English: Patel, M. (2010). *Trading with Ichimoku Clouds*. Wiley.)',
        'topic': ['ichimoku', 'technical_analysis', 'kumo', 'tenkan', 'kijun', 'chikou'],
        'note_vi': 'Tác phẩm gốc tiếng Nhật giới thiệu Ichimoku Kinko Hyo.',
        'note_en': 'Original Japanese work on Ichimoku Kinko Hyo.',
    },
    'elliott_2007': {
        'apa': 'Elliott, N. (2007). *Ichimoku Charts: An Introduction to Ichimoku Kinko Clouds*. Petersfield: Harriman House.',
        'topic': ['ichimoku', 'technical_analysis'],
        'note_vi': 'Giới thiệu Ichimoku bằng tiếng Anh, hệ thống và dễ hiểu.',
        'note_en': 'Systematic English introduction to Ichimoku.',
    },
    'murphy_1999': {
        'apa': 'Murphy, J. J. (1999). *Technical Analysis of the Financial Markets*. New York: NY Institute of Finance.',
        'topic': ['technical_analysis', 'rsi', 'moving_average'],
        'note_vi': 'Bách khoa về phân tích kỹ thuật.',
        'note_en': 'Encyclopedic technical analysis reference.',
    },
    'fama_1970': {
        'apa': 'Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. *The Journal of Finance*, 25(2), 383-417.',
        'topic': ['efficient_market', 'market_efficiency', 'emh'],
        'note_vi': 'Bài báo gốc về Giả thuyết Thị trường Hiệu quả (EMH).',
        'note_en': 'Seminal paper on Efficient Market Hypothesis.',
    },
    'vnstock_2024': {
        'apa': 'Vnstock Team. (2024). *vnstock: Python library for Vietnamese stock market data*. https://github.com/thinh-vu/vnstock',
        'topic': ['vnstock', 'hose', 'data'],
        'note_vi': 'Thư viện Python nguồn mở cho dữ liệu HOSE, HNX.',
        'note_en': 'Open-source Python library for HOSE, HNX data.',
    },
    # ── Sprint B math additions (v49) ─────────────────────────────────
    'markowitz_1952': {
        'apa': 'Markowitz, H. (1952). Portfolio selection. *The Journal of Finance, 7*(1), 77-91.',
        'topic': ['markowitz', 'portfolio', 'mean_variance', 'optimization'],
        'note_vi': 'Bài báo Nobel đặt nền tảng Modern Portfolio Theory (MPT).',
        'note_en': 'Nobel paper founding Modern Portfolio Theory.',
    },
    'tobin_1958': {
        'apa': 'Tobin, J. (1958). Liquidity preference as behavior towards risk. *Review of Economic Studies, 25*(2), 65-86.',
        'topic': ['portfolio', 'two_fund_theorem', 'risk_free'],
        'note_vi': 'Two-fund theorem — kết hợp risk-free asset với portfolio risky tối ưu.',
        'note_en': 'Two-fund theorem — combining risk-free asset with optimal risky portfolio.',
    },
    'sharpe_1964': {
        'apa': 'Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. *The Journal of Finance, 19*(3), 425-442.',
        'topic': ['capm', 'beta', 'sml', 'market_risk'],
        'note_vi': 'Bài báo Nobel giới thiệu CAPM — quan hệ tuyến tính β và lợi suất kỳ vọng.',
        'note_en': 'Nobel paper introducing CAPM — linear β-return relationship.',
    },
    'lintner_1965': {
        'apa': 'Lintner, J. (1965). The valuation of risk assets and the selection of risky investments in stock portfolios and capital budgets. *Review of Economics and Statistics, 47*(1), 13-37.',
        'topic': ['capm', 'beta', 'portfolio_selection'],
        'note_vi': 'Đồng thời với Sharpe 1964 — phát triển độc lập CAPM.',
        'note_en': 'Parallel with Sharpe 1964 — independent development of CAPM.',
    },
    'sharpe_1966': {
        'apa': 'Sharpe, W. F. (1966). Mutual fund performance. *The Journal of Business, 39*(1), 119-138.',
        'topic': ['sharpe_ratio', 'risk_adjusted_return', 'performance'],
        'note_vi': 'Định nghĩa Sharpe ratio = (E[R]-rf)/σ — chuẩn đánh giá lợi suất điều chỉnh rủi ro.',
        'note_en': 'Sharpe ratio definition — risk-adjusted return standard.',
    },
    'jensen_1968': {
        'apa': "Jensen, M. C. (1968). The performance of mutual funds in the period 1945-1964. *The Journal of Finance, 23*(2), 389-416.",
        'topic': ['alpha', 'jensen_alpha', 'capm'],
        'note_vi': 'Định nghĩa Jensen alpha — outperform/underperform sau khi điều chỉnh CAPM.',
        'note_en': 'Jensen alpha definition — CAPM-adjusted excess return.',
    },
    'pearson_1901': {
        'apa': 'Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. *Philosophical Magazine, 2*(11), 559-572.',
        'topic': ['pca', 'eigendecomposition', 'dimensionality_reduction'],
        'note_vi': 'Công trình gốc về PCA — đường/mặt phẳng gần điểm nhất.',
        'note_en': 'Original PCA work — closest-fit lines and planes.',
    },
    'hotelling_1933': {
        'apa': 'Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. *Journal of Educational Psychology, 24*(6 & 7), 417-441, 498-520.',
        'topic': ['pca', 'principal_components'],
        'note_vi': 'Hotelling đặt tên "principal components" và phát triển thuật toán hiện đại.',
        'note_en': 'Hotelling named "principal components" and developed the modern algorithm.',
    },
    'jolliffe_2002': {
        'apa': 'Jolliffe, I. T. (2002). *Principal Component Analysis* (2nd ed.). New York: Springer.',
        'topic': ['pca', 'eigendecomposition', 'textbook'],
        'note_vi': 'Sách giáo khoa kinh điển về PCA — covered từ lý thuyết tới ứng dụng.',
        'note_en': 'Classical PCA textbook covering theory to applications.',
    },
    'engle_granger_1987': {
        'apa': 'Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. *Econometrica, 55*(2), 251-276.',
        'topic': ['cointegration', 'engle_granger', 'pairs_trading', 'unit_root'],
        'note_vi': 'Bài báo Nobel 2003 — cointegration test 2 bước cho chuỗi giá I(1).',
        'note_en': '2003 Nobel paper — 2-step cointegration test for I(1) series.',
    },
    'dickey_fuller_1979': {
        'apa': 'Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. *Journal of the American Statistical Association, 74*(366), 427-431.',
        'topic': ['adf', 'unit_root', 'stationarity'],
        'note_vi': 'Test ADF — kiểm tra unit root trong chuỗi thời gian.',
        'note_en': 'ADF test — unit root in time series.',
    },
    'vidyamurthy_2004': {
        'apa': 'Vidyamurthy, G. (2004). *Pairs Trading: Quantitative methods and analysis*. Hoboken, NJ: Wiley.',
        'topic': ['pairs_trading', 'cointegration', 'statistical_arbitrage'],
        'note_vi': 'Sách thực hành về pairs trading dựa trên cointegration.',
        'note_en': 'Practical book on cointegration-based pairs trading.',
    },
    'kelly_1956': {
        'apa': 'Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal, 35*(4), 917-926.',
        'topic': ['kelly', 'position_sizing', 'log_growth'],
        'note_vi': 'Công trình gốc về Kelly criterion — tỉ lệ vốn tối ưu max log-growth.',
        'note_en': 'Original Kelly criterion — optimal fraction maximizing log-growth.',
    },
    'thorp_1969': {
        'apa': 'Thorp, E. O. (1969). Optimal gambling systems for favorable games. *Review of the International Statistical Institute, 37*(3), 273-293.',
        'topic': ['kelly', 'fractional_kelly', 'gambling'],
        'note_vi': 'Mở rộng Kelly cho continuous + fractional Kelly để giảm phương sai.',
        'note_en': 'Kelly extension to continuous + fractional Kelly for variance reduction.',
    },
    'wilder_1978': {
        'apa': 'Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Greensboro, NC: Trend Research.',
        'topic': ['rsi', 'atr', 'wilder', 'technical_analysis'],
        'note_vi': 'Sách gốc giới thiệu RSI, ATR, Parabolic SAR, ADX.',
        'note_en': 'Original book introducing RSI, ATR, Parabolic SAR, ADX.',
    },
    'boyle_1977': {
        'apa': 'Boyle, P. P. (1977). Options: A Monte Carlo approach. *Journal of Financial Economics, 4*(3), 323-338.',
        'topic': ['monte_carlo', 'gbm', 'simulation', 'options'],
        'note_vi': 'Bài báo đầu tiên áp dụng Monte Carlo vào pricing tài chính.',
        'note_en': 'First paper applying Monte Carlo to financial pricing.',
    },
    'ito_1944': {
        'apa': 'Itô, K. (1944). Stochastic integral. *Proceedings of the Imperial Academy, Tokyo, 20*(8), 519-524.',
        'topic': ['ito_calculus', 'gbm', 'sde'],
        'note_vi': 'Itô calculus — nền tảng GBM với drift correction μ - σ²/2.',
        'note_en': 'Itô calculus — foundation for GBM with drift correction.',
    },
    'jorion_2007': {
        'apa': 'Jorion, P. (2007). *Value at Risk: The new benchmark for managing financial risk* (3rd ed.). New York: McGraw-Hill.',
        'topic': ['var', 'cvar', 'risk_management'],
        'note_vi': 'Sách chuẩn về VaR — chuẩn mực quản trị rủi ro tài chính.',
        'note_en': 'Standard book on VaR — financial risk management benchmark.',
    },
    'rockafellar_uryasev_2000': {
        'apa': 'Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *Journal of Risk, 2*(3), 21-41.',
        'topic': ['cvar', 'expected_shortfall', 'risk_measure'],
        'note_vi': 'CVaR (Expected Shortfall) — coherent risk measure, chặt hơn VaR.',
        'note_en': 'CVaR (Expected Shortfall) — coherent risk measure stricter than VaR.',
    },
    'sortino_price_1994': {
        'apa': 'Sortino, F. A., & Price, L. N. (1994). Performance measurement in a downside risk framework. *The Journal of Investing, 3*(3), 59-64.',
        'topic': ['sortino', 'downside_risk', 'performance'],
        'note_vi': 'Sortino ratio — chỉ phạt biến động NEGATIVE (downside deviation).',
        'note_en': 'Sortino ratio — penalizes only negative deviation.',
    },
    'diebold_mariano_1995': {
        'apa': 'Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics, 13*(3), 253-263.',
        'topic': ['diebold_mariano', 'forecast_comparison', 'hypothesis_test'],
        'note_vi': 'Test DM — so sánh độ chính xác 2 mô hình dự báo.',
        'note_en': 'DM test — compares forecast accuracy of two models.',
    },
    'harvey_leybourne_newbold_1997': {
        'apa': 'Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting, 13*(2), 281-291.',
        'topic': ['diebold_mariano', 'hln_correction', 'small_sample'],
        'note_vi': 'HLN correction cho DM test — bù mẫu nhỏ.',
        'note_en': 'HLN small-sample correction for the DM test.',
    },
    'wang_carreira_perpinan_2013': {
        'apa': 'Wang, W., & Carreira-Perpiñán, M. Á. (2013). Projection onto the probability simplex: An efficient algorithm with a simple proof, and an application. *arXiv preprint arXiv:1309.1541*.',
        'topic': ['simplex_projection', 'optimization', 'markowitz'],
        'note_vi': 'Thuật toán O(n log n) chiếu vector lên simplex — dùng trong Markowitz long-only.',
        'note_en': 'O(n log n) simplex projection algorithm — used in long-only Markowitz.',
    },
    'friedman_2001': {
        'apa': 'Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *Annals of Statistics, 29*(5), 1189-1232.',
        'topic': ['gbr', 'gradient_boosting', 'ensemble_learning'],
        'note_vi': 'Công trình gốc về Gradient Boosting — ensemble cây quyết định fit residual.',
        'note_en': 'Original Gradient Boosting — ensemble decision trees fitting residuals.',
    },
    'aronson_2007': {
        'apa': 'Aronson, D. R. (2007). *Evidence-Based Technical Analysis: Applying the Scientific Method and Statistical Inference to Trading Signals*. Hoboken, NJ: Wiley.',
        'topic': ['signal_engine', 'evidence_based', 'data_mining_bias'],
        'note_vi': 'Triết lý evidence-based — combine signals theo phương pháp khoa học.',
        'note_en': 'Evidence-based philosophy — combining signals scientifically.',
    },
}


def get_references_by_topic(topic: str, lang: str = 'VI') -> str:
    topic_lower = topic.lower().replace(' ', '_')
    matched = [r for r in REFERENCES.values() if topic_lower in r['topic']]
    if not matched:
        return ''
    header = '### Tài liệu tham khảo' if lang == 'VI' else '### References'
    lines = [header, '']
    for i, ref in enumerate(matched, 1):
        lines.append(f'[{i}] {ref["apa"]}')
        note = ref.get(f'note_{lang.lower()}', '')
        if note:
            lines.append(f'    *{note}*')
        lines.append('')
    return '\n'.join(lines)


def get_all_references(lang: str = 'VI') -> str:
    header = '### Danh mục tài liệu tham khảo' if lang == 'VI' else '### Complete Bibliography'
    lines = [header, '']
    for i, ref in enumerate(REFERENCES.values(), 1):
        lines.append(f'[{i}] {ref["apa"]}')
        lines.append('')
    return '\n'.join(lines)


def detect_citation_request(query: str):
    import re
    q = query.lower()
    citation_kws = [
        r'(tài liệu|tham khảo|nguồn|reference|citation|sách|paper|bibliography)',
        r'(ở đâu|where|which book|cuốn sách nào|công trình nào)',
        r'(cited from|trích dẫn|dẫn nguồn)',
    ]
    is_citation = any(re.search(k, q) for k in citation_kws)
    if not is_citation:
        return False, None

    topic_kws = {
        'ar':                ['ar ', 'autoregressive', 'tự hồi quy'],
        'mlr':               ['mlr', 'multiple regression', 'hồi quy bội'],
        'cart':              ['cart', 'decision tree', 'cây quyết định'],
        'ichimoku':          ['ichimoku', 'kinko', 'kumo', 'tenkan', 'kijun'],
        'mape':              ['mape', 'rmse', 'mae', 'metric', 'đánh giá'],
        'technical_analysis':['phân tích kỹ thuật', 'technical analysis'],
        'efficient_market':  ['efficient market', 'thị trường hiệu quả', 'emh'],
    }
    for topic, kws in topic_kws.items():
        if any(kw in q for kw in kws):
            return True, topic
    return True, None

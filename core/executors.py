"""Shared ThreadPoolExecutor singleton (`@st.cache_resource`).

Trước v56: app.py + core/preload.py + app_pages/splash.py + app_pages/portfolio.py
mỗi nơi tạo ThreadPoolExecutor riêng (max_workers=8/4) → tổng kernel thread
nhiều hơn cần thiết + tear-up/tear-down cost.

Sau v56: 1 pool dùng chung trên toàn process. Streamlit `@st.cache_resource`
giữ instance sống suốt lifetime → các module submit() vào cùng pool.

Tham khảo: Streamlit perf docs — cache_resource cho expensive global objects.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

import streamlit as st


@st.cache_resource(show_spinner=False)
def get_pool(max_workers: int = 8) -> ThreadPoolExecutor:
    """Shared pool — singleton. max_workers chỉ tác động khi gọi LẦN ĐẦU."""
    return ThreadPoolExecutor(max_workers=max_workers,
                              thread_name_prefix='finscope-pool')

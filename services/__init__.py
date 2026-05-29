"""Tầng dịch vụ (backend) — tách logic ra khỏi UI.

Mục tiêu: trang Streamlit chỉ làm việc render; tính toán tín hiệu, quản trị
rủi ro và lập kế hoạch giao dịch nằm trọn ở `services/`. Dễ test, dễ tái sử
dụng, dễ thay engine sau này.

Module chính:
  • signal_engine — gộp 8 trụ cột tín hiệu (trend / Ichimoku / momentum /
    volume / S-R / volatility / pattern / fundamentals) thành 1 conviction
    score [-100, +100] kèm "reason chain".
  • trade_planner — từ conviction + ATR + S/R đề xuất 3 phương án giao dịch
    Conservative / Balanced / Aggressive với entry, stop, take-profit và
    position size dựa trên Kelly-lite & risk per trade.
  • risk         — công cụ rủi ro: ATR, position sizing, R-multiple.
"""

from services.signal_engine import build_signal_report
from services.trade_planner import build_trade_plans
from services import risk

__all__ = ['build_signal_report', 'build_trade_plans', 'risk']

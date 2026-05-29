"""Huy hiệu thành tựu (gamification) cho FinScope Paper Trading.

KHÔNG lưu state riêng — tính từ state Paper hiện tại + watchlist + journal.
Mỗi badge có:
  • code        — định danh (key trong dict trả về)
  • title_vi/en — tiêu đề
  • desc_vi/en  — mô tả điều kiện
  • icon        — tên SVG icon trong ui.icons (KHÔNG dùng emoji)
  • earned      — True/False
  • progress    — (cur, target) cho thanh tiến độ; None nếu binary
"""
from __future__ import annotations
from typing import Optional


def evaluate(state: dict, stats: dict,
             watchlist: Optional[list] = None,
             journal_entries: Optional[list] = None) -> list:
    """Trả list badge dict đã đánh giá xong (earned + progress)."""
    history = state.get('history', []) if state else []
    n_trades = len(history)
    n_buys = sum(1 for h in history if h.get('side') == 'BUY')
    n_sells = sum(1 for h in history if h.get('side') == 'SELL')
    tickers_touched = len({h.get('ticker') for h in history if h.get('ticker')})
    n_wins = (stats or {}).get('n_wins', 0)
    n_losses = (stats or {}).get('n_losses', 0)
    total_return = (stats or {}).get('total_return_pct', 0.0)
    win_rate = (stats or {}).get('win_rate', 0.0)
    max_dd = (stats or {}).get('max_drawdown_pct', 0.0)
    sharpe = (stats or {}).get('sharpe_ratio', 0.0)
    wl = watchlist or []
    je = journal_entries or []

    def _bin(code, t_vi, t_en, d_vi, d_en, ic, ok):
        return {'code': code, 'title_vi': t_vi, 'title_en': t_en,
                'desc_vi': d_vi, 'desc_en': d_en, 'icon': ic,
                'earned': bool(ok), 'progress': None}

    def _prog(code, t_vi, t_en, d_vi, d_en, ic, cur, target):
        return {'code': code, 'title_vi': t_vi, 'title_en': t_en,
                'desc_vi': d_vi, 'desc_en': d_en, 'icon': ic,
                'earned': cur >= target,
                'progress': (min(int(cur), int(target)), int(target))}

    badges = [
        _bin('first_trade', 'Lệnh đầu tay', 'First Trade',
             'Đặt lệnh giao dịch đầu tiên', 'Place your first trade',
             'bullseye-fill', n_trades >= 1),
        _prog('ten_trades', '10 lệnh', '10 Trades',
              'Đặt đủ 10 lệnh để quen với cách thị trường vận động',
              'Reach 10 trades to learn how markets move',
              'bar-chart-line-fill', n_trades, 10),
        _prog('explorer', 'Nhà thám hiểm', 'Explorer',
              'Giao dịch trên 5 mã khác nhau',
              'Trade 5 different tickers',
              'compass-fill', tickers_touched, 5),
        _bin('first_sell', 'Chốt lời lần đầu', 'First Sell',
             'Đóng vị thế lần đầu (lệnh SELL)',
             'Close a position for the first time',
             'briefcase-fill', n_sells >= 1),
        _bin('first_win', 'Trận thắng đầu tiên', 'First Win',
             'Có 1 lệnh chốt lời dương sau phí',
             'A first realized winning trade (net of fees)',
             'award-fill', n_wins >= 1),
        _prog('win_streak', 'Tay giao dịch', 'Trader Track',
              'Thắng 5 lệnh tích lũy', 'Reach 5 winning trades',
              'fire', n_wins, 5),
        _prog('disciplined_loss', 'Cắt lỗ kỷ luật', 'Disciplined Cuts',
              'Chấp nhận 3 lệnh cắt lỗ — quan trọng không kém thắng',
              'Take 3 disciplined stop-losses — as important as wins',
              'shield-fill-check', n_losses, 3),
        _bin('hi_winrate', 'Tỷ lệ thắng > 60%', 'Win-rate > 60%',
             'Tỷ lệ thắng vượt 60% (tối thiểu 5 lệnh SELL)',
             'Win-rate exceeds 60% with ≥ 5 sells',
             'trophy-fill', n_sells >= 5 and win_rate >= 60.0),
        _bin('green_book', 'Sổ xanh', 'Green Book',
             'Lãi tổng > 0 (tổng tài sản vượt vốn)',
             'Total return positive (equity > capital)',
             'flower2', total_return > 0),
        _bin('roi_10', 'Tăng trưởng 10%', 'ROI 10%',
             'Lợi suất danh mục > 10%', 'Portfolio return > 10%',
             'graph-up-arrow', total_return >= 10),
        _bin('mdd_guard', 'Phòng thủ tốt', 'Drawdown Guard',
             'MDD nông hơn -5% (kiểm soát rủi ro tốt)',
             'Max drawdown shallower than -5%',
             'life-preserver', max_dd > -5 and len(history) >= 5),
        _bin('sharpe_1', 'Sharpe ≥ 1', 'Sharpe ≥ 1',
             'Hệ số Sharpe hoá năm ≥ 1.0', 'Annualized Sharpe ≥ 1.0',
             'speedometer', sharpe == sharpe and sharpe >= 1.0),
        _prog('curator', 'Nhà sưu tầm', 'Curator',
              'Thêm 5 mã vào danh mục yêu thích',
              'Add 5 tickers to your watchlist',
              'star-fill', len(wl), 5),
        _prog('journalist', 'Người viết nhật ký', 'Journalist',
              'Ghi 5 entry nhật ký giao dịch',
              'Log 5 trade journal entries',
              'journal-text', len(je), 5),
    ]
    return badges


def summary(badges: list) -> dict:
    earned = sum(1 for b in badges if b.get('earned'))
    return {'earned': earned, 'total': len(badges),
            'pct': (earned / len(badges) * 100.0) if badges else 0.0}

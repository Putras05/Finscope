"""Giao dịch Demo (paper trading) — sổ lệnh ảo, lãi/lỗ + thống kê người dùng.

Lưu trạng thái vào JSON tại thư mục app (`paper_state.json`); mỗi máy/thiết
bị một sổ riêng. KHÔNG phải khuyến nghị đầu tư — chỉ để học cách quản trị
lệnh, theo dõi P&L và đánh giá kỷ luật giao dịch của chính mình.

Quy ước giá: lưu giá ở đơn vị ĐỒNG (đã ×1000 từ Close gốc).
"""
import json
import datetime as _dt
from pathlib import Path

_STATE_FILE = Path(__file__).resolve().parent.parent / 'paper_state.json'
_DEFAULT_CAPITAL = 100_000_000.0      # 100 triệu đồng


def _empty_state(capital: float = _DEFAULT_CAPITAL) -> dict:
    return {
        'cash':            float(capital),
        'initial_capital': float(capital),
        'positions':       {},   # {ticker: {qty, avg_price}}
        'history':         [],   # [{ts, ticker, side, qty, price, value, realized}]
        'created_at':      _dt.datetime.now().isoformat(timespec='seconds'),
    }


def load_state() -> dict:
    """Đọc trạng thái từ file; nếu thiếu/lỗi → state rỗng (mặc định 100tr đ)."""
    try:
        if _STATE_FILE.exists():
            with _STATE_FILE.open('r', encoding='utf-8') as f:
                s = json.load(f)
            # bảo đảm các khoá tồn tại
            for k in ('cash', 'initial_capital', 'positions', 'history'):
                s.setdefault(k, _empty_state()[k])
            return s
    except Exception:
        pass
    return _empty_state()


def save_state(s: dict) -> None:
    """Ghi trạng thái xuống file — best-effort, không ném lỗi."""
    try:
        with _STATE_FILE.open('w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def reset_state(capital: float = _DEFAULT_CAPITAL) -> dict:
    """Tạo sổ mới với vốn ban đầu cho trước. Ghi đè file cũ."""
    s = _empty_state(capital)
    save_state(s)
    return s


def buy(state: dict, ticker: str, qty: int, price: float) -> tuple:
    """Đặt lệnh MUA. Trả (state, ok, msg). Giá ở đơn vị ĐỒNG."""
    if qty <= 0:
        return state, False, 'Khối lượng phải > 0.'
    cost = qty * price
    if cost > state['cash'] + 1e-6:
        return state, False, f'Không đủ tiền: cần {cost:,.0f} đ, có {state["cash"]:,.0f} đ.'
    pos = state['positions'].get(ticker)
    if pos is None:
        new_avg = price
        new_qty = qty
    else:
        # bình quân gia quyền
        new_qty = pos['qty'] + qty
        new_avg = (pos['qty'] * pos['avg_price'] + qty * price) / new_qty
    state['positions'][ticker] = {'qty': int(new_qty), 'avg_price': float(new_avg)}
    state['cash'] = float(state['cash'] - cost)
    state['history'].append({
        'ts': _dt.datetime.now().isoformat(timespec='seconds'),
        'ticker': ticker, 'side': 'BUY', 'qty': int(qty),
        'price': float(price), 'value': float(cost), 'realized': None,
    })
    save_state(state)
    return state, True, f'Mua {qty} {ticker} @ {price:,.0f} đ ({cost:,.0f} đ).'


def sell(state: dict, ticker: str, qty: int, price: float) -> tuple:
    """Đặt lệnh BÁN. Trả (state, ok, msg). Tính realized P&L theo avg_price."""
    pos = state['positions'].get(ticker)
    if pos is None or pos['qty'] <= 0:
        return state, False, f'Không có vị thế {ticker}.'
    if qty <= 0:
        return state, False, 'Khối lượng phải > 0.'
    if qty > pos['qty']:
        return state, False, f'Chỉ có {pos["qty"]} {ticker}, không đủ để bán {qty}.'
    proceeds = qty * price
    realized = (price - pos['avg_price']) * qty
    pos['qty'] = int(pos['qty'] - qty)
    if pos['qty'] == 0:
        state['positions'].pop(ticker, None)
    else:
        state['positions'][ticker] = pos
    state['cash'] = float(state['cash'] + proceeds)
    state['history'].append({
        'ts': _dt.datetime.now().isoformat(timespec='seconds'),
        'ticker': ticker, 'side': 'SELL', 'qty': int(qty),
        'price': float(price), 'value': float(proceeds),
        'realized': float(realized),
    })
    save_state(state)
    return state, True, (f'Bán {qty} {ticker} @ {price:,.0f} đ '
                         f'(realized {realized:+,.0f} đ).')


def compute_stats(state: dict, current_prices: dict) -> dict:
    """Tính giá trị danh mục + lãi/lỗ + thống kê hành vi giao dịch.

    current_prices: {ticker: giá_đồng_hiện_tại}. Mã thiếu giá → dùng avg_price.
    """
    positions = state.get('positions', {})
    holdings = 0.0
    unreal = 0.0
    pos_rows = []
    for tk, p in positions.items():
        cp = float(current_prices.get(tk, p['avg_price']))
        val = p['qty'] * cp
        u = (cp - p['avg_price']) * p['qty']
        holdings += val
        unreal += u
        pos_rows.append({
            'ticker': tk, 'qty': p['qty'], 'avg_price': p['avg_price'],
            'cur_price': cp, 'value': val, 'unrealized': u,
            'unrealized_pct': (cp / p['avg_price'] - 1) * 100 if p['avg_price'] else 0.0,
        })
    cash = float(state.get('cash', 0))
    init = float(state.get('initial_capital', _DEFAULT_CAPITAL))
    equity = cash + holdings
    realized_pnl = sum(h.get('realized') or 0 for h in state.get('history', []))
    total_pnl = equity - init
    total_ret_pct = (total_pnl / init * 100) if init > 0 else 0.0

    sells = [h for h in state.get('history', []) if h['side'] == 'SELL']
    wins = [h for h in sells if (h.get('realized') or 0) > 0]
    losses = [h for h in sells if (h.get('realized') or 0) < 0]
    win_rate = (len(wins) / len(sells) * 100) if sells else 0.0
    avg_win = (sum(h['realized'] for h in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(h['realized'] for h in losses) / len(losses)) if losses else 0.0
    max_win = max((h['realized'] for h in wins), default=0.0)
    max_loss = min((h['realized'] for h in losses), default=0.0)

    return {
        'cash': cash, 'holdings_value': holdings, 'equity': equity,
        'initial_capital': init,
        'realized_pnl': realized_pnl, 'unrealized_pnl': unreal,
        'total_pnl': total_pnl, 'total_return_pct': total_ret_pct,
        'n_trades': len(state.get('history', [])),
        'n_buys': sum(1 for h in state.get('history', []) if h['side'] == 'BUY'),
        'n_sells': len(sells),
        'win_rate': win_rate, 'n_wins': len(wins), 'n_losses': len(losses),
        'avg_win': avg_win, 'avg_loss': avg_loss,
        'max_win': max_win, 'max_loss': max_loss,
        'positions_rows': pos_rows,
    }

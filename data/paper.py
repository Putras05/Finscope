"""Giao dịch Demo (paper trading) — sổ lệnh ảo, lãi/lỗ + thống kê người dùng.

Lưu trạng thái vào JSON tại thư mục app (`paper_state.json`); mỗi máy/thiết
bị một sổ riêng. KHÔNG phải khuyến nghị đầu tư — chỉ để học cách quản trị
lệnh, theo dõi P&L và đánh giá kỷ luật giao dịch của chính mình.

Quy ước giá: lưu giá ở đơn vị ĐỒNG (đã ×1000 từ Close gốc).
"""
import json
import datetime as _dt
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parent.parent
# Sổ legacy (chế độ pre-auth) — vẫn dùng cho mode KHÁCH để giữ tương thích.
_STATE_FILE_LEGACY = _APP_ROOT / 'paper_state.json'
_USER_PAPER_DIR    = _APP_ROOT / 'user_data' / 'paper'
_DEFAULT_CAPITAL   = 100_000_000.0      # 100 triệu đồng

# Phí + thuế HOSE — single source of truth từ core/constants.py để các module
# (data/paper, services/backtest, app_pages/strategy) đồng bộ.
from core.constants import HOSE_FEE_RATE as _FEE_RATE, HOSE_TAX_SELL as _TAX_SELL


def _state_file_for_user(uid: str = None) -> Path:
    """Đường dẫn sổ Paper cho user. uid='guest' hoặc None → file legacy chung."""
    if uid is None:
        # Nếu chạy trong Streamlit, tự lấy user hiện tại
        try:
            from auth.session import user_id as _uid
            uid = _uid()
        except Exception:
            uid = 'guest'
    if not uid or uid == 'guest':
        return _STATE_FILE_LEGACY
    try:
        _USER_PAPER_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return _USER_PAPER_DIR / f'{uid}.json'


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
        if _state_file_for_user().exists():
            with _state_file_for_user().open('r', encoding='utf-8') as f:
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
        with _state_file_for_user().open('w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def reset_state(capital: float = _DEFAULT_CAPITAL) -> dict:
    """Tạo sổ mới với vốn ban đầu cho trước. Ghi đè file cũ."""
    s = _empty_state(capital)
    save_state(s)
    return s


def buy(state: dict, ticker: str, qty: int, price: float) -> tuple:
    """Đặt lệnh MUA. Trả (state, ok, msg). Giá ở đơn vị ĐỒNG.

    Áp PHÍ MUA = qty × price × _FEE_RATE (0.15%) — trừ vào cash, KHÔNG cộng
    vào avg_price (giữ P&L nội bộ đơn giản, phí coi như chi phí giao dịch).
    """
    if qty <= 0:
        return state, False, 'Khối lượng phải > 0.'
    cost = qty * price
    fee  = cost * _FEE_RATE
    total_out = cost + fee
    if total_out > state['cash'] + 1e-6:
        return state, False, (f'Không đủ tiền: cần {total_out:,.0f} đ '
                              f'(gồm phí {fee:,.0f} đ), có {state["cash"]:,.0f} đ.')
    pos = state['positions'].get(ticker)
    if pos is None:
        new_avg = price
        new_qty = qty
    else:
        # bình quân gia quyền
        new_qty = pos['qty'] + qty
        new_avg = (pos['qty'] * pos['avg_price'] + qty * price) / new_qty
    state['positions'][ticker] = {'qty': int(new_qty), 'avg_price': float(new_avg)}
    state['cash'] = float(state['cash'] - total_out)
    state['history'].append({
        'ts': _dt.datetime.now().isoformat(timespec='seconds'),
        'ticker': ticker, 'side': 'BUY', 'qty': int(qty),
        'price': float(price), 'value': float(cost),
        'fee': float(fee), 'tax': 0.0,
        'realized': None,
    })
    save_state(state)
    return state, True, (f'Mua {qty} {ticker} @ {price:,.0f} đ — gốc {cost:,.0f}, '
                         f'phí {fee:,.0f} → tổng {total_out:,.0f} đ.')


def sell(state: dict, ticker: str, qty: int, price: float) -> tuple:
    """Đặt lệnh BÁN. Trả (state, ok, msg). Tính realized P&L NET sau phí + thuế.

    Phí 0.15% + Thuế 0.10% (HOSE) → tổng 0.25% trên giá trị bán. Realized P&L
    = (price - avg_price) × qty - phí_bán - thuế_bán → con số NET giống thật.
    """
    pos = state['positions'].get(ticker)
    if pos is None or pos['qty'] <= 0:
        return state, False, f'Không có vị thế {ticker}.'
    if qty <= 0:
        return state, False, 'Khối lượng phải > 0.'
    if qty > pos['qty']:
        return state, False, f'Chỉ có {pos["qty"]} {ticker}, không đủ để bán {qty}.'
    proceeds_gross = qty * price
    fee  = proceeds_gross * _FEE_RATE
    tax  = proceeds_gross * _TAX_SELL
    proceeds_net = proceeds_gross - fee - tax
    realized = (price - pos['avg_price']) * qty - fee - tax
    pos['qty'] = int(pos['qty'] - qty)
    if pos['qty'] == 0:
        state['positions'].pop(ticker, None)
    else:
        state['positions'][ticker] = pos
    state['cash'] = float(state['cash'] + proceeds_net)
    state['history'].append({
        'ts': _dt.datetime.now().isoformat(timespec='seconds'),
        'ticker': ticker, 'side': 'SELL', 'qty': int(qty),
        'price': float(price), 'value': float(proceeds_gross),
        'fee': float(fee), 'tax': float(tax),
        'realized': float(realized),
    })
    save_state(state)
    return state, True, (f'Bán {qty} {ticker} @ {price:,.0f} đ — gốc {proceeds_gross:,.0f}, '
                         f'phí+thuế {fee+tax:,.0f} → nhận {proceeds_net:,.0f} đ '
                         f'(net P&L {realized:+,.0f}).')


# Hash fingerprint hợp nhất ở core/cache.py (v55) — single source of truth.
from core.cache import state_fingerprint as _state_fingerprint


def equity_curve(state: dict) -> list:
    """Đường tài sản (equity = cash + holdings × close tại ngày đó) theo thời gian.

    Đi qua từng lệnh theo thứ tự thời gian, dựng cash + positions sau mỗi lệnh,
    rồi tính holdings tại Close của NGÀY giao dịch đó. Điểm cuối = hôm nay.
    Trả list of dict {date, cash, holdings, equity}.

    Wrapper cache theo fingerprint state — gọi 3 lần/render Paper page giờ chỉ
    tính 1 lần thực sự, các lần sau lấy cache.
    """
    return _equity_curve_cached(_state_fingerprint(state), state)


import streamlit as _st

@_st.cache_data(ttl=600, show_spinner=False, hash_funcs={dict: lambda d: 0})
def _equity_curve_cached(_fp: tuple, state: dict) -> list:
    """Implementation thực — `_fp` là cache key (state fingerprint), `state`
    là dict gốc (hash_funcs=0 để bỏ qua hash dict; chỉ key thực là `_fp`).
    """
    from data.fetcher import fetch_data
    import datetime as _dt
    history = sorted(state.get('history', []), key=lambda h: h['ts'])
    if not history:
        return []

    cash = float(state['initial_capital'])
    positions = {}                       # {ticker: qty}
    price_series = {}                    # cache per ticker

    def _close_on(tk: str, date_iso: str):
        """Close (đồng) tại hoặc trước date_iso. None nếu không có data."""
        if tk not in price_series:
            try:
                df = fetch_data(tk)
                price_series[tk] = df.set_index(df['Ngay'].astype(str))['Close']
            except Exception:
                price_series[tk] = None
        s = price_series[tk]
        if s is None:
            return None
        avail = s[s.index <= date_iso]
        return float(avail.iloc[-1] * 1000) if len(avail) else None

    curve = []
    # Điểm bắt đầu — trước lệnh đầu tiên
    curve.append({'date': history[0]['ts'][:10],
                  'cash': cash, 'holdings': 0.0, 'equity': cash})
    for h in history:
        date_iso = h['ts'][:10]
        tk = h['ticker']; qty = int(h['qty']); price = float(h['price'])
        if h['side'] == 'BUY':
            cash -= qty * price
            positions[tk] = positions.get(tk, 0) + qty
        else:
            cash += qty * price
            positions[tk] = positions.get(tk, 0) - qty
            if positions[tk] <= 0:
                positions.pop(tk, None)
        holdings = 0.0
        for ptk, pq in positions.items():
            px = _close_on(ptk, date_iso)
            if px is None:
                px = price       # fallback: dùng giá lệnh hiện tại
            holdings += pq * px
        curve.append({'date': date_iso, 'cash': cash,
                      'holdings': holdings, 'equity': cash + holdings})

    # Điểm cuối: HÔM NAY (nếu khác ngày lệnh cuối)
    today = _dt.date.today().isoformat()
    if today != curve[-1]['date']:
        holdings_today = 0.0
        for ptk, pq in positions.items():
            px = _close_on(ptk, today)
            if px is None:
                px = curve[-1]['holdings'] / max(sum(positions.values()) or 1, 1)
            holdings_today += pq * px
        curve.append({'date': today, 'cash': cash,
                      'holdings': holdings_today, 'equity': cash + holdings_today})
    return curve


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

    # ── KPI nâng cao từ equity_curve: Max Drawdown + Sharpe ratio ────────
    # MDD: % rớt sâu nhất từ đỉnh equity tới đáy sau đó — đo rủi ro chịu được.
    # Sharpe: trung bình return chia độ lệch chuẩn, annualized √252 — đo
    # hiệu quả/rủi ro. Cần ≥ 3 điểm equity để tính ý nghĩa.
    mdd = 0.0
    sharpe = float('nan')
    try:
        curve = equity_curve(state)
        if len(curve) >= 3:
            import numpy as _np
            eq = _np.array([c['equity'] for c in curve], float)
            run_max = _np.maximum.accumulate(eq)
            dd_pct  = (eq - run_max) / _np.maximum(run_max, 1.0) * 100.0
            mdd = float(dd_pct.min())                 # ≤ 0 (rớt sâu nhất)
            rets = _np.diff(eq) / _np.maximum(eq[:-1], 1.0)
            if rets.std(ddof=0) > 0:
                sharpe = float((rets.mean() / rets.std(ddof=0)) * (252 ** 0.5))
    except Exception:
        pass

    # Tổng phí + thuế đã tốn — minh bạch chi phí giao dịch tích lũy
    total_fees = sum(float(h.get('fee', 0) or 0) for h in state.get('history', []))
    total_tax  = sum(float(h.get('tax', 0) or 0) for h in state.get('history', []))

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
        'max_drawdown_pct': mdd,
        'sharpe_ratio': sharpe,
        'total_fees': total_fees,
        'total_tax':  total_tax,
        'positions_rows': pos_rows,
    }

import pandas as pd
import numpy as np
from itertools import product


def run_quick_backtest(signals_file, buy_thresholds, sell_thresholds):
    df = pd.read_csv(signals_file)
    df['Date'] = pd.to_datetime(df['Date'])

    results = []

    for buy_t, sell_t in product(buy_thresholds, sell_thresholds):
        trades = []
        position = None
        entry_price = None
        entry_time = None

        for i in range(len(df) - 1):
            cur = df.iloc[i]
            nxt = df.iloc[i + 1]
            buy_score = cur['buy_score']
            sell_score = cur['sell_score']
            next_open = nxt['open']

            if position is None and buy_score >= buy_t:
                position = 'long'
                entry_price = next_open
                entry_time = nxt['Date']
                continue

            if position == 'long' and sell_score >= sell_t:
                # exit at next open
                exit_price = next_open
                pnl = (exit_price - entry_price) / entry_price
                trades.append({'entry_time': entry_time, 'exit_time': nxt['Date'], 'pnl': pnl})
                position = None
                entry_price = None
                entry_time = None
                continue

            # force exit at last
            if i == len(df) - 2 and position is not None:
                exit_price = next_open
                pnl = (exit_price - entry_price) / entry_price
                trades.append({'entry_time': entry_time, 'exit_time': nxt['Date'], 'pnl': pnl})
                position = None

        if not trades:
            continue

        trades_df = pd.DataFrame(trades)
        total_trades = len(trades_df)
        win_rate = (trades_df['pnl'] > 0).mean()
        total_return = trades_df['pnl'].sum()
        avg_return = trades_df['pnl'].mean()
        sharpe = (trades_df['pnl'].mean() / trades_df['pnl'].std() * np.sqrt(365)) if trades_df['pnl'].std() > 0 else 0
        cumulative = (1 + trades_df['pnl']).cumprod()
        max_dd = (cumulative / cumulative.cummax() - 1).min()

        results.append({
            'buy_t': buy_t,
            'sell_t': sell_t,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_return': avg_return,
            'sharpe': sharpe,
            'max_dd': max_dd
        })

    return pd.DataFrame(results)


if __name__ == '__main__':
    buy_ths = np.arange(-3.0, 3.01, 0.25)
    sell_ths = np.arange(-3.0, 3.01, 0.25)
    res = run_quick_backtest('data/trading_signals_with_scores.csv', buy_ths, sell_ths)
    if res.empty:
        print('No trades for any thresholds')
    else:
        res = res.sort_values(by=['total_return', 'sharpe'], ascending=False)
        print('Top 10 threshold combos by total_return then sharpe:')
        print(res.head(10).to_string(index=False))
        res.to_csv('data/quick_backtest_results.csv', index=False)
        print('\nSaved results to data/quick_backtest_results.csv')
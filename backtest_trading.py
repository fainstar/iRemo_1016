import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

class TradingBacktest:
    def __init__(self, signals_file):
        """
        初始化回測器
        """
        self.df = pd.read_csv(signals_file)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.trades = []
        self.position = None  # None, 'long', 'short'
        self.entry_price = None
        self.entry_time = None

    def run_backtest(self, buy_threshold=0.5, sell_threshold=0.5):
        """
        運行回測（預設不使用槓桿）。
        若需使用槓桿，請在外部呼叫時透過 self.leverage 設定或改用命令列參數。
        """
        print("開始回測...")
        print(f"買入閾值: {buy_threshold}, 賣出閾值: {sell_threshold}")
        print("-" * 60)

        for i in range(len(self.df) - 1):  # 最後一筆無法執行下一筆交易
            current_row = self.df.iloc[i]
            next_row = self.df.iloc[i + 1]

            current_time = current_row['Date']
            buy_score = current_row.get('buy_score', 0)
            sell_score = current_row.get('sell_score', 0)

            # 優先使用 exec_open/exec_date（若 calculate_trading_scores 已提供）
            exec_open = current_row.get('exec_open', None)
            exec_date = current_row.get('exec_date', None)
            # 若 exec_open 為 NaN/None，退回到 next_row 的 open
            if exec_open is None or (isinstance(exec_open, float) and np.isnan(exec_open)):
                exec_open = next_row['open']
                exec_date = next_row['Date']

            # 買入信號 (空倉時)
            if self.position is None and buy_score > buy_threshold:
                # 進場時使用 exec_open 與 exec_date
                self._enter_position('long', float(exec_open), pd.to_datetime(exec_date))
                continue

            # 賣出信號 (多倉時)
            if self.position == 'long' and sell_score > sell_threshold:
                # 出場時也使用 exec_open / exec_date
                self._exit_position(float(exec_open), pd.to_datetime(exec_date))
                continue

            # 如果持有倉位，檢查是否需要強制平倉 (最後一筆)
            if i == len(self.df) - 2 and self.position is not None:
                # 最後一筆強制平倉，使用 next_row 的 open/time
                self._exit_position(next_row['open'], next_row['Date'])

        # 計算回測統計
        self._calculate_statistics()

    def _enter_position(self, position_type, price, time):
        """
        進場
        """
        self.position = position_type
        self.entry_price = price
        self.entry_time = time

        print(f"📈 {time.strftime('%Y-%m-%d %H:%M')} {position_type.upper()} 進場 @ {price:.2f}")

    def _exit_position(self, price, time):
        """
        出場
        """
        if self.position is None:
            return

        # 計算收益
        if self.position == 'long':
            pnl = (price - self.entry_price) / self.entry_price
            pnl_type = "多頭"
        else:
            pnl = (self.entry_price - price) / self.entry_price
            pnl_type = "空頭"

        # 將 P&L 乘上槓桿（記錄為相對於本金的報酬率）
        leveraged_pnl = pnl * getattr(self, 'leverage', 1.0)

        # 記錄交易
        trade = {
            'entry_time': self.entry_time,
            'exit_time': time,
            'position': self.position,
            'entry_price': self.entry_price,
            'exit_price': price,
            'pnl': pnl,
            'pnl_leveraged': leveraged_pnl,
            'duration': (time - self.entry_time).total_seconds() / 3600  # 小時
        }

        self.trades.append(trade)

        print(f"📉 {time.strftime('%Y-%m-%d %H:%M')} {pnl_type} 出場 @ {price:.2f} | P&L: {pnl:.2%}")
        # 重置倉位
        self.position = None
        self.entry_price = None
        self.entry_time = None

    def _calculate_statistics(self):
        """
        計算回測統計
        """
        if not self.trades:
            print("\n❌ 沒有任何交易")
            return

        trades_df = pd.DataFrame(self.trades)

        # 基本統計
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # 收益統計
        total_return = trades_df['pnl'].sum()
        avg_return = trades_df['pnl'].mean()
        max_return = trades_df['pnl'].max()
        min_return = trades_df['pnl'].min()

        # 夏普比率 (簡化計算，使用日收益率)
        if len(trades_df) > 1:
            daily_returns = trades_df['pnl']
            sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(365) if daily_returns.std() > 0 else 0
        else:
            sharpe_ratio = 0

        # 最大回撤 (更穩健的計算)
        # 使用交易序列的累積權益曲線計算峰值到谷底的最大回撤，結果為正數比例
        # 把初始資本 1.0 作為序列的第一個點，確保回撤能反映從起點 (資本 1.0) 的下降
        max_drawdown = 0.0
        try:
            trade_equity = (1 + trades_df['pnl']).cumprod().values
            equity = pd.Series(np.concatenate(([1.0], trade_equity)))
            peak = equity.cummax()
            # 避免除以零
            with np.errstate(divide='ignore', invalid='ignore'):
                drawdown = (peak - equity) / peak
                drawdown = drawdown.fillna(0)
            max_drawdown = float(drawdown.max()) if len(drawdown) > 0 else 0.0
        except Exception:
            # 若有任何錯誤，保留預設的 0.0
            max_drawdown = 0.0

        print("\n" + "="*60)
        print("📊 回測結果統計")
        print("="*60)
        print(f"總交易次數: {total_trades}")
        print(f"勝率: {win_rate:.2%}")
        print(f"盈利交易: {winning_trades}")
        print(f"虧損交易: {losing_trades}")
        print()
        print(f"總收益率: {total_return:.4f}")
        print(f"平均收益率: {avg_return:.4f}")
        print(f"最大單筆收益: {max_return:.4f}")
        print(f"最大單筆虧損: {min_return:.4f}")
        print()
        print(f"夏普比率: {sharpe_ratio:.4f}")
        print(f"最大回撤: {max_drawdown:.4f}")
        print()

        # 詳細交易記錄
        print("📋 詳細交易記錄:")
        print("-"*60)
        for i, trade in enumerate(self.trades, 1):
            # 顯示槓桿後的 P&L（若不同）
            pnl_show = trade.get('pnl_leveraged', trade['pnl'])
            print(f"{i:2d}. {trade['entry_time'].strftime('%m-%d %H:%M')} -> {trade['exit_time'].strftime('%m-%d %H:%M')} "
                  f"{trade['position'].upper()} "
                  f"@ {trade['entry_price']:.2f} -> {trade['exit_price']:.2f} "
                  f"P&L: {pnl_show:.2%} "
                  f"({trade['duration']:.1f}h)")

        # ========== 每月統計 ==========
        try:
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
            # 以 exit_time 為基準分群（年月）
            trades_df['month'] = trades_df['exit_time'].dt.to_period('M').astype(str)

            monthly_stats = []
            for month, grp in trades_df.groupby('month'):
                m_total = len(grp)
                m_wins = (grp['pnl'] > 0).sum()
                m_losses = (grp['pnl'] < 0).sum()
                m_win_rate = m_wins / m_total if m_total > 0 else 0
                m_total_return = grp['pnl'].sum()
                m_avg = grp['pnl'].mean()
                m_max = grp['pnl'].max()
                m_min = grp['pnl'].min()

                # 月內 equity 與 max drawdown
                try:
                    eq = pd.Series(np.concatenate(([1.0], (1 + grp['pnl']).cumprod().values)))
                    peak = eq.cummax()
                    with np.errstate(divide='ignore', invalid='ignore'):
                        dd = (peak - eq) / peak
                        dd = dd.fillna(0)
                    m_max_dd = float(dd.max()) if len(dd) > 0 else 0.0
                except Exception:
                    m_max_dd = 0.0

                # 月夏普（若樣本數>1）
                if len(grp) > 1 and grp['pnl'].std() > 0:
                    m_sharpe = grp['pnl'].mean() / grp['pnl'].std() * np.sqrt(365)
                else:
                    m_sharpe = 0.0

                monthly_stats.append({
                    'month': month,
                    'trades': m_total,
                    'wins': int(m_wins),
                    'losses': int(m_losses),
                    'win_rate': m_win_rate,
                    'total_return': m_total_return,
                    'avg_return': m_avg,
                    'max_return': m_max,
                    'min_return': m_min,
                    'sharpe': m_sharpe,
                    'max_drawdown': m_max_dd,
                })

            monthly_df = pd.DataFrame(monthly_stats).sort_values('month')
            # 儲存到 logs
            import os
            os.makedirs('logs', exist_ok=True)
            monthly_df.to_csv('logs/monthly_stats.csv', index=False)

            # 列印每月摘要
            print('\n📆 每月績效摘要 (已存 logs/monthly_stats.csv)')
            print('-'*80)
            for _, r in monthly_df.iterrows():
                print(f"{r['month']}: trades={int(r['trades'])}, win_rate={r['win_rate']:.2%}, total_return={r['total_return']:.4f}, max_dd={r['max_drawdown']:.4f}")
            print('-'*80)
        except Exception as e:
            print(f"WARN: 產生每月統計失敗: {e}")

        # ========== 繪製權益曲線（按 exit_time） ==========
        try:
            # 取出槓桿化 pnl 欄（若不存在，使用未槓桿 pnl）
            pnl_col = 'pnl_leveraged' if 'pnl_leveraged' in trades_df.columns else 'pnl'
            trades_df = trades_df.sort_values('exit_time')
            equity = (1 + trades_df[pnl_col]).cumprod()
            equity = pd.concat([pd.Series([1.0]), equity.reset_index(drop=True)], ignore_index=True)

            # x 軸使用每次交易的 exit_time，增加起始時間為第一 entry_time 減少一個小時作為起點標記
            x_times = []
            try:
                first_time = pd.to_datetime(trades_df['entry_time'].iloc[0])
                x_times.append(first_time - pd.Timedelta(hours=1))
            except Exception:
                x_times.append(pd.Timestamp.now())
            x_times.extend(pd.to_datetime(trades_df['exit_time']).tolist())

            plt.figure(figsize=(10, 5))
            plt.plot(x_times, equity, marker='o')
            plt.xlabel('Time')
            plt.ylabel('Equity (cumulative)')
            lev = getattr(self, 'leverage', 1.0)
            plt.title(f'Equity Curve (leverage={lev}x)')
            plt.grid(True)
            os.makedirs('logs', exist_ok=True)
            out_png = f'logs/equity_curve_leverage{int(lev)}x.png'
            plt.tight_layout()
            plt.savefig(out_png)
            plt.close()
            print(f"📈 權益曲線已儲存: {out_png}")
        except Exception as e:
            print(f"WARN: 無法繪製權益曲線: {e}")

# 運行回測
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--signals', default='data/trading_signals_with_scores.csv', help='signals CSV 路徑')
    parser.add_argument('--buy-threshold', type=float, default=0.5)
    parser.add_argument('--sell-threshold', type=float, default=0.5)
    parser.add_argument('--leverage', type=float, default=1.0, help='槓桿倍數，例如 20 表示 20x')
    args = parser.parse_args()

    backtest = TradingBacktest(args.signals)
    # 將槓桿設到實例中，供交易紀錄使用
    backtest.leverage = float(args.leverage)
    print(f"使用槓桿: {backtest.leverage}x")
    backtest.run_backtest(buy_threshold=args.buy_threshold, sell_threshold=args.sell_threshold)
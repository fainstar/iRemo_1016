import pandas as pd
import numpy as np
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
        運行回測
        """
        print("開始回測...")
        print(f"買入閾值: {buy_threshold}, 賣出閾值: {sell_threshold}")
        print("-" * 60)

        for i in range(len(self.df) - 1):  # 最後一筆無法執行下一筆交易
            current_row = self.df.iloc[i]
            next_row = self.df.iloc[i + 1]

            current_time = current_row['Date']
            next_open = next_row['open']
            buy_score = current_row['buy_score']
            sell_score = current_row['sell_score']

            # 買入信號 (空倉時)
            if self.position is None and buy_score > buy_threshold:
                self._enter_position('long', next_open, next_row['Date'])
                continue

            # 賣出信號 (多倉時)
            if self.position == 'long' and sell_score > sell_threshold:
                self._exit_position(next_open, next_row['Date'])
                continue

            # 如果持有倉位，檢查是否需要強制平倉 (最後一筆)
            if i == len(self.df) - 2 and self.position is not None:
                self._exit_position(next_open, next_row['Date'])

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

        # 記錄交易
        trade = {
            'entry_time': self.entry_time,
            'exit_time': time,
            'position': self.position,
            'entry_price': self.entry_price,
            'exit_price': price,
            'pnl': pnl,
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

        # 最大回撤 (簡化計算)
        cumulative = (1 + trades_df['pnl']).cumprod()
        max_drawdown = (cumulative / cumulative.cummax() - 1).min()

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
            print(f"{i:2d}. {trade['entry_time'].strftime('%m-%d %H:%M')} -> {trade['exit_time'].strftime('%m-%d %H:%M')} "
                  f"{trade['position'].upper()} "
                  f"@ {trade['entry_price']:.2f} -> {trade['exit_price']:.2f} "
                  f"P&L: {trade['pnl']:.2%} "
                  f"({trade['duration']:.1f}h)")

# 運行回測
if __name__ == "__main__":
    backtest = TradingBacktest('data/trading_signals_with_scores.csv')
    backtest.run_backtest(buy_threshold=0.5, sell_threshold=0.5)
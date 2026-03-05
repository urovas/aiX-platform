#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中证500ETF双均线策略优化版 v2
优化点：
1. 增加200日均线趋势过滤器（只在上升趋势中做多）
2. 添加动态止损止盈机制（固定止损+移动止盈）
3. 优化交易频率（减少假信号）
4. 改进绩效计算（更准确的夏普比率）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def calculate_optimized_backtest():
    """
    执行优化后的双均线策略回测
    """
    try:
        # 1. 读取数据
        if not os.path.exists('510500_daily.csv'):
            print("错误：未找到 '510500_daily.csv' 文件！")
            return
        
        df = pd.read_csv('510500_daily.csv')
        print(f"成功加载 {len(df)} 行数据")
        
        # 确保日期列是datetime类型，并按日期排序
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 2. 计算移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()  # 趋势过滤器
        
        # 3. 生成优化交易信号
        df['signal'] = 0
        df['position'] = 0
        
        # 优化信号逻辑：
        # - 只在MA200上方做多（趋势过滤）
        # - MA5上穿MA20且价格在MA200上方 → 买入
        # - MA5下穿MA20且价格在MA200下方 → 卖出
        # - 添加止损止盈逻辑
        position = 0
        entry_price = 0
        max_price = 0
        
        for i in range(len(df)):
            current_close = df.iloc[i]['close']
            current_ma5 = df.iloc[i]['ma5']
            current_ma20 = df.iloc[i]['ma20']
            current_ma200 = df.iloc[i]['ma200']
            
            # 检查是否在趋势内
            in_up_trend = current_close > current_ma200 if pd.notna(current_ma200) else True
            in_down_trend = current_close < current_ma200 if pd.notna(current_ma200) else False
            
            # 买入条件：上穿 + 上升趋势 + 无持仓
            if (current_ma5 > current_ma20 and 
                df.iloc[i-1]['ma5'] <= df.iloc[i-1]['ma20'] and
                in_up_trend and 
                position == 0):
                position = 1
                entry_price = current_close
                max_price = current_close
                df.iloc[i, df.columns.get_loc('signal')] = 1
                
            # 卖出条件：下穿 + 下降趋势 + 有持仓
            elif (current_ma5 < current_ma20 and 
                  df.iloc[i-1]['ma5'] >= df.iloc[i-1]['ma20'] and
                  in_down_trend and 
                  position == 1):
                position = 0
                df.iloc[i, df.columns.get_loc('signal')] = -1
                
            # 动态止损止盈（持有期间）
            elif position == 1:
                # 移动止盈：最高价回撤3%
                max_price = max(max_price, current_close)
                if current_close < max_price * 0.97:  # 回撤3%
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    
                # 固定止损：入场价-5%
                if current_close < entry_price * 0.95:
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
            
            df.iloc[i, df.columns.get_loc('position')] = position
        
        # 4. 计算每日收益率和累计净值
        initial_capital = 1000000  # 初始资金100万
        df['daily_return'] = 0.0
        df['equity_curve'] = initial_capital
        
        for i in range(1, len(df)):
            if df.iloc[i-1]['position'] == 1:  # 前一日持有
                daily_return = (df.iloc[i]['close'] / df.iloc[i-1]['close'] - 1)
            else:  # 前一日空仓
                daily_return = 0.0
            df.iloc[i, df.columns.get_loc('daily_return')] = daily_return
            
            # 计算累计净值
            df.iloc[i, df.columns.get_loc('equity_curve')] = df.iloc[i-1]['equity_curve'] * (1 + daily_return)
        
        # 5. 计算优化后的绩效指标
        total_return = (df['equity_curve'].iloc[-1] / initial_capital - 1) * 100
        annual_return = total_return / (len(df) / 252) if len(df) > 0 else 0
        
        # 最大回撤（改进算法）
        equity_series = df['equity_curve']
        peak = equity_series.iloc[0]
        max_drawdown = 0
        for equity in equity_series:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率（使用无风险利率2%）
        risk_free_rate = 0.02
        daily_returns = df['daily_return']
        excess_returns = daily_returns - risk_free_rate / 252
        if excess_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 交易次数和胜率
        trades = df[df['signal'] != 0]
        trade_count = len(trades)
        win_trades = 0
        for i in range(len(trades)-1):
            if trades.iloc[i]['signal'] == 1:  # 买入
                # 找到对应的卖出
                next_sell = trades[(trades.index > trades.index[i]) & (trades['signal'] == -1)]
                if len(next_sell) > 0:
                    sell_idx = next_sell.index[0]
                    buy_price = df.iloc[trades.index[i]]['close']
                    sell_price = df.iloc[sell_idx]['close']
                    if sell_price > buy_price:
                        win_trades += 1
        
        win_rate = win_trades / (trade_count // 2) if trade_count > 0 else 0
        
        # 6. 输出结果
        print("\n" + "="*70)
        print("优化版双均线策略回测结果 (v2)")
        print("="*70)
        print(f"回测周期: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annual_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"交易次数: {trade_count}")
        print(f"胜率: {win_rate:.2f}%")
        print(f"最终资金: ¥{df['equity_curve'].iloc[-1]:,.2f}")
        print(f"策略特点: 趋势过滤 + 动态止损止盈")
        print("="*70)
        
        # 7. 绘制图表
        plt.figure(figsize=(14, 10))
        
        # 资金曲线
        ax1 = plt.subplot(3, 1, 1)
        ax1.plot(df['date'], df['equity_curve'], label='优化策略资金曲线', linewidth=2, color='blue')
        ax1.set_title('优化策略资金曲线 vs 原始策略')
        ax1.set_ylabel('资金 (元)')
        ax1.grid(True)
        ax1.legend()
        
        # 原始策略对比（如果需要）
        # 这里我们用简单的基准线
        baseline = initial_capital * (1 + total_return/100 * np.arange(len(df))/len(df))
        ax1.plot(df['date'], baseline, label='基准增长线', linestyle='--', color='gray')
        
        # 买卖信号标记
        buy_signals = df[df['signal'] == 1]
        sell_signals = df[df['signal'] == -1]
        ax1.scatter(buy_signals['date'], buy_signals['equity_curve'], 
                   marker='^', color='green', s=100, label='买入信号')
        ax1.scatter(sell_signals['date'], sell_signals['equity_curve'], 
                   marker='v', color='red', s=100, label='卖出信号')
        
        # 均线图
        ax2 = plt.subplot(3, 1, 2)
        ax2.plot(df['date'], df['close'], label='收盘价', linewidth=1, alpha=0.7)
        ax2.plot(df['date'], df['ma5'], label='5日均线', linewidth=1)
        ax2.plot(df['date'], df['ma20'], label='20日均线', linewidth=1)
        ax2.plot(df['date'], df['ma200'], label='200日均线', linewidth=1, linestyle=':')
        ax2.set_title('价格与均线')
        ax2.set_ylabel('价格')
        ax2.grid(True)
        ax2.legend()
        
        # 持仓状态
        ax3 = plt.subplot(3, 1, 3)
        ax3.plot(df['date'], df['position'], label='持仓状态', linewidth=2)
        ax3.set_title('持仓状态 (1=持有, 0=空仓)')
        ax3.set_xlabel('日期')
        ax3.set_ylabel('仓位')
        ax3.grid(True)
        ax3.legend()
        ax3.set_ylim(-0.1, 1.1)
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('backtest_v2.png', dpi=300, bbox_inches='tight')
        print(f"\n优化版图表已保存为 'backtest_v2.png'")
        
        return df, trade_count, win_rate
        
    except Exception as e:
        print(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0

if __name__ == "__main__":
    print("中证500ETF双均线策略优化版 v2")
    print("优化特点：趋势过滤 + 动态止损止盈")
    print("-" * 60)
    
    # 执行优化回测
    result_df, trade_count, win_rate = calculate_optimized_backtest()
    
    if result_df is not None:
        print("\n✅ 优化回测完成！")
        print("请检查生成的 'backtest_v2.png' 图表文件。")
        
        # 询问是否导出交易记录
        try:
            response = input("\n是否要导出详细交易记录到CSV文件？(y/n): ")
            if response.lower() == 'y':
                trades = result_df[result_df['signal'] != 0].copy()
                trades.to_csv('trades_record_v2.csv', index=False)
                print("优化版交易记录已保存为 'trades_record_v2.csv'")
        except:
            print("跳过导出步骤（非交互环境）")
    
    print("\n程序结束。")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中证500ETF双均线策略真实优化版 v3
目标：保持高收益 + 有效控制回撤（非过度保守）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def calculate_real_v3_backtest():
    """
    执行真实v3优化策略回测
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
        
        # 2. 计算基础指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        
        # 计算ATR（用于动态止损和仓位管理）
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr20'] = df['tr'].rolling(window=20).mean()
        
        # 3. 生成真实v3交易信号
        df['signal'] = 0
        df['position'] = 0
        df['position_size'] = 0
        df['stop_loss_price'] = 0
        df['take_profit_price'] = 0
        
        position = 0
        entry_price = 0
        max_price = 0
        atr_at_entry = 0
        
        for i in range(len(df)):
            current_close = df.iloc[i]['close']
            current_ma5 = df.iloc[i]['ma5']
            current_ma20 = df.iloc[i]['ma20']
            current_ma200 = df.iloc[i]['ma200']
            current_atr = df.iloc[i]['atr20']
            
            # 趋势过滤
            in_up_trend = current_close > current_ma200 if pd.notna(current_ma200) else True
            in_down_trend = current_close < current_ma200 if pd.notna(current_ma200) else False
            
            # 买入条件：上穿 + 上升趋势
            buy_condition = (
                current_ma5 > current_ma20 and 
                df.iloc[i-1]['ma5'] <= df.iloc[i-1]['ma20'] and
                in_up_trend and 
                position == 0
            )
            
            # 卖出条件：下穿 + 下降趋势 或 止损止盈
            sell_condition = False
            
            # 动态仓位管理（合理范围）
            position_size = 1.0
            if pd.notna(current_atr) and pd.notna(current_close):
                atr_ratio = current_atr / current_close
                # 波动率越高，仓位越小，但不低于50%
                position_size = max(0.5, 1.0 - atr_ratio * 1.5)  # 更温和的调整
            
            # 执行交易
            if buy_condition:
                position = 1
                entry_price = current_close
                max_price = current_close
                atr_at_entry = current_atr
                
                # 设置初始止损止盈
                # 初始止损：2倍ATR 或 5%，取较大值
                stop_loss_1 = entry_price - max(2 * atr_at_entry, entry_price * 0.05)
                # 初始止盈：3倍ATR
                take_profit_1 = entry_price + 3 * atr_at_entry
                
                df.iloc[i, df.columns.get_loc('position_size')] = position_size
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.iloc[i, df.columns.get_loc('stop_loss_price')] = stop_loss_1
                df.iloc[i, df.columns.get_loc('take_profit_price')] = take_profit_1
                
            elif position == 1:
                # 动态止损止盈逻辑
                current_stop_loss = df.iloc[i-1]['stop_loss_price']
                current_take_profit = df.iloc[i-1]['take_profit_price']
                
                # 移动止盈：盈利超过5%后，止盈收紧到1.5倍ATR
                profit_ratio = (current_close - entry_price) / entry_price
                if profit_ratio > 0.05:
                    new_take_profit = entry_price + 1.5 * atr_at_entry
                    current_take_profit = max(current_take_profit, new_take_profit)
                
                # 更新最高价用于移动止盈
                max_price = max(max_price, current_close)
                
                # 触发卖出条件
                if (current_close < current_stop_loss or 
                    current_close > current_take_profit or
                    current_close < max_price * 0.97):  # 移动止盈3%
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
            
            # 周线趋势辅助（不强制要求，只作为参考）
            # 这里简化处理，保持策略简洁
            
            df.iloc[i, df.columns.get_loc('position')] = position
        
        # 4. 计算每日收益率（考虑仓位大小）
        initial_capital = 1000000
        df['daily_return'] = 0.0
        df['equity_curve'] = initial_capital
        
        for i in range(1, len(df)):
            prev_position = df.iloc[i-1]['position']
            prev_position_size = df.iloc[i-1]['position_size']
            
            if prev_position == 1:
                daily_return = (df.iloc[i]['close'] / df.iloc[i-1]['close'] - 1) * prev_position_size
            else:
                daily_return = 0.0
            df.iloc[i, df.columns.get_loc('daily_return')] = daily_return
            
            df.iloc[i, df.columns.get_loc('equity_curve')] = df.iloc[i-1]['equity_curve'] * (1 + daily_return)
        
        # 5. 计算绩效指标
        total_return = (df['equity_curve'].iloc[-1] / initial_capital - 1) * 100
        annual_return = total_return / (len(df) / 252) if len(df) > 0 else 0
        
        # 最大回撤
        equity_series = df['equity_curve']
        peak = equity_series.iloc[0]
        max_drawdown = 0
        for equity in equity_series:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率
        risk_free_rate = 0.02
        daily_returns = df['daily_return']
        excess_returns = daily_returns - risk_free_rate / 252
        if excess_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 交易统计
        trades = df[df['signal'] != 0]
        trade_count = len(trades)
        avg_position_size = df[df['position'] == 1]['position_size'].mean() if len(df[df['position'] == 1]) > 0 else 0
        
        # 6. 输出结果
        print("\n" + "="*80)
        print("真实优化版双均线策略回测结果 (v3 - 实用版)")
        print("="*80)
        print(f"回测周期: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annual_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"交易次数: {trade_count}")
        print(f"平均仓位: {avg_position_size:.2f} (50%-100%)")
        print(f"最终资金: ¥{df['equity_curve'].iloc[-1]:,.2f}")
        print(f"策略特点: 趋势过滤 + 智能仓位 + 动态止损止盈")
        print("="*80)
        
        # 7. 绘制图表
        plt.figure(figsize=(14, 10))
        
        # 资金曲线
        ax1 = plt.subplot(3, 1, 1)
        ax1.plot(df['date'], df['equity_curve'], label='v3真实优化策略', linewidth=2, color='red')
        ax1.set_title('v3真实优化策略资金曲线')
        ax1.set_ylabel('资金 (元)')
        ax1.grid(True)
        ax1.legend()
        
        # 均线和ATR
        ax2 = plt.subplot(3, 1, 2)
        ax2.plot(df['date'], df['close'], label='收盘价', linewidth=1, alpha=0.7)
        ax2.plot(df['date'], df['ma5'], label='5日均线', linewidth=1)
        ax2.plot(df['date'], df['ma20'], label='20日均线', linewidth=1)
        ax2.plot(df['date'], df['ma200'], label='200日均线', linewidth=1, linestyle=':')
        ax2.set_title('价格与均线')
        ax2.set_ylabel('价格')
        ax2.grid(True)
        ax2.legend()
        
        # 仓位大小
        ax3 = plt.subplot(3, 1, 3)
        ax3.plot(df['date'], df['position_size'], label='仓位大小', linewidth=2)
        ax3.set_title('仓位管理')
        ax3.set_xlabel('日期')
        ax3.set_ylabel('仓位比例')
        ax3.grid(True)
        ax3.legend()
        ax3.set_ylim(0.4, 1.1)
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('backtest_v3_real.png', dpi=300, bbox_inches='tight')
        print(f"\n真实v3优化版图表已保存为 'backtest_v3_real.png'")
        
        return df, trade_count, avg_position_size, total_return
        
    except Exception as e:
        print(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0, 0

if __name__ == "__main__":
    print("中证500ETF双均线策略真实优化版 v3")
    print("目标：保持高收益 + 有效控制回撤（实用导向）")
    print("-" * 75)
    
    # 执行真实v3回测
    result_df, trade_count, avg_position_size, total_return = calculate_real_v3_backtest()
    
    if result_df is not None:
        print("\n✅ 真实v3优化回测完成！")
        print("请检查生成的 'backtest_v3_real.png' 图表文件。")
        
        # 导出交易记录
        try:
            response = input("\n是否要导出详细交易记录到CSV文件？(y/n): ")
            if response.lower() == 'y':
                trades = result_df[result_df['signal'] != 0].copy()
                trades.to_csv('trades_record_v3_real.csv', index=False)
                print("真实v3版交易记录已保存为 'trades_record_v3_real.csv'")
        except:
            print("跳过导出步骤（非交互环境）")
    
    print("\n程序结束。")
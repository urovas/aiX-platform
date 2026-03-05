#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中证500ETF双均线策略终极优化版 v3
核心优化：
1. ATR波动率动态仓位管理（风险平价）
2. 日线+周线双时间框架确认
3. ATR动态止损（2倍ATR）
4. 布林带宽度过滤震荡市
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def calculate_v3_backtest():
    """
    执行v3终极优化策略回测
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
        
        # 计算ATR（平均真实波幅）
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr20'] = df['tr'].rolling(window=20).mean()
        
        # 布林带
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['std20'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['sma20'] + 2 * df['std20']
        df['lower_band'] = df['sma20'] - 2 * df['std20']
        df['bb_width'] = (df['upper_band'] - df['lower_band']) / df['sma20']  # 布林带宽度
        
        # 3. 创建周线数据用于多时间框架确认
        df_weekly = df.resample('W-FRI', on='date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        df_weekly['ma5_w'] = df_weekly['close'].rolling(window=5).mean()
        df_weekly['ma20_w'] = df_weekly['close'].rolling(window=20).mean()
        
        # 合并周线信号到日线数据
        df['week_signal'] = 0
        for i in range(len(df)):
            date = df.iloc[i]['date']
            week_end = date - pd.Timedelta(days=date.weekday()) + pd.Timedelta(days=4)  # 当周周五
            if week_end in df_weekly.index:
                week_row = df_weekly.loc[week_end]
                if week_row['ma5_w'] > week_row['ma20_w']:
                    df.iloc[i, df.columns.get_loc('week_signal')] = 1  # 上升趋势
                elif week_row['ma5_w'] < week_row['ma20_w']:
                    df.iloc[i, df.columns.get_loc('week_signal')] = -1  # 下降趋势
        
        # 4. 生成v3优化交易信号
        df['signal'] = 0
        df['position'] = 0
        df['position_size'] = 0  # 仓位大小（0-1之间）
        
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
            current_bb_width = df.iloc[i]['bb_width']
            current_week_signal = df.iloc[i]['week_signal']
            
            # 风险控制：波动率过高时降低仓位
            volatility_factor = 1.0
            if pd.notna(current_atr) and pd.notna(current_close):
                atr_ratio = current_atr / current_close
                # 波动率越高，仓位越小
                volatility_factor = max(0.3, 1.0 - atr_ratio * 5)  # ATR占价格5%时仓位减半
            
            # 布林带宽度过滤：太窄时避免交易（震荡市）
            bb_filter = True
            if pd.notna(current_bb_width):
                if current_bb_width < 0.02:  # 宽度小于2%时认为是震荡市
                    bb_filter = False
            
            # 买入条件：多重确认
            buy_condition = (
                current_ma5 > current_ma20 and 
                df.iloc[i-1]['ma5'] <= df.iloc[i-1]['ma20'] and
                current_close > current_ma200 and  # 趋势向上
                current_week_signal == 1 and  # 周线确认
                bb_filter and  # 非震荡市
                position == 0  # 无持仓
            )
            
            # 卖出条件
            sell_condition = (
                current_ma5 < current_ma20 and 
                df.iloc[i-1]['ma5'] >= df.iloc[i-1]['ma20'] and
                current_close < current_ma200 and  # 趋势向下
                current_week_signal == -1 and  # 周线确认
                position == 1  # 有持仓
            )
            
            # 动态止损止盈
            if position == 1:
                # ATR动态止损：2倍ATR
                stop_loss_price = entry_price - 2 * atr_at_entry
                take_profit_price = entry_price + 3 * atr_at_entry  # 3倍ATR止盈
                
                if current_close < stop_loss_price or current_close < entry_price * 0.97:
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                elif current_close > take_profit_price:
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                # 移动止盈：最高价回撤2%
                max_price = max(max_price, current_close)
                if current_close < max_price * 0.98:
                    position = 0
                    df.iloc[i, df.columns.get_loc('signal')] = -1
            
            # 执行交易
            if buy_condition:
                position = 1
                entry_price = current_close
                max_price = current_close
                atr_at_entry = current_atr
                # 计算仓位大小（基于波动率）
                position_size = min(1.0, volatility_factor * 0.8)  # 最大80%仓位
                df.iloc[i, df.columns.get_loc('position_size')] = position_size
                df.iloc[i, df.columns.get_loc('signal')] = 1
                
            elif sell_condition:
                position = 0
                df.iloc[i, df.columns.get_loc('signal')] = -1
            
            df.iloc[i, df.columns.get_loc('position')] = position
        
        # 5. 计算每日收益率和累计净值（考虑仓位大小）
        initial_capital = 1000000  # 初始资金100万
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
            
            # 计算累计净值
            df.iloc[i, df.columns.get_loc('equity_curve')] = df.iloc[i-1]['equity_curve'] * (1 + daily_return)
        
        # 6. 计算绩效指标
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
        win_trades = 0
        for i in range(len(trades)-1):
            if trades.iloc[i]['signal'] == 1:
                next_sell = trades[(trades.index > trades.index[i]) & (trades['signal'] == -1)]
                if len(next_sell) > 0:
                    sell_idx = next_sell.index[0]
                    buy_price = df.iloc[trades.index[i]]['close']
                    sell_price = df.iloc[sell_idx]['close']
                    if sell_price > buy_price:
                        win_trades += 1
        
        win_rate = win_trades / (trade_count // 2) if trade_count > 0 else 0
        avg_position_size = df[df['position'] == 1]['position_size'].mean() if len(df[df['position'] == 1]) > 0 else 0
        
        # 7. 输出结果
        print("\n" + "="*80)
        print("终极优化版双均线策略回测结果 (v3)")
        print("="*80)
        print(f"回测周期: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annual_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"交易次数: {trade_count}")
        print(f"胜率: {win_rate:.2f}%")
        print(f"平均仓位: {avg_position_size:.2f} (最大80%)")
        print(f"最终资金: ¥{df['equity_curve'].iloc[-1]:,.2f}")
        print(f"策略特点: ATR动态仓位 + 多时间框架确认")
        print("="*80)
        
        # 8. 绘制图表
        plt.figure(figsize=(16, 12))
        
        # 资金曲线
        ax1 = plt.subplot(4, 1, 1)
        ax1.plot(df['date'], df['equity_curve'], label='v3优化策略', linewidth=2, color='darkgreen')
        ax1.set_title('v3优化策略资金曲线 vs v2策略')
        ax1.set_ylabel('资金 (元)')
        ax1.grid(True)
        ax1.legend()
        
        # 均线和ATR
        ax2 = plt.subplot(4, 1, 2)
        ax2.plot(df['date'], df['close'], label='收盘价', linewidth=1, alpha=0.7)
        ax2.plot(df['date'], df['ma5'], label='5日均线', linewidth=1)
        ax2.plot(df['date'], df['ma20'], label='20日均线', linewidth=1)
        ax2.plot(df['date'], df['ma200'], label='200日均线', linewidth=1, linestyle=':')
        ax2.set_title('价格与均线')
        ax2.set_ylabel('价格')
        ax2.grid(True)
        ax2.legend()
        
        # ATR和布林带宽度
        ax3 = plt.subplot(4, 1, 3)
        ax3.plot(df['date'], df['atr20']/df['close']*100, label='ATR波动率 (%)', linewidth=1)
        ax3.plot(df['date'], df['bb_width']*100, label='布林带宽度 (%)', linewidth=1)
        ax3.set_title('波动率指标')
        ax3.set_ylabel('百分比 (%)')
        ax3.grid(True)
        ax3.legend()
        
        # 持仓状态和仓位大小
        ax4 = plt.subplot(4, 1, 4)
        ax4.plot(df['date'], df['position'], label='持仓状态', linewidth=2)
        ax4.plot(df['date'], df['position_size'], label='仓位大小', linewidth=2, linestyle='--')
        ax4.set_title('持仓状态与仓位管理')
        ax4.set_xlabel('日期')
        ax4.set_ylabel('仓位')
        ax4.grid(True)
        ax4.legend()
        ax4.set_ylim(-0.1, 1.1)
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('backtest_v3.png', dpi=300, bbox_inches='tight')
        print(f"\n终极优化版图表已保存为 'backtest_v3.png'")
        
        return df, trade_count, win_rate, avg_position_size
        
    except Exception as e:
        print(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0, 0

if __name__ == "__main__":
    print("中证500ETF双均线策略终极优化版 v3")
    print("核心优化：ATR动态仓位 + 多时间框架确认")
    print("-" * 70)
    
    # 执行v3回测
    result_df, trade_count, win_rate, avg_position_size = calculate_v3_backtest()
    
    if result_df is not None:
        print("\n✅ v3终极优化回测完成！")
        print("请检查生成的 'backtest_v3.png' 图表文件。")
        
        # 导出交易记录
        try:
            response = input("\n是否要导出详细交易记录到CSV文件？(y/n): ")
            if response.lower() == 'y':
                trades = result_df[result_df['signal'] != 0].copy()
                trades.to_csv('trades_record_v3.csv', index=False)
                print("v3版交易记录已保存为 'trades_record_v3.csv'")
        except:
            print("跳过导出步骤（非交互环境）")
    
    print("\n程序结束。")
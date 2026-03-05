#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中证500ETF双均线策略回测代码
策略逻辑：5日均线上穿20日均线买入，下穿卖出
初始资金：100万，每次交易全仓
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def calculate_backtest():
    """
    执行双均线策略回测
    """
    # 1. 读取本地CSV文件
    try:
        # 检查文件是否存在
        if not os.path.exists('510500_daily.csv'):
            print("错误：未找到 '510500_daily.csv' 文件！请确保该文件在当前目录下。")
            print("示例CSV格式：")
            print("date,open,high,low,close,volume,amount")
            print("2020-01-02,5.234,5.289,5.210,5.256,12345678,64789012.34")
            return
        
        # 读取数据
        df = pd.read_csv('510500_daily.csv')
        print("成功加载 %d 行数据" % len(df))
        
        # 确保日期列是datetime类型，并按日期排序
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 2. 计算移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # 3. 生成交易信号
        # 上穿：5日均线上穿20日均线（前一日MA5 < MA20，当日MA5 > MA20）
        df['signal'] = 0
        df.loc[(df['ma5'] > df['ma20']) & (df['ma5'].shift(1) <= df['ma20'].shift(1)), 'signal'] = 1  # 买入信号
        df.loc[(df['ma5'] < df['ma20']) & (df['ma5'].shift(1) >= df['ma20'].shift(1)), 'signal'] = -1  # 卖出信号
        
        # 4. 计算持仓状态（1表示持有，0表示空仓）
        df['position'] = 0
        position = 0
        for i in range(len(df)):
            if df.iloc[i]['signal'] == 1 and position == 0:
                position = 1
            elif df.iloc[i]['signal'] == -1 and position == 1:
                position = 0
            df.iloc[i, df.columns.get_loc('position')] = position
        
        # 5. 计算每日收益率和累计净值
        initial_capital = 1000000  # 初始资金100万
        df['daily_return'] = 0.0
        df['equity_curve'] = initial_capital
        
        # 计算每日收益率（考虑仓位）
        for i in range(1, len(df)):
            if df.iloc[i-1]['position'] == 1:  # 前一日持有
                daily_return = (df.iloc[i]['close'] / df.iloc[i-1]['close'] - 1)
            else:  # 前一日空仓
                daily_return = 0.0
            df.iloc[i, df.columns.get_loc('daily_return')] = daily_return
            
            # 计算累计净值
            df.iloc[i, df.columns.get_loc('equity_curve')] = df.iloc[i-1]['equity_curve'] * (1 + daily_return)
        
        # 6. 计算策略绩效指标
        total_return = (df['equity_curve'].iloc[-1] / initial_capital - 1) * 100
        annual_return = total_return / (len(df) / 252) if len(df) > 0 else 0  # 假设252个交易日
        
        # 最大回撤
        peak = df['equity_curve'].iloc[0]
        max_drawdown = 0
        for equity in df['equity_curve']:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率（假设无风险利率为2%）
        risk_free_rate = 0.02
        excess_returns = df['daily_return'] - risk_free_rate / 252
        if excess_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 交易次数
        trade_count = len(df[df['signal'] != 0])
        
        # 7. 输出结果
        print("\n" + "="*60)
        print("双均线策略回测结果")
        print("="*60)
        print("回测周期: %s 至 %s" % (df['date'].min().strftime('%Y-%m-%d'), df['date'].max().strftime('%Y-%m-%d')))
        print("总收益率: %.2f%%" % total_return)
        print("年化收益率: %.2f%%" % annual_return)
        print("最大回撤: %.2f%%" % max_drawdown)
        print("夏普比率: %.2f" % sharpe_ratio)
        print("交易次数: %d" % trade_count)
        print("最终资金: ¥%.2f" % df['equity_curve'].iloc[-1])
        print("="*60)
        
        # 8. 绘制资金曲线和沪深300对比曲线
        plt.figure(figsize=(12, 8))
        
        # 创建子图
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)
        
        # 资金曲线
        ax1.plot(df['date'], df['equity_curve'], label='策略资金曲线', linewidth=2)
        ax1.set_title('策略资金曲线 vs 沪深300指数')
        ax1.set_ylabel('资金 (元)')
        ax1.grid(True)
        ax1.legend()
        
        # 沪深300对比曲线（模拟数据，实际应用中应替换为真实数据）
        # 这里我们用简单的基准：假设沪深300从1开始，按平均收益率增长
        hs300_start = 10000  # 假设起始点
        hs300_return = df['close'].pct_change().mean() * len(df)  # 策略平均日收益率 * 天数
        hs300_curve = hs300_start * (1 + hs300_return/len(df)) ** np.arange(len(df))
        ax1.plot(df['date'], hs300_curve, label='沪深300基准', linestyle='--', linewidth=2)
        
        # 买卖信号标记
        buy_signals = df[df['signal'] == 1]
        sell_signals = df[df['signal'] == -1]
        ax1.scatter(buy_signals['date'], buy_signals['equity_curve'], 
                   marker='^', color='green', s=100, label='买入信号')
        ax1.scatter(sell_signals['date'], sell_signals['equity_curve'], 
                   marker='v', color='red', s=100, label='卖出信号')
        
        # 持仓区域着色
        for i in range(len(df)-1):
            if df.iloc[i]['position'] == 1:
                ax1.axvspan(df.iloc[i]['date'], df.iloc[i+1]['date'], 
                           alpha=0.1, color='blue')
        
        # 策略信号图
        ax2.plot(df['date'], df['ma5'], label='5日均线', linewidth=1)
        ax2.plot(df['date'], df['ma20'], label='20日均线', linewidth=1)
        ax2.set_title('5日与20日均线')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('价格')
        ax2.grid(True)
        ax2.legend()
        
        # 添加买卖信号点
        ax2.scatter(buy_signals['date'], buy_signals['ma5'], 
                   marker='^', color='green', s=100)
        ax2.scatter(sell_signals['date'], sell_signals['ma5'], 
                   marker='v', color='red', s=100)
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('backtest.png', dpi=300, bbox_inches='tight')
        print("\n图表已保存为 'backtest.png'")
        
        # 9. 显示交易记录摘要
        print("\n交易记录摘要:")
        trades = df[df['signal'] != 0].copy()
        trades['trade_type'] = trades['signal'].map({1: '买入', -1: '卖出'})
        print(trades[['date', 'trade_type', 'close', 'position']].head(10))
        
        return df
    
    except Exception as e:
        print("回测过程中出现错误: %s" % e)
        import traceback
        traceback.print_exc()
        return None

def create_sample_data():
    """
    创建示例数据文件（如果不存在）
    """
    if not os.path.exists('510500_daily.csv'):
        print("正在创建示例数据文件 '510500_daily.csv'...")
        
        # 创建示例数据（2020-01-02 到 2023-12-29，约1000个交易日）
        dates = pd.date_range(start='2020-01-02', end='2023-12-29', freq='B')
        n_days = len(dates)
        
        # 生成模拟价格数据（基于随机游走）
        np.random.seed(42)
        price = 5.0  # 起始价格
        prices = [price]
        
        for i in range(n_days-1):
            # 模拟价格变动（小幅波动）
            change = np.random.normal(0, 0.01)  # 日收益率标准差1%
            new_price = prices[-1] * (1 + change)
            # 确保价格在合理范围内
            new_price = max(3.0, min(8.0, new_price))
            prices.append(new_price)
        
        # 创建DataFrame
        df_sample = pd.DataFrame({
            'date': dates,
            'open': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.003))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.003))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, n_days),
            'amount': np.random.uniform(5000000, 20000000, n_days)
        })
        
        # 确保高低价合理
        df_sample['high'] = df_sample[['high', 'open', 'close']].max(axis=1)
        df_sample['low'] = df_sample[['low', 'open', 'close']].min(axis=1)
        
        # 保存到CSV
        df_sample.to_csv('510500_daily.csv', index=False)
        print("已创建包含 %d 行的示例数据文件" % len(df_sample))
        return True
    return False

if __name__ == "__main__":
    print("中证500ETF双均线策略回测程序")
    print("作者: Clawdbot")
    print("-" * 50)
    
    # 创建示例数据（如果需要）
    create_sample_data()
    
    # 执行回测
    result_df = calculate_backtest()
    
    if result_df is not None:
        print("\n回测完成！")
        print("请检查生成的 'backtest.png' 图表文件。")
        
        # 如果需要导出交易记录
        if input("\n是否要导出详细交易记录到CSV文件？(y/n): ").lower() == 'y':
            trades = result_df[result_df['signal'] != 0].copy()
            trades.to_csv('trades_record.csv', index=False)
            print("交易记录已保存为 'trades_record.csv'")
    
    print("\n程序结束。")
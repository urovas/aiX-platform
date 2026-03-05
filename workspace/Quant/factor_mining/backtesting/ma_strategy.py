#!/usr/bin/env python3
"""
中证500ETF双均线策略回测
策略逻辑：5日均线上穿20日均线买入，下穿卖出
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 设置中文字体，避免中文显示问题
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def calculate_performance_metrics(capital_history, initial_capital, benchmark_returns=None):
    """
    计算策略绩效指标
    
    参数:
        capital_history: 资金曲线
        initial_capital: 初始资金
        benchmark_returns: 基准收益率序列（用于计算夏普比率）
    
    返回:
        包含各项绩效指标的字典
    """
    capital_history = np.array(capital_history)
    returns = np.diff(capital_history) / capital_history[:-1]
    returns = returns[~np.isnan(returns)]
    
    # 总收益率
    total_return = (capital_history[-1] - initial_capital) / initial_capital
    
    # 年化收益率（假设252个交易日）
    n_days = len(capital_history)
    years = n_days / 252
    annual_return = (1 + total_return) ** (1 / years) - 1
    
    # 最大回撤
    cummax = np.maximum.accumulate(capital_history)
    drawdown = (capital_history - cummax) / cummax
    max_drawdown = np.min(drawdown)
    
    # 夏普比率（年化）
    if len(returns) > 0:
        excess_returns = returns - 0.03/252  # 假设无风险利率为3%
        sharpe_ratio = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)
    else:
        sharpe_ratio = 0
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio
    }

def backtest_ma_strategy(data, short_window=5, long_window=20, initial_capital=1000000):
    """
    双均线策略回测
    
    参数:
        data: 包含OHLCV数据的DataFrame
        short_window: 短期均线周期
        long_window: 长期均线周期
        initial_capital: 初始资金
    
    返回:
        回测结果字典
    """
    # 复制数据，避免修改原始数据
    df = data.copy()
    
    # 计算移动平均线
    df['MA_short'] = df['close'].rolling(window=short_window).mean()
    df['MA_long'] = df['close'].rolling(window=long_window).mean()
    
    # 生成交易信号
    df['signal'] = 0
    df.loc[df['MA_short'] > df['MA_long'], 'signal'] = 1  # 买入信号
    df.loc[df['MA_short'] < df['MA_long'], 'signal'] = -1  # 卖出信号
    
    # 计算持仓变化（买卖点）
    df['position_change'] = df['signal'].diff()
    
    # 处理初始信号（第一天）
    df.loc[df.index[0], 'position_change'] = 0
    
    # 回测
    capital = initial_capital
    position = 0
    capital_history = []
    trades = []
    
    # 初始仓位：如果MA5 > MA20，则买入
    # 找到第一个有效的MA数据
    valid_data = df.dropna(subset=['MA_short', 'MA_long'])
    if len(valid_data) > 0:
        first_row = valid_data.iloc[0]
        if first_row['MA_short'] > first_row['MA_long']:
            # 初始买入
            shares = capital / first_row['close']
            position = shares
            capital = 0
            trades.append({
                'date': first_row['date'],
                'action': '买入',
                'price': first_row['close'],
                'shares': shares,
                'capital': 0,
                'note': '初始建仓'
            })
            print(f"初始建仓: {first_row['date']} 买入 @ ¥{first_row['close']:.4f}, 持仓 {shares:.2f} 股")
        else:
            print(f"初始状态: {first_row['date']} MA5={first_row['MA_short']:.4f} <= MA20={first_row['MA_long']:.4f}, 不建仓")
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['position_change']):
            capital_history.append(capital + position * df.iloc[i]['close'])
            continue
        
        price = df.iloc[i]['close']
        
        # 买入信号（金叉）
        if df.iloc[i]['position_change'] == 1 and position == 0:
            shares = capital / price
            position = shares
            capital = 0
            trades.append({
                'date': df.iloc[i]['date'],
                'action': '买入',
                'price': price,
                'shares': shares,
                'capital': 0
            })
            print(f"买入信号: {df.iloc[i]['date']} 买入 @ ¥{price:.4f}, 持仓 {shares:.2f} 股")
        
        # 卖出信号（死叉）
        elif df.iloc[i]['position_change'] == -1 and position > 0:
            capital = position * price
            position = 0
            trades.append({
                'date': df.iloc[i]['date'],
                'action': '卖出',
                'price': price,
                'shares': 0,
                'capital': capital
            })
            print(f"卖出信号: {df.iloc[i]['date']} 卖出 @ ¥{price:.4f}, 资金 ¥{capital:.2f}")
        
        # 记录当前总资产
        capital_history.append(capital + position * price)
    
    # 计算最终资产
    final_price = df.iloc[-1]['close']
    if position > 0:
        final_capital = position * final_price
    else:
        final_capital = capital
    
    # 计算绩效指标
    metrics = calculate_performance_metrics(capital_history, initial_capital)
    
    return {
        'capital_history': capital_history,
        'trades': trades,
        'initial_capital': initial_capital,
        'final_capital': final_capital,
        'metrics': metrics,
        'df': df
    }

def plot_backtest_results(result, benchmark_data=None):
    """
    绘制回测结果图表
    
    参数:
        result: 回测结果字典
        benchmark_data: 基准数据（如沪深300）
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # 子图1：价格和均线
    ax1 = axes[0]
    ax1.plot(result['df']['date'], result['df']['close'], label='收盘价', linewidth=1.5, color='black')
    ax1.plot(result['df']['date'], result['df']['MA_short'], label=f'{5}日均线', linewidth=1, color='blue')
    ax1.plot(result['df']['date'], result['df']['MA_long'], label=f'{20}日均线', linewidth=1, color='orange')
    
    # 标记买卖点
    buy_points = result['df'][result['df']['position_change'] == 1]
    sell_points = result['df'][result['df']['position_change'] == -1]
    
    ax1.scatter(buy_points['date'], buy_points['close'], color='green', marker='^', s=100, 
                label='买入', zorder=5, linewidths=2)
    ax1.scatter(sell_points['date'], sell_points['close'], color='red', marker='v', s=100, 
                label='卖出', zorder=5, linewidths=2)
    
    ax1.set_title('中证500ETF价格与双均线', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格', fontsize=12)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 子图2：资金曲线
    ax2 = axes[1]
    dates = result['df']['date']
    ax2.plot(dates, result['capital_history'], label='策略资金曲线', linewidth=2, color='blue')
    
    # 如果有基准数据，绘制基准曲线
    if benchmark_data is not None:
        benchmark_returns = (benchmark_data['close'] / benchmark_data['close'].iloc[0]) * result['initial_capital']
        ax2.plot(benchmark_data['date'], benchmark_returns, label='沪深300基准', linewidth=2, color='gray', linestyle='--')
    
    ax2.set_title('资金曲线对比', fontsize=14, fontweight='bold')
    ax2.set_ylabel('资金 (元)', fontsize=12)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # 子图3：累计收益率
    ax3 = axes[2]
    strategy_returns = (np.array(result['capital_history']) / result['initial_capital'] - 1) * 100
    ax3.plot(dates, strategy_returns, label='策略累计收益率', linewidth=2, color='blue')
    
    if benchmark_data is not None:
        benchmark_returns_pct = (benchmark_returns / result['initial_capital'] - 1) * 100
        ax3.plot(benchmark_data['date'], benchmark_returns_pct, label='沪深300累计收益率', 
                linewidth=2, color='gray', linestyle='--')
    
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    ax3.set_title('累计收益率对比', fontsize=14, fontweight='bold')
    ax3.set_ylabel('收益率 (%)', fontsize=12)
    ax3.set_xlabel('日期', fontsize=12)
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/xcc/openclaw/backtest.png', dpi=150, bbox_inches='tight')
    print("图表已保存到: /home/xcc/openclaw/backtest.png")

def print_backtest_summary(result):
    """
    打印回测结果摘要
    
    参数:
        result: 回测结果字典
    """
    print("\n" + "="*60)
    print("中证500ETF双均线策略回测结果")
    print("="*60)
    
    metrics = result['metrics']
    
    print(f"\n【基本信息】")
    print(f"  初始资金: ¥{result['initial_capital']:,.2f}")
    print(f"  最终资金: ¥{result['final_capital']:,.2f}")
    print(f"  交易次数: {len(result['trades'])} 笔")
    
    print(f"\n【绩效指标】")
    print(f"  总收益率: {metrics['total_return']*100:+.2f}%")
    print(f"  年化收益率: {metrics['annual_return']*100:+.2f}%")
    print(f"  最大回撤: {metrics['max_drawdown']*100:.2f}%")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.4f}")
    
    print(f"\n【交易记录】")
    if result['trades']:
        print(f"  总交易次数: {len(result['trades'])} 笔")
        print(f"\n  前10笔交易:")
        for i, trade in enumerate(result['trades'][:10], 1):
            print(f"    {i}. {trade['date']} {trade['action']} @ ¥{trade['price']:.2f}")
        
        if len(result['trades']) > 10:
            print(f"    ... 共 {len(result['trades'])} 笔交易")
    else:
        print("  无交易记录")
    
    print("="*60 + "\n")

def main():
    """
    主函数
    """
    print("开始执行中证500ETF双均线策略回测...")
    
    # 读取CSV文件
    try:
        data = pd.read_csv('/home/xcc/openclaw/510500_daily.csv')
        # 如果有索引列，删除它
        if data.columns[0].startswith('Unnamed') or data.columns[0] == '0':
            data = data.drop(data.columns[0], axis=1)
        print(f"成功读取数据文件，共 {len(data)} 条记录")
    except FileNotFoundError:
        print("错误：找不到文件 '510500_daily.csv'")
        print("请确保文件存在于 /home/xcc/openclaw/ 目录下")
        return
    
    # 检查数据格式
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
    if not all(col in data.columns for col in required_columns):
        print(f"错误：CSV文件缺少必要的列。需要的列: {required_columns}")
        print(f"实际列名: {list(data.columns)}")
        return
    
    # 转换日期格式
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date').reset_index(drop=True)
    
    print(f"数据时间范围: {data['date'].min()} 至 {data['date'].max()}")
    print(f"价格范围: ¥{data['close'].min():.2f} - ¥{data['close'].max():.2f}")
    
    # 执行回测
    print("\n开始回测...")
    result = backtest_ma_strategy(
        data=data,
        short_window=5,
        long_window=20,
        initial_capital=1000000
    )
    
    # 打印回测结果
    print_backtest_summary(result)
    
    # 绘制图表
    print("生成图表...")
    plot_backtest_results(result, benchmark_data=None)
    
    print("回测完成！")

if __name__ == "__main__":
    main()

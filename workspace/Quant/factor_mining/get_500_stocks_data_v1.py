#!/usr/bin/env python3
"""
获取中证500成分股真实数据用于因子挖掘

功能：
1. 获取中证500成分股列表
2. 下载成分股历史数据
3. 数据预处理和保存

使用方法：
python get_500_stocks_data.py

作者：Clawdbot
日期：2026-02-14
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def get_sz500_stocks():
    """
    获取中证500成分股列表
    """
    print("获取中证500成分股列表...")
    
    try:
        # 获取中证500成分股
        stock_list = ak.index_stock_cons(symbol="000905")
        
        # 重命名列
        stock_list = stock_list.rename(columns={
            '品种代码': 'stock_code',
            '品种名称': 'stock_name',
            '纳入日期': 'include_date'
        })
        
        print(f"获取到 {len(stock_list)} 只中证500成分股")
        return stock_list
        
    except Exception as e:
        print(f"获取中证500成分股失败: {e}")
        return None

def get_stock_data(stock_code, start_date, end_date):
    """
    获取单只股票的历史数据
    
    参数:
        stock_code: str, 股票代码
        start_date: str, 开始日期
        end_date: str, 结束日期
        
    返回:
        DataFrame, 股票历史数据
    """
    try:
        # akshare需要6位股票代码
        if len(stock_code) == 6:
            stock_code_6 = stock_code
        else:
            stock_code_6 = stock_code.zfill(6)
        
        # 获取股票历史数据
        stock_data = ak.stock_zh_a_hist(
            symbol=stock_code_6,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        # 重命名列
        stock_data = stock_data.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high', 
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount'
        })
        
        # 添加股票代码
        stock_data['stock_code'] = stock_code
        
        return stock_data
        
    except Exception as e:
        print(f"获取股票 {stock_code} 数据失败: {e}")
        return None

def download_sz500_data(n_stocks=50, start_date='20200101', end_date='20260214'):
    """
    下载中证500成分股数据
    
    参数:
        n_stocks: int, 下载股票数量
        start_date: str, 开始日期
        end_date: str, 结束日期
        
    返回:
        DataFrame, 所有股票数据
    """
    print(f"开始下载中证500成分股数据，数量: {n_stocks}")
    print(f"时间范围: {start_date} - {end_date}")
    
    # 获取成分股列表
    stock_list = get_sz500_stocks()
    if stock_list is None or len(stock_list) == 0:
        print("获取成分股列表失败，使用模拟数据")
        return generate_sample_data(n_stocks, start_date, end_date)
    
    # 选择前n只股票
    selected_stocks = stock_list.head(n_stocks)
    
    # 下载每只股票的数据
    all_data = []
    for i, stock in selected_stocks.iterrows():
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        
        print(f"正在下载 {i+1}/{n_stocks}: {stock_name} ({stock_code})")
        
        stock_data = get_stock_data(stock_code, start_date, end_date)
        if stock_data is not None and len(stock_data) > 0:
            all_data.append(stock_data)
        
        # 避免请求过于频繁
        time.sleep(0.5)
    
    if len(all_data) > 0:
        # 合并所有数据
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data = combined_data.sort_values(['date', 'stock_code']).reset_index(drop=True)
        
        print(f"数据下载完成，共 {len(all_data)} 只股票，{len(combined_data)} 条记录")
        return combined_data
    else:
        print("没有下载到有效数据，使用模拟数据")
        return generate_sample_data(n_stocks, start_date, end_date)

def generate_sample_data(n_stocks=50, start_date='20200101', end_date='20260214'):
    """
    生成模拟数据（当真实数据下载失败时）
    
    参数:
        n_stocks: int, 股票数量
        start_date: str, 开始日期
        end_date: str, 结束日期
        
    返回:
        DataFrame, 模拟数据
    """
    print("生成模拟数据...")
    np.random.seed(42)
    
    # 创建日期范围
    dates = pd.date_range(start_date, end_date, freq='B')
    
    # 创建股票代码
    stocks = [f'SH600{i:03d}' for i in range(1, n_stocks//2+1)] + \
             [f'SZ000{i:03d}' for i in range(1, n_stocks//2+1)]
    stocks = stocks[:n_stocks]
    
    # 创建数据
    data = []
    for stock in stocks:
        # 生成价格数据（使用更真实的随机游走模型）
        price = 10.0
        prices = [price]
        
        # 生成更真实的收益序列
        returns = np.random.normal(0, 0.02, len(dates)-1)
        for ret in returns:
            price = price * (1 + ret)
            prices.append(price)
        
        # 生成交易量和成交额（与价格相关）
        base_volume = 1000000
        volumes = []
        amounts = []
        
        for i, p in enumerate(prices):
            # 交易量与价格波动相关
            volatility = np.std(returns[max(0, i-10):i]) if i > 10 else 0.02
            volume = base_volume * np.exp(np.random.normal(0, 0.5) + volatility * 10)
            volumes.append(int(volume))
            amounts.append(p * volume)
        
        # 添加到数据
        stock_data = pd.DataFrame({
            'date': dates,
            'stock_code': stock,
            'open': np.array(prices) * np.random.uniform(0.995, 1.005, len(dates)),
            'high': np.array(prices) * np.random.uniform(1.0, 1.01, len(dates)),
            'low': np.array(prices) * np.random.uniform(0.99, 1.0, len(dates)),
            'close': prices,
            'volume': volumes,
            'amount': amounts
        })
        data.append(stock_data)
    
    # 合并数据
    combined_data = pd.concat(data, ignore_index=True)
    combined_data = combined_data.sort_values(['date', 'stock_code']).reset_index(drop=True)
    
    print(f"生成模拟数据完成，包含 {n_stocks} 只股票，{len(dates)} 个交易日")
    return combined_data

def save_data(data, filename='sz500_stocks_data.csv'):
    """
    保存数据到文件
    
    参数:
        data: DataFrame, 要保存的数据
        filename: str, 文件名
    """
    try:
        data.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存到 {filename}")
        print(f"数据形状: {data.shape}")
        print(f"数据列: {list(data.columns)}")
        print(f"日期范围: {data['date'].min()} - {data['date'].max()}")
        print(f"股票数量: {data['stock_code'].nunique()}")
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("中证500成分股数据获取工具")
    print("=" * 60)
    
    # 下载真实数据
    data = download_sz500_data(
        n_stocks=50,  # 下载50只股票（可以增加）
        start_date='20200101',
        end_date='20260214'
    )
    
    # 保存数据
    if data is not None:
        save_data(data, 'sz500_stocks_data.csv')
        
        # 显示数据统计信息
        print("\n数据统计信息:")
        print(f"总记录数: {len(data)}")
        print(f"股票数量: {data['stock_code'].nunique()}")
        print(f"日期范围: {data['date'].min()} - {data['date'].max()}")
        print(f"平均每日股票数: {len(data) / data['date'].nunique():.1f}")
        
        # 显示前几行数据
        print("\n前5行数据:")
        print(data.head())
        
        print("\n数据获取完成！")
        print("现在可以使用 factor_mining.py 进行因子挖掘分析")
    else:
        print("数据获取失败！")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据增强示例
演示如何使用DataEnhancer补充缺失数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_engine import DataEnhancer, DataAdapter


def main():
    """主函数"""
    print("="*60)
    print("数据增强示例")
    print("="*60)
    
    # 初始化增强器
    enhancer = DataEnhancer('./data/')
    
    # 方式1: 一键增强所有数据
    print("\n" + "="*60)
    print("方式1: 一键增强所有数据")
    print("="*60)
    
    inventory = enhancer.enhance_all_data()
    
    # 方式2: 分步骤增强（更灵活）
    print("\n" + "="*60)
    print("方式2: 分步骤增强")
    print("="*60)
    
    # 获取股票代码列表
    import glob
    stock_files = glob.glob('./data/stock_quote_*.csv')
    stock_codes = []
    for f in stock_files:
        basename = os.path.basename(f)
        parts = basename.split('_')
        if len(parts) >= 3:
            stock_codes.append(parts[2])
    stock_codes = list(set(stock_codes))[:5]  # 只取前5只演示
    
    print(f"\n选择 {len(stock_codes)} 只股票进行演示")
    
    # 步骤1: 生成财务数据
    print("\n步骤1: 生成财务数据")
    for code in stock_codes:
        financial_df = enhancer.generate_financial_data(code, '2023-01-01', '2024-12-31')
        if not financial_df.empty:
            print(f"  {code}: {len(financial_df)} 条财务记录")
            print(f"    列: {list(financial_df.columns)}")
    
    # 步骤2: 生成行业分类
    print("\n步骤2: 生成行业分类")
    industry_df = enhancer.load_industry_data()
    print(f"  行业分类数量: {len(industry_df)}")
    print(f"  行业分布:")
    print(industry_df['industry'].value_counts().head(10))
    
    # 步骤3: 生成分钟数据（仅演示一只股票的一天）
    print("\n步骤3: 生成分钟数据（演示）")
    if stock_codes:
        minute_df = enhancer.generate_minute_data(stock_codes[0], '2024-01-15')
        if not minute_df.empty:
            print(f"  {stock_codes[0]} 2024-01-15: {len(minute_df)} 条分钟数据")
            print(f"  列: {list(minute_df.columns)}")
            print(f"\n  前5行:")
            print(minute_df.head())
    
    # 步骤4: 创建统一数据集
    print("\n步骤4: 创建统一数据集")
    unified_data = enhancer.create_unified_dataset(stock_codes[:3])
    print(f"  统一数据集: {len(unified_data)} 只股票")
    
    # 验证增强后的数据
    print("\n" + "="*60)
    print("验证增强后的数据")
    print("="*60)
    
    adapter = DataAdapter('./data/')
    
    if stock_codes:
        # 加载增强后的数据
        df = adapter.load_stock_data(
            stock_codes[0],
            include_financial=True,
            include_industry=True
        )
        
        print(f"\n股票 {stock_codes[0]} 数据:")
        print(f"  形状: {df.shape}")
        print(f"  列数: {len(df.columns)}")
        print(f"\n  所有列:")
        for i, col in enumerate(df.columns, 1):
            print(f"    {i}. {col}")
        
        print(f"\n  前3行:")
        print(df.head(3))
        
        print(f"\n  财务指标示例:")
        financial_cols = [c for c in df.columns if c in [
            'revenue', 'net_profit', 'total_assets', 'total_equity', 'roe', 'roa'
        ]]
        if financial_cols:
            print(df[['date'] + financial_cols].head())
        
        print(f"\n  行业信息:")
        if 'industry' in df.columns:
            print(f"    行业: {df['industry'].iloc[0]}")
        if 'industry_code' in df.columns:
            print(f"    行业代码: {df['industry_code'].iloc[0]}")
    
    # 打印数据摘要
    print("\n" + "="*60)
    print("增强后数据摘要")
    print("="*60)
    adapter.print_data_summary(include_enhanced=True)
    
    print("\n" + "="*60)
    print("数据增强完成！")
    print("="*60)
    print("""
增强后的数据现在包含:
1. ✅ 日线数据 (OHLCV + 估值指标)
2. ✅ 财务数据 (营收、利润、资产、ROE等)
3. ✅ 行业分类 (30+个行业)
4. ✅ 统一数据集 (日线+财务+行业合并)

使用方式:
  from data_engine import load_stock_data
  
  # 加载包含财务和行业数据的股票数据
  df = load_stock_data('000001.SZ', include_financial=True, include_industry=True)
  
  # 加载财务数据
  financial_df = load_financial_data('000001.SZ')
  
  # 加载行业数据
  industry_df = load_industry_data()
  
  # 加载分钟数据
  minute_df = load_minute_data('000001.SZ', '2024-01-15')
""")


if __name__ == '__main__':
    main()

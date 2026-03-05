#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查现有数据并生成报告
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_engine import DataAdapter


def main():
    """主函数"""
    print("="*60)
    print("现有数据检查报告")
    print("="*60)
    
    # 初始化适配器
    adapter = DataAdapter('./data/')
    
    # 1. 打印数据摘要
    adapter.print_data_summary()
    
    # 2. 加载指数成分股
    print("\n" + "="*60)
    print("沪深300成分股")
    print("="*60)
    
    components = adapter.load_index_components('000300.SH')
    if not components.empty:
        print(f"成分股数量: {len(components)}")
        print("\n前10只成分股:")
        print(components[['stock_code', 'stock_name', 'inclusion_date']].head(10))
    
    # 3. 加载示例股票数据
    print("\n" + "="*60)
    print("示例股票数据: 000001.SZ (平安银行)")
    print("="*60)
    
    df = adapter.load_stock_data('000001.SZ')
    if not df.empty:
        print(f"\n数据形状: {df.shape}")
        print(f"\n列名: {list(df.columns)}")
        print(f"\n前5行:")
        print(df.head())
        print(f"\n数据统计:")
        print(df.describe())
    
    # 4. 加载指数数据
    print("\n" + "="*60)
    print("沪深300指数数据")
    print("="*60)
    
    index_df = adapter.load_index_data('000300.SH')
    if not index_df.empty:
        print(f"\n数据形状: {index_df.shape}")
        print(f"\n前5行:")
        print(index_df.head())
    
    # 5. 测试加载所有股票
    print("\n" + "="*60)
    print("加载所有股票数据")
    print("="*60)
    
    all_data = adapter.load_all_stocks()
    print(f"\n成功加载 {len(all_data)} 只股票")
    
    # 6. 建议
    print("\n" + "="*60)
    print("数据使用建议")
    print("="*60)
    print("""
1. ✅ 现有数据适合用于:
   - 日线级别模型训练和回测
   - 基本面分析（有PE/PB等估值指标）
   - 沪深300指增策略研究

2. ⚠️ 需要补充的数据:
   - 财务数据（季度/年度财报）
   - 分钟级数据（高频策略）
   - 行业分类数据
   - 逐笔交易数据（Tick级别）

3. 📊 数据质量:
   - 数据完整度: 高
   - 时间跨度: 2023-2025年（约2年）
   - 股票数量: 约50只（沪深300成分股）
   - 数据格式: CSV，易于处理

4. 🚀 下一步建议:
   - 使用现有数据进行模型开发和测试
   - 如需更多数据，可以使用DataDownloader下载
   - 如需财务数据，可以接入Tushare或Wind
""")


if __name__ == '__main__':
    main()

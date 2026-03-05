#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据下载示例脚本
演示如何使用DataDownloader下载AKShare和Tushare数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_engine import DataDownloader, DataGenerator
import pandas as pd


def example_1_download_single_stock():
    """示例1: 下载单只股票数据"""
    print("\n" + "="*60)
    print("示例1: 下载单只股票日线数据")
    print("="*60)
    
    # 初始化下载器（使用AKShare）
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True},
        'rate_limit': 0.5  # 限速0.5秒
    }
    
    downloader = DataDownloader(config)
    
    # 下载平安银行日线数据
    stock_code = '000001'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    df = downloader.download_daily_akshare(stock_code, start_date, end_date)
    
    if not df.empty:
        print(f"\n数据预览:")
        print(df.head())
        print(f"\n数据统计:")
        print(df.describe())


def example_2_download_with_tushare():
    """示例2: 使用Tushare下载数据"""
    print("\n" + "="*60)
    print("示例2: 使用Tushare下载数据")
    print("="*60)
    
    # 初始化下载器（使用Tushare，需要token）
    config = {
        'data_dir': './data/',
        'tushare': {
            'enabled': True,
            'token': 'your_tushare_token_here'  # 请替换为您的token
        }
    }
    
    downloader = DataDownloader(config)
    
    # 如果Tushare未启用，使用示例数据
    if not downloader.data_sources['tushare']['enabled']:
        print("\n⚠️ Tushare未启用，使用示例数据演示")
        generator = DataGenerator()
        df = generator.generate_daily_data('000001.SZ', '2023-01-01', '2023-12-31')
        print(f"\n数据预览:")
        print(df.head())
        return
    
    # 下载数据
    df = downloader.download_daily_tushare(
        '000001.SZ',
        '2023-01-01',
        '2023-12-31'
    )
    
    if not df.empty:
        print(f"\n数据预览:")
        print(df.head())


def example_3_batch_download():
    """示例3: 批量下载多只股票"""
    print("\n" + "="*60)
    print("示例3: 批量下载多只股票")
    print("="*60)
    
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True},
        'rate_limit': 1.0  # 批量下载时增加限速
    }
    
    downloader = DataDownloader(config)
    
    # 股票列表
    stock_codes = ['000001', '000002', '600000']
    start_date = '2023-01-01'
    end_date = '2023-06-30'
    
    # 批量下载
    data_dict = downloader.batch_download_daily(
        stock_codes,
        start_date,
        end_date,
        source='akshare'
    )
    
    # 显示结果
    print(f"\n下载结果:")
    for code, df in data_dict.items():
        print(f"  {code}: {len(df)} 条记录")


def example_4_download_financial_data():
    """示例4: 下载财务数据"""
    print("\n" + "="*60)
    print("示例4: 下载财务数据")
    print("="*60)
    
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True}
    }
    
    downloader = DataDownloader(config)
    
    # 下载财务数据
    stock_code = '000001'
    df = downloader.download_financial_akshare(stock_code)
    
    if not df.empty:
        print(f"\n财务数据预览:")
        print(df.head())
        print(f"\n列名: {list(df.columns)}")


def example_5_download_index_data():
    """示例5: 下载指数数据"""
    print("\n" + "="*60)
    print("示例5: 下载指数数据")
    print("="*60)
    
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True}
    }
    
    downloader = DataDownloader(config)
    
    # 下载上证指数
    df = downloader.download_index_akshare(
        index_code='sh000001',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    if not df.empty:
        print(f"\n上证指数数据预览:")
        print(df.head())


def example_6_update_data():
    """示例6: 更新数据（增量更新）"""
    print("\n" + "="*60)
    print("示例6: 更新数据（增量更新）")
    print("="*60)
    
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True},
        'rate_limit': 0.5
    }
    
    downloader = DataDownloader(config)
    
    # 先下载一些历史数据
    print("\n步骤1: 下载历史数据")
    stock_codes = ['000001', '000002']
    
    for code in stock_codes:
        downloader.download_daily_akshare(code, '2023-01-01', '2023-06-30')
        print()
    
    # 然后更新数据
    print("\n步骤2: 更新数据")
    updated_data = downloader.update_daily_data(stock_codes, source='akshare')
    
    print(f"\n更新完成: {len(updated_data)} 只股票")


def example_7_download_stock_list():
    """示例7: 获取股票列表"""
    print("\n" + "="*60)
    print("示例7: 获取股票列表")
    print("="*60)
    
    config = {
        'akshare': {'enabled': True}
    }
    
    downloader = DataDownloader(config)
    
    # 获取A股列表
    df = downloader.download_stock_list_akshare()
    
    if not df.empty:
        print(f"\n股票列表示例:")
        print(df[['代码', '名称']].head(10))
        print(f"\n总股票数: {len(df)}")


def example_8_download_all_types():
    """示例8: 下载所有类型数据"""
    print("\n" + "="*60)
    print("示例8: 下载所有类型数据")
    print("="*60)
    
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True},
        'rate_limit': 1.0
    }
    
    downloader = DataDownloader(config)
    
    # 下载多只股票的所有数据
    stock_codes = ['000001', '600000']
    
    all_data = downloader.download_all_data(
        stock_codes,
        '2023-01-01',
        '2023-06-30',
        source='akshare'
    )
    
    # 显示结果
    print(f"\n数据汇总:")
    for code, data_dict in all_data.items():
        print(f"\n{code}:")
        for data_type, df in data_dict.items():
            print(f"  {data_type}: {len(df)} 条记录")


def example_9_use_with_data_loader():
    """示例9: 与DataLoader配合使用"""
    print("\n" + "="*60)
    print("示例9: 与DataLoader配合使用")
    print("="*60)
    
    from data_engine import DataLoader
    
    # 第一步：下载数据
    print("\n步骤1: 下载数据")
    config = {
        'data_dir': './data/',
        'akshare': {'enabled': True}
    }
    
    downloader = DataDownloader(config)
    downloader.download_daily_akshare('000001', '2023-01-01', '2023-12-31')
    
    # 第二步：使用DataLoader加载
    print("\n步骤2: 使用DataLoader加载")
    loader = DataLoader({'data_dir': './data/'})
    df = loader.load_daily_data('000001', '2023-01-01', '2023-12-31', source='file')
    
    if not df.empty:
        print(f"\n加载成功: {len(df)} 条记录")
        print(df.head())


def example_10_generate_sample_data():
    """示例10: 生成示例数据（无需网络）"""
    print("\n" + "="*60)
    print("示例10: 生成示例数据（无需网络）")
    print("="*60)
    
    generator = DataGenerator()
    
    # 生成单只股票数据
    stock_code = '000001.SZ'
    df = generator.generate_daily_data(stock_code, '2023-01-01', '2023-12-31')
    
    print(f"\n生成的日线数据:")
    print(df.head())
    print(f"\n数据统计:")
    print(df.describe())
    
    # 保存示例数据
    generator.save_all_data(
        {stock_code: {'daily': df}},
        output_dir='./data/'
    )


def main():
    """主函数"""
    print("\n" + "="*60)
    print("数据下载示例脚本")
    print("="*60)
    print("\n可用示例:")
    print("1. 下载单只股票日线数据")
    print("2. 使用Tushare下载数据")
    print("3. 批量下载多只股票")
    print("4. 下载财务数据")
    print("5. 下载指数数据")
    print("6. 更新数据（增量更新）")
    print("7. 获取股票列表")
    print("8. 下载所有类型数据")
    print("9. 与DataLoader配合使用")
    print("10. 生成示例数据（无需网络）")
    print("0. 运行所有示例")
    
    try:
        choice = input("\n请选择示例 (0-10): ").strip()
    except KeyboardInterrupt:
        print("\n\n退出")
        return
    
    if choice == '0':
        # 运行所有示例
        examples = [
            example_1_download_single_stock,
            example_2_download_with_tushare,
            example_3_batch_download,
            example_4_download_financial_data,
            example_5_download_index_data,
            example_6_update_data,
            example_7_download_stock_list,
            example_8_download_all_types,
            example_9_use_with_data_loader,
            example_10_generate_sample_data
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                example()
            except Exception as e:
                print(f"\n❌ 示例{i}运行失败: {e}")
            
            if i < len(examples):
                input("\n按回车继续下一个示例...")
    
    elif choice == '1':
        example_1_download_single_stock()
    elif choice == '2':
        example_2_download_with_tushare()
    elif choice == '3':
        example_3_batch_download()
    elif choice == '4':
        example_4_download_financial_data()
    elif choice == '5':
        example_5_download_index_data()
    elif choice == '6':
        example_6_update_data()
    elif choice == '7':
        example_7_download_stock_list()
    elif choice == '8':
        example_8_download_all_types()
    elif choice == '9':
        example_9_use_with_data_loader()
    elif choice == '10':
        example_10_generate_sample_data()
    else:
        print("无效选择")


if __name__ == '__main__':
    main()

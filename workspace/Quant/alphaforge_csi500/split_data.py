#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据划分脚本
按时间序列划分训练集、验证集、测试集
关键原则：
1.时间不可穿越 - 训练数据必须早于验证数据
2.避免未来函数 - 不能用未来信息训练
3.市场周期覆盖 - 训练集应包含牛熊市
"""

import pandas as pd
import glob
import os
import shutil
from datetime import datetime

def split_data():
    """划分数据集"""
    
    print("="*60)
    print("数据集划分")
    print("="*60)
    
    # 划分日期
    TRAIN_END = '2023-12-31'
    VAL_END = '2024-06-30'
    
    # 目录
    data_dir = './data/zz500/'
    train_dir = './data/zz500/train/'
    val_dir = './data/zz500/val/'
    test_dir = './data/zz500/test/'
    
    # 创建目录
    for d in [train_dir, val_dir, test_dir]:
        os.makedirs(d, exist_ok=True)
    
    # 获取所有股票文件
    files = glob.glob(os.path.join(data_dir, 'stock_quote_*.csv'))
    print(f"\n总文件数: {len(files)}")
    
    # 统计
    stats = {
        'train': {'files': 0, 'records': 0},
        'val': {'files': 0, 'records': 0},
        'test': {'files': 0, 'records': 0}
    }
    
    # 处理每个文件
    for i, file in enumerate(files):
        if (i+1) % 200 == 0:
            print(f"处理进度: {i+1}/{len(files)}")
        
        try:
            df = pd.read_csv(file)
            df['date'] = pd.to_datetime(df['date'])
            
            stock_code = os.path.basename(file).split('_')[2]
            
            # 划分数据
            train_df = df[df['date'] <= TRAIN_END]
            val_df = df[(df['date'] > TRAIN_END) & (df['date'] <= VAL_END)]
            test_df = df[df['date'] > VAL_END]
            
            # 保存训练集
            if len(train_df) > 0:
                train_file = os.path.join(train_dir, f"{stock_code}.csv")
                train_df.to_csv(train_file, index=False)
                stats['train']['files'] += 1
                stats['train']['records'] += len(train_df)
            
            # 保存验证集
            if len(val_df) > 0:
                val_file = os.path.join(val_dir, f"{stock_code}.csv")
                val_df.to_csv(val_file, index=False)
                stats['val']['files'] += 1
                stats['val']['records'] += len(val_df)
            
            # 保存测试集
            if len(test_df) > 0:
                test_file = os.path.join(test_dir, f"{stock_code}.csv")
                test_df.to_csv(test_file, index=False)
                stats['test']['files'] += 1
                stats['test']['records'] += len(test_df)
                
        except Exception as e:
            print(f"处理失败: {file}, 错误: {e}")
    
    # 处理指数数据
    print("\n处理指数数据...")
    index_file = os.path.join(data_dir, 'index_000905.csv')
    if os.path.exists(index_file):
        df_index = pd.read_csv(index_file)
        df_index['date'] = pd.to_datetime(df_index['date'])
        
        # 划分
        train_idx = df_index[df_index['date'] <= TRAIN_END]
        val_idx = df_index[(df_index['date'] > TRAIN_END) & (df_index['date'] <= VAL_END)]
        test_idx = df_index[df_index['date'] > VAL_END]
        
        # 保存
        if len(train_idx) > 0:
            train_idx.to_csv(os.path.join(train_dir, 'index_000905.csv'), index=False)
        if len(val_idx) > 0:
            val_idx.to_csv(os.path.join(val_dir, 'index_000905.csv'), index=False)
        if len(test_idx) > 0:
            test_idx.to_csv(os.path.join(test_dir, 'index_000905.csv'), index=False)
        
        print(f"指数数据已划分")
    
    # 输出统计
    print("\n" + "="*60)
    print("划分结果统计")
    print("="*60)
    
    print(f"\n训练集 (2020-01-01 ~ {TRAIN_END}):")
    print(f"  股票数: {stats['train']['files']}")
    print(f"  记录数: {stats['train']['records']:,}")
    
    print(f"\n验证集 ({TRAIN_END} ~ {VAL_END}):")
    print(f"  股票数: {stats['val']['files']}")
    print(f"  记录数: {stats['val']['records']:,}")
    
    print(f"\n测试集 ({VAL_END} ~ 2025-12-31):")
    print(f"  股票数: {stats['test']['files']}")
    print(f"  记录数: {stats['test']['records']:,}")
    
    # 保存划分信息
    split_info = {
        'train_end': TRAIN_END,
        'val_end': VAL_END,
        'train_files': stats['train']['files'],
        'val_files': stats['val']['files'],
        'test_files': stats['test']['files'],
        'train_records': stats['train']['records'],
        'val_records': stats['val']['records'],
        'test_records': stats['test']['records'],
        'split_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    import json
    with open('./data/zz500/split_info.json', 'w') as f:
        json.dump(split_info, f, indent=2)
    
    print(f"\n划分信息已保存到: ./data/zz500/split_info.json")
    print("\n✅ 数据划分完成！")
    
    return stats


if __name__ == '__main__':
    split_data()

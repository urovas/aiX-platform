#!/usr/bin/env python3
"""
中证500因子挖掘主程序

功能：
1. 数据获取和处理
2. 因子计算和挖掘
3. 策略回测和优化
4. 结果可视化和报告

使用方法：
python main.py --mode data
python main.py --mode factor
python main.py --mode backtest
python main.py --mode all

作者：Clawdbot
日期：2026-02-14
"""

import argparse
import sys
import os
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """设置环境"""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 设置样式
    sns.set_style('whitegrid')
    
    print("环境设置完成")

def run_data_pipeline():
    """运行数据处理流程"""
    print("=" * 60)
    print("开始数据处理流程")
    print("=" * 60)
    
    from code.factor_mining.get_500_stocks_data import download_sz500_data
    
    # 下载真实数据
    data = download_sz500_data(
        n_stocks=50,
        start_date='20200101',
        end_date='20260214'
    )
    
    if data is not None:
        print("数据处理流程完成！")
        return True
    else:
        print("数据处理流程失败！")
        return False

def run_factor_pipeline():
    """运行因子挖掘流程"""
    print("=" * 60)
    print("开始因子挖掘流程")
    print("=" * 60)
    
    from code.factor_mining.factor_mining import AdvancedFactorMining
    
    # 创建因子挖掘实例
    factor_miner = AdvancedFactorMining()
    
    # 加载真实数据
    factor_miner.load_real_data(filename='data/raw/sz500_stocks_data.csv')
    
    # 计算所有因子
    factor_miner.calculate_all_factors()
    
    # 进行IC测试
    ic_results = factor_miner.factor_ic_test()
    
    # 因子优化
    optimized_weights = factor_miner.factor_optimization(method='ridge')
    
    # 回测策略
    backtest_result = factor_miner.backtest_strategy(
        top_n=40,
        holding_days=5
    )
    
    # 参数优化
    optimization_results = factor_miner.parameter_optimization(
        top_n_range=[10, 20, 30, 40],
        holding_days_range=[5, 10, 15, 20]
    )
    
    print("因子挖掘流程完成！")
    return True

def run_backtest_pipeline():
    """运行回测流程"""
    print("=" * 60)
    print("开始回测流程")
    print("=" * 60)
    
    from code.factor_mining.factor_mining import AdvancedFactorMining
    
    # 创建因子挖掘实例
    factor_miner = AdvancedFactorMining()
    
    # 加载真实数据
    factor_miner.load_real_data(filename='data/raw/sz500_stocks_data.csv')
    
    # 计算所有因子
    factor_miner.calculate_all_factors()
    
    # 因子优化
    optimized_weights = factor_miner.factor_optimization(method='ridge')
    
    # 回测策略
    backtest_result = factor_miner.backtest_strategy(
        top_n=40,
        holding_days=5
    )
    
    print("回测流程完成！")
    return True

def run_all_pipeline():
    """运行完整流程"""
    print("=" * 60)
    print("开始完整流程")
    print("=" * 60)
    
    # 数据处理
    print("\n[1/3] 数据处理流程")
    data_success = run_data_pipeline()
    
    if not data_success:
        print("数据处理失败，终止流程")
        return False
    
    # 因子挖掘
    print("\n[2/3] 因子挖掘流程")
    factor_success = run_factor_pipeline()
    
    if not factor_success:
        print("因子挖掘失败，终止流程")
        return False
    
    # 回测
    print("\n[3/3] 回测流程")
    backtest_success = run_backtest_pipeline()
    
    if not backtest_success:
        print("回测失败")
        return False
    
    print("\n" + "=" * 60)
    print("完整流程执行成功！")
    print("=" * 60)
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='中证500因子挖掘主程序')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['data', 'factor', 'backtest', 'all'],
        default='all',
        help='运行模式: data(数据), factor(因子), backtest(回测), all(全部)'
    )
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 根据模式运行相应流程
    if args.mode == 'data':
        success = run_data_pipeline()
    elif args.mode == 'factor':
        success = run_factor_pipeline()
    elif args.mode == 'backtest':
        success = run_backtest_pipeline()
    elif args.mode == 'all':
        success = run_all_pipeline()
    else:
        print(f"未知的运行模式: {args.mode}")
        success = False
    
    # 返回状态码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
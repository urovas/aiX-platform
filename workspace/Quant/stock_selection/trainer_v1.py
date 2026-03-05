#!/usr/bin/env python3
# 量化选股模型主脚本

import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/stock_selection')

from config import config
from utils.data_fetcher import DataFetcher
from utils.factor_calculator import FactorCalculator
from models.selection_model import StockSelectionModel
from strategies.execution_strategy import ExecutionStrategy

def print_banner():
    """打印横幅"""
    banner = """
    ==============================================================
                    量化选股模型 v1.0.0
    ==============================================================
    功能：
    1. 基于多因子模型的股票选择
    2. 行业分布分析
    3. 市值分布分析
    4. 投资组合构建
    5. 策略回测
    ==============================================================
    """
    print(banner)

def main():
    """主函数"""
    print_banner()
    
    # 初始化组件
    print("初始化组件...")
    data_fetcher = DataFetcher(config)
    factor_calculator = FactorCalculator(data_fetcher)
    selection_model = StockSelectionModel(config, data_fetcher, factor_calculator)
    execution_strategy = ExecutionStrategy(config, data_fetcher, selection_model)
    
    print("✓ 初始化完成")
    print()
    
    # 显示菜单
    while True:
        print("请选择操作：")
        print("1. 运行量化选股策略")
        print("2. 训练选股模型")
        print("3. 回测策略")
        print("4. 查看选股结果")
        print("5. 退出")
        
        choice = input("请输入选项 (1-5): ")
        print()
        
        if choice == "1":
            # 运行量化选股策略
            print("运行量化选股策略")
            print("-" * 60)
            
            # 选择股票池
            print("选择股票池:")
            print("1. 沪深300 (CSI300)")
            print("2. 中证500 (CSI500) (推荐)")
            print("3. 中证1000 (CSI1000)")
            print("4. 上证50 (SH50)")
            print("5. 深证50 (SZ50)")
            
            universe_choice = input("请输入选项 (1-5, 默认2): ") or "2"
            universe_map = {
                "1": "CSI300",
                "2": "CSI500",
                "3": "CSI1000",
                "4": "SH50",
                "5": "SZ50"
            }
            universe = universe_map.get(universe_choice, "CSI500")
            
            # 选择选股数量
            top_n = input("请输入选股数量 (默认50): ")
            top_n = int(top_n) if top_n.isdigit() else 50
            
            # 选择模型类型
            print("选择模型类型:")
            print("1. 线性回归 (linear)")
            print("2. 随机森林 (rf)")
            
            model_choice = input("请输入选项 (1-2): ")
            model_map = {
                "1": "linear",
                "2": "rf"
            }
            model_type = model_map.get(model_choice, "linear")
            
            # 选择加权方法
            print("选择加权方法:")
            print("1. 等权 (equal)")
            print("2. 市值加权 (market_cap)")
            print("3. 收益率加权 (return_based)")
            
            weight_choice = input("请输入选项 (1-3): ")
            weight_map = {
                "1": "equal",
                "2": "market_cap",
                "3": "return_based"
            }
            weight_method = weight_map.get(weight_choice, "equal")
            
            print()
            # 运行策略
            try:
                result = execution_strategy.run_full_strategy(
                    universe=universe,
                    top_n=top_n,
                    model_type=model_type,
                    weight_method=weight_method
                )
                if result:
                    print("✓ 策略运行成功")
                else:
                    print("✗ 策略运行失败")
            except Exception as e:
                print(f"策略运行时出错: {e}")
                import traceback
                traceback.print_exc()
            
        elif choice == "2":
            # 训练选股模型
            print("训练选股模型")
            print("-" * 60)
            
            # 设置训练时间范围
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            print(f"训练时间范围: {start_date} 到 {end_date}")
            print("正在训练模型...")
            
            # 准备训练数据
            training_data = selection_model.prepare_training_data(
                start_date=start_date,
                end_date=end_date
            )
            
            if training_data is not None:
                # 提取特征和标签
                feature_cols = [col for col in training_data.columns 
                              if col not in ['future_return', 'ts_code', 'date']]
                
                if feature_cols:
                    X = training_data[feature_cols]
                    y = training_data['future_return']
                    
                    # 训练模型
                    models = selection_model.build_factor_model(X, y)
                    
                    if models:
                        print("✓ 模型训练完成")
                    else:
                        print("✗ 模型训练失败")
                else:
                    print("✗ 无法提取特征列")
            else:
                print("✗ 无法准备训练数据")
            
        elif choice == "3":
            # 回测策略
            print("回测策略")
            print("-" * 60)
            
            # 设置回测时间范围
            end_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            print(f"回测时间范围: {start_date} 到 {end_date}")
            print("正在回测...")
            
            # 获取股票池
            stock_pool = execution_strategy.get_stock_pool("CSI300")
            
            if stock_pool:
                # 回测
                backtest_result = selection_model.backtest_strategy(
                    start_date=start_date,
                    end_date=end_date,
                    stock_pool=stock_pool[:100],  # 限制股票数量
                    top_n=50
                )
                
                if backtest_result:
                    print("回测结果:")
                    print(pd.DataFrame(backtest_result))
                else:
                    print("✗ 回测失败")
            else:
                print("✗ 无法获取股票池")
            
        elif choice == "4":
            # 查看选股结果
            print("查看选股结果")
            print("-" * 60)
            
            # 列出结果文件
            result_dir = os.path.join(config.DATA_DIR, "results")
            if os.path.exists(result_dir):
                files = os.listdir(result_dir)
                stock_selection_files = [f for f in files if f.startswith("stock_selection_")]
                
                if stock_selection_files:
                    print("可用的选股结果文件:")
                    for i, file in enumerate(stock_selection_files[-5:], 1):  # 显示最近5个文件
                        print(f"{i}. {file}")
                    
                    file_choice = input("请选择查看的文件 (1-5): ")
                    if file_choice.isdigit():
                        idx = int(file_choice) - 1
                        if 0 <= idx < len(stock_selection_files[-5:]):
                            selected_file = stock_selection_files[-5:][idx]
                            file_path = os.path.join(result_dir, selected_file)
                            
                            try:
                                df = pd.read_csv(file_path)
                                print(f"\n文件: {selected_file}")
                                print("选股结果:")
                                print(df[['rank', 'name', 'ts_code', 'industry', 'predicted_return']].head(20))
                            except Exception as e:
                                print(f"查看文件失败: {e}")
                else:
                    print("✗ 没有选股结果文件")
            else:
                print("✗ 结果目录不存在")
            
        elif choice == "5":
            # 退出
            print("退出程序...")
            break
        
        else:
            print("无效选项，请重新输入")
        
        print()
        input("按 Enter 键继续...")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        print("程序退出")

# 量化指数增强策略测试脚本

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from utils.data_fetcher import IndexDataFetcher
from utils.traditional_factors import TraditionalFactorCalculator
from models.ai_model import AIModel
from models.model_fusion import ModelFusion
from models.dual_balance import DualBalanceFramework
from strategies.portfolio_optimizer import PortfolioOptimizer
from strategies.backtester import Backtester

def test_data_fetcher():
    """测试数据获取模块"""
    print("="*60)
    print("测试数据获取模块")
    print("="*60)
    
    data_fetcher = IndexDataFetcher(config)
    
    # 获取数据源状态
    status = data_fetcher.get_data_source_status()
    print("数据源状态:")
    for source, s in status.items():
        print(f"  {source}: {s}")
    
    # 测试获取指数数据
    print("\n测试获取沪深300指数数据...")
    index_data = data_fetcher.get_index_data("000300.SH", "2023-01-01", "2024-12-31")
    
    if not index_data.empty:
        print(f"成功获取指数数据，共 {len(index_data)} 条记录")
        print(index_data.head())
    else:
        print("获取指数数据失败")
    
    # 测试获取成分股数据
    print("\n测试获取沪深300成分股数据...")
    components_data = data_fetcher.get_index_components("000300.SH")
    
    if not components_data.empty:
        print(f"成功获取成分股数据，共 {len(components_data)} 只股票")
        print(components_data.head(10))
    else:
        print("获取成分股数据失败")
    
    # 测试获取股票数据
    if not components_data.empty:
        stock_code = components_data['code'].iloc[0] if 'code' in components_data.columns else "000001.SZ"
        print(f"\n测试获取股票数据: {stock_code}")
        stock_data = data_fetcher.get_stock_quote(stock_code, "2023-01-01", "2024-12-31")
        
        if not stock_data.empty:
            print(f"成功获取股票数据，共 {len(stock_data)} 条记录")
            print(stock_data.head())
        else:
            print("获取股票数据失败")
    
    print("\n数据获取模块测试完成")
    return index_data, components_data

def test_traditional_factors(stock_data):
    """测试传统因子计算"""
    print("\n" + "="*60)
    print("测试传统因子计算")
    print("="*60)
    
    if stock_data is None or stock_data.empty:
        print("没有股票数据，跳过因子计算测试")
        return None
    
    factor_calculator = TraditionalFactorCalculator(None)
    
    # 计算所有传统因子
    factors = factor_calculator.calculate_all_traditional_factors(stock_data)
    
    print(f"计算得到 {len(factors)} 个因子:")
    for factor_name, factor_value in factors.items():
        if isinstance(factor_value, (pd.Series, np.ndarray)):
            print(f"  {factor_name}: {len(factor_value)} 个值")
        else:
            print(f"  {factor_name}: {factor_value}")
    
    # 打印因子权重
    weights = factor_calculator.calculate_factor_weights()
    print(f"\n因子权重配置:")
    for factor_name, weight in weights.items():
        print(f"  {factor_name}: {weight:.4f}")
    
    print("\n传统因子计算测试完成")
    return factors

def test_ai_model(stock_data):
    """测试AI模型"""
    print("\n" + "="*60)
    print("测试AI模型")
    print("="*60)
    
    if stock_data is None or stock_data.empty:
        print("没有股票数据，跳过AI模型测试")
        return None
    
    ai_model = AIModel(config)
    
    # 准备数据
    print("准备AI模型数据...")
    X, y = ai_model.prepare_data(stock_data, lookback=20)
    
    if X is None or len(X) == 0:
        print("无法准备AI模型数据")
        return None
    
    print(f"数据准备完成，X shape: {X.shape}, y shape: {y.shape}")
    
    # 训练模型
    print("训练AI模型...")
    model = ai_model.train(X, y, validation_split=0.2)
    
    # 评估模型
    print("评估AI模型...")
    X_test, y_test = X[:10], y[:10]
    metrics = ai_model.evaluate(X_test, y_test)
    
    # 预测
    print("进行预测...")
    predictions, confidence = ai_model.predict(X_test[:1])
    print(f"预测值: {predictions[0]:.6f}, 置信度: {confidence:.6f}")
    
    print("\nAI模型测试完成")
    return ai_model

def test_model_fusion(stock_data):
    """测试模型融合"""
    print("\n" + "="*60)
    print("测试模型融合")
    print("="*60)
    
    if stock_data is None or stock_data.empty:
        print("没有股票数据，跳过模型融合测试")
        return None
    
    model_fusion = ModelFusion(config)
    
    # 训练融合模型
    print("训练融合模型...")
    models = model_fusion.train_fusion_model(stock_data, lookback=20)
    
    if models:
        print("融合模型训练成功")
        
        # 评估融合模型
        print("评估融合模型...")
        metrics = model_fusion.evaluate_fusion(stock_data, lookback=20)
        
        # 预测
        print("进行预测...")
        predictions = model_fusion.predict_fusion(stock_data, lookback=20)
        print(f"融合预测: {predictions['fusion_prediction']:.6f}")
        print(f"GBDT预测: {predictions['gbdt_prediction']:.6f}")
        print(f"AI预测: {predictions['ai_prediction']:.6f}")
    else:
        print("融合模型训练失败")
    
    print("\n模型融合测试完成")
    return model_fusion

def test_dual_balance(stock_data):
    """测试双均衡框架"""
    print("\n" + "="*60)
    print("测试双均衡框架")
    print("="*60)
    
    if stock_data is None or stock_data.empty:
        print("没有股票数据，跳过双均衡框架测试")
        return None
    
    dual_balance = DualBalanceFramework(config)
    
    # 打印双均衡框架报告
    dual_balance.print_balance_report()
    
    # 训练双均衡模型
    print("\n训练双均衡模型...")
    models = dual_balance.train_dual_balance_model(stock_data, lookback=20)
    
    if models:
        print("双均衡模型训练成功")
        
        # 计算均衡预测
        print("计算均衡预测...")
        result = dual_balance.calculate_balanced_prediction(stock_data, lookback=20)
        
        print(f"均衡预测: {result['balanced_prediction']:.6f}")
        print(f"方法论均衡预测: {result['methodology_balanced_prediction']:.6f}")
        print(f"GBDT预测: {result['gbdt_prediction']:.6f}")
        print(f"AI预测: {result['ai_prediction']:.6f}")
        
        # 评估双均衡模型
        print("\n评估双均衡模型...")
        evaluation = dual_balance.evaluate_dual_balance(stock_data, lookback=20)
    else:
        print("双均衡模型训练失败")
    
    print("\n双均衡框架测试完成")
    return dual_balance

def test_portfolio_optimizer():
    """测试组合优化"""
    print("\n" + "="*60)
    print("测试组合优化")
    print("="*60)
    
    optimizer = PortfolioOptimizer(config)
    
    # 模拟预测
    n_stocks = 50
    stock_codes = [f"00000{i}.SZ" for i in range(1, n_stocks + 1)]
    predictions = {code: np.random.normal(0, 0.01) for code in stock_codes}
    
    # 模拟指数权重（等权重）
    index_weights = {code: 1/n_stocks for code in stock_codes}
    
    print(f"模拟 {n_stocks} 只股票的预测")
    
    # 优化组合
    optimized_weights = optimizer.optimize_portfolio(predictions, index_weights)
    
    # 计算组合指标
    cov_matrix = np.eye(n_stocks) * 0.02 ** 2
    metrics = optimizer.calculate_portfolio_metrics(
        optimized_weights,
        predictions,
        index_weights,
        cov_matrix
    )
    
    optimizer.print_portfolio_metrics(metrics)
    
    print("\n组合优化测试完成")
    return optimizer

def test_backtester():
    """测试回测器"""
    print("\n" + "="*60)
    print("测试回测器")
    print("="*60)
    
    backtester = Backtester(config)
    
    # 模拟回测数据
    n_days = 252
    dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")
    
    # 模拟指数数据
    index_data = pd.DataFrame({
        'close': 100 * np.cumprod(1 + np.random.normal(0.0001, 0.01, n_days)),
        'pct_chg': np.random.normal(0.0001, 0.01, n_days) * 100
    }, index=dates)
    
    # 模拟权重
    n_stocks = 50
    stock_codes = [f"00000{i}.SZ" for i in range(1, n_stocks + 1)]
    equal_weights = {code: 1/n_stocks for code in stock_codes}
    
    portfolio_weights_list = {date: equal_weights for date in dates}
    index_weights_list = {date: equal_weights for date in dates}
    
    print(f"模拟 {n_days} 天的回测数据")
    
    # 运行回测
    backtest_results = backtester.run_backtest(
        index_data,
        portfolio_weights_list,
        index_weights_list
    )
    
    # 评估表现
    metrics = backtester.evaluate_performance(backtest_results)
    
    print("\n回测器测试完成")
    return backtester

def run_full_test():
    """运行完整测试"""
    print("\n" + "="*60)
    print("量化指数增强策略完整测试")
    print("="*60)
    
    # 测试数据获取
    index_data, components_data = test_data_fetcher()
    
    # 获取一只股票的数据用于后续测试
    stock_data = None
    if components_data is not None and not components_data.empty:
        stock_code = components_data['code'].iloc[0] if 'code' in components_data.columns else "000001.SZ"
        data_fetcher = IndexDataFetcher(config)
        stock_data = data_fetcher.get_stock_quote(stock_code, "2023-01-01", "2024-12-31")
    
    # 测试传统因子
    test_traditional_factors(stock_data)
    
    # 测试AI模型
    test_ai_model(stock_data)
    
    # 测试模型融合
    test_model_fusion(stock_data)
    
    # 测试双均衡框架
    test_dual_balance(stock_data)
    
    # 测试组合优化
    test_portfolio_optimizer()
    
    # 测试回测器
    test_backtester()
    
    print("\n" + "="*60)
    print("完整测试完成")
    print("="*60)

if __name__ == "__main__":
    run_full_test()

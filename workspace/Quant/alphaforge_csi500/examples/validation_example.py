# 多频段信号融合策略 - 验证模块使用示例

import pandas as pd
import numpy as np
from models.multi_frequency_fusion import MultiFrequencySignalFusionStrategy

# 配置参数
config = {
    'model_path': './models/saved/',
    'enable_monitoring': False
}

# 初始化策略
strategy = MultiFrequencySignalFusionStrategy(config)

# 准备训练数据
train_data = {
    'tick': [pd.DataFrame()],
    'minute': [pd.DataFrame()],
    'financial': [pd.DataFrame()],
    'price': [pd.DataFrame()]
}

val_data = {
    'tick': [pd.DataFrame()],
    'minute': [pd.DataFrame()],
    'financial': [pd.DataFrame()],
    'price': [pd.DataFrame()],
    'actual_returns': []
}

# 训练策略
strategy.train(train_data, val_data)

# 准备测试数据
test_data = {
    'stock_001': {
        'tick': pd.DataFrame(),
        'minute': pd.DataFrame(),
        'financial': pd.DataFrame(),
        'price': pd.DataFrame()
    },
    'stock_002': {
        'tick': pd.DataFrame(),
        'minute': pd.DataFrame(),
        'financial': pd.DataFrame(),
        'price': pd.DataFrame()
    }
}

# 验证策略整体表现
print("="*80)
print("验证策略整体表现")
print("="*80)

validation_result = strategy.validate_strategy(test_data, initial_capital=1000000)

# 查看验证结果
if validation_result:
    print("\n【策略性能】")
    strategy_metrics = validation_result['strategy']
    print(f"  年化收益率: {strategy_metrics['annualized_return']:.4f}")
    print(f"  年化波动率: {strategy_metrics['volatility']:.4f}")
    print(f"  夏普比率: {strategy_metrics['sharpe_ratio']:.4f}")
    print(f"  最大回撤: {strategy_metrics['max_drawdown']:.4f}")
    print(f"  胜率: {strategy_metrics['win_rate']:.4f}")
    
    print("\n【预测性能】")
    prediction_metrics = validation_result['prediction']
    print(f"  信息系数(IC): {prediction_metrics['information_coefficient']:.4f}")
    print(f"  方向准确率: {prediction_metrics['direction_accuracy']:.4f}")
    print(f"  R²: {prediction_metrics['r2']:.4f}")
    print(f"  MSE: {prediction_metrics['mse']:.6f}")
    
    print("\n【分组测试】")
    group_test = validation_result['group_test']
    for group_name, group_data in group_test.items():
        print(f"  {group_name}组:")
        print(f"    样本数: {group_data['count']}")
        print(f"    IC: {group_data['ic']:.4f}")
        print(f"    方向准确率: {group_data['direction_accuracy']:.4f}")
        print(f"    平均收益率: {group_data['avg_return']:.4f}")

# 验证子模型
print("\n" + "="*80)
print("验证子模型")
print("="*80)

submodel_results = strategy.validate_submodels(test_data)

if submodel_results:
    print("\n【子模型比较】")
    comparison_df = pd.DataFrame(submodel_results).T
    print(comparison_df)
    
    # 找出最佳模型
    best_ic_model = comparison_df['ic'].idxmax()
    best_direction_model = comparison_df['direction_accuracy'].idxmax()
    best_mse_model = comparison_df['mse'].idxmin()
    
    print(f"\n最佳IC模型: {best_ic_model}")
    print(f"最佳方向准确率模型: {best_direction_model}")
    print(f"最佳MSE模型: {best_mse_model}")

# 生成验证报告
print("\n" + "="*80)
print("生成验证报告")
print("="*80)

report = strategy.generate_validation_report()

if report:
    print("\n【验证报告】")
    print(f"  验证时间: {report['validation_timestamp']}")
    print(f"  报告生成时间: {report['timestamp']}")
    
    if report['strategy_metrics']:
        print(f"\n  策略夏普比率: {report['strategy_metrics']['sharpe_ratio']:.4f}")
    
    if report['prediction_metrics']:
        print(f"  策略IC: {report['prediction_metrics']['information_coefficient']:.4f}")
    
    if report['submodels']:
        print(f"\n  子模型验证完成")

# 绘制验证结果图表
print("\n" + "="*80)
print("绘制验证结果图表")
print("="*80)

strategy.plot_validation_results()

# 获取验证摘要
print("\n" + "="*80)
print("获取验证摘要")
print("="*80)

summary = strategy.get_validation_summary()

if summary:
    print(f"  状态: {summary['status']}")
    print(f"  验证时间: {summary.get('validation_time', 'N/A')}")
    print(f"  策略IC: {summary.get('strategy_ic', 'N/A')}")
    print(f"  策略方向准确率: {summary.get('strategy_direction_accuracy', 'N/A')}")
    print(f"  策略夏普比率: {summary.get('strategy_sharpe', 'N/A')}")
    print(f"  最佳子模型: {summary.get('best_submodel', 'N/A')}")
    print(f"  整体评估: {summary.get('overall_assessment', 'N/A')}")

# 完整的验证流程示例
print("\n" + "="*80)
print("完整验证流程示例")
print("="*80)

def complete_validation_workflow(strategy, test_data):
    """
    完整的验证工作流程
    """
    # 1. 验证策略整体表现
    print("\n【步骤1】验证策略整体表现")
    validation_result = strategy.validate_strategy(test_data)
    
    if validation_result is None:
        print("❌ 验证失败")
        return None
    
    # 2. 验证子模型
    print("\n【步骤2】验证子模型")
    submodel_results = strategy.validate_submodels(test_data)
    
    # 3. 生成验证报告
    print("\n【步骤3】生成验证报告")
    report = strategy.generate_validation_report()
    
    # 4. 绘制验证结果
    print("\n【步骤4】绘制验证结果")
    strategy.plot_validation_results()
    
    # 5. 获取验证摘要
    print("\n【步骤5】获取验证摘要")
    summary = strategy.get_validation_summary()
    
    return {
        'validation_result': validation_result,
        'submodel_results': submodel_results,
        'report': report,
        'summary': summary
    }

# 执行完整验证流程
results = complete_validation_workflow(strategy, test_data)

if results:
    print("\n✅ 完整验证流程执行成功")
    print(f"  策略IC: {results['summary'].get('strategy_ic', 'N/A')}")
    print(f"  整体评估: {results['summary'].get('overall_assessment', 'N/A')}")
else:
    print("\n❌ 完整验证流程执行失败")

# 验证指标说明
print("\n" + "="*80)
print("验证指标说明")
print("="*80)

print("""
【策略性能指标】
- 总收益率: 策略在测试期间的总收益率
- 年化收益率: 策略的年化收益率
- 年化波动率: 策略收益率的年化波动率
- 夏普比率: 风险调整后收益，越高越好
- 最大回撤: 策略最大回撤，越小越好
- 胜率: 盈利交易占比，越高越好

【预测性能指标】
- MSE: 均方误差，越小越好
- RMSE: 均方根误差，越小越好
- MAE: 平均绝对误差，越小越好
- R²: 决定系数，越接近1越好
- IC: 信息系数，衡量预测与实际的相关性，越高越好
- 方向准确率: 预测方向与实际方向一致的比例，越高越好

【分组测试】
- strong组: 强信号组（信号强度>0.05）
- moderate组: 中等信号组（0.02<信号强度<=0.05）
- weak组: 弱信号组（信号强度<=0.02）

【子模型】
- high_frequency: 高频市场情绪感知模型
- fundamental: 基本面价值评估模型
- fusion: AI信号融合模型

【整体评估】
- excellent: IC > 0.05（优秀）
- good: 0.02 < IC <= 0.05（良好）
- acceptable: 0 < IC <= 0.02（可接受）
- poor: IC <= 0（较差）
""")

# 自定义验证流程示例
print("\n" + "="*80)
print("自定义验证流程示例")
print("="*80)

def custom_validation(strategy, test_data, custom_metrics=None):
    """
    自定义验证流程
    
    Args:
        strategy: 策略对象
        test_data: 测试数据
        custom_metrics: 自定义指标函数列表
    """
    # 执行标准验证
    validation_result = strategy.validate_strategy(test_data)
    
    if validation_result is None:
        return None
    
    # 执行自定义指标计算
    if custom_metrics:
        print("\n【自定义指标】")
        for metric_func in custom_metrics:
            metric_name, metric_value = metric_func(validation_result)
            print(f"  {metric_name}: {metric_value}")
    
    return validation_result

# 示例：计算自定义指标
def calculate_ic_rank(validation_result):
    """计算IC排名"""
    ic = validation_result['prediction']['information_coefficient']
    rank = 'high' if ic > 0.05 else ('medium' if ic > 0.02 else 'low')
    return 'IC排名', rank

def calculate_sharpe_grade(validation_result):
    """计算夏普比率等级"""
    sharpe = validation_result['strategy']['sharpe_ratio']
    grade = 'A' if sharpe > 2 else ('B' if sharpe > 1 else ('C' if sharpe > 0.5 else 'D'))
    return '夏普等级', grade

# 使用自定义验证
custom_validation(strategy, test_data, [
    calculate_ic_rank,
    calculate_sharpe_grade
])

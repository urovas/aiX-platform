# 统一的模型验证工具

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class ModelValidator:
    def __init__(self, config=None):
        """初始化模型验证器"""
        self.config = config or {}
        self.validation_results = {}
    
    def validate_model(self, model, X, y, model_name='model'):
        """
        验证模型性能
        
        Args:
            model: 训练好的模型
            X: 特征矩阵
            y: 标签向量
            model_name: 模型名称
            
        Returns:
            metrics: 模型性能指标
        """
        print(f"\n验证 {model_name} 模型")
        print("=" * 60)
        
        # 基本指标计算
        y_pred = model.predict(X)
        
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        # 计算方向准确率
        direction_accuracy = np.mean(np.sign(y) == np.sign(y_pred))
        
        # 计算信息系数（IC）
        ic = np.corrcoef(y, y_pred)[0, 1]
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'direction_accuracy': direction_accuracy,
            'information_coefficient': ic
        }
        
        print(f"MSE: {mse:.6f}")
        print(f"RMSE: {rmse:.6f}")
        print(f"MAE: {mae:.6f}")
        print(f"R²: {r2:.4f}")
        print(f"方向准确率: {direction_accuracy:.4f}")
        print(f"信息系数: {ic:.4f}")
        
        # 保存结果
        self.validation_results[model_name] = metrics
        
        return metrics
    
    def cross_validate_model(self, model, X, y, cv=5, model_name='model'):
        """
        交叉验证模型
        
        Args:
            model: 模型对象
            X: 特征矩阵
            y: 标签向量
            cv: 交叉验证折数
            model_name: 模型名称
            
        Returns:
            cv_results: 交叉验证结果
        """
        print(f"\n交叉验证 {model_name} 模型")
        print("=" * 60)
        
        # 使用时间序列交叉验证
        tscv = TimeSeriesSplit(n_splits=cv)
        
        # 计算多个指标
        mse_scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_squared_error')
        r2_scores = cross_val_score(model, X, y, cv=tscv, scoring='r2')
        mae_scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_absolute_error')
        
        cv_results = {
            'mse_mean': -np.mean(mse_scores),
            'mse_std': np.std(mse_scores),
            'rmse_mean': np.sqrt(-np.mean(mse_scores)),
            'r2_mean': np.mean(r2_scores),
            'r2_std': np.std(r2_scores),
            'mae_mean': -np.mean(mae_scores),
            'mae_std': np.std(mae_scores)
        }
        
        print(f"交叉验证 MSE: {cv_results['mse_mean']:.6f} ± {cv_results['mse_std']:.6f}")
        print(f"交叉验证 RMSE: {cv_results['rmse_mean']:.6f}")
        print(f"交叉验证 R²: {cv_results['r2_mean']:.4f} ± {cv_results['r2_std']:.4f}")
        print(f"交叉验证 MAE: {cv_results['mae_mean']:.6f} ± {cv_results['mae_std']:.6f}")
        
        # 保存结果
        if f'{model_name}_cv' not in self.validation_results:
            self.validation_results[f'{model_name}_cv'] = cv_results
        
        return cv_results
    
    def validate_strategy(self, signals, actual_returns):
        """
        验证策略性能
        
        Args:
            signals: 信号列表
            actual_returns: 实际收益率列表
            
        Returns:
            strategy_metrics: 策略性能指标
        """
        print("\n验证策略性能")
        print("=" * 60)
        
        # 计算策略收益率
        strategy_returns = []
        for signal, actual_return in zip(signals, actual_returns):
            if isinstance(signal, dict) and 'strength' in signal:
                position = np.sign(signal['strength'])
                strategy_returns.append(position * actual_return)
            elif isinstance(signal, (int, float)):
                position = np.sign(signal)
                strategy_returns.append(position * actual_return)
        
        strategy_returns = np.array(strategy_returns)
        
        # 计算策略指标
        total_return = np.sum(strategy_returns)
        annualized_return = np.mean(strategy_returns) * 252
        volatility = np.std(strategy_returns) * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        max_drawdown = self.calculate_max_drawdown(strategy_returns)
        win_rate = np.mean(strategy_returns > 0)
        
        strategy_metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': len(strategy_returns)
        }
        
        print(f"总收益率: {total_return:.4f}")
        print(f"年化收益率: {annualized_return:.4f}")
        print(f"年化波动率: {volatility:.4f}")
        print(f"夏普比率: {sharpe_ratio:.4f}")
        print(f"最大回撤: {max_drawdown:.4f}")
        print(f"胜率: {win_rate:.4f}")
        print(f"交易次数: {len(strategy_returns)}")
        
        # 保存结果
        self.validation_results['strategy'] = strategy_metrics
        
        return strategy_metrics
    
    def calculate_max_drawdown(self, returns):
        """
        计算最大回撤
        
        Args:
            returns: 收益率序列
            
        Returns:
            max_drawdown: 最大回撤
        """
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        return max_drawdown
    
    def compare_models(self, models_results):
        """
        比较多个模型的性能
        
        Args:
            models_results: 模型结果字典 {model_name: metrics}
            
        Returns:
            comparison: 比较结果
        """
        print("\n模型性能比较")
        print("=" * 60)
        
        # 创建比较表格
        comparison_df = pd.DataFrame(models_results).T
        
        # 打印比较结果
        print(comparison_df)
        
        # 找出每个指标的最佳模型
        best_models = {}
        for metric in comparison_df.columns:
            if metric in ['mse', 'rmse', 'mae']:
                # 这些指标越小越好
                best_models[metric] = comparison_df[metric].idxmin()
            else:
                # 这些指标越大越好
                best_models[metric] = comparison_df[metric].idxmax()
        
        print("\n最佳模型:")
        for metric, best_model in best_models.items():
            print(f"{metric}: {best_model}")
        
        return comparison_df, best_models
    
    def plot_prediction_vs_actual(self, y_true, y_pred, model_name='model'):
        """
        绘制预测值与实际值的对比图
        
        Args:
            y_true: 实际值
            y_pred: 预测值
            model_name: 模型名称
        """
        plt.figure(figsize=(12, 6))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        plt.xlabel('实际值')
        plt.ylabel('预测值')
        plt.title(f'{model_name} 预测值与实际值对比')
        plt.grid(True)
        plt.savefig(f'validation/{model_name}_prediction_vs_actual.png')
        plt.close()
    
    def plot_returns_distribution(self, returns, title='收益率分布'):
        """
        绘制收益率分布图
        
        Args:
            returns: 收益率序列
            title: 图表标题
        """
        plt.figure(figsize=(10, 6))
        plt.hist(returns, bins=50, alpha=0.7)
        plt.xlabel('收益率')
        plt.ylabel('频率')
        plt.title(title)
        plt.grid(True)
        plt.savefig(f'validation/{title.replace(" ", "_").lower()}.png')
        plt.close()
    
    def get_validation_report(self):
        """
        获取验证报告
        
        Returns:
            report: 验证报告
        """
        report = """
        模型验证报告
        """
        report += "=" * 80 + "\n"
        report += "模型验证报告\n"
        report += "=" * 80 + "\n"
        
        for model_name, metrics in self.validation_results.items():
            report += f"\n{model_name}:\n"
            report += "-" * 40 + "\n"
            for metric, value in metrics.items():
                if isinstance(value, float):
                    report += f"{metric}: {value:.4f}\n"
                else:
                    report += f"{metric}: {value}\n"
        
        report += "=" * 80 + "\n"
        
        # 保存报告到文件
        with open('validation/validation_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
    
    def stability_test(self, predictions, actuals, window_size=20, model_name='model'):
        """
        稳定性测试：测试模型在不同时间窗口的稳定性
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            window_size: 时间窗口大小
            model_name: 模型名称
            
        Returns:
            stability_results: 稳定性测试结果
        """
        print(f"\n稳定性测试 {model_name}")
        print("=" * 60)
        
        n = len(predictions)
        ic_values = []
        direction_acc_values = []
        
        # 滑动窗口计算IC和方向准确率
        for i in range(window_size, n):
            window_pred = predictions[i-window_size:i]
            window_actual = actuals[i-window_size:i]
            
            window_ic = np.corrcoef(window_pred, window_actual)[0, 1] if len(window_pred) > 1 else 0
            window_direction_acc = np.mean(np.sign(window_pred) == np.sign(window_actual))
            
            ic_values.append(window_ic)
            direction_acc_values.append(window_direction_acc)
        
        ic_values = np.array(ic_values)
        direction_acc_values = np.array(direction_acc_values)
        
        stability_results = {
            'ic_mean': np.mean(ic_values),
            'ic_std': np.std(ic_values),
            'ic_min': np.min(ic_values),
            'ic_max': np.max(ic_values),
            'direction_acc_mean': np.mean(direction_acc_values),
            'direction_acc_std': np.std(direction_acc_values),
            'direction_acc_min': np.min(direction_acc_values),
            'direction_acc_max': np.max(direction_acc_values),
            'stability_score': 1 - (np.std(ic_values) + np.std(direction_acc_values)) / 2
        }
        
        print(f"IC均值: {stability_results['ic_mean']:.4f}")
        print(f"IC标准差: {stability_results['ic_std']:.4f}")
        print(f"IC范围: [{stability_results['ic_min']:.4f}, {stability_results['ic_max']:.4f}]")
        print(f"方向准确率均值: {stability_results['direction_acc_mean']:.4f}")
        print(f"方向准确率标准差: {stability_results['direction_acc_std']:.4f}")
        print(f"稳定性得分: {stability_results['stability_score']:.4f}")
        
        # 保存结果
        self.validation_results[f'{model_name}_stability'] = stability_results
        
        return stability_results
    
    def group_test(self, predictions, actuals, groups=None, model_name='model'):
        """
        分组测试：测试模型在不同分组的表现
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            groups: 分组标签，如果为None则按预测值强度分组
            model_name: 模型名称
            
        Returns:
            group_results: 分组测试结果
        """
        print(f"\n分组测试 {model_name}")
        print("=" * 60)
        
        if groups is None:
            # 按预测值强度分组
            pred_abs = np.abs(predictions)
            q1, q2, q3 = np.percentile(pred_abs, [25, 50, 75])
            
            groups = np.where(pred_abs <= q1, 'weak',
                           np.where(pred_abs <= q2, 'moderate',
                                   np.where(pred_abs <= q3, 'strong', 'very_strong')))
        
        unique_groups = np.unique(groups)
        group_results = {}
        
        for group in unique_groups:
            mask = groups == group
            group_pred = predictions[mask]
            group_actual = actuals[mask]
            
            if len(group_pred) > 1:
                group_ic = np.corrcoef(group_pred, group_actual)[0, 1]
                group_direction_acc = np.mean(np.sign(group_pred) == np.sign(group_actual))
                group_mse = mean_squared_error(group_actual, group_pred)
                group_avg_return = np.mean(group_actual)
                
                group_results[group] = {
                    'count': len(group_pred),
                    'ic': group_ic,
                    'direction_accuracy': group_direction_acc,
                    'mse': group_mse,
                    'avg_return': group_avg_return
                }
                
                print(f"{group}组: 样本数={len(group_pred)}, IC={group_ic:.4f}, "
                      f"方向准确率={group_direction_acc:.4f}, 平均收益率={group_avg_return:.4f}")
        
        # 保存结果
        self.validation_results[f'{model_name}_group'] = group_results
        
        return group_results
    
    def overfitting_test(self, train_predictions, train_actuals, 
                        test_predictions, test_actuals, model_name='model'):
        """
        过拟合检测：比较训练集和测试集的表现
        
        Args:
            train_predictions: 训练集预测值
            train_actuals: 训练集实际值
            test_predictions: 测试集预测值
            test_actuals: 测试集实际值
            model_name: 模型名称
            
        Returns:
            overfitting_results: 过拟合检测结果
        """
        print(f"\n过拟合检测 {model_name}")
        print("=" * 60)
        
        # 计算训练集指标
        train_mse = mean_squared_error(train_actuals, train_predictions)
        train_r2 = r2_score(train_actuals, train_predictions)
        train_ic = np.corrcoef(train_predictions, train_actuals)[0, 1] if len(train_predictions) > 1 else 0
        
        # 计算测试集指标
        test_mse = mean_squared_error(test_actuals, test_predictions)
        test_r2 = r2_score(test_actuals, test_predictions)
        test_ic = np.corrcoef(test_predictions, test_actuals)[0, 1] if len(test_predictions) > 1 else 0
        
        # 计算过拟合程度
        mse_ratio = test_mse / train_mse if train_mse > 0 else float('inf')
        r2_diff = train_r2 - test_r2
        ic_diff = train_ic - test_ic
        
        # 判断是否过拟合
        overfitting_level = 'none'
        if mse_ratio > 2 or r2_diff > 0.3 or ic_diff > 0.2:
            overfitting_level = 'severe'
        elif mse_ratio > 1.5 or r2_diff > 0.2 or ic_diff > 0.1:
            overfitting_level = 'moderate'
        elif mse_ratio > 1.2 or r2_diff > 0.1 or ic_diff > 0.05:
            overfitting_level = 'mild'
        
        overfitting_results = {
            'train_mse': train_mse,
            'train_r2': train_r2,
            'train_ic': train_ic,
            'test_mse': test_mse,
            'test_r2': test_r2,
            'test_ic': test_ic,
            'mse_ratio': mse_ratio,
            'r2_diff': r2_diff,
            'ic_diff': ic_diff,
            'overfitting_level': overfitting_level
        }
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}, IC: {train_ic:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}, IC: {test_ic:.4f}")
        print(f"MSE比率: {mse_ratio:.4f}")
        print(f"R²差异: {r2_diff:.4f}")
        print(f"IC差异: {ic_diff:.4f}")
        print(f"过拟合程度: {overfitting_level}")
        
        # 保存结果
        self.validation_results[f'{model_name}_overfitting'] = overfitting_results
        
        return overfitting_results
    
    def time_decay_test(self, predictions, actuals, time_indices=None, model_name='model'):
        """
        时间衰减测试：测试预测能力随时间的变化
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            time_indices: 时间索引，如果为None则使用序列索引
            model_name: 模型名称
            
        Returns:
            decay_results: 时间衰减测试结果
        """
        print(f"\n时间衰减测试 {model_name}")
        print("=" * 60)
        
        if time_indices is None:
            time_indices = np.arange(len(predictions))
        
        n = len(predictions)
        decay_periods = [1, 5, 10, 20, 40]
        decay_results = {}
        
        for period in decay_periods:
            if period >= n:
                continue
            
            # 计算前period期的IC
            early_pred = predictions[:period]
            early_actual = actuals[:period]
            early_ic = np.corrcoef(early_pred, early_actual)[0, 1] if len(early_pred) > 1 else 0
            
            # 计算后period期的IC
            late_pred = predictions[-period:]
            late_actual = actuals[-period:]
            late_ic = np.corrcoef(late_pred, late_actual)[0, 1] if len(late_pred) > 1 else 0
            
            # 计算整体IC
            overall_ic = np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0
            
            decay_results[f'period_{period}'] = {
                'early_ic': early_ic,
                'late_ic': late_ic,
                'ic_decay': early_ic - late_ic,
                'overall_ic': overall_ic
            }
            
            print(f"周期{period}: 早期IC={early_ic:.4f}, 晚期IC={late_ic:.4f}, "
                  f"衰减={early_ic - late_ic:.4f}")
        
        # 保存结果
        self.validation_results[f'{model_name}_decay'] = decay_results
        
        return decay_results
    
    def outlier_detection(self, predictions, actuals, threshold=3, model_name='model'):
        """
        异常值检测：检测预测和实际值中的异常值
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            threshold: 异常值阈值（标准差倍数）
            model_name: 模型名称
            
        Returns:
            outlier_results: 异常值检测结果
        """
        print(f"\n异常值检测 {model_name}")
        print("=" * 60)
        
        # 计算预测误差
        errors = predictions - actuals
        
        # 检测异常值
        error_mean = np.mean(errors)
        error_std = np.std(errors)
        outlier_mask = np.abs(errors - error_mean) > threshold * error_std
        
        # 检测预测值异常
        pred_mean = np.mean(predictions)
        pred_std = np.std(predictions)
        pred_outlier_mask = np.abs(predictions - pred_mean) > threshold * pred_std
        
        # 检测实际值异常
        actual_mean = np.mean(actuals)
        actual_std = np.std(actuals)
        actual_outlier_mask = np.abs(actuals - actual_mean) > threshold * actual_std
        
        outlier_results = {
            'error_outliers': {
                'count': np.sum(outlier_mask),
                'percentage': np.mean(outlier_mask) * 100,
                'indices': np.where(outlier_mask)[0].tolist()
            },
            'prediction_outliers': {
                'count': np.sum(pred_outlier_mask),
                'percentage': np.mean(pred_outlier_mask) * 100,
                'indices': np.where(pred_outlier_mask)[0].tolist()
            },
            'actual_outliers': {
                'count': np.sum(actual_outlier_mask),
                'percentage': np.mean(actual_outlier_mask) * 100,
                'indices': np.where(actual_outlier_mask)[0].tolist()
            },
            'error_stats': {
                'mean': error_mean,
                'std': error_std,
                'min': np.min(errors),
                'max': np.max(errors)
            }
        }
        
        print(f"误差异常值: {outlier_results['error_outliers']['count']} "
              f"({outlier_results['error_outliers']['percentage']:.2f}%)")
        print(f"预测值异常值: {outlier_results['prediction_outliers']['count']} "
              f"({outlier_results['prediction_outliers']['percentage']:.2f}%)")
        print(f"实际值异常值: {outlier_results['actual_outliers']['count']} "
              f"({outlier_results['actual_outliers']['percentage']:.2f}%)")
        
        # 保存结果
        self.validation_results[f'{model_name}_outliers'] = outlier_results
        
        return outlier_results
    
    def plot_ic_over_time(self, predictions, actuals, window_size=20, model_name='model'):
        """
        绘制IC随时间变化图
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            window_size: 时间窗口大小
            model_name: 模型名称
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        n = len(predictions)
        ic_values = []
        
        # 滑动窗口计算IC
        for i in range(window_size, n):
            window_pred = predictions[i-window_size:i]
            window_actual = actuals[i-window_size:i]
            window_ic = np.corrcoef(window_pred, window_actual)[0, 1] if len(window_pred) > 1 else 0
            ic_values.append(window_ic)
        
        plt.figure(figsize=(12, 6))
        plt.plot(range(window_size, n), ic_values, linewidth=2)
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        plt.axhline(y=np.mean(ic_values), color='g', linestyle='--', alpha=0.5, label=f'均值={np.mean(ic_values):.4f}')
        plt.xlabel('时间')
        plt.ylabel('IC')
        plt.title(f'{model_name} - IC随时间变化（窗口={window_size}）')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'validation/{model_name}_ic_over_time.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_prediction_vs_actual_scatter(self, predictions, actuals, model_name='model'):
        """
        绘制预测值与实际值的散点图
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            model_name: 模型名称
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        plt.figure(figsize=(10, 10))
        plt.scatter(actuals, predictions, alpha=0.5, s=20)
        
        # 添加对角线
        min_val = min(np.min(predictions), np.min(actuals))
        max_val = max(np.max(predictions), np.max(actuals))
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='完美预测')
        
        # 添加回归线
        z = np.polyfit(actuals, predictions, 1)
        p = np.poly1d(z)
        plt.plot(actuals, p(actuals), "g--", linewidth=2, label=f'回归线 (斜率={z[0]:.4f})')
        
        # 计算IC
        ic = np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0
        
        plt.xlabel('实际值')
        plt.ylabel('预测值')
        plt.title(f'{model_name} - 预测值 vs 实际值 (IC={ic:.4f})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'validation/{model_name}_prediction_vs_actual_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_error_distribution(self, predictions, actuals, model_name='model'):
        """
        绘制误差分布图
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            model_name: 模型名称
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        errors = predictions - actuals
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # 误差直方图
        axes[0].hist(errors, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0].axvline(x=0, color='r', linestyle='--', linewidth=2)
        axes[0].axvline(x=np.mean(errors), color='g', linestyle='--', linewidth=2, label=f'均值={np.mean(errors):.4f}')
        axes[0].set_xlabel('误差')
        axes[0].set_ylabel('频率')
        axes[0].set_title('误差分布')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Q-Q图
        from scipy import stats
        stats.probplot(errors, dist="norm", plot=axes[1])
        axes[1].set_title('Q-Q图')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'validation/{model_name}_error_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_cumulative_returns(self, predictions, actuals, model_name='model'):
        """
        绘制累计收益率图
        
        Args:
            predictions: 预测值序列
            actuals: 实际值序列
            model_name: 模型名称
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        # 计算策略收益率
        strategy_returns = np.sign(predictions) * actuals
        
        # 计算累计收益率
        cumulative_actual = np.cumprod(1 + actuals) - 1
        cumulative_strategy = np.cumprod(1 + strategy_returns) - 1
        
        plt.figure(figsize=(12, 6))
        plt.plot(cumulative_actual, label='基准累计收益率', linewidth=2)
        plt.plot(cumulative_strategy, label='策略累计收益率', linewidth=2)
        plt.xlabel('时间')
        plt.ylabel('累计收益率')
        plt.title(f'{model_name} - 累计收益率对比')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'validation/{model_name}_cumulative_returns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def reset(self):
        """重置验证结果"""
        self.validation_results = {}
        print("验证结果已重置")

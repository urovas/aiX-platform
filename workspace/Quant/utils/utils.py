#!/usr/bin/env python3
"""
量化交易工具函数库

功能：
1. 数据处理工具函数
2. 因子计算工具函数
3. 可视化工具函数
4. 性能分析工具函数

使用方法：
from utils import data_utils, plot_utils, performance_utils

作者：Clawdbot
日期：2026-02-14
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class DataUtils:
    """数据处理工具类"""
    
    @staticmethod
    def clean_data(df, columns=None, method='clip', threshold=3):
        """
        清理数据中的异常值
        
        参数:
            df: DataFrame, 输入数据
            columns: list, 要清理的列名
            method: str, 清理方法 ('clip', 'remove', 'winsorize')
            threshold: float, 标准差阈值
            
        返回:
            DataFrame, 清理后的数据
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        cleaned_df = df.copy()
        
        for col in columns:
            if col not in cleaned_df.columns:
                continue
                
            # 替换无穷大值为NaN
            cleaned_df[col] = cleaned_df[col].replace([np.inf, -np.inf], np.nan)
            
            if method == 'clip':
                # 截断法：将极端值截断到阈值范围内
                mean = cleaned_df[col].mean()
                std = cleaned_df[col].std()
                if std > 0:
                    cleaned_df[col] = cleaned_df[col].clip(
                        lower=mean - threshold * std,
                        upper=mean + threshold * std
                    )
                    
            elif method == 'remove':
                # 删除法：删除极端值所在的行
                mean = cleaned_df[col].mean()
                std = cleaned_df[col].std()
                if std > 0:
                    lower_bound = mean - threshold * std
                    upper_bound = mean + threshold * std
                    cleaned_df = cleaned_df[
                        (cleaned_df[col] >= lower_bound) & 
                        (cleaned_df[col] <= upper_bound)
                    ]
                    
            elif method == 'winsorize':
                # 缩尾法：将极端值替换为边界值
                lower_bound = cleaned_df[col].quantile(0.01)
                upper_bound = cleaned_df[col].quantile(0.99)
                cleaned_df[col] = cleaned_df[col].clip(
                    lower=lower_bound,
                    upper=upper_bound
                )
        
        return cleaned_df
    
    @staticmethod
    def calculate_returns(df, price_col='close', periods=[1, 5, 10, 20]):
        """
        计算多周期收益率
        
        参数:
            df: DataFrame, 价格数据
            price_col: str, 价格列名
            periods: list, 计算周期列表
            
        返回:
            DataFrame, 包含收益率的数据
        """
        returns_df = df.copy()
        
        for period in periods:
            returns_df[f'return_{period}d'] = returns_df.groupby('stock_code')[price_col].pct_change(period)
        
        return returns_df
    
    @staticmethod
    def calculate_rolling_stats(df, value_col, window=20, stats=['mean', 'std', 'min', 'max']):
        """
        计算滚动统计量
        
        参数:
            df: DataFrame, 输入数据
            value_col: str, 值列名
            window: int, 窗口大小
            stats: list, 统计量列表
            
        返回:
            DataFrame, 包含滚动统计量的数据
        """
        stats_df = df.copy()
        
        for stat in stats:
            if stat == 'mean':
                stats_df[f'{value_col}_ma{window}'] = stats_df.groupby('stock_code')[value_col].rolling(window).mean()
            elif stat == 'std':
                stats_df[f'{value_col}_std{window}'] = stats_df.groupby('stock_code')[value_col].rolling(window).std()
            elif stat == 'min':
                stats_df[f'{value_col}_min{window}'] = stats_df.groupby('stock_code')[value_col].rolling(window).min()
            elif stat == 'max':
                stats_df[f'{value_col}_max{window}'] = stats_df.groupby('stock_code')[value_col].rolling(window).max()
        
        return stats_df
    
    @staticmethod
    def normalize_data(df, columns=None, method='standard'):
        """
        标准化数据
        
        参数:
            df: DataFrame, 输入数据
            columns: list, 要标准化的列名
            method: str, 标准化方法 ('standard', 'minmax', 'robust')
            
        返回:
            tuple, (标准化后的数据, 标准化器)
        """
        from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            raise ValueError(f"未知的标准化方法: {method}")
        
        scaled_data = scaler.fit_transform(df[columns].values)
        normalized_df = df.copy()
        normalized_df[columns] = scaled_data
        
        return normalized_df, scaler
    
    @staticmethod
    def split_data(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        按时间分割数据集
        
        参数:
            df: DataFrame, 输入数据
            train_ratio: float, 训练集比例
            val_ratio: float, 验证集比例
            test_ratio: float, 测试集比例
            
        返回:
            tuple, (train_df, val_df, test_df)
        """
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
            raise ValueError("比例之和必须为1.0")
        
        df_sorted = df.sort_values('date').reset_index(drop=True)
        n = len(df_sorted)
        
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_df = df_sorted.iloc[:train_end]
        val_df = df_sorted.iloc[train_end:val_end]
        test_df = df_sorted.iloc[val_end:]
        
        return train_df, val_df, test_df

class PlotUtils:
    """可视化工具类"""
    
    @staticmethod
    def setup_plot_style(style='whitegrid', figsize=(12, 8)):
        """
        设置图表样式
        
        参数:
            style: str, 样式名称
            figsize: tuple, 图表大小
        """
        sns.set_style(style)
        plt.rcParams['figure.figsize'] = figsize
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
    
    @staticmethod
    def plot_factor_ic(ic_results, save_path='factor_ic_analysis.png'):
        """
        绘制因子IC分析图表
        
        参数:
            ic_results: DataFrame, IC测试结果
            save_path: str, 保存路径
        """
        PlotUtils.setup_plot_style()
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # IC均值条形图
        ic_summary = ic_results.groupby('factor')['ic'].mean().sort_values(ascending=False)
        colors = ['#4CAF50' if x > 0 else '#F44336' for x in ic_summary.values]
        
        axes[0].bar(ic_summary.index, ic_summary.values, color=colors)
        axes[0].set_title('因子IC均值分布')
        axes[0].set_xlabel('因子')
        axes[0].set_ylabel('IC均值')
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].grid(axis='y', alpha=0.3)
        plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=45)
        
        # IC时间序列
        top_factors = ic_summary.head(5).index.tolist()
        for factor in top_factors:
            factor_ic = ic_results[ic_results['factor'] == factor]
            factor_ic['ic_ma'] = factor_ic['ic'].rolling(20).mean()
            axes[1].plot(factor_ic['date'], factor_ic['ic_ma'], label=factor)
        
        axes[1].set_title('Top 5 因子IC时间序列（20日移动平均）')
        axes[1].set_xlabel('日期')
        axes[1].set_ylabel('IC值')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"IC分析图表已保存到 {save_path}")
    
    @staticmethod
    def plot_correlation_heatmap(df, save_path='correlation_heatmap.png'):
        """
        绘制相关性热力图
        
        参数:
            df: DataFrame, 相关性数据
            save_path: str, 保存路径
        """
        PlotUtils.setup_plot_style()
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(df.corr(), annot=True, fmt='.2f', cmap='coolwarm', center=0)
        plt.title('相关性热力图')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"相关性热力图已保存到 {save_path}")
    
    @staticmethod
    def plot_backtest_results(backtest_df, save_path='backtest_results.png'):
        """
        绘制回测结果图表
        
        参数:
            backtest_df: DataFrame, 回测结果
            save_path: str, 保存路径
        """
        PlotUtils.setup_plot_style()
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 计算累计收益
        backtest_df['cumulative_return'] = (backtest_df['avg_return'] + 1).cumprod() - 1
        
        # 累计收益率曲线
        axes[0].plot(backtest_df['date'], backtest_df['cumulative_return'], linewidth=2, color='#2196F3')
        axes[0].set_title('策略累计收益率')
        axes[0].set_xlabel('日期')
        axes[0].set_ylabel('累计收益率')
        axes[0].grid(alpha=0.3)
        
        # 回撤曲线
        cumulative = backtest_df['cumulative_return'] + 1
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        
        axes[1].fill_between(backtest_df['date'], drawdown, 0, color='#FF5252', alpha=0.5)
        axes[1].set_title('策略回撤曲线')
        axes[1].set_xlabel('日期')
        axes[1].set_ylabel('回撤')
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"回测结果图表已保存到 {save_path}")

class PerformanceUtils:
    """性能分析工具类"""
    
    @staticmethod
    def calculate_ic(df, factor_col, target_col='next_return', method='spearman'):
        """
        计算IC值
        
        参数:
            df: DataFrame, 输入数据
            factor_col: str, 因子列名
            target_col: str, 目标列名
            method: str, 计算方法 ('spearman', 'pearson')
            
        返回:
            float, IC值
        """
        valid_data = df[[factor_col, target_col]].dropna()
        
        if method == 'spearman':
            ic, _ = stats.spearmanr(valid_data[factor_col], valid_data[target_col])
        elif method == 'pearson':
            ic, _ = stats.pearsonr(valid_data[factor_col], valid_data[target_col])
        else:
            raise ValueError(f"未知的IC计算方法: {method}")
        
        return ic
    
    @staticmethod
    def calculate_performance_metrics(returns):
        """
        计算性能指标
        
        参数:
            returns: Series, 收益率序列
            
        返回:
            dict, 性能指标字典
        """
        metrics = {}
        
        # 总收益率
        metrics['total_return'] = (returns + 1).prod() - 1
        
        # 年化收益率
        n_days = len(returns)
        metrics['annual_return'] = (1 + metrics['total_return']) ** (252 / n_days) - 1
        
        # 夏普比率
        metrics['sharpe_ratio'] = np.sqrt(252) * returns.mean() / returns.std()
        
        # 最大回撤
        cumulative = (returns + 1).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        metrics['max_drawdown'] = drawdown.min()
        
        # 胜率
        metrics['win_rate'] = (returns > 0).mean()
        
        # 平均盈利和亏损
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        metrics['avg_win'] = wins.mean() if len(wins) > 0 else 0
        metrics['avg_loss'] = losses.mean() if len(losses) > 0 else 0
        
        # 盈利因子
        metrics['profit_factor'] = abs(metrics['avg_win'] / metrics['avg_loss']) if metrics['avg_loss'] != 0 else float('inf')
        
        return metrics
    
    @staticmethod
    def generate_performance_report(metrics, save_path='performance_report.txt'):
        """
        生成性能报告
        
        参数:
            metrics: dict, 性能指标字典
            save_path: str, 保存路径
        """
        report = f"""
        策略性能报告
        {'=' * 60}
        
        总收益率: {metrics['total_return']:.4f}
        年化收益率: {metrics['annual_return']:.4f}
        夏普比率: {metrics['sharpe_ratio']:.4f}
        最大回撤: {metrics['max_drawdown']:.4f}
        胜率: {metrics['win_rate']:.4f}
        平均盈利: {metrics['avg_win']:.4f}
        平均亏损: {metrics['avg_loss']:.4f}
        盈利因子: {metrics['profit_factor']:.4f}
        
        {'=' * 60}
        """
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"性能报告已保存到 {save_path}")

# 便捷函数
def clean_data(df, columns=None, method='clip', threshold=3):
    """清理数据异常值"""
    return DataUtils.clean_data(df, columns, method, threshold)

def calculate_returns(df, price_col='close', periods=[1, 5, 10, 20]):
    """计算多周期收益率"""
    return DataUtils.calculate_returns(df, price_col, periods)

def normalize_data(df, columns=None, method='standard'):
    """标准化数据"""
    return DataUtils.normalize_data(df, columns, method)

def plot_factor_ic(ic_results, save_path='factor_ic_analysis.png'):
    """绘制因子IC分析图表"""
    return PlotUtils.plot_factor_ic(ic_results, save_path)

def plot_correlation_heatmap(df, save_path='correlation_heatmap.png'):
    """绘制相关性热力图"""
    return PlotUtils.plot_correlation_heatmap(df, save_path)

def plot_backtest_results(backtest_df, save_path='backtest_results.png'):
    """绘制回测结果图表"""
    return PlotUtils.plot_backtest_results(backtest_df, save_path)

def calculate_performance_metrics(returns):
    """计算性能指标"""
    return PerformanceUtils.calculate_performance_metrics(returns)

def generate_performance_report(metrics, save_path='performance_report.txt'):
    """生成性能报告"""
    return PerformanceUtils.generate_performance_report(metrics, save_path)
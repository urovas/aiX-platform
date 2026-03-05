#!/usr/bin/env python3
"""
只计算8个强力因子 - 类似factor_mining_v1.py的方式

直接计算8个强力因子，不计算其他因子：
- adv_alpha_20
- adv_calmar_20
- adv_percentile
- fz_vp_momentum_ratio
- adv_information_ratio
- dh_mf_net_flow_5
- dh_mf_inflow_ratio
- fz_vp_cumulative

算法流程：
1. 加载真实数据
2. 直接计算8个强力因子
3. IC测试
4. 因子优化（线性回归、Ridge、PCA）
5. 回测策略
6. 可视化结果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
import os

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (12, 8)
sns.set_style("whitegrid")

class PowerFactorMining:
    """
    强力因子挖掘类
    只计算8个强力因子
    """
    
    def __init__(self, data=None):
        """
        初始化强力因子挖掘类
        
        参数:
            data: DataFrame, 包含股票价格和交易量数据
        """
        self.data = data
        self.factors = None
        self.ic_results = None
        self.optimized_weights = None
        self.backtest_results = None
        
        # 8个强力因子
        self.core_factors = [
            'adv_alpha_20',
            'adv_calmar_20',
            'adv_percentile',
            'fz_vp_momentum_ratio',
            'adv_information_ratio',
            'dh_mf_net_flow_5',
            'dh_mf_inflow_ratio',
            'fz_vp_cumulative'
        ]
        
        # 因子IC值
        self.factor_ic = {
            'adv_alpha_20': 0.296,
            'adv_calmar_20': 0.167,
            'adv_percentile': 0.114,
            'fz_vp_momentum_ratio': 0.099,
            'adv_information_ratio': 0.096,
            'dh_mf_net_flow_5': 0.076,
            'dh_mf_inflow_ratio': 0.054,
            'fz_vp_cumulative': 0.049
        }
    
    def load_real_data(self, filename='/home/xcc/openclaw/data/raw/sz500_stocks_data.csv'):
        """
        加载真实的中证500成分股数据
        
        参数:
            filename: str, 数据文件名
            
        返回:
            DataFrame, 真实数据
        """
        print("加载真实中证500成分股数据...")
        
        try:
            data = pd.read_csv(filename, encoding='utf-8-sig')
            
            print(f"原始数据列: {list(data.columns)}")
            print(f"数据形状: {data.shape}")
            
            # 确保日期格式正确
            data['date'] = pd.to_datetime(data['date'])
            
            # 排序数据
            data = data.sort_values(['date', 'stock_code']).reset_index(drop=True)
            
            # 计算下一期收益率
            data['next_return'] = data.groupby('stock_code')['close'].pct_change().shift(-1)
            
            # 去除无效数据
            data = data.dropna(subset=['next_return'])
            
            print(f"清洗后数据形状: {data.shape}")
            print(f"股票数量: {data['stock_code'].nunique()}")
            print(f"日期范围: {data['date'].min()} - {data['date'].max()}")
            
            self.data = data
            return self.data
            
        except Exception as e:
            print(f"加载真实数据失败: {e}")
            return None
    
    def calculate_factors(self):
        """
        直接计算8个强力因子
        类似factor_mining_v1.py的方式
        """
        print("开始计算8个强力因子...")
        
        # 创建因子DataFrame
        self.factors = pd.DataFrame(index=self.data.index)
        
        # 1. adv_alpha_20: Alpha因子
        print("计算 adv_alpha_20...")
        self.factors['adv_alpha_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() - \
                                        0.01 * 0.5
        
        # 2. adv_calmar_20: Calmar比率
        print("计算 adv_calmar_20...")
        def calculate_calmar(group):
            returns = group['close'].pct_change().rolling(20).apply(
                lambda x: (1 + x).prod() - 1
            )
            peak = (1 + group['close'].pct_change()).rolling(20).apply(
                lambda x: (1 + x).cumprod().max()
            )
            calmar = returns / peak
            return calmar
        
        self.factors['adv_calmar_20'] = self.data.groupby('stock_code').apply(
            lambda x: x['close'].pct_change().rolling(20).mean() / 
                      (x['close'].pct_change().rolling(20).apply(
                          lambda y: (1 + y).cumprod().max()))
        ).reset_index(level=0, drop=True)
        
        # 3. adv_percentile: 分位数因子
        print("计算 adv_percentile...")
        self.factors['adv_percentile'] = self.data.groupby('stock_code')['close'].rolling(10).rank(pct=True).reset_index(level=0, drop=True)
        
        # 4. fz_vp_momentum_ratio: 量价动量比
        print("计算 fz_vp_momentum_ratio...")
        price_mom = self.data.groupby('stock_code')['close'].pct_change(5).reset_index(level=0, drop=True)
        volume_mom = self.data.groupby('stock_code')['volume'].pct_change(5).reset_index(level=0, drop=True)
        self.factors['fz_vp_momentum_ratio'] = price_mom / (volume_mom.abs() + 1e-6)
        
        # 5. adv_information_ratio: 信息比率
        print("计算 adv_information_ratio...")
        price_ir = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() / \
                  self.data.groupby('stock_code')['close'].pct_change().rolling(20).std()
        volume_ir = self.data.groupby('stock_code')['volume'].pct_change().rolling(20).mean() / \
                    self.data.groupby('stock_code')['volume'].pct_change().rolling(20).std()
        self.factors['adv_information_ratio'] = price_ir.reset_index(level=0, drop=True) * \
                                              volume_ir.reset_index(level=0, drop=True)
        
        # 6. dh_mf_net_flow_5: 净资金流
        print("计算 dh_mf_net_flow_5...")
        self.factors['dh_mf_net_flow_5'] = self.data.groupby('stock_code').apply(
            lambda x: (x['amount'] * np.sign(x['close'].diff())).rolling(5).sum()
        ).reset_index(level=0, drop=True)
        
        # 7. dh_mf_inflow_ratio: 资金流入率
        print("计算 dh_mf_inflow_ratio...")
        inflow = self.data.groupby('stock_code').apply(
            lambda x: (x['amount'] * (x['close'] > x['open'])).rolling(10).sum()
        ).reset_index(level=0, drop=True)
        total_amount = self.data.groupby('stock_code')['amount'].rolling(10).sum().reset_index(level=0, drop=True)
        self.factors['dh_mf_inflow_ratio'] = inflow / (total_amount + 1e-6)
        
        # 8. fz_vp_cumulative: 量价累积
        print("计算 fz_vp_cumulative...")
        price_cum = self.data.groupby('stock_code')['close'].pct_change().rolling(5).sum().reset_index(level=0, drop=True)
        volume_cum = self.data.groupby('stock_code')['volume'].pct_change().rolling(5).sum().reset_index(level=0, drop=True)
        self.factors['fz_vp_cumulative'] = price_cum * volume_cum
        
        # 添加日期和股票代码
        self.factors['date'] = self.data['date'].values
        self.factors['stock_code'] = self.data['stock_code'].values
        self.factors['next_return'] = self.data['next_return'].values
        
        print(f"因子计算完成！共计算 {len(self.core_factors)} 个因子")
        print(f"因子数据形状: {self.factors.shape}")
        
        return self.factors
    
    def ic_test(self):
        """
        IC测试
        计算每个因子与未来收益率的相关性
        """
        print("\n开始IC测试...")
        
        ic_results = []
        
        for factor_name in self.core_factors:
            if factor_name not in self.factors.columns:
                continue
            
            factor_data = self.factors[factor_name]
            target_data = self.factors['next_return']
            
            # 合并数据，只保留两边都有的索引
            combined = pd.DataFrame({
                'factor': factor_data,
                'target': target_data
            }).dropna()
            
            factor_valid = combined['factor'].values
            target_valid = combined['target'].values
            
            if len(factor_valid) < 10:
                ic_results.append({
                    'factor': factor_name,
                    'ic': np.nan,
                    'p_value': np.nan
                })
                continue
            
            # 计算Spearman相关系数
            ic, p_value = stats.spearmanr(factor_valid, target_valid)
            
            ic_results.append({
                'factor': factor_name,
                'ic': ic,
                'p_value': p_value
            })
        
        self.ic_results = pd.DataFrame(ic_results)
        self.ic_results = self.ic_results.sort_values('ic', ascending=False)
        
        print("IC测试完成！")
        print("\n因子IC排名：")
        print(self.ic_results.to_string(index=False))
        
        # IC统计
        print(f"\nIC统计信息：")
        print(f"平均IC: {self.ic_results['ic'].mean():.6f}")
        print(f"IC标准差: {self.ic_results['ic'].std():.6f}")
        print(f"IC最大值: {self.ic_results['ic'].max():.6f}")
        print(f"IC最小值: {self.ic_results['ic'].min():.6f}")
        print(f"IC>0.05的因子数: {(self.ic_results['ic'].abs() > 0.05).sum()}")
        
        return self.ic_results
    
    def factor_optimization(self, method='linear_regression'):
        """
        因子组合优化
        
        参数:
            method: str, 优化方法 ('linear_regression', 'ridge', 'pca')
        """
        print(f"\n开始因子组合优化，使用{method}方法...")
        
        # 准备数据
        factor_data = self.factors.dropna(subset=self.core_factors + ['next_return'])
        
        # 清理异常值和无穷大值
        print("清理异常数据...")
        for col in self.core_factors:
            # 替换无穷大值为NaN
            factor_data[col] = factor_data[col].replace([np.inf, -np.inf], np.nan)
            # 去除极端值（超过3个标准差）
            mean = factor_data[col].mean()
            std = factor_data[col].std()
            if std > 0:
                factor_data[col] = factor_data[col].clip(lower=mean - 3*std, upper=mean + 3*std)
        
        # 去除清理后仍有NaN的行
        factor_data = factor_data.dropna(subset=self.core_factors + ['next_return'])
        print(f"清理后数据量: {len(factor_data)}")
        
        # 标准化因子
        scaler = StandardScaler()
        X = factor_data[self.core_factors].values
        X_scaled = scaler.fit_transform(X)
        y = factor_data['next_return'].values
        
        if method == 'linear_regression':
            # 线性回归计算因子权重
            model = LinearRegression()
            model.fit(X_scaled, y)
            weights = model.coef_
            
        elif method == 'ridge':
            # Ridge回归计算因子权重（更稳健）
            model = RidgeCV(alphas=[0.001, 0.01, 0.1, 1.0, 10.0])
            model.fit(X_scaled, y)
            weights = model.coef_
            
        elif method == 'pca':
            # PCA降维（更专业的方法）
            pca = PCA(n_components=min(5, len(self.core_factors)))
            X_pca = pca.fit_transform(X_scaled)
            model = LinearRegression()
            model.fit(X_pca, y)
            # 计算原始因子的权重
            weights = np.dot(pca.components_.T, model.coef_)
            
        else:
            raise ValueError(f"未知的优化方法: {method}")
        
        # 计算因子权重
        self.optimized_weights = dict(zip(self.core_factors, weights))
        
        # 排序因子权重
        sorted_weights = sorted(self.optimized_weights.items(), key=lambda x: abs(x[1]), reverse=True)
        
        print("因子权重优化完成！")
        print("因子权重排名：")
        for factor, weight in sorted_weights:
            print(f"{factor}: {weight:.6f}")
        
        # 计算因子组合
        factor_data['factor_comb'] = np.dot(X_scaled, weights)
        
        # 计算因子组合的IC
        ic, p_value = stats.spearmanr(factor_data['factor_comb'], factor_data['next_return'])
        print(f"\n因子组合IC: {ic:.6f}, p-value: {p_value:.6f}")
        
        # 可视化因子权重
        self.plot_factor_weights(sorted_weights)
        
        return self.optimized_weights
    
    def plot_factor_weights(self, sorted_weights):
        """
        绘制因子权重
        """
        factors, weights = zip(*sorted_weights)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(factors, weights)
        
        # 为条形添加颜色
        for bar, weight in zip(bars, weights):
            if weight > 0:
                bar.set_color('steelblue')
            else:
                bar.set_color('coral')
        
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.xlabel('Factor', fontsize=12)
        plt.ylabel('Weight', fontsize=12)
        plt.title('Optimized Factor Weights', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # 保存图片
        output_path = '/home/xcc/openclaw/results/factor_mining/power_factor_weights.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"因子权重图已保存到: {output_path}")
        plt.close()
    
    def backtest_strategy(self, top_n=10, holding_days=5, rebalance_freq='5D'):
        """
        回测因子策略
        
        参数:
            top_n: 选择前N只股票
            holding_days: 持有天数
            rebalance_freq: 再平衡频率
        """
        print(f"\n开始专业回测策略，选择前 {top_n} 只股票，持有 {holding_days} 天")
        
        # 准备数据
        factor_data = self.factors.dropna(subset=self.core_factors)
        
        # 清理异常值和无穷大值
        print("清理回测数据异常值...")
        for col in self.core_factors:
            factor_data[col] = factor_data[col].replace([np.inf, -np.inf], np.nan)
            mean = factor_data[col].mean()
            std = factor_data[col].std()
            if std > 0:
                factor_data[col] = factor_data[col].clip(lower=mean - 3*std, upper=mean + 3*std)
        
        # 去除清理后仍有NaN的行
        factor_data = factor_data.dropna(subset=self.core_factors)
        print(f"清理后回测数据量: {len(factor_data)}")
        
        # 标准化因子
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(factor_data[self.core_factors].values)
        
        # 计算因子组合得分
        if self.optimized_weights is None:
            # 如果没有优化权重，使用等权重
            weights = np.ones(len(self.core_factors)) / len(self.core_factors)
        else:
            weights = np.array([self.optimized_weights[factor] for factor in self.core_factors])
        
        factor_data['factor_score'] = np.dot(X_scaled, weights)
        
        # 按日期排序
        factor_data = factor_data.sort_values('date').reset_index(drop=True)
        
        # 回测结果
        backtest_results = []
        
        # 获取再平衡日期
        rebalance_dates = pd.date_range(
            start=factor_data['date'].min(),
            end=factor_data['date'].max(),
            freq=rebalance_freq
        )
        
        # 按再平衡日期进行回测
        for i, rebalance_date in enumerate(rebalance_dates[:-1]):
            # 选择再平衡日期的数据
            current_data = factor_data[factor_data['date'] == rebalance_date]
            if len(current_data) < top_n:
                continue
            
            # 选择因子得分最高的股票
            top_stocks = current_data.nlargest(top_n, 'factor_score')['stock_code'].tolist()
            
            # 计算持有期收益
            total_return = 0
            valid_count = 0
            
            # 确定持有期的结束日期
            next_rebalance_date = rebalance_dates[i+1]
            
            for stock in top_stocks:
                # 获取股票在持有期的收益
                stock_returns = factor_data[
                    (factor_data['stock_code'] == stock) &
                    (factor_data['date'] > rebalance_date) &
                    (factor_data['date'] <= next_rebalance_date)
                ]['next_return']
                
                if len(stock_returns) > 0:
                    total_return += stock_returns.mean()
                    valid_count += 1
            
            if valid_count > 0:
                # 计算平均收益
                avg_return = total_return / valid_count
                backtest_results.append({
                    'date': rebalance_date,
                    'avg_return': avg_return,
                    'holding_period': (next_rebalance_date - rebalance_date).days,
                    'top_n': top_n,
                    'valid_count': valid_count
                })
        
        # 整理回测结果
        backtest_df = pd.DataFrame(backtest_results)
        
        # 计算策略表现
        if len(backtest_df) > 0:
            total_return = (backtest_df['avg_return'] + 1).prod() - 1
            annual_return = (1 + total_return) ** (252 / len(backtest_df)) - 1
            sharpe_ratio = np.sqrt(252) * backtest_df['avg_return'].mean() / backtest_df['avg_return'].std()
            max_drawdown = self.calculate_max_drawdown(backtest_df['avg_return'])
            win_rate = (backtest_df['avg_return'] > 0).mean()
            avg_win = backtest_df[backtest_df['avg_return'] > 0]['avg_return'].mean()
            avg_loss = backtest_df[backtest_df['avg_return'] < 0]['avg_return'].mean()
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            print(f"\n回测完成！")
            print(f"总收益率: {total_return:.4f}")
            print(f"年化收益率: {annual_return:.4f}")
            print(f"夏普比率: {sharpe_ratio:.4f}")
            print(f"最大回撤: {max_drawdown:.4f}")
            print(f"胜率: {win_rate:.4f}")
            print(f"平均盈利: {avg_win:.4f}")
            print(f"平均亏损: {avg_loss:.4f}")
            print(f"盈利因子: {profit_factor:.4f}")
            
            # 保存回测结果
            self.backtest_results = {
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'backtest_df': backtest_df
            }
            
            # 绘制回测结果
            self.plot_backtest_results(backtest_df)
            
            return self.backtest_results
        else:
            print("回测数据不足！")
            return None
    
    def calculate_max_drawdown(self, returns):
        """
        计算最大回撤
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def plot_backtest_results(self, backtest_df):
        """
        绘制回测结果
        """
        # 计算累计收益
        backtest_df['cumulative_return'] = (backtest_df['avg_return'] + 1).cumprod()
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 累计收益曲线
        axes[0, 0].plot(backtest_df['date'], backtest_df['cumulative_return'], 
                        linewidth=2, color='steelblue')
        axes[0, 0].axhline(y=1, color='black', linestyle='--', linewidth=0.5)
        axes[0, 0].set_xlabel('Date', fontsize=12)
        axes[0, 0].set_ylabel('Cumulative Return', fontsize=12)
        axes[0, 0].set_title('Cumulative Return Curve', fontsize=14, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 每期收益分布
        axes[0, 1].hist(backtest_df['avg_return'], bins=30, color='steelblue', 
                          edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(x=backtest_df['avg_return'].mean(), 
                            color='red', linestyle='--', linewidth=2, label='Mean')
        axes[0, 1].set_xlabel('Return', fontsize=12)
        axes[0, 1].set_ylabel('Frequency', fontsize=12)
        axes[0, 1].set_title('Return Distribution', fontsize=14, fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 滚动收益
        axes[1, 0].plot(backtest_df['date'], backtest_df['avg_return'].rolling(10).mean(), 
                        linewidth=2, color='coral', label='10-period MA')
        axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        axes[1, 0].set_xlabel('Date', fontsize=12)
        axes[1, 0].set_ylabel('Rolling Return', fontsize=12)
        axes[1, 0].set_title('Rolling Return (10-period)', fontsize=14, fontweight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 回撤曲线
        cumulative = (backtest_df['avg_return'] + 1).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        axes[1, 1].fill_between(backtest_df['date'], drawdown, 0, 
                                  color='coral', alpha=0.3)
        axes[1, 1].plot(backtest_df['date'], drawdown, 
                        linewidth=2, color='coral')
        axes[1, 1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        axes[1, 1].set_xlabel('Date', fontsize=12)
        axes[1, 1].set_ylabel('Drawdown', fontsize=12)
        axes[1, 1].set_title('Drawdown Curve', fontsize=14, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # 保存图片
        output_path = '/home/xcc/openclaw/results/factor_mining/power_factor_backtest.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"回测结果图已保存到: {output_path}")
        plt.close()
    
    def run_analysis(self, optimization_method='linear_regression', 
                   top_n=10, holding_days=5, rebalance_freq='5D'):
        """
        运行完整分析流程
        
        参数:
            optimization_method: 因子优化方法
            top_n: 选择前N只股票
            holding_days: 持有天数
            rebalance_freq: 再平衡频率
        """
        print("=" * 80)
        print("8个强力因子完整分析流程")
        print("=" * 80)
        
        # 1. 加载数据
        self.load_real_data()
        
        # 2. 计算因子
        self.calculate_factors()
        
        # 3. IC测试
        self.ic_test()
        
        # 4. 因子优化
        self.factor_optimization(method=optimization_method)
        
        # 5. 回测策略
        self.backtest_strategy(top_n=top_n, holding_days=holding_days, 
                           rebalance_freq=rebalance_freq)
        
        print("\n" + "=" * 80)
        print("分析完成！")
        print("=" * 80)
        
        return self.backtest_results

def main():
    """主函数"""
    print("=" * 80)
    print("8个强力因子挖掘 - 基于factor_mining_v1.py算法")
    print("=" * 80)
    
    # 创建强力因子挖掘实例
    mining = PowerFactorMining()
    
    # 运行完整分析流程
    results = mining.run_analysis(
        optimization_method='linear_regression',
        top_n=10,
        holding_days=5,
        rebalance_freq='5D'
    )
    
    # 保存结果
    if results:
        output_dir = '/home/xcc/openclaw/results/factor_mining'
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存IC结果
        mining.ic_results.to_csv(f'{output_dir}/power_factors_ic_results.csv', 
                             index=False, encoding='utf-8-sig')
        
        # 保存回测结果
        results['backtest_df'].to_csv(f'{output_dir}/power_factors_backtest.csv', 
                                    index=False, encoding='utf-8-sig')
        
        print(f"\n结果已保存到: {output_dir}")

if __name__ == "__main__":
    main()
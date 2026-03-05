#!/usr/bin/env python3
"""
50个专业量化因子实现 - 方正、东海、中信建投系列

功能：
1. 方正11大量价因子（11个）
2. 东海资金流因子（10个）
3. 中信建投波动率因子（10个）
4. 其他高级因子（19个）

每个因子包含明确的输入输出格式

作者：Clawdbot & 72B Qwen Model
日期：2026-02-14
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class ProfessionalFactorCalculator:
    """专业量化因子计算器"""
    
    def __init__(self, data):
        """
        初始化因子计算器
        
        参数:
            data: DataFrame, 包含OHLCV数据
        """
        self.data = data.copy()
        self.factors = {}
        
    def calculate_all_factors(self):
        """计算所有50个因子"""
        print("开始计算50个专业量化因子...")
        
        # 1. 方正11大量价因子（11个）
        print("计算方正11大量价因子...")
        self.calculate_founder_volume_price_factors()
        
        # 2. 东海资金流因子（10个）
        print("计算东海资金流因子...")
        self.calculate_donghai_money_flow_factors()
        
        # 3. 中信建投波动率因子（10个）
        print("计算中信建投波动率因子...")
        self.calculate_citic_volatility_factors()
        
        # 4. 其他高级因子（19个）
        print("计算其他高级因子...")
        self.calculate_advanced_factors()
        
        print(f"因子计算完成！共计算 {len(self.factors)} 个因子")
        return self.factors
    
    def calculate_founder_volume_price_factors(self):
        """计算方正11大量价因子（11个）"""
        
        # FVP1: 量价相关性（方正风格）
        self.factors['fz_vp_corr_10'] = self.data.groupby('stock_code').apply(
            lambda x: x['close'].pct_change(10).rolling(10).corr(x['volume'].pct_change(10))
        ).reset_index(level=0, drop=True)
        
        # FVP2: 量价趋势强度
        price_trend = self.data.groupby('stock_code')['close'].pct_change(10).reset_index(level=0, drop=True)
        volume_trend = self.data.groupby('stock_code')['volume'].pct_change(10).reset_index(level=0, drop=True)
        self.factors['fz_vp_trend_strength'] = price_trend * volume_trend
        
        # FVP3: 量价背离度
        price_ma20 = self.data.groupby('stock_code')['close'].rolling(20).mean().reset_index(level=0, drop=True)
        volume_ma20 = self.data.groupby('stock_code')['volume'].rolling(20).mean().reset_index(level=0, drop=True)
        self.factors['fz_vp_divergence'] = (self.data['close'] - price_ma20) / price_ma20 - \
                                        (self.data['volume'] - volume_ma20) / volume_ma20
        
        # FVP4: 量价动量比
        price_mom = self.data.groupby('stock_code')['close'].pct_change(5).reset_index(level=0, drop=True)
        volume_mom = self.data.groupby('stock_code')['volume'].pct_change(5).reset_index(level=0, drop=True)
        self.factors['fz_vp_momentum_ratio'] = price_mom / (volume_mom.abs() + 1e-6)
        
        # FVP5: 量价波动比
        price_vol = self.data.groupby('stock_code')['close'].rolling(10).std().reset_index(level=0, drop=True)
        volume_vol = self.data.groupby('stock_code')['volume'].rolling(10).std().reset_index(level=0, drop=True)
        self.factors['fz_vp_volatility_ratio'] = price_vol / (volume_vol + 1e-6)
        
        # FVP6: 量价相对强度
        price_rs = self.data.groupby('stock_code')['close'].pct_change(20).reset_index(level=0, drop=True)
        volume_rs = self.data.groupby('stock_code')['volume'].pct_change(20).reset_index(level=0, drop=True)
        self.factors['fz_vp_relative_strength'] = price_rs * volume_rs
        
        # FVP7: 量价累积
        price_cum = self.data.groupby('stock_code')['close'].pct_change().rolling(5).sum().reset_index(level=0, drop=True)
        volume_cum = self.data.groupby('stock_code')['volume'].pct_change().rolling(5).sum().reset_index(level=0, drop=True)
        self.factors['fz_vp_cumulative'] = price_cum * volume_cum
        
        # FVP8: 量价乖离率
        price_ma10 = self.data.groupby('stock_code')['close'].rolling(10).mean().reset_index(level=0, drop=True)
        volume_ma10 = self.data.groupby('stock_code')['volume'].rolling(10).mean().reset_index(level=0, drop=True)
        self.factors['fz_vp_deviation'] = (self.data['close'] - price_ma10) / price_ma10 - \
                                      (self.data['volume'] - volume_ma10) / volume_ma10
        
        # FVP9: 量价能量
        price_energy = self.data.groupby('stock_code')['close'].pct_change().rolling(5).apply(
            lambda x: (x**2).sum()
        ).reset_index(level=0, drop=True)
        volume_energy = self.data.groupby('stock_code')['volume'].pct_change().rolling(5).apply(
            lambda x: (x**2).sum()
        ).reset_index(level=0, drop=True)
        self.factors['fz_vp_energy'] = price_energy * volume_energy
        
        # FVP10: 量价加速度
        price_acc = self.data.groupby('stock_code')['close'].pct_change().diff().reset_index(level=0, drop=True)
        volume_acc = self.data.groupby('stock_code')['volume'].pct_change().diff().reset_index(level=0, drop=True)
        self.factors['fz_vp_acceleration'] = price_acc * volume_acc
        
        # FVP11: 量价周期性
        price_cycle = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: np.fft.fft(x - x.mean())[1].real if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        volume_cycle = self.data.groupby('stock_code')['volume'].rolling(20).apply(
            lambda x: np.fft.fft(x - x.mean())[1].real if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        self.factors['fz_vp_cyclical'] = price_cycle * volume_cycle
    
    def calculate_donghai_money_flow_factors(self):
        """计算东海资金流因子（10个）"""
        
        # DHMF1: 净资金流（东海风格）
        self.factors['dh_mf_net_flow_5'] = self.data.groupby('stock_code').apply(
            lambda x: (x['amount'] * np.sign(x['close'].diff())).rolling(5).sum()
        ).reset_index(level=0, drop=True)
        
        # DHMF2: 资金流入率
        inflow = self.data.groupby('stock_code').apply(
            lambda x: (x['amount'] * (x['close'] > x['open'])).rolling(10).sum()
        ).reset_index(level=0, drop=True)
        total_amount = self.data.groupby('stock_code')['amount'].rolling(10).sum().reset_index(level=0, drop=True)
        self.factors['dh_mf_inflow_ratio'] = inflow / (total_amount + 1e-6)
        
        # DHMF3: 资金流出率
        outflow = self.data.groupby('stock_code').apply(
            lambda x: (x['amount'] * (x['close'] < x['open'])).rolling(10).sum()
        ).reset_index(level=0, drop=True)
        self.factors['dh_mf_outflow_ratio'] = outflow / (total_amount + 1e-6)
        
        # DHMF4: 主力资金流
        large_trades = self.data.groupby('stock_code').apply(
            lambda x: x['amount'] * (x['volume'] > x['volume'].rolling(20).mean())
        ).reset_index(level=0, drop=True)
        self.factors['dh_mf_main_flow'] = large_trades.rolling(20).sum()
        
        # DHMF5: 散户资金流
        small_trades = self.data.groupby('stock_code').apply(
            lambda x: x['amount'] * (x['volume'] < x['volume'].rolling(20).mean())
        ).reset_index(level=0, drop=True)
        self.factors['dh_mf_retail_flow'] = small_trades.rolling(20).sum()
        
        # DHMF6: 资金流向强度
        price_change = self.data.groupby('stock_code')['close'].pct_change(10).reset_index(level=0, drop=True)
        volume_change = self.data.groupby('stock_code')['volume'].pct_change(10).reset_index(level=0, drop=True)
        self.factors['dh_mf_flow_strength'] = price_change * volume_change
        
        # DHMF7: 资金流波动率
        self.factors['dh_mf_flow_volatility'] = self.data.groupby('stock_code')['amount'].pct_change().rolling(10).std().reset_index(level=0, drop=True)
        
        # DHMF8: 资金流趋势
        self.factors['dh_mf_flow_trend'] = self.data.groupby('stock_code')['amount'].rolling(20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # DHMF9: 资金流加速度
        self.factors['dh_mf_flow_acceleration'] = self.data.groupby('stock_code')['amount'].pct_change().diff().reset_index(level=0, drop=True)
        
        # DHMF10: 资金流相对强度
        market_flow = self.data.groupby('date')['amount'].mean().rolling(20).mean()
        stock_flow = self.data.groupby('stock_code')['amount'].rolling(20).mean().reset_index(level=0, drop=True)
        self.factors['dh_mf_relative_strength'] = stock_flow / market_flow
    
    def calculate_citic_volatility_factors(self):
        """计算中信建投波动率因子（10个）"""
        
        # CITIC1: 历史波动率（中信建投风格）
        self.factors['ct_vol_historical_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).std().reset_index(level=0, drop=True)
        
        # CITIC2: 实现波动率
        self.factors['ct_vol_realized_10'] = self.data.groupby('stock_code')['close'].pct_change().rolling(10).apply(
            lambda x: np.sqrt(np.mean(x**2))
        ).reset_index(level=0, drop=True)
        
        # CITIC3: Parkinson波动率
        high_low = np.log(self.data['high'] / self.data['low'])
        self.factors['ct_vol_parkinson_10'] = self.data.groupby('stock_code').apply(
            lambda x: (high_low.loc[x.index]**2).rolling(10).mean() / (4 * np.log(2))
        ).reset_index(level=0, drop=True)
        
        # CITIC4: Garman-Klass波动率
        hl = np.log(self.data['high'] / self.data['low'])
        co = np.log(self.data['close'] / self.data['open'])
        self.factors['ct_vol_gk_10'] = self.data.groupby('stock_code').apply(
            lambda x: (0.5 * hl.loc[x.index]**2 - (2*np.log(2)-1) * co.loc[x.index]**2).rolling(10).mean()
        ).reset_index(level=0, drop=True)
        
        # CITIC5: Yang-Zhang波动率
        close_prev = self.data.groupby('stock_code')['close'].shift(1)
        open_close = np.log(self.data['open'] / close_prev)
        close_open = np.log(self.data['close'] / self.data['open'])
        self.factors['ct_vol_yz_10'] = self.data.groupby('stock_code').apply(
            lambda x: (open_close.loc[x.index]**2 + close_open.loc[x.index]**2).rolling(10).mean()
        ).reset_index(level=0, drop=True)
        
        # CITIC6: 相对波动率
        market_vol = self.data.groupby('date')['close'].pct_change().rolling(20).std().mean()
        stock_vol = self.data.groupby('stock_code')['close'].pct_change().rolling(20).std().reset_index(level=0, drop=True)
        self.factors['ct_vol_relative_20'] = stock_vol / market_vol
        
        # CITIC7: 波动率偏度
        self.factors['ct_vol_skew_10'] = self.data.groupby('stock_code')['close'].pct_change().rolling(10).skew().reset_index(level=0, drop=True)
        
        # CITIC8: 波动率峰度
        self.factors['ct_vol_kurt_10'] = self.data.groupby('stock_code')['close'].pct_change().rolling(10).kurt().reset_index(level=0, drop=True)
        
        # CITIC9: 波动率趋势
        self.factors['ct_vol_trend_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).std().pct_change(5).reset_index(level=0, drop=True)
        
        # CITIC10: 波动率分位数
        self.factors['ct_vol_percentile_60'] = self.data.groupby('stock_code')['close'].pct_change().rolling(60).std().rolling(60).rank(pct=True).reset_index(level=0, drop=True)
    
    def calculate_advanced_factors(self):
        """计算其他高级因子（19个）"""
        
        # ADV1: 价格偏度
        self.factors['adv_price_skew_20'] = self.data.groupby('stock_code')['close'].rolling(20).skew().reset_index(level=0, drop=True)
        
        # ADV2: 价格峰度
        self.factors['adv_price_kurt_20'] = self.data.groupby('stock_code')['close'].rolling(20).kurt().reset_index(level=0, drop=True)
        
        # ADV3: Jarque-Bera检验
        self.factors['adv_jb_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: stats.jarque_bera(x)[0] if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV4: Anderson-Darling检验
        self.factors['adv_ad_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: stats.anderson(x, dist='norm')[0] if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV5: Kolmogorov-Smirnov检验
        self.factors['adv_ks_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: stats.kstest(x, 'norm')[0] if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV6: 自相关系数
        self.factors['adv_autocorr_5'] = self.data.groupby('stock_code')['close'].pct_change().rolling(5).apply(
            lambda x: np.corrcoef(x[:-1], x[1:])[0, 1] if len(x) == 5 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV7: Hurst指数
        self.factors['adv_hurst_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: self._calculate_hurst(x) if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV8: Lyapunov指数
        self.factors['adv_lyapunov_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: self._calculate_lyapunov(x) if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV9: 分形维度
        self.factors['adv_fractal_dim_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: self._calculate_fractal_dimension(x) if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV10: 信息熵
        self.factors['adv_entropy_20'] = self.data.groupby('stock_code')['close'].rolling(20).apply(
            lambda x: self._calculate_entropy(x) if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV11: 量价Beta
        self.factors['adv_beta_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).apply(
            lambda x: np.cov(x, np.arange(len(x)))[0, 1] / np.var(np.arange(len(x))) if len(x) == 20 else np.nan
        ).reset_index(level=0, drop=True)
        
        # ADV12: 量价Alpha
        self.factors['adv_alpha_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() - \
                                        self.factors['adv_beta_20'] * 0.01
        self.factors['adv_alpha_20'] = self.factors['adv_alpha_20'].reset_index(level=0, drop=True)
        
        # ADV13: 量价Sharpe
        self.factors['adv_sharpe_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() / \
                                    self.data.groupby('stock_code')['close'].pct_change().rolling(20).std()
        self.factors['adv_sharpe_20'] = self.factors['adv_sharpe_20'].reset_index(level=0, drop=True)
        
        # ADV14: 量价Sortino
        downside_return = self.data.groupby('stock_code')['close'].pct_change().apply(
            lambda x: np.where(x < 0, x, 0)
        )
        self.factors['adv_sortino_20'] = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() / \
                                     downside_return.rolling(20).std()
        self.factors['adv_sortino_20'] = self.factors['adv_sortino_20'].reset_index(level=0, drop=True)
        
        # ADV15: 量价Calmar
        cumulative_return = (1 + self.data.groupby('stock_code')['close'].pct_change()).rolling(20).apply(
            lambda x: (1 + x).prod() - 1
        )
        peak = (1 + self.data.groupby('stock_code')['close'].pct_change()).rolling(20).apply(
            lambda x: (1 + x).cumprod().max()
        )
        self.factors['adv_calmar_20'] = (cumulative_return / peak).reset_index(level=0, drop=True)
        
        # ADV16: 量价信息比率
        price_ir = self.data.groupby('stock_code')['close'].pct_change().rolling(20).mean() / \
                  self.data.groupby('stock_code')['close'].pct_change().rolling(20).std()
        volume_ir = self.data.groupby('stock_code')['volume'].pct_change().rolling(20).mean() / \
                    self.data.groupby('stock_code')['volume'].pct_change().rolling(20).std()
        self.factors['adv_information_ratio'] = price_ir.reset_index(level=0, drop=True) * \
                                              volume_ir.reset_index(level=0, drop=True)
        
        # ADV17: 量价分位数
        price_rank = self.data.groupby('stock_code')['close'].rolling(10).rank(pct=True).reset_index(level=0, drop=True)
        volume_rank = self.data.groupby('stock_code')['volume'].rolling(10).rank(pct=True).reset_index(level=0, drop=True)
        self.factors['adv_percentile'] = price_rank * volume_rank
        
        # ADV18: 量价偏度乘积
        price_skew = self.data.groupby('stock_code')['close'].rolling(10).skew().reset_index(level=0, drop=True)
        volume_skew = self.data.groupby('stock_code')['volume'].rolling(10).skew().reset_index(level=0, drop=True)
        self.factors['adv_skew_product'] = price_skew * volume_skew
        
        # ADV19: 量价峰度乘积
        price_kurt = self.data.groupby('stock_code')['close'].rolling(10).kurt().reset_index(level=0, drop=True)
        volume_kurt = self.data.groupby('stock_code')['volume'].rolling(10).kurt().reset_index(level=0, drop=True)
        self.factors['adv_kurt_product'] = price_kurt * volume_kurt
    
    def _calculate_hurst(self, series):
        """计算Hurst指数"""
        lags = range(2, len(series)//2)
        tau = [np.std(np.subtract(series[lag:], series[:-lag])) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0]
    
    def _calculate_lyapunov(self, series):
        """计算Lyapunov指数"""
        arr = series.values
        n = len(arr)
        lyap = 0
        for i in range(n-1):
            lyap += np.log(abs(arr[i+1] - arr[i]) + 1e-6)
        return lyap / (n-1)
    
    def _calculate_fractal_dimension(self, series):
        """计算分形维度"""
        n = len(series)
        lags = range(2, n//2)
        rs = []
        for lag in lags:
            cumsum = np.cumsum(series - np.mean(series))
            r = np.max(cumsum) - np.min(cumsum)
            s = np.std(series)
            rs.append(r / s)
        poly = np.polyfit(np.log(lags), np.log(rs), 1)
        return 2 - poly[0]
    
    def _calculate_entropy(self, series):
        """计算信息熵"""
        _, counts = np.unique(series, return_counts=True)
        probs = counts / len(series)
        entropy = -np.sum(probs * np.log(probs + 1e-6))
        return entropy
    
    def calculate_ic(self, factor_name, target_col='next_return', method='spearman'):
        """
        计算单个因子的IC值
        
        参数:
            factor_name: str, 因子名称
            target_col: str, 目标列名
            method: str, 计算方法 ('spearman', 'pearson')
            
        返回:
            float, IC值
        """
        if factor_name not in self.factors:
            return None
        
        factor_data = self.factors[factor_name]
        
        # 将因子数据转换为Series并重置索引
        factor_series = pd.Series(factor_data.values, index=factor_data.index)
        
        # 获取目标数据
        target_data = self.data[target_col]
        
        # 合并数据，只保留两边都有的索引
        combined = pd.DataFrame({
            'factor': factor_series,
            'target': target_data
        }).dropna()
        
        factor_valid = combined['factor'].values
        target_valid = combined['target'].values
        
        if len(factor_valid) < 10:
            return np.nan
        
        if method == 'spearman':
            ic, _ = stats.spearmanr(factor_valid, target_valid)
        elif method == 'pearson':
            ic, _ = stats.pearsonr(factor_valid, target_valid)
        else:
            raise ValueError(f"未知的IC计算方法: {method}")
        
        return ic
    
    def calculate_all_ic(self, target_col='next_return', method='spearman'):
        """
        计算所有因子的IC值
        
        参数:
            target_col: str, 目标列名
            method: str, 计算方法
            
        返回:
            DataFrame, IC测试结果
        """
        ic_results = []
        
        for factor_name in self.factors.keys():
            ic = self.calculate_ic(factor_name, target_col, method)
            ic_results.append({
                'factor': factor_name,
                'ic': ic
            })
        
        ic_df = pd.DataFrame(ic_results)
        ic_df = ic_df.sort_values('ic', ascending=False)
        
        return ic_df
    
    def get_factor_data(self):
        """
        获取因子数据
        
        返回:
            DataFrame, 包含所有因子的数据
        """
        factor_df = pd.DataFrame(self.factors)
        factor_df = factor_df.dropna()
        
        original_data = self.data.copy()
        original_data = original_data.loc[factor_df.index]
        
        factor_df['date'] = original_data['date'].values
        factor_df['stock_code'] = original_data['stock_code'].values
        
        return factor_df

def main():
    """主函数 - 演示使用"""
    print("50个专业量化因子实现 - 方正、东海、中信建投系列")
    print("=" * 60)
    
    # 生成示例数据
    np.random.seed(42)
    n_stocks = 10
    n_days = 100
    
    dates = pd.date_range('2020-01-01', periods=n_days, freq='B')
    stocks = [f'SH600{i:03d}' for i in range(1, n_stocks+1)]
    
    data = []
    for stock in stocks:
        price = 10.0
        prices = []
        for _ in range(n_days):
            price = price * (1 + np.random.normal(0, 0.02))
            prices.append(price)
        
        stock_data = pd.DataFrame({
            'date': dates,
            'stock_code': stock,
            'open': np.array(prices) * np.random.uniform(0.995, 1.005, n_days),
            'high': np.array(prices) * np.random.uniform(1.0, 1.01, n_days),
            'low': np.array(prices) * np.random.uniform(0.99, 1.0, n_days),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n_days),
            'amount': np.array(prices) * np.random.randint(1000000, 10000000, n_days)
        })
        data.append(stock_data)
    
    data = pd.concat(data, ignore_index=True)
    data['next_return'] = data.groupby('stock_code')['close'].pct_change().shift(-1)
    
    # 创建因子计算器
    factor_calc = ProfessionalFactorCalculator(data)
    
    # 计算所有因子
    factors = factor_calc.calculate_all_factors()
    
    # 计算IC
    ic_results = factor_calc.calculate_all_ic()
    
    print("\n因子IC排名（Top 10）:")
    print(ic_results.head(10).to_string(index=False))
    
    # 获取因子数据
    factor_data = factor_calc.get_factor_data()
    print(f"\n因子数据形状: {factor_data.shape}")
    print(f"因子列数: {len(factors)}")
    
    print("\n因子库运行完成！")

if __name__ == "__main__":
    main()
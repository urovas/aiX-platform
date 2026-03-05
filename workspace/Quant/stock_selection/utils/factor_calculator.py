# 因子计算模块
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FactorCalculator:
    def __init__(self, data_fetcher):
        """初始化因子计算器"""
        self.data_fetcher = data_fetcher
    
    def calculate_value_factors(self, df):
        """计算价值因子"""
        factors = {}
        
        # 市净率 (PB) - 支持多种列名
        if 'pb' in df.columns:
            factors['pb'] = df['pb']
        elif 'pbMRQ' in df.columns:
            factors['pb'] = df['pbMRQ']
        else:
            factors['pb'] = np.nan
        
        # 市盈率 (PE_TTM) - 支持多种列名
        if 'pe_ttm' in df.columns:
            factors['pe_ttm'] = df['pe_ttm']
        elif 'peTTM' in df.columns:
            factors['pe_ttm'] = df['peTTM']
        else:
            factors['pe_ttm'] = np.nan
        
        # 市销率 (PS_TTM) - 支持多种列名
        if 'ps_ttm' in df.columns:
            factors['ps_ttm'] = df['ps_ttm']
        elif 'psTTM' in df.columns:
            factors['ps_ttm'] = df['psTTM']
        else:
            factors['ps_ttm'] = np.nan
        
        # 市现率 (PCF_TTM) - 支持多种列名
        if 'pcf_ttm' in df.columns:
            factors['pcf_ttm'] = df['pcf_ttm']
        elif 'pcfNcfTTM' in df.columns:
            factors['pcf_ttm'] = df['pcfNcfTTM']
        else:
            factors['pcf_ttm'] = np.nan
        
        return factors
    
    def calculate_growth_factors(self, df):
        """计算成长因子"""
        factors = {}
        
        # 营收增长率
        if 'revenue_growth_rate' in df.columns:
            factors['revenue_growth_rate'] = df['revenue_growth_rate']
        else:
            factors['revenue_growth_rate'] = np.nan
        
        # 净利润增长率
        if 'net_profit_growth_rate' in df.columns:
            factors['net_profit_growth_rate'] = df['net_profit_growth_rate']
        else:
            factors['net_profit_growth_rate'] = np.nan
        
        # 每股收益增长率
        if 'eps_growth_rate' in df.columns:
            factors['eps_growth_rate'] = df['eps_growth_rate']
        else:
            factors['eps_growth_rate'] = np.nan
        
        return factors
    
    def calculate_quality_factors(self, df):
        """计算质量因子"""
        factors = {}
        
        # 净资产收益率 (ROE)
        if 'roe' in df.columns:
            factors['roe'] = df['roe']
        elif 'roe_ttm' in df.columns:
            factors['roe'] = df['roe_ttm']
        else:
            factors['roe'] = np.nan
        
        # 总资产收益率 (ROA)
        if 'roa' in df.columns:
            factors['roa'] = df['roa']
        else:
            factors['roa'] = np.nan
        
        # 净利润率
        if 'net_profit_margin' in df.columns:
            factors['net_profit_margin'] = df['net_profit_margin']
        else:
            factors['net_profit_margin'] = np.nan
        
        # 资产负债率
        if 'debt_to_asset_ratio' in df.columns:
            factors['debt_to_asset_ratio'] = df['debt_to_asset_ratio']
        else:
            factors['debt_to_asset_ratio'] = np.nan
        
        return factors
    
    def calculate_momentum_factors(self, price_df):
        """计算动量因子"""
        factors = {}
        
        if price_df.empty:
            return factors
        
        # 确保close列是数值类型
        if 'close' in price_df.columns:
            price_df['close'] = pd.to_numeric(price_df['close'], errors='coerce')
        
        # 1个月收益率
        factors['return_1m'] = price_df['close'].pct_change(20)
        
        # 3个月收益率
        factors['return_3m'] = price_df['close'].pct_change(60)
        
        # 6个月收益率
        factors['return_6m'] = price_df['close'].pct_change(120)
        
        # 12个月收益率（如果数据长度足够）
        if len(price_df) >= 240:
            factors['return_12m'] = price_df['close'].pct_change(240)
        else:
            factors['return_12m'] = np.nan
        
        # 1个月波动率
        factors['volatility_1m'] = price_df['close'].pct_change().rolling(20).std()
        
        # 3个月波动率
        factors['volatility_3m'] = price_df['close'].pct_change().rolling(60).std()
        
        return factors
    
    def calculate_technical_factors(self, price_df):
        """计算技术因子"""
        factors = {}
        
        if price_df.empty:
            return factors
        
        # 确保数值列是数值类型
        for col in ['close', 'high', 'low', 'volume']:
            if col in price_df.columns:
                price_df[col] = pd.to_numeric(price_df[col], errors='coerce')
        
        # MACD指标
        factors['macd'] = self.calculate_macd(price_df['close'])
        
        # KDJ指标
        k, d = self.calculate_kdj(price_df['high'], price_df['low'], price_df['close'])
        factors['kdj_k'] = k
        factors['kdj_d'] = d
        
        # RSI指标
        factors['rsi'] = self.calculate_rsi(price_df['close'])
        
        # 5日均线与20日均线差值
        ma5 = price_df['close'].rolling(5).mean()
        ma20 = price_df['close'].rolling(20).mean()
        factors['ma_5_20_diff'] = (ma5 - ma20) / ma20
        
        # 成交量变化率
        if 'volume' in price_df.columns:
            factors['volume_change_rate'] = price_df['volume'].pct_change()
        else:
            factors['volume_change_rate'] = np.nan
        
        return factors
    
    def calculate_macd(self, close, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标"""
        ema_fast = close.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_hist = macd_line - signal_line
        return macd_hist
    
    def calculate_kdj(self, high, low, close, n=9, m1=3, m2=3):
        """计算KDJ指标"""
        # 计算RSV
        low_n = low.rolling(n).min()
        high_n = high.rolling(n).max()
        rsv = (close - low_n) / (high_n - low_n) * 100
        
        # 计算K值
        k = rsv.ewm(alpha=1/m1, adjust=False).mean()
        
        # 计算D值
        d = k.ewm(alpha=1/m2, adjust=False).mean()
        
        return k, d
    
    def calculate_rsi(self, close, period=14):
        """计算RSI指标"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def normalize_factors(self, factors):
        """标准化因子"""
        normalized = {}
        
        for factor_name, factor_values in factors.items():
            if isinstance(factor_values, pd.Series):
                # 处理无穷值
                factor_values = factor_values.replace([np.inf, -np.inf], np.nan)
                
                # 计算均值和标准差
                mean = factor_values.mean()
                std = factor_values.std()
                
                # 标准化
                if std > 0:
                    normalized[factor_name] = (factor_values - mean) / std
                else:
                    normalized[factor_name] = factor_values - mean
            else:
                normalized[factor_name] = factor_values
        
        return normalized
    
    def rank_factors(self, factors):
        """对因子进行排序"""
        ranked = {}
        
        for factor_name, factor_values in factors.items():
            if isinstance(factor_values, pd.Series):
                # 处理价值因子（低估值更好）
                if factor_name in ['pb', 'pe_ttm', 'ps_ttm', 'pcf_ttm', 'debt_to_asset_ratio']:
                    ranked[factor_name] = factor_values.rank(ascending=True)
                else:
                    ranked[factor_name] = factor_values.rank(ascending=False)
            else:
                ranked[factor_name] = factor_values
        
        return ranked
    
    def calculate_combined_score(self, ranked_factors, weights):
        """计算综合评分"""
        score = pd.Series(0, index=next(iter(ranked_factors.values())).index)
        
        for factor_name, ranks in ranked_factors.items():
            # 确定因子所属类别
            factor_category = self._get_factor_category(factor_name)
            if factor_category in weights:
                weight = weights[factor_category]
                score += ranks * weight
        
        return score
    
    def _get_factor_category(self, factor_name):
        """获取因子所属类别"""
        value_factors = ['pb', 'pe_ttm', 'ps_ttm', 'pcf_ttm', 'ev_ebitda']
        growth_factors = ['revenue_growth_rate', 'net_profit_growth_rate', 'eps_growth_rate', 
                         'roe_growth_rate', 'operating_profit_growth_rate']
        quality_factors = ['roe', 'roa', 'net_profit_margin', 'operating_profit_margin', 
                          'asset_turnover', 'debt_to_asset_ratio', 'current_ratio']
        momentum_factors = ['return_1m', 'return_3m', 'return_6m', 'return_12m', 
                          'volatility_1m', 'volatility_3m']
        technical_factors = ['macd', 'kdj_k', 'kdj_d', 'rsi', 'ma_5_20_diff', 'volume_change_rate']
        
        if factor_name in value_factors:
            return 'value'
        elif factor_name in growth_factors:
            return 'growth'
        elif factor_name in quality_factors:
            return 'quality'
        elif factor_name in momentum_factors:
            return 'momentum'
        elif factor_name in technical_factors:
            return 'technical'
        else:
            return 'other'

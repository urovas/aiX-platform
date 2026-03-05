# 传统因子计算模块（基本面、量价、估值）

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TraditionalFactorCalculator:
    def __init__(self, data_fetcher):
        """初始化因子计算器"""
        self.data_fetcher = data_fetcher
    
    def calculate_fundamental_factors(self, price_df, financial_df=None):
        """
        计算基本面因子（捕捉企业盈利，即EPS）
        
        包括：
        - eps_growth: EPS增长率
        - roe: 净资产收益率
        - roa: 总资产收益率
        - revenue_growth: 营收增长率
        - profit_growth: 利润增长率
        - debt_ratio: 资产负债率
        - current_ratio: 流动比率
        """
        factors = {}
        
        if price_df.empty:
            return factors
        
        # 确保数值列是数值类型
        for col in ['close', 'open', 'high', 'low', 'volume']:
            if col in price_df.columns:
                price_df[col] = pd.to_numeric(price_df[col], errors='coerce')
        
        # EPS增长率（如果有财务数据）
        if financial_df is not None and not financial_df.empty:
            if 'epsTTM' in financial_df.columns:
                factors['eps_growth'] = financial_df['epsTTM'].pct_change(4)  # 季度增长率
            else:
                factors['eps_growth'] = np.nan
        else:
            factors['eps_growth'] = np.nan
        
        # 净资产收益率（ROE）
        if 'roeTTM' in price_df.columns:
            factors['roe'] = pd.to_numeric(price_df['roeTTM'], errors='coerce')
        elif 'roe' in price_df.columns:
            factors['roe'] = pd.to_numeric(price_df['roe'], errors='coerce')
        else:
            factors['roe'] = np.nan
        
        # 总资产收益率（ROA）
        if 'roaTTM' in price_df.columns:
            factors['roa'] = pd.to_numeric(price_df['roaTTM'], errors='coerce')
        elif 'roa' in price_df.columns:
            factors['roa'] = pd.to_numeric(price_df['roa'], errors='coerce')
        else:
            factors['roa'] = np.nan
        
        # 营收增长率（使用价格作为代理）
        # 如果没有财务数据，使用价格增长率作为代理
        factors['revenue_growth'] = price_df['close'].pct_change(60)  # 60日增长率
        
        # 利润增长率（使用价格作为代理）
        factors['profit_growth'] = price_df['close'].pct_change(60)  # 60日增长率
        
        # 资产负债率（如果有财务数据）
        if financial_df is not None and not financial_df.empty:
            if 'debtToAssets' in financial_df.columns:
                factors['debt_ratio'] = financial_df['debtToAssets']
            else:
                factors['debt_ratio'] = np.nan
        else:
            factors['debt_ratio'] = np.nan
        
        # 流动比率（如果有财务数据）
        if financial_df is not None and not financial_df.empty:
            if 'currentRatio' in financial_df.columns:
                factors['current_ratio'] = financial_df['currentRatio']
            else:
                factors['current_ratio'] = np.nan
        else:
            factors['current_ratio'] = np.nan
        
        return factors
    
    def calculate_price_volume_factors(self, price_df):
        """
        计算量价因子（捕捉市场情绪）
        
        包括：
        - momentum_5d: 5日动量
        - momentum_20d: 20日动量
        - momentum_60d: 60日动量
        - volatility_5d: 5日波动率
        - volatility_20d: 20日波动率
        - volume_ratio: 成交量比率
        - turnover_rate: 换手率
        """
        factors = {}
        
        if price_df.empty:
            return factors
        
        # 确保数值列是数值类型
        for col in ['close', 'open', 'high', 'low', 'volume']:
            if col in price_df.columns:
                price_df[col] = pd.to_numeric(price_df[col], errors='coerce')
        
        # 动量因子
        factors['momentum_5d'] = price_df['close'].pct_change(5)
        factors['momentum_20d'] = price_df['close'].pct_change(20)
        factors['momentum_60d'] = price_df['close'].pct_change(60)
        
        # 波动率因子
        factors['volatility_5d'] = price_df['close'].pct_change().rolling(5).std()
        factors['volatility_20d'] = price_df['close'].pct_change().rolling(20).std()
        
        # 成交量比率（当前成交量与平均成交量的比率）
        if 'volume' in price_df.columns:
            avg_volume = price_df['volume'].rolling(20).mean()
            factors['volume_ratio'] = price_df['volume'] / avg_volume
        else:
            factors['volume_ratio'] = np.nan
        
        # 换手率
        if 'turn' in price_df.columns:
            factors['turnover_rate'] = price_df['turn']
        else:
            factors['turnover_rate'] = np.nan
        
        return factors
    
    def calculate_valuation_factors(self, price_df):
        """
        计算估值因子（捕捉市场情绪，即PE）
        
        包括：
        - pe_ttm: 滚动市盈率
        - pb: 市净率
        - ps_ttm: 滚动市销率
        - pcf_ttm: 滚动市现率
        - pe_g: PEG比率
        """
        factors = {}
        
        if price_df.empty:
            return factors
        
        # 市净率（PB）
        if 'pbMRQ' in price_df.columns:
            factors['pb'] = pd.to_numeric(price_df['pbMRQ'], errors='coerce')
        elif 'pb' in price_df.columns:
            factors['pb'] = pd.to_numeric(price_df['pb'], errors='coerce')
        else:
            factors['pb'] = np.nan
        
        # 市盈率（PE_TTM）
        if 'peTTM' in price_df.columns:
            factors['pe_ttm'] = pd.to_numeric(price_df['peTTM'], errors='coerce')
        elif 'pe_ttm' in price_df.columns:
            factors['pe_ttm'] = pd.to_numeric(price_df['pe_ttm'], errors='coerce')
        else:
            factors['pe_ttm'] = np.nan
        
        # 市销率（PS_TTM）
        if 'psTTM' in price_df.columns:
            factors['ps_ttm'] = pd.to_numeric(price_df['psTTM'], errors='coerce')
        elif 'ps_ttm' in price_df.columns:
            factors['ps_ttm'] = pd.to_numeric(price_df['ps_ttm'], errors='coerce')
        else:
            factors['ps_ttm'] = np.nan
        
        # 市现率（PCF_TTM）
        if 'pcfNcfTTM' in price_df.columns:
            factors['pcf_ttm'] = pd.to_numeric(price_df['pcfNcfTTM'], errors='coerce')
        elif 'pcf_ttm' in price_df.columns:
            factors['pcf_ttm'] = pd.to_numeric(price_df['pcf_ttm'], errors='coerce')
        else:
            factors['pcf_ttm'] = np.nan
        
        # PEG比率（PE/增长率）
        if 'peTTM' in price_df.columns:
            pe_ttm = pd.to_numeric(price_df['peTTM'], errors='coerce')
            # 使用价格增长率作为盈利增长率
            earnings_growth = price_df['close'].pct_change(60)
            factors['pe_g'] = pe_ttm / (earnings_growth * 100 + 1)
        elif 'pe_ttm' in price_df.columns:
            pe_ttm = pd.to_numeric(price_df['pe_ttm'], errors='coerce')
            earnings_growth = price_df['close'].pct_change(60)
            factors['pe_g'] = pe_ttm / (earnings_growth * 100 + 1)
        else:
            factors['pe_g'] = np.nan
        
        return factors
    
    def calculate_all_traditional_factors(self, price_df, financial_df=None):
        """
        计算所有传统因子
        
        根据双均衡框架：
        - 因子来源均衡：收益预测的一半来源于基本面因子，另一半来源于量价、估值因子
        """
        fundamental_factors = self.calculate_fundamental_factors(price_df, financial_df)
        price_volume_factors = self.calculate_price_volume_factors(price_df)
        valuation_factors = self.calculate_valuation_factors(price_df)
        
        # 合并所有因子
        all_factors = {}
        all_factors.update(fundamental_factors)
        all_factors.update(price_volume_factors)
        all_factors.update(valuation_factors)
        
        return all_factors
    
    def calculate_factor_weights(self):
        """
        计算因子权重（根据双均衡框架）
        
        因子来源均衡：
        - 基本面因子权重：50%
        - 量价+估值因子权重：50%
        """
        weights = {
            # 基本面因子权重：50%
            'eps_growth': 0.5 / 7,  # 7个基本面因子
            'roe': 0.5 / 7,
            'roa': 0.5 / 7,
            'revenue_growth': 0.5 / 7,
            'profit_growth': 0.5 / 7,
            'debt_ratio': 0.5 / 7,
            'current_ratio': 0.5 / 7,
            
            # 量价因子权重：25%
            'momentum_5d': 0.25 / 7,  # 7个量价因子
            'momentum_20d': 0.25 / 7,
            'momentum_60d': 0.25 / 7,
            'volatility_5d': 0.25 / 7,
            'volatility_20d': 0.25 / 7,
            'volume_ratio': 0.25 / 7,
            'turnover_rate': 0.25 / 7,
            
            # 估值因子权重：25%
            'pe_ttm': 0.25 / 5,  # 5个估值因子
            'pb': 0.25 / 5,
            'ps_ttm': 0.25 / 5,
            'pcf_ttm': 0.25 / 5,
            'pe_g': 0.25 / 5,
        }
        
        return weights

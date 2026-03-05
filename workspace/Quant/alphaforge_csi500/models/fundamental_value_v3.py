# 中低频基本面价值评估模型（公司体质）

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings('ignore')

# 导入行业数据
from utils.industry_data import industry_classification, industry_to_code

# 尝试导入XGBoost和LightGBM
try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None

class SectorSpecificModel:
    """
    行业专用模型
    """
    def __init__(self, sector):
        self.sector = sector
        self.model = None
    
    def fit(self, X, y):
        """
        训练模型
        """
        from sklearn.ensemble import GradientBoostingRegressor
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42
        )
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """
        预测
        """
        return self.model.predict(X)


class CapSpecificModel:
    """
    市值分层模型
    """
    def __init__(self, cap_type):
        self.cap_type = cap_type
        self.model = None
    
    def fit(self, X, y):
        """
        训练模型
        """
        from sklearn.ensemble import GradientBoostingRegressor
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42
        )
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """
        预测
        """
        return self.model.predict(X)


class QualitySpecificModel:
    """
    质量分层模型
    """
    def __init__(self, quality_type):
        self.quality_type = quality_type
        self.model = None
    
    def fit(self, X, y):
        """
        训练模型
        """
        from sklearn.ensemble import GradientBoostingRegressor
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42
        )
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """
        预测
        """
        return self.model.predict(X)


class HierarchicalFundamentalModel:
    """
    分层基本面模型
    """
    def __init__(self):
        # 1. 行业专用模型
        self.sector_models = {
            '金融': SectorSpecificModel('金融'),
            '消费': SectorSpecificModel('消费'),
            '科技': SectorSpecificModel('科技'),
            '周期': SectorSpecificModel('周期')
        }
        
        # 2. 市值分层模型
        self.cap_models = {
            'large_cap': CapSpecificModel('large'),
            'mid_cap': CapSpecificModel('mid'),
            'small_cap': CapSpecificModel('small')
        }
        
        # 3. 质量分层模型
        self.quality_models = {
            'high_quality': QualitySpecificModel('high'),
            'medium_quality': QualitySpecificModel('medium'),
            'low_quality': QualitySpecificModel('low')
        }
    
    def select_model(self, stock_info):
        """
        动态选择最合适的模型
        
        Args:
            stock_info: 股票信息，包含行业、市值、质量得分等
            
        Returns:
            base_model: 基础模型
            adjustment: 调整模型
        """
        sector = stock_info.get('sector', '其他')
        market_cap = stock_info.get('market_cap', 0)
        quality_score = stock_info.get('quality_score', 0.5)
        
        # 优先使用行业模型
        if sector in self.sector_models:
            base_model = self.sector_models[sector]
        else:
            # 否则使用市值模型
            if market_cap > 100e9:  # 1000亿以上
                base_model = self.cap_models['large_cap']
            elif market_cap > 10e9:  # 100亿以上
                base_model = self.cap_models['mid_cap']
            else:
                base_model = self.cap_models['small_cap']
        
        # 根据质量调整预测
        if quality_score > 0.7:
            adjustment = self.quality_models['high_quality']
        elif quality_score > 0.4:
            adjustment = self.quality_models['medium_quality']
        else:
            adjustment = self.quality_models['low_quality']
        
        return base_model, adjustment

class FundamentalValueModel:
    def __init__(self, config):
        """初始化基本面价值评估模型"""
        # 兼容Config对象和字典
        if config is not None and hasattr(config, '__dict__'):
            self.config = {k: v for k, v in config.__dict__.items() if not k.startswith('_')}
        else:
            self.config = config or {}
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        
        # 价值评估维度
        self.value_dimensions = {
            'profitability': ['roe', 'roa', 'gross_margin', 'operating_margin'],
            'growth': ['revenue_growth', 'profit_growth', 'eps_growth', 'asset_growth'],
            'quality': ['debt_ratio', 'current_ratio', 'quick_ratio', 'interest_coverage'],
            'valuation': ['pe_ttm', 'pb', 'ps_ttm', 'pcf_ttm', 'ev_ebitda'],
            'efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
        }
        
        # 价值因子
        self.value_factors = [
            # 盈利能力因子
            'roe_quality',           # ROE质量
            'roa_stability',         # ROA稳定性
            'margin_trend',          # 利润率趋势
            
            # 成长能力因子
            'growth_consistency',    # 成长一致性
            'growth_sustainability', # 成长可持续性
            'growth_momentum',       # 成长动量
            
            # 财务质量因子
            'financial_health',      # 财务健康度
            'debt_sustainability',  # 债务可持续性
            'liquidity_strength',   # 流动性强度
            
            # 估值因子
            'value_score',          # 价值得分
            'valuation_attractiveness', # 估值吸引力
            'pe_g_quality',         # PEG质量
            
            # 效率因子
            'operational_efficiency', # 运营效率
            'capital_efficiency',   # 资本效率
            
            # 预期差因子
            'earnings_surprise',    # 盈利超预期
            'revenue_surprise',     # 收入超预期
            'eps_surprise',         # 盈利超预期（新格式）
            'eps_surprise_std',     # 标准化盈利超预期
            'surprise_momentum',    # 超预期持续性
            
            # 产业链因子
            'industry_chain_position', # 产业链位置
            'supply_chain_strength',   # 供应链强度
            'bargaining_power',       # 上下游议价能力
            'margin_position',         # 毛利率位置
            'inventory_signal',        # 库存信号
            
            # 时间衰减因子
            'roe_decayed',            # 衰减后的ROE
            'revenue_growth_decayed', # 衰减后的收入增长
            'operating_margin_decayed', # 衰减后的营业利润率
            'roe_trend',              # ROE趋势
        ]
        
        # 模型选择
        self.model_type = 'voting'  # 'ridge', 'lasso', 'elasticnet', 'gbdt', 'ensemble', 'voting'
    
    def calculate_profitability_factors(self, financial_data):
        """
        计算盈利能力因子
        
        Args:
            financial_data: 财务数据
            
        Returns:
            factors: 盈利能力因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # ROE质量（ROE的稳定性和持续性）
        if 'roe' in financial_data.columns:
            roe = pd.to_numeric(financial_data['roe'], errors='coerce')
            roe_mean = roe.rolling(4).mean()  # 4季度均值
            roe_std = roe.rolling(4).std()
            factors['roe_quality'] = roe_mean / (roe_std + 1e-6)
        
        # ROA稳定性
        if 'roa' in financial_data.columns:
            roa = pd.to_numeric(financial_data['roa'], errors='coerce')
            roa_mean = roa.rolling(4).mean()
            roa_std = roa.rolling(4).std()
            factors['roa_stability'] = roa_mean / (roa_std + 1e-6)
        
        # 利润率趋势
        if 'gross_margin' in financial_data.columns and 'operating_margin' in financial_data.columns:
            gross_margin = pd.to_numeric(financial_data['gross_margin'], errors='coerce')
            operating_margin = pd.to_numeric(financial_data['operating_margin'], errors='coerce')
            combined_margin = (gross_margin + operating_margin) / 2
            factors['margin_trend'] = combined_margin.diff(4)  # 同比变化
        
        return factors
    
    def calculate_growth_factors(self, financial_data):
        """
        计算成长能力因子
        
        Args:
            financial_data: 财务数据
            
        Returns:
            factors: 成长能力因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 成长一致性（多个成长指标的一致性）
        growth_metrics = []
        for metric in ['revenue_growth', 'profit_growth', 'eps_growth']:
            if metric in financial_data.columns:
                growth = pd.to_numeric(financial_data[metric], errors='coerce')
                growth_metrics.append(growth)
        
        if growth_metrics:
            growth_df = pd.concat(growth_metrics, axis=1)
            growth_mean = growth_df.mean(axis=1)
            growth_std = growth_df.std(axis=1)
            factors['growth_consistency'] = growth_mean / (growth_std + 1e-6)
        
        # 成长可持续性（成长与盈利能力的匹配度）
        if 'revenue_growth' in financial_data.columns and 'roe' in financial_data.columns:
            revenue_growth = pd.to_numeric(financial_data['revenue_growth'], errors='coerce')
            roe = pd.to_numeric(financial_data['roe'], errors='coerce')
            factors['growth_sustainability'] = revenue_growth * roe / 100
        
        # 成长动量（成长的加速度）
        if 'revenue_growth' in financial_data.columns:
            revenue_growth = pd.to_numeric(financial_data['revenue_growth'], errors='coerce')
            factors['growth_momentum'] = revenue_growth.diff(4)  # 同比加速度
        
        return factors
    
    def calculate_quality_factors(self, financial_data):
        """
        计算财务质量因子
        
        Args:
            financial_data: 财务数据
            
        Returns:
            factors: 财务质量因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 财务健康度（综合评分）
        health_score = 0
        if 'debt_ratio' in financial_data.columns:
            debt_ratio = pd.to_numeric(financial_data['debt_ratio'], errors='coerce')
            health_score += (1 - debt_ratio / 100) * 0.4
        
        if 'current_ratio' in financial_data.columns:
            current_ratio = pd.to_numeric(financial_data['current_ratio'], errors='coerce')
            health_score += np.tanh(current_ratio - 1) * 0.3
        
        if 'roe' in financial_data.columns:
            roe = pd.to_numeric(financial_data['roe'], errors='coerce')
            health_score += np.tanh(roe / 10) * 0.3
        
        factors['financial_health'] = health_score
        
        # 债务可持续性
        if 'debt_ratio' in financial_data.columns and 'interest_coverage' in financial_data.columns:
            debt_ratio = pd.to_numeric(financial_data['debt_ratio'], errors='coerce')
            interest_coverage = pd.to_numeric(financial_data['interest_coverage'], errors='coerce')
            factors['debt_sustainability'] = interest_coverage / (debt_ratio + 1e-6)
        
        # 流动性强度
        if 'current_ratio' in financial_data.columns and 'quick_ratio' in financial_data.columns:
            current_ratio = pd.to_numeric(financial_data['current_ratio'], errors='coerce')
            quick_ratio = pd.to_numeric(financial_data['quick_ratio'], errors='coerce')
            factors['liquidity_strength'] = (current_ratio + quick_ratio) / 2
        
        return factors
    
    def calculate_valuation_factors(self, financial_data, price_data):
        """
        计算估值因子
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            
        Returns:
            factors: 估值因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 价值得分（综合估值指标）
        value_score = 0
        count = 0
        
        # PE_TTM（反向，越低越好）
        if 'pe_ttm' in financial_data.columns:
            pe_ttm = pd.to_numeric(financial_data['pe_ttm'], errors='coerce')
            # 使用倒数，并限制范围
            pe_score = 1 / (pe_ttm + 1e-6)
            pe_score = np.clip(pe_score, 0, 0.2)
            value_score += pe_score
            count += 1
        
        # PB（反向，越低越好）
        if 'pb' in financial_data.columns:
            pb = pd.to_numeric(financial_data['pb'], errors='coerce')
            pb_score = 1 / (pb + 1e-6)
            pb_score = np.clip(pb_score, 0, 0.5)
            value_score += pb_score
            count += 1
        
        # PS_TTM（反向，越低越好）
        if 'ps_ttm' in financial_data.columns:
            ps_ttm = pd.to_numeric(financial_data['ps_ttm'], errors='coerce')
            ps_score = 1 / (ps_ttm + 1e-6)
            ps_score = np.clip(ps_score, 0, 0.5)
            value_score += ps_score
            count += 1
        
        if count > 0:
            factors['value_score'] = value_score / count
        
        # 估值吸引力（相对于历史）
        if 'pe_ttm' in financial_data.columns:
            pe_ttm = pd.to_numeric(financial_data['pe_ttm'], errors='coerce')
            pe_percentile = pe_ttm.rolling(252).rank(pct=True)  # 一年分位数
            factors['valuation_attractiveness'] = 1 - pe_percentile
        
        # PEG质量
        if 'pe_ttm' in financial_data.columns and 'eps_growth' in financial_data.columns:
            pe_ttm = pd.to_numeric(financial_data['pe_ttm'], errors='coerce')
            eps_growth = pd.to_numeric(financial_data['eps_growth'], errors='coerce')
            peg = pe_ttm / (eps_growth + 1e-6)
            factors['pe_g_quality'] = 1 / (peg + 1e-6)
        
        return factors
    
    def calculate_efficiency_factors(self, financial_data):
        """
        计算效率因子
        
        Args:
            financial_data: 财务数据
            
        Returns:
            factors: 效率因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 运营效率（综合周转率）
        efficiency_score = 0
        count = 0
        
        for metric in ['asset_turnover', 'inventory_turnover', 'receivables_turnover']:
            if metric in financial_data.columns:
                turnover = pd.to_numeric(financial_data[metric], errors='coerce')
                efficiency_score += turnover
                count += 1
        
        if count > 0:
            factors['operational_efficiency'] = efficiency_score / count
        
        # 资本效率（ROE与资产周转率的结合）
        if 'roe' in financial_data.columns and 'asset_turnover' in financial_data.columns:
            roe = pd.to_numeric(financial_data['roe'], errors='coerce')
            asset_turnover = pd.to_numeric(financial_data['asset_turnover'], errors='coerce')
            factors['capital_efficiency'] = roe * asset_turnover / 100
        
        return factors
    
    def calculate_surprise_factors(self, financial_data, analyst_estimates=None):
        """
        计算预期差因子
        
        Args:
            financial_data: 财务数据
            analyst_estimates: 分析师预期数据（可选）
            
        Returns:
            factors: 预期差因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 1. 盈利超预期
        if 'eps_actual' in financial_data.columns and analyst_estimates is not None and 'eps_estimate' in analyst_estimates.columns:
            eps_actual = pd.to_numeric(financial_data['eps_actual'], errors='coerce')
            eps_estimate = pd.to_numeric(analyst_estimates['eps_estimate'], errors='coerce')
            eps_surprise = (eps_actual - eps_estimate) / (abs(eps_estimate) + 1e-6)
            factors['eps_surprise'] = eps_surprise
            
            # 标准化后的超预期
            if len(eps_surprise) >= 20:
                factors['eps_surprise_std'] = eps_surprise / eps_surprise.rolling(20).std()
        elif 'eps' in financial_data.columns and 'eps_forecast' in financial_data.columns:
            # 兼容旧格式
            eps = pd.to_numeric(financial_data['eps'], errors='coerce')
            eps_forecast = pd.to_numeric(financial_data['eps_forecast'], errors='coerce')
            factors['earnings_surprise'] = (eps - eps_forecast) / (abs(eps_forecast) + 1e-6)
        
        # 2. 收入超预期
        if 'revenue_actual' in financial_data.columns and analyst_estimates is not None and 'revenue_estimate' in analyst_estimates.columns:
            revenue_actual = pd.to_numeric(financial_data['revenue_actual'], errors='coerce')
            revenue_estimate = pd.to_numeric(analyst_estimates['revenue_estimate'], errors='coerce')
            revenue_surprise = (revenue_actual - revenue_estimate) / (abs(revenue_estimate) + 1e-6)
            factors['revenue_surprise'] = revenue_surprise
        elif 'revenue' in financial_data.columns and 'revenue_forecast' in financial_data.columns:
            # 兼容旧格式
            revenue = pd.to_numeric(financial_data['revenue'], errors='coerce')
            revenue_forecast = pd.to_numeric(financial_data['revenue_forecast'], errors='coerce')
            factors['revenue_surprise'] = (revenue - revenue_forecast) / (abs(revenue_forecast) + 1e-6)
        
        # 3. 超预期的持续性
        if 'eps_surprise' in factors:
            factors['surprise_momentum'] = factors['eps_surprise'].diff(4)  # 超预期的变化
        elif 'earnings_surprise' in factors:
            factors['surprise_momentum'] = factors['earnings_surprise'].diff(4)
        
        return factors
    
    def calculate_supply_chain_factors(self, company_data, industry_data=None):
        """
        计算产业链因子
        
        Args:
            company_data: 公司财务数据
            industry_data: 行业数据（可选）
            
        Returns:
            factors: 产业链因子字典
        """
        factors = {}
        
        if company_data is None or company_data.empty:
            return factors
        
        # 1. 上下游议价能力
        if 'receivables_turnover' in company_data.columns and 'payables_turnover' in company_data.columns:
            # 应收周转 vs 应付周转
            receivables_turnover = pd.to_numeric(company_data['receivables_turnover'], errors='coerce')
            payables_turnover = pd.to_numeric(company_data['payables_turnover'], errors='coerce')
            factors['bargaining_power'] = payables_turnover / (receivables_turnover + 1e-6)
        
        # 2. 产业链位置
        if 'gross_margin' in company_data.columns:
            gross_margin = pd.to_numeric(company_data['gross_margin'], errors='coerce')
            if industry_data is not None and 'gross_margin' in industry_data.columns:
                industry_avg_margin = industry_data['gross_margin'].mean()
                factors['margin_position'] = gross_margin - industry_avg_margin
            else:
                # 简化实现：使用历史平均作为行业平均
                factors['margin_position'] = gross_margin - gross_margin.rolling(12).mean()
        
        # 3. 景气度传导
        if 'inventory_turnover' in company_data.columns:
            # 库存周转变化反映下游景气度
            inventory_turnover = pd.to_numeric(company_data['inventory_turnover'], errors='coerce')
            factors['inventory_signal'] = inventory_turnover.pct_change(4)
        
        # 4. 产业链位置（兼容旧接口）
        factors['industry_chain_position'] = 2  # 默认中游
        
        # 5. 供应链强度（兼容旧接口）
        if 'receivables_turnover' in company_data.columns and 'payables_turnover' in company_data.columns:
            receivables_turnover = pd.to_numeric(company_data['receivables_turnover'], errors='coerce')
            payables_turnover = pd.to_numeric(company_data['payables_turnover'], errors='coerce')
            factors['supply_chain_strength'] = payables_turnover / (receivables_turnover + 1e-6)
        
        return factors
    
    def calculate_decay_factors(self, financial_data):
        """
        计算时间衰减因子
        
        Args:
            financial_data: 财务数据
            
        Returns:
            factors: 时间衰减因子字典
        """
        factors = {}
        
        if financial_data is None or financial_data.empty:
            return factors
        
        # 1. 数据新鲜度
        for col in ['roe', 'revenue_growth', 'operating_margin']:
            if col in financial_data.columns:
                values = pd.to_numeric(financial_data[col], errors='coerce')
                # 指数衰减权重
                weights = np.exp(-0.1 * np.arange(len(values))[::-1])
                # 计算加权平均
                if len(values) > 0 and np.sum(weights) > 0:
                    weighted_avg = np.average(values, weights=weights)
                    factors[f'{col}_decayed'] = weighted_avg
        
        # 2. 质量趋势
        if 'roe' in financial_data.columns:
            roe_values = pd.to_numeric(financial_data['roe'], errors='coerce').values
            # 计算最近4个季度的线性趋势
            if len(roe_values) >= 4:
                x = np.arange(4)
                slope = np.polyfit(x, roe_values[-4:], 1)[0]
                factors['roe_trend'] = slope
        
        return factors
    
    def calculate_all_value_factors(self, financial_data, price_data=None, industry_data=None, analyst_estimates=None):
        """
        计算所有价值因子
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据（可选）
            industry_data: 行业数据（可选）
            analyst_estimates: 分析师预期数据（可选）
            
        Returns:
            all_factors: 所有价值因子字典
        """
        profitability_factors = self.calculate_profitability_factors(financial_data)
        growth_factors = self.calculate_growth_factors(financial_data)
        quality_factors = self.calculate_quality_factors(financial_data)
        valuation_factors = self.calculate_valuation_factors(financial_data, price_data)
        efficiency_factors = self.calculate_efficiency_factors(financial_data)
        surprise_factors = self.calculate_surprise_factors(financial_data, analyst_estimates)
        supply_chain_factors = self.calculate_supply_chain_factors(financial_data, industry_data)
        decay_factors = self.calculate_decay_factors(financial_data)
        
        # 合并所有因子
        all_factors = {}
        all_factors.update(profitability_factors)
        all_factors.update(growth_factors)
        all_factors.update(quality_factors)
        all_factors.update(valuation_factors)
        all_factors.update(efficiency_factors)
        all_factors.update(surprise_factors)
        all_factors.update(supply_chain_factors)
        all_factors.update(decay_factors)
        
        return all_factors
    
    def _winsorize(self, series, limits=[0.01, 0.01]):
        """
        截尾均值处理
        
        Args:
            series: 待处理的序列
            limits: 上下限分位数
            
        Returns:
            winsorized_series: 处理后的序列
        """
        if isinstance(series, pd.Series):
            lower = series.quantile(limits[0])
            upper = series.quantile(1 - limits[1])
            return series.clip(lower, upper)
        return series
    
    def prepare_training_data_improved(self, financial_data, price_data):
        """
        多时间尺度标签构造
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            
        Returns:
            labels_short: 短期标签
            labels_medium: 中期标签
        """
        # 1. 短期标签（1-3个月）- 捕捉财报后的反应
        labels_short = {
            'return_1m': price_data['close'].pct_change(20).shift(-20),   # 1个月
            'return_3m': price_data['close'].pct_change(60).shift(-60),   # 3个月
        }
        
        # 2. 中期标签（6-12个月）- 捕捉价值回归
        labels_medium = {
            'return_6m': price_data['close'].pct_change(120).shift(-120), # 6个月
            'return_12m': price_data['close'].pct_change(240).shift(-240),# 12个月
        }
        
        # 3. 使用截尾均值平滑标签
        for name, label in labels_short.items():
            # 去除极端收益的影响
            labels_short[name] = self._winsorize(label, limits=[0.01, 0.01])
        
        for name, label in labels_medium.items():
            labels_medium[name] = self._winsorize(label, limits=[0.01, 0.01])
        
        # 4. 训练多个模型分别预测不同时间尺度
        # 或者让模型输出多个头
        return labels_short, labels_medium
    
    def align_financial_data(self, financial_data, price_data):
        """
        正确处理财报发布日期
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            
        Returns:
            aligned_data: 对齐后的数据
        """
        # 1. 获取真实的财报发布日期（不是财报截止日）
        if 'report_date' in financial_data.columns:
            report_dates = financial_data['report_date']
        else:
            # 如果没有发布日期，假设在季度结束后45天发布
            quarter_end = financial_data.index
            report_dates = quarter_end + pd.DateOffset(days=45)
        
        # 2. 对齐数据：只有在财报发布后，才能使用该财报数据
        aligned_data = []
        for i, (idx, row) in enumerate(financial_data.iterrows()):
            report_date = report_dates[i]
            
            # 获取财报发布后的价格数据
            future_prices = price_data[price_data.index > report_date]
            if len(future_prices) > 20:  # 至少需要20个交易日
                # 计算不同时间尺度的收益率
                returns = {}
                for horizon, days in [(1, 20), (3, 60), (6, 120), (12, 240)]:
                    if len(future_prices) > days:
                        returns[f'return_{horizon}m'] = future_prices['close'].iloc[days] / future_prices['close'].iloc[0] - 1
                
                aligned_data.append({
                    'financial_data': row,
                    'report_date': report_date,
                    **returns
                })
        
        return pd.DataFrame(aligned_data)
    
    def prepare_training_data(self, financial_data, price_data, future_return_horizon=20):
        """
        准备训练数据
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            future_return_horizon: 未来收益率预测期（交易日）
            
        Returns:
            X: 特征矩阵
            y: 标签向量
            feature_cols: 特征列
        """
        # 正确处理财报发布日期，避免前视偏差
        aligned_data = self.align_financial_data(financial_data, price_data)
        
        if aligned_data.empty:
            print("无法对齐财务数据和价格数据")
            return None, None, []
        
        # 提取财务数据
        financial_data_aligned = pd.DataFrame([item for item in aligned_data['financial_data']])
        
        # 计算价值因子
        value_factors = self.calculate_all_value_factors(financial_data_aligned, price_data)
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(value_factors)
        
        # 添加不同时间尺度的收益率
        for col in aligned_data.columns:
            if col.startswith('return_'):
                factor_df[col] = aligned_data[col].values
        
        # 选择目标标签
        target_label = f'return_{int(future_return_horizon/20)}m' if future_return_horizon in [20, 60, 120, 240] else 'return_1m'
        
        if target_label not in factor_df.columns:
            target_label = 'return_1m'
        
        # 去除空值
        factor_df = factor_df.dropna(subset=[target_label])
        
        # 删除大部分为空的列
        cols_to_drop = []
        for col in factor_df.columns:
            if col not in aligned_data.columns:
                non_null_ratio = factor_df[col].notna().sum() / len(factor_df)
                if non_null_ratio < 0.3:
                    cols_to_drop.append(col)
        
        if cols_to_drop:
            factor_df = factor_df.drop(columns=cols_to_drop)
        
        # 极端值处理：分位数缩尾
        feature_cols = [col for col in factor_df.columns if not col.startswith('return_')]
        for col in feature_cols:
            if col in factor_df.columns:
                # 使用5%和95%分位数进行缩尾
                q1 = factor_df[col].quantile(0.05)
                q9 = factor_df[col].quantile(0.95)
                factor_df[col] = factor_df[col].clip(q1, q9)
        
        # 删除所有包含NaN的行
        factor_df = factor_df.dropna()
        
        if factor_df.empty:
            return None, None, []
        
        # 特征选择：使用LASSO进行特征选择
        if len(feature_cols) > 5:  # 当特征数量较多时进行选择
            selected_cols = self.feature_selection(factor_df, feature_cols, target_label)
            if selected_cols:
                feature_cols = selected_cols
                print(f"特征选择完成，保留 {len(selected_cols)} 个特征: {selected_cols}")
        
        # 添加复合逻辑特征
        if 'roe_quality' in factor_df.columns and 'asset_turnover' in factor_df.columns:
            # (毛利率 * 资产周转率) 类似ROA的概念
            factor_df['profit_turnover'] = factor_df['roe_quality'] * factor_df['asset_turnover']
            feature_cols.append('profit_turnover')
        
        # 行业中性化处理
        # 注意：实际应用中需要传入股票代码列表
        # 这里使用模拟数据进行演示
        factor_df = self.industry_neutralization(factor_df, feature_cols)
        
        X = factor_df[feature_cols].values
        y = factor_df[target_label].values
        
        return X, y, feature_cols
    
    def industry_neutralization(self, factor_df, feature_cols):
        """
        行业中性化处理
        
        Args:
            factor_df: 因子数据
            feature_cols: 特征列
            stock_codes: 股票代码列表
            
        Returns:
            factor_df: 行业中性化后的因子数据
        """
        # 模拟股票代码（实际应用中需要传入）
        stock_codes = ['000001.SZ', '000002.SZ', '000008.SZ', '000009.SZ', '000012.SZ'] * (len(factor_df) // 5 + 1)
        stock_codes = stock_codes[:len(factor_df)]
        
        # 添加行业代码
        factor_df['industry_code'] = [industry_to_code.get(industry_classification.get(code, '综合'), 0) for code in stock_codes]
        
        # 对每个特征进行行业中性化
        for col in feature_cols:
            if col in factor_df.columns:
                # 对行业虚拟变量做回归，取残差
                # 这里使用简化的行业中性化方法
                # 实际实现应该：1. 生成行业虚拟变量 2. 做线性回归 3. 取残差
                industry_means = factor_df.groupby('industry_code')[col].transform('mean')
                factor_df[col] = factor_df[col] - industry_means
        
        # 删除行业代码列
        if 'industry_code' in factor_df.columns:
            factor_df = factor_df.drop(columns=['industry_code'])
        
        return factor_df
    
    def feature_selection(self, factor_df, feature_cols, target_label='return_1m'):
        """
        使用LASSO进行特征选择
        
        Args:
            factor_df: 因子数据
            feature_cols: 特征列
            target_label: 目标标签列名
            
        Returns:
            selected_cols: 选择的特征列
        """
        from sklearn.linear_model import LassoCV
        
        X = factor_df[feature_cols].values
        y = factor_df[target_label].values
        
        # 使用交叉验证的LASSO
        lasso_cv = LassoCV(cv=5, random_state=42)
        lasso_cv.fit(X, y)
        
        # 获取特征系数
        coefficients = lasso_cv.coef_
        
        # 选择系数非零的特征
        selected_cols = []
        for i, col in enumerate(feature_cols):
            if abs(coefficients[i]) > 1e-5:  # 阈值
                selected_cols.append(col)
        
        # 如果没有特征被选择，保留前5个重要特征
        if not selected_cols and feature_cols:
            # 使用随机森林获取特征重要性
            from sklearn.ensemble import RandomForestRegressor
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(X, y)
            importances = rf.feature_importances_
            indices = np.argsort(importances)[-5:]
            selected_cols = [feature_cols[i] for i in indices]
        
        return selected_cols
    
    def train_with_residuals(self, X, y):
        """
        残差建模：先拟合基础模型，再对残差建模
        
        Args:
            X: 特征矩阵
            y: 目标变量
            
        Returns:
            base_model: 基础模型
            residual_model: 残差模型
        """
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import GradientBoostingRegressor
        
        # 1. 基础模型 - 捕捉线性关系
        base_model = Ridge(alpha=10.0)
        base_model.fit(X, y)
        y_pred_base = base_model.predict(X)
        
        # 2. 计算残差
        residuals = y - y_pred_base
        
        # 3. 对残差建模 - 捕捉非线性关系
        residual_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42
        )
        residual_model.fit(X, residuals)
        
        return base_model, residual_model
    
    def train_ensemble(self, X, y):
        """
        改进的模型融合策略
        
        Args:
            X: 特征矩阵
            y: 目标变量
            
        Returns:
            ensemble_model: 加权集成模型
        """
        from sklearn.linear_model import Ridge, Lasso
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score
        import numpy as np
        
        # 1. 基础模型池
        models = {
            'ridge': Ridge(alpha=10.0),
            'lasso': Lasso(alpha=0.1),
            'gbdt_light': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=2,
                learning_rate=0.01,
                random_state=42
            ),
            'gbdt_deep': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.01,
                random_state=42
            )
        }
        
        # 2. 训练所有模型并记录验证集表现
        performances = {}
        trained_models = {}
        
        for name, model in models.items():
            # 交叉验证
            scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
            performances[name] = np.mean(scores)
            
            # 在整个训练集上重新训练
            model.fit(X, y)
            trained_models[name] = model
        
        # 3. 根据验证表现计算权重
        total = sum(np.exp(perf) for perf in performances.values())
        weights = {name: np.exp(perf) / total for name, perf in performances.items()}
        
        # 4. 创建加权集成模型
        class WeightedEnsemble:
            def __init__(self, models, weights):
                self.models = models
                self.weights = weights
            
            def predict(self, X):
                preds = np.zeros(len(X))
                for name, model in self.models.items():
                    preds += self.weights[name] * model.predict(X)
                return preds
        
        return WeightedEnsemble(trained_models, weights)
    
    def train(self, financial_data, price_data, future_return_horizon=20, use_hierarchical=False, use_residual=False, use_ensemble=False):
        """
        训练基本面价值评估模型
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            future_return_horizon: 未来收益率预测期（交易日）
            use_hierarchical: 是否使用分层建模
            use_residual: 是否使用残差建模
            use_ensemble: 是否使用改进的模型融合
        """
        print("="*60)
        print("训练基本面价值评估模型")
        print("="*60)
        
        # 准备数据
        X, y, feature_cols = self.prepare_training_data(financial_data, price_data, future_return_horizon)
        
        if X is None or len(X) == 0:
            print("无法准备训练数据")
            return None
        
        # 保存特征列信息
        self.feature_cols = feature_cols
        
        print(f"训练数据量: {len(X)}")
        print(f"特征数量: {X.shape[1]}")
        print(f"特征列: {feature_cols}")
        
        # 标准化特征
        self.scaler_X = StandardScaler()
        X_scaled = self.scaler_X.fit_transform(X)
        
        # 标准化标签
        self.scaler_y = StandardScaler()
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_scaled, 
            test_size=0.2, 
            random_state=42
        )
        
        if use_hierarchical:
            # 分层建模：不同行业、市值分别处理
            print("使用分层建模")
            # 这里使用简化实现，实际应用中需要根据行业和市值分组
            self.models = {}
            
            # 模拟行业分组
            n_groups = 3
            group_indices = np.random.randint(0, n_groups, size=len(X_train))
            
            for i in range(n_groups):
                group_mask = group_indices == i
                X_train_group = X_train[group_mask]
                y_train_group = y_train[group_mask]
                
                if len(X_train_group) > 10:
                    # 为每个组创建模型
                    if use_ensemble:
                        # 使用改进的模型融合
                        self.models[f'group_{i}'] = self.train_ensemble(X_train_group, y_train_group)
                    elif self.model_type == 'voting':
                        estimators = []
                        estimators.append(('gbdt', GradientBoostingRegressor(
                            n_estimators=200,
                            max_depth=3,
                            learning_rate=0.01,
                            subsample=0.7,
                            random_state=42
                        )))
                        estimators.append(('ridge', Ridge(alpha=10.0)))
                        
                        if XGBRegressor:
                            estimators.append(('xgb', XGBRegressor(
                                n_estimators=200,
                                max_depth=3,
                                learning_rate=0.01,
                                subsample=0.7,
                                random_state=42
                            )))
                        
                        if LGBMRegressor:
                            estimators.append(('lgb', LGBMRegressor(
                                n_estimators=200,
                                max_depth=3,
                                learning_rate=0.01,
                                subsample=0.7,
                                random_state=42
                            )))
                        
                        self.models[f'group_{i}'] = VotingRegressor(estimators=estimators)
                        self.models[f'group_{i}'].fit(X_train_group, y_train_group)
                    else:
                        self.models[f'group_{i}'] = GradientBoostingRegressor(
                            n_estimators=300,
                            max_depth=2,
                            learning_rate=0.005,
                            subsample=0.7,
                            min_samples_split=150,
                            min_samples_leaf=75,
                            validation_fraction=0.2,
                            n_iter_no_change=30,
                            random_state=42
                        )
                        self.models[f'group_{i}'].fit(X_train_group, y_train_group)
        elif use_residual:
            # 残差建模：先线性后非线性
            print("使用残差建模")
            
            # 使用改进的残差建模
            base_model, residual_model = self.train_with_residuals(X_train, y_train)
            
            # 保存模型
            self.linear_model = base_model
            self.residual_model = residual_model
            self.model_type = 'residual'
        else:
            # 根据模型类型选择模型
            if use_ensemble:
                # 使用改进的模型融合
                print("使用改进的模型融合")
                self.model = self.train_ensemble(X_train, y_train)
            elif self.model_type == 'ridge':
                self.model = Ridge(alpha=10.0)  # 增加正则化强度
                self.model.fit(X_train, y_train)
            elif self.model_type == 'lasso':
                self.model = Lasso(alpha=0.1)
                self.model.fit(X_train, y_train)
            elif self.model_type == 'elasticnet':
                self.model = ElasticNet(alpha=0.1, l1_ratio=0.5)
                self.model.fit(X_train, y_train)
            elif self.model_type == 'gbdt':
                self.model = GradientBoostingRegressor(
                    n_estimators=300,      # 树的数量
                    max_depth=2,           # 进一步限制树深度
                    learning_rate=0.005,    # 进一步降低学习率
                    subsample=0.7,          # 子采样
                    min_samples_split=150,  # 增加最小样本分割数
                    min_samples_leaf=75,    # 增加最小叶子节点数
                    validation_fraction=0.2, # 留出验证集
                    n_iter_no_change=30,    # 早停
                    random_state=42
                )
                self.model.fit(X_train, y_train)
            elif self.model_type == 'voting':
                # 模型融合：使用投票集成
                estimators = []
                
                # 添加GradientBoostingRegressor
                estimators.append(('gbdt', GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=3,
                    learning_rate=0.01,
                    subsample=0.7,
                    random_state=42
                )))
                
                # 添加Ridge
                estimators.append(('ridge', Ridge(alpha=10.0)))
                
                # 尝试添加XGBoost
                if XGBRegressor:
                    estimators.append(('xgb', XGBRegressor(
                        n_estimators=200,
                        max_depth=3,
                        learning_rate=0.01,
                        subsample=0.7,
                        random_state=42
                    )))
                
                # 尝试添加LightGBM
                if LGBMRegressor:
                    estimators.append(('lgb', LGBMRegressor(
                        n_estimators=200,
                        max_depth=3,
                        learning_rate=0.01,
                        subsample=0.7,
                        random_state=42
                    )))
                
                # 创建投票集成模型
                self.model = VotingRegressor(estimators=estimators)
                self.model.fit(X_train, y_train)
            else:  # ensemble
                # 使用集成方法
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    min_samples_split=10,
                    min_samples_leaf=5,
                    random_state=42
                )
                self.model.fit(X_train, y_train)
        
        # 评估模型
        if use_hierarchical:
            # 分层模型评估
            y_pred_train = np.zeros_like(y_train)
            y_pred_test = np.zeros_like(y_test)
            
            # 模拟分组
            train_group_indices = np.random.randint(0, n_groups, size=len(X_train))
            test_group_indices = np.random.randint(0, n_groups, size=len(X_test))
            
            for i in range(n_groups):
                train_mask = train_group_indices == i
                test_mask = test_group_indices == i
                
                if f'group_{i}' in self.models:
                    if train_mask.sum() > 0:
                        y_pred_train[train_mask] = self.models[f'group_{i}'].predict(X_train[train_mask])
                    if test_mask.sum() > 0:
                        y_pred_test[test_mask] = self.models[f'group_{i}'].predict(X_test[test_mask])
        elif use_residual:
            # 残差模型评估
            y_pred_train_linear = self.linear_model.predict(X_train)
            y_pred_train_residual = self.residual_model.predict(X_train)
            y_pred_train = y_pred_train_linear + y_pred_train_residual
            
            y_pred_test_linear = self.linear_model.predict(X_test)
            y_pred_test_residual = self.residual_model.predict(X_test)
            y_pred_test = y_pred_test_linear + y_pred_test_residual
        else:
            # 传统模型评估
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)
        
        # 反标准化
        y_pred_train_original = self.scaler_y.inverse_transform(y_pred_train.reshape(-1, 1)).flatten()
        y_pred_test_original = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).flatten()
        y_train_original = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        train_mse = np.mean((y_train_original - y_pred_train_original) ** 2)
        test_mse = np.mean((y_test_original - y_pred_test_original) ** 2)
        train_r2 = 1 - (np.sum((y_train_original - y_pred_train_original) ** 2) / 
                       np.sum((y_train_original - np.mean(y_train_original)) ** 2))
        test_r2 = 1 - (np.sum((y_test_original - y_pred_test_original) ** 2) / 
                      np.sum((y_test_original - np.mean(y_test_original)) ** 2))
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
        
        # 交叉验证
        if not use_hierarchical and not use_residual:
            if hasattr(self.model, 'fit'):
                cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='r2')
                print(f"交叉验证 R²: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        
        print("="*60)
        
        return self.model
    
    def predict(self, financial_data, price_data=None, industry_data=None, analyst_estimates=None, stock_info=None):
        """
        预测基本面价值
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据（可选）
            industry_data: 行业数据（可选）
            analyst_estimates: 分析师预期数据（可选）
            stock_info: 股票信息，用于分层模型（可选）
            
        Returns:
            prediction: 预测结果字典
        """
        if not hasattr(self, 'model') and not hasattr(self, 'models') and not hasattr(self, 'linear_model'):
            raise ValueError("模型未训练，请先调用train方法")
        
        # 计算价值因子
        value_factors = self.calculate_all_value_factors(financial_data, price_data, industry_data, analyst_estimates)
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(value_factors)
        
        # 提取最新特征，使用训练时的特征列
        feature_values = []
        if hasattr(self, 'feature_cols'):
            # 使用训练时的特征列
            for col in self.feature_cols:
                if col in factor_df.columns:
                    if isinstance(factor_df[col], pd.Series):
                        val = factor_df[col].iloc[-1]
                    else:
                        val = factor_df[col]
                    
                    # 处理NaN值
                    if pd.isna(val):
                        val = 0
                else:
                    val = 0
                feature_values.append(val)
        else:
            # 使用所有因子作为特征
            for col in factor_df.columns:
                if isinstance(factor_df[col], pd.Series):
                    val = factor_df[col].iloc[-1]
                else:
                    val = factor_df[col]
                
                # 处理NaN值
                if pd.isna(val):
                    val = 0
                feature_values.append(val)
        
        X = np.array(feature_values).reshape(1, -1)
        
        # 标准化
        X_scaled = self.scaler_X.transform(X)
        
        # 预测
        if hasattr(self, 'models'):
            # 分层模型预测
            if stock_info:
                # 使用分层模型选择器
                hierarchical_model = HierarchicalFundamentalModel()
                base_model, adjustment = hierarchical_model.select_model(stock_info)
                # 这里使用简化实现，实际应用中需要根据股票信息选择合适的模型
                # 模拟分组
                group_id = np.random.randint(0, len(self.models))
                group_key = f'group_{group_id}'
                if group_key in self.models:
                    y_pred_scaled = self.models[group_key].predict(X_scaled)
                else:
                    # 使用第一个模型
                    group_key = list(self.models.keys())[0]
                    y_pred_scaled = self.models[group_key].predict(X_scaled)
            else:
                # 模拟分组
                group_id = np.random.randint(0, len(self.models))
                group_key = f'group_{group_id}'
                if group_key in self.models:
                    y_pred_scaled = self.models[group_key].predict(X_scaled)
                else:
                    # 使用第一个模型
                    group_key = list(self.models.keys())[0]
                    y_pred_scaled = self.models[group_key].predict(X_scaled)
        elif hasattr(self, 'linear_model') and hasattr(self, 'residual_model'):
            # 残差模型预测
            y_pred_scaled_linear = self.linear_model.predict(X_scaled)
            y_pred_scaled_residual = self.residual_model.predict(X_scaled)
            y_pred_scaled = y_pred_scaled_linear + y_pred_scaled_residual
        else:
            # 传统模型预测
            y_pred_scaled = self.model.predict(X_scaled)
        
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
        
        # 计算价值评估
        value_assessment = self.assess_company_quality(value_factors)
        
        prediction = {
            'predicted_return': y_pred,
            'value_assessment': value_assessment,
            'value_score': value_assessment['overall_score'],
            'quality_grade': value_assessment['grade'],
            'value_factors': value_factors
        }
        
        return prediction
    
    def assess_company_quality(self, value_factors):
        """
        评估公司质量
        
        Args:
            value_factors: 价值因子字典
            
        Returns:
            assessment: 质量评估字典
        """
        assessment = {}
        
        # 盈利能力评估
        profitability_score = 0
        if 'roe_quality' in value_factors:
            roe_q = value_factors['roe_quality']
            if isinstance(roe_q, pd.Series):
                roe_q = roe_q.iloc[-1]
            profitability_score += min(roe_q / 10, 1) * 0.4
        
        if 'margin_trend' in value_factors:
            margin_t = value_factors['margin_trend']
            if isinstance(margin_t, pd.Series):
                margin_t = margin_t.iloc[-1]
            profitability_score += np.tanh(margin_t) * 0.3
        
        if 'roa_stability' in value_factors:
            roa_s = value_factors['roa_stability']
            if isinstance(roa_s, pd.Series):
                roa_s = roa_s.iloc[-1]
            profitability_score += min(roa_s / 5, 1) * 0.3
        
        assessment['profitability_score'] = min(profitability_score, 1)
        
        # 成长能力评估
        growth_score = 0
        if 'growth_consistency' in value_factors:
            growth_c = value_factors['growth_consistency']
            if isinstance(growth_c, pd.Series):
                growth_c = growth_c.iloc[-1]
            growth_score += min(abs(growth_c), 1) * 0.4
        
        if 'growth_sustainability' in value_factors:
            growth_s = value_factors['growth_sustainability']
            if isinstance(growth_s, pd.Series):
                growth_s = growth_s.iloc[-1]
            growth_score += np.tanh(growth_s / 10) * 0.3
        
        if 'growth_momentum' in value_factors:
            growth_m = value_factors['growth_momentum']
            if isinstance(growth_m, pd.Series):
                growth_m = growth_m.iloc[-1]
            growth_score += np.tanh(growth_m / 5) * 0.3
        
        assessment['growth_score'] = min(growth_score, 1)
        
        # 财务质量评估
        quality_score = 0
        if 'financial_health' in value_factors:
            fh = value_factors['financial_health']
            if isinstance(fh, pd.Series):
                fh = fh.iloc[-1]
            quality_score += min(fh, 1) * 0.5
        
        if 'debt_sustainability' in value_factors:
            ds = value_factors['debt_sustainability']
            if isinstance(ds, pd.Series):
                ds = ds.iloc[-1]
            quality_score += min(ds / 10, 1) * 0.3
        
        if 'liquidity_strength' in value_factors:
            ls = value_factors['liquidity_strength']
            if isinstance(ls, pd.Series):
                ls = ls.iloc[-1]
            quality_score += min(ls / 3, 1) * 0.2
        
        assessment['quality_score'] = min(quality_score, 1)
        
        # 估值吸引力评估
        valuation_score = 0
        if 'value_score' in value_factors:
            vs = value_factors['value_score']
            if isinstance(vs, pd.Series):
                vs = vs.iloc[-1]
            valuation_score += min(vs, 1) * 0.6
        
        if 'valuation_attractiveness' in value_factors:
            va = value_factors['valuation_attractiveness']
            if isinstance(va, pd.Series):
                va = va.iloc[-1]
            valuation_score += va * 0.4
        
        assessment['valuation_score'] = min(valuation_score, 1)
        
        # 综合评分
        assessment['overall_score'] = (
            assessment['profitability_score'] * 0.3 +
            assessment['growth_score'] * 0.25 +
            assessment['quality_score'] * 0.25 +
            assessment['valuation_score'] * 0.2
        )
        
        # 评级
        if assessment['overall_score'] > 0.8:
            assessment['grade'] = 'A+'
        elif assessment['overall_score'] > 0.7:
            assessment['grade'] = 'A'
        elif assessment['overall_score'] > 0.6:
            assessment['grade'] = 'B+'
        elif assessment['overall_score'] > 0.5:
            assessment['grade'] = 'B'
        elif assessment['overall_score'] > 0.4:
            assessment['grade'] = 'C+'
        elif assessment['overall_score'] > 0.3:
            assessment['grade'] = 'C'
        else:
            assessment['grade'] = 'D'
        
        return assessment
    
    def get_fundamental_signal(self, prediction):
        """
        获取基本面信号
        
        Args:
            prediction: 预测结果
            
        Returns:
            signal: 基本面信号
        """
        # 综合考虑预测收益率和价值评估
        pred_return = prediction['predicted_return']
        value_score = prediction['value_score']
        quality_grade = prediction['value_assessment']['grade']
        
        # 基本面信号强度
        signal_strength = pred_return * value_score
        
        # 根据评级调整
        grade_multiplier = {
            'A+': 1.5,
            'A': 1.3,
            'B+': 1.1,
            'B': 1.0,
            'C+': 0.9,
            'C': 0.8,
            'D': 0.6
        }
        
        signal_strength *= grade_multiplier.get(quality_grade, 1.0)
        
        signal = {
            'strength': signal_strength,
            'direction': 'positive' if signal_strength > 0 else 'negative',
            'confidence': value_score,
            'grade': quality_grade,
            'time_horizon': 'long_term'  # 基本面信号是长期信号
        }
        
        return signal
    
    def calculate_position_size(self, signal, risk_params=None):
        """
        动态仓位计算
        
        Args:
            signal: 基本面信号
            risk_params: 风险参数
            
        Returns:
            position_size: 仓位大小
        """
        if risk_params is None:
            risk_params = {
                'max_position': 1.0,  # 最大仓位
                'base_position': 0.5,  # 基础仓位
                'confidence_threshold': 0.6  # 置信度阈值
            }
        
        # 根据置信度动态调整仓位
        confidence = signal['confidence']
        direction = 1 if signal['direction'] == 'positive' else -1
        
        if confidence < risk_params['confidence_threshold']:
            # 低置信度时使用基础仓位
            position_size = direction * risk_params['base_position']
        else:
            # 高置信度时根据置信度调整仓位
            position_size = direction * min(risk_params['max_position'], 
                                           risk_params['base_position'] + (confidence - risk_params['confidence_threshold']) * 2)
        
        return position_size
    
    def is_event_driven_update(self, financial_data, last_update_date=None):
        """
        事件驱动更新判断
        
        Args:
            financial_data: 财务数据
            last_update_date: 上次更新日期
            
        Returns:
            bool: 是否需要更新
        """
        # 检查是否有新的财报发布
        if 'report_date' in financial_data.columns:
            latest_report_date = financial_data['report_date'].max()
            if last_update_date is None or latest_report_date > last_update_date:
                return True
        
        # 检查是否有重大事件（如并购、重组等）
        # 这里使用简化实现，实际应用中需要更复杂的事件检测
        
        return False
    
    def calculate_risk_metrics(self, financial_data, price_data):
        """
        计算风险指标
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            
        Returns:
            risk_metrics: 风险指标
        """
        risk_metrics = {}
        
        # 波动率风险
        if price_data is not None and 'close' in price_data.columns:
            returns = price_data['close'].pct_change()
            risk_metrics['volatility'] = returns.std() * np.sqrt(252)  # 年化波动率
            risk_metrics['max_drawdown'] = self._calculate_max_drawdown(price_data['close'])
        
        # 流动性风险
        if price_data is not None and 'volume' in price_data.columns:
            avg_volume = price_data['volume'].mean()
            risk_metrics['liquidity_score'] = min(avg_volume / 1e6, 1.0)  # 标准化流动性得分
        
        # 财务风险
        if financial_data is not None:
            if 'debt_ratio' in financial_data.columns:
                debt_ratio = pd.to_numeric(financial_data['debt_ratio'], errors='coerce').iloc[-1]
                risk_metrics['debt_risk'] = min(debt_ratio / 100, 1.0)  # 标准化债务风险
            
            if 'interest_coverage' in financial_data.columns:
                interest_coverage = pd.to_numeric(financial_data['interest_coverage'], errors='coerce').iloc[-1]
                risk_metrics['interest_risk'] = max(0, 1 - min(interest_coverage / 5, 1.0))  # 标准化利息风险
        
        # 综合风险得分
        risk_factors = []
        if 'volatility' in risk_metrics:
            risk_factors.append(risk_metrics['volatility'] / 0.5)  # 假设0.5是正常波动率
        if 'debt_risk' in risk_metrics:
            risk_factors.append(risk_metrics['debt_risk'])
        if 'interest_risk' in risk_metrics:
            risk_factors.append(risk_metrics['interest_risk'])
        
        if risk_factors:
            risk_metrics['overall_risk'] = min(np.mean(risk_factors), 1.0)
        else:
            risk_metrics['overall_risk'] = 0.5
        
        return risk_metrics
    
    def _calculate_max_drawdown(self, price_series):
        """
        计算最大回撤
        
        Args:
            price_series: 价格序列
            
        Returns:
            max_drawdown: 最大回撤
        """
        if len(price_series) < 2:
            return 0
        
        cumulative_returns = (price_series / price_series.iloc[0]) - 1
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) * 100
        max_drawdown = drawdown.min()
        
        return abs(max_drawdown)
    
    def get_optimized_position(self, prediction, price_data, risk_params=None):
        """
        获取优化后的仓位
        
        Args:
            prediction: 预测结果
            price_data: 价格数据
            risk_params: 风险参数
            
        Returns:
            optimized_position: 优化后的仓位
        """
        # 获取基本面信号
        signal = self.get_fundamental_signal(prediction)
        
        # 计算风险指标
        risk_metrics = self.calculate_risk_metrics(prediction['value_factors'], price_data)
        
        # 基础仓位
        base_position = self.calculate_position_size(signal, risk_params)
        
        # 根据风险调整仓位
        risk_adjustment = 1 - risk_metrics['overall_risk']
        optimized_position = base_position * risk_adjustment
        
        # 限制仓位范围
        optimized_position = max(-1.0, min(1.0, optimized_position))
        
        return {
            'position': optimized_position,
            'signal': signal,
            'risk_metrics': risk_metrics,
            'risk_adjustment': risk_adjustment
        }

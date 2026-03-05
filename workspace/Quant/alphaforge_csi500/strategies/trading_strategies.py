# 统一的策略工具 - 封装高频和基本面模型

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 导入模型
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.high_frequency_sentiment import HighFrequencySentimentModel
from models.fundamental_value_v3 import FundamentalValueModel
from models.ai_signal_fusion import AISignalFusion
from models.dynamic_weight_allocator import DynamicWeightAllocator
from models.multi_frequency_fusion import MultiFrequencySignalFusionStrategy


class BaseTradingStrategy:
    """基础交易策略类"""
    def __init__(self, config=None):
        """初始化策略"""
        self.config = config or {}
        self.name = "BaseStrategy"
        self.params = {}
        self.is_trained = False
    
    def generate_signals(self, data):
        """生成交易信号"""
        raise NotImplementedError("子类必须实现generate_signals方法")
    
    def execute_trade(self, signal, price):
        """执行交易"""
        raise NotImplementedError("子类必须实现execute_trade方法")
    
    def train(self, *args, **kwargs):
        """训练策略"""
        raise NotImplementedError("子类必须实现train方法")


class HighFrequencySentimentStrategy(BaseTradingStrategy):
    """
    高频情绪策略
    
    封装 HighFrequencySentimentModel，基于市场微观结构和情绪生成交易信号
    """
    def __init__(self, config=None, hf_model=None):
        """
        初始化高频情绪策略
        
        Args:
            config: 配置参数
            hf_model: 高频情绪模型实例（可选，如果不提供则自动创建）
        """
        super().__init__(config)
        self.name = "HighFrequencySentimentStrategy"
        self.params = {
            'signal_threshold': self.config.get('signal_threshold', 0.02),
            'temperature_threshold': self.config.get('temperature_threshold', 0.7),
            'sentiment_threshold': self.config.get('sentiment_threshold', 0.5),
            'confidence_threshold': self.config.get('confidence_threshold', 0.6)
        }
        
        # 初始化或引用高频模型
        if hf_model is not None:
            self.hf_model = hf_model
        else:
            self.hf_model = HighFrequencySentimentModel(config)
    
    def train(self, tick_data, minute_data, future_return_horizon=60, multi_scale=False):
        """
        训练高频情绪策略
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            future_return_horizon: 未来收益率预测期
            multi_scale: 是否使用多尺度标签
        """
        print(f"\n训练 {self.name}")
        print("=" * 60)
        
        self.hf_model.train(tick_data, minute_data, future_return_horizon, multi_scale)
        self.is_trained = True
        
        print(f"{self.name} 训练完成")
        return self
    
    def generate_signals(self, tick_data, minute_data, order_book=None, market_data=None):
        """
        基于高频情绪生成交易信号
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            order_book: 订单簿数据（可选）
            market_data: 市场数据（可选）
            
        Returns:
            signals: 交易信号字典
        """
        if not self.is_trained:
            raise ValueError("策略未训练，请先调用train方法")
        
        # 调用高频模型进行预测
        prediction = self.hf_model.predict(tick_data, minute_data, 
                                          multi_scale=False, 
                                          order_book=order_book, 
                                          market_data=market_data)
        
        # 提取关键指标
        predicted_return = prediction.get('predicted_return', 0)
        temperature_score = prediction.get('temperature_score', 0.5)
        sentiment_score = prediction.get('sentiment_score', 0)
        reaction_path = prediction.get('reaction_path', {})
        confidence = reaction_path.get('confidence', 0.5)
        
        # 生成交易信号
        signal_strength = 0
        signal_direction = 'neutral'
        
        # 基于预测收益率生成信号
        if abs(predicted_return) > self.params['signal_threshold']:
            if predicted_return > 0:
                signal_direction = 'positive'
                signal_strength = min(abs(predicted_return) * 10, 1.0)  # 归一化到0-1
            else:
                signal_direction = 'negative'
                signal_strength = -min(abs(predicted_return) * 10, 1.0)
        
        # 根据市场温度调整信号强度
        if temperature_score > self.params['temperature_threshold']:
            # 高温市场，信号更可靠
            signal_strength *= 1.2
        elif temperature_score < 0.3:
            # 低温市场，信号可靠性降低
            signal_strength *= 0.8
        
        # 根据置信度过滤信号
        if confidence < self.params['confidence_threshold']:
            signal_strength *= 0.5  # 降低低置信度信号的权重
        
        # 确定信号等级
        abs_strength = abs(signal_strength)
        if abs_strength > 0.8:
            signal_level = 'strong'
        elif abs_strength > 0.5:
            signal_level = 'moderate'
        elif abs_strength > 0.2:
            signal_level = 'weak'
        else:
            signal_level = 'none'
        
        signals = {
            'signal_strength': signal_strength,
            'signal_direction': signal_direction,
            'signal_level': signal_level,
            'predicted_return': predicted_return,
            'temperature_score': temperature_score,
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'reaction_speed': reaction_path.get('reaction_speed', 0.5),
            'reaction_magnitude': reaction_path.get('reaction_magnitude', 0.5),
            'raw_prediction': prediction
        }
        
        return signals
    
    def execute_trade(self, signals, price):
        """
        执行交易
        
        Args:
            signals: 交易信号字典
            price: 当前价格
            
        Returns:
            trade: 交易信息
        """
        signal_strength = signals.get('signal_strength', 0)
        signal_level = signals.get('signal_level', 'none')
        
        # 根据信号强度决定仓位
        if signal_level == 'strong':
            position_size = 1.0
        elif signal_level == 'moderate':
            position_size = 0.6
        elif signal_level == 'weak':
            position_size = 0.3
        else:
            position_size = 0.0
        
        # 确定交易方向
        if signal_strength > 0:
            action = 'buy'
        elif signal_strength < 0:
            action = 'sell'
        else:
            action = 'hold'
        
        return {
            'action': action,
            'price': price,
            'position_size': position_size,
            'signal_strength': signal_strength,
            'signal_level': signal_level
        }


class FundamentalValueStrategy(BaseTradingStrategy):
    """
    基本面价值策略
    
    封装 FundamentalValueModel，基于公司基本面价值生成交易信号
    """
    def __init__(self, config=None, fd_model=None):
        """
        初始化基本面价值策略
        
        Args:
            config: 配置参数
            fd_model: 基本面价值模型实例（可选，如果不提供则自动创建）
        """
        super().__init__(config)
        self.name = "FundamentalValueStrategy"
        self.params = {
            'value_threshold': self.config.get('value_threshold', 0.6),
            'quality_threshold': self.config.get('quality_threshold', 0.5),
            'grade_threshold': self.config.get('grade_threshold', 'B'),
            'holding_period': self.config.get('holding_period', 60)  # 持有期（交易日）
        }
        
        # 初始化或引用基本面模型
        if fd_model is not None:
            self.fd_model = fd_model
        else:
            self.fd_model = FundamentalValueModel(config)
    
    def train(self, financial_data, price_data, future_return_horizon=20, 
              use_hierarchical=False, use_residual=False, use_ensemble=False):
        """
        训练基本面价值策略
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            future_return_horizon: 未来收益率预测期
            use_hierarchical: 是否使用分层建模
            use_residual: 是否使用残差建模
            use_ensemble: 是否使用改进的模型融合
        """
        print(f"\n训练 {self.name}")
        print("=" * 60)
        
        self.fd_model.train(financial_data, price_data, future_return_horizon,
                           use_hierarchical, use_residual, use_ensemble)
        self.is_trained = True
        
        print(f"{self.name} 训练完成")
        return self
    
    def generate_signals(self, financial_data, price_data):
        """
        基于基本面价值生成交易信号
        
        Args:
            financial_data: 财务数据
            price_data: 价格数据
            
        Returns:
            signals: 交易信号字典
        """
        if not self.is_trained:
            raise ValueError("策略未训练，请先调用train方法")
        
        # 调用基本面模型进行预测
        prediction = self.fd_model.predict(financial_data, price_data)
        
        # 提取关键指标
        predicted_return = prediction.get('predicted_return', 0)
        value_score = prediction.get('value_score', 0.5)
        value_assessment = prediction.get('value_assessment', {})
        grade = value_assessment.get('grade', 'C')
        profitability_score = value_assessment.get('profitability_score', 0.5)
        quality_score = value_assessment.get('quality_score', 0.5)
        
        # 生成交易信号
        signal_strength = 0
        signal_direction = 'neutral'
        
        # 基于价值评分生成信号
        if value_score > self.params['value_threshold']:
            signal_direction = 'positive'
            signal_strength = (value_score - 0.5) * 2  # 归一化到0-1
        elif value_score < (1 - self.params['value_threshold']):
            signal_direction = 'negative'
            signal_strength = -(0.5 - value_score) * 2
        
        # 根据质量评级调整信号
        grade_scores = {'A+': 1.0, 'A': 0.9, 'B+': 0.8, 'B': 0.7, 
                       'C+': 0.6, 'C': 0.5, 'D': 0.3}
        grade_score = grade_scores.get(grade, 0.5)
        
        if grade_score >= grade_scores.get(self.params['grade_threshold'], 0.7):
            signal_strength *= 1.2  # 高质量公司信号加强
        else:
            signal_strength *= 0.8  # 低质量公司信号减弱
        
        # 根据盈利能力调整
        if profitability_score > 0.7:
            signal_strength *= 1.1
        elif profitability_score < 0.3:
            signal_strength *= 0.9
        
        # 确定信号等级
        abs_strength = abs(signal_strength)
        if abs_strength > 0.8:
            signal_level = 'strong'
        elif abs_strength > 0.5:
            signal_level = 'moderate'
        elif abs_strength > 0.2:
            signal_level = 'weak'
        else:
            signal_level = 'none'
        
        signals = {
            'signal_strength': signal_strength,
            'signal_direction': signal_direction,
            'signal_level': signal_level,
            'predicted_return': predicted_return,
            'value_score': value_score,
            'grade': grade,
            'profitability_score': profitability_score,
            'quality_score': quality_score,
            'raw_prediction': prediction
        }
        
        return signals
    
    def execute_trade(self, signals, price):
        """
        执行交易
        
        Args:
            signals: 交易信号字典
            price: 当前价格
            
        Returns:
            trade: 交易信息
        """
        signal_strength = signals.get('signal_strength', 0)
        signal_level = signals.get('signal_level', 'none')
        grade = signals.get('grade', 'C')
        
        # 根据信号等级决定仓位
        if signal_level == 'strong':
            position_size = 1.0
        elif signal_level == 'moderate':
            position_size = 0.7
        elif signal_level == 'weak':
            position_size = 0.4
        else:
            position_size = 0.0
        
        # 根据质量评级微调仓位
        grade_scores = {'A+': 1.0, 'A': 0.95, 'B+': 0.9, 'B': 0.85, 
                       'C+': 0.8, 'C': 0.75, 'D': 0.6}
        position_size *= grade_scores.get(grade, 0.8)
        
        # 确定交易方向
        if signal_strength > 0:
            action = 'buy'
        elif signal_strength < 0:
            action = 'sell'
        else:
            action = 'hold'
        
        return {
            'action': action,
            'price': price,
            'position_size': position_size,
            'signal_strength': signal_strength,
            'signal_level': signal_level,
            'holding_period': self.params['holding_period']
        }


class MultiFrequencyFusionStrategy(BaseTradingStrategy):
    """
    多频段融合策略
    
    封装 MultiFrequencySignalFusionStrategy，整合高频和基本面信号生成最终交易信号
    """
    def __init__(self, config=None, fusion_strategy=None):
        """
        初始化多频段融合策略
        
        Args:
            config: 配置参数
            fusion_strategy: 多频段融合策略实例（可选，如果不提供则自动创建）
        """
        super().__init__(config)
        self.name = "MultiFrequencyFusionStrategy"
        self.params = {
            'signal_threshold': self.config.get('signal_threshold', 0.02),
            'confidence_threshold': self.config.get('confidence_threshold', 0.6),
            'max_position_size': self.config.get('max_position_size', 0.05),
            'rebalance_frequency': self.config.get('rebalance_frequency', 'daily')
        }
        
        # 初始化或引用融合策略
        if fusion_strategy is not None:
            self.fusion_strategy = fusion_strategy
        else:
            self.fusion_strategy = MultiFrequencySignalFusionStrategy(config)
        
        # 保存预测历史
        self.predictions_history = []
    
    def train(self, tick_data_list, minute_data_list, financial_data_list, 
              price_data_list, actual_returns):
        """
        训练多频段融合策略
        
        Args:
            tick_data_list: 逐笔交易数据列表
            minute_data_list: 分钟级数据列表
            financial_data_list: 财务数据列表
            price_data_list: 价格数据列表
            actual_returns: 实际收益率列表
        """
        print(f"\n训练 {self.name}")
        print("=" * 60)
        
        self.fusion_strategy.train(tick_data_list, minute_data_list, 
                                  financial_data_list, price_data_list, 
                                  actual_returns)
        self.is_trained = True
        
        print(f"{self.name} 训练完成")
        return self
    
    def generate_signals(self, tick_data, minute_data, financial_data, 
                        price_data, market_data=None, signal_age=0):
        """
        生成融合交易信号
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            financial_data: 财务数据
            price_data: 价格数据
            market_data: 市场数据（可选）
            signal_age: 信号年龄
            
        Returns:
            signals: 融合交易信号字典
        """
        if not self.is_trained:
            raise ValueError("策略未训练，请先调用train方法")
        
        # 调用融合策略生成信号
        fusion_signals = self.fusion_strategy.generate_signals(
            tick_data, minute_data, financial_data, price_data, 
            market_data, signal_age
        )
        
        # 提取关键信息
        final_signal = fusion_signals.get('final_signal', {})
        weights = fusion_signals.get('weights', {})
        fusion_prediction = fusion_signals.get('fusion', {})
        
        signal_strength = final_signal.get('strength', 0)
        signal_direction = final_signal.get('direction', 'neutral')
        signal_level = final_signal.get('level', 'none')
        confidence = final_signal.get('confidence', 0.5)
        action = final_signal.get('action', 'no_action')
        
        # 构建统一的信号格式
        signals = {
            'signal_strength': signal_strength,
            'signal_direction': signal_direction,
            'signal_level': signal_level,
            'confidence': confidence,
            'action': action,
            'expected_return': final_signal.get('expected_return', 0),
            'time_frame': final_signal.get('time_frame', 'medium_term'),
            'validity_period': final_signal.get('validity_period', 20),
            'risk_level': final_signal.get('risk_level', 'medium'),
            
            # 权重信息
            'hf_weight': weights.get('high_frequency', 0.5),
            'fd_weight': weights.get('fundamental', 0.5),
            'market_regime': weights.get('market_regime', 'sideways'),
            
            # 原始预测
            'fusion_prediction': fusion_prediction,
            'raw_signals': fusion_signals
        }
        
        # 保存历史
        self.predictions_history.append(signals)
        
        return signals
    
    def execute_trade(self, signals, price):
        """
        执行交易
        
        Args:
            signals: 交易信号字典
            price: 当前价格
            
        Returns:
            trade: 交易信息
        """
        signal_strength = signals.get('signal_strength', 0)
        signal_level = signals.get('signal_level', 'none')
        confidence = signals.get('confidence', 0.5)
        action = signals.get('action', 'no_action')
        risk_level = signals.get('risk_level', 'medium')
        
        # 根据信号等级和置信度决定仓位
        base_position = 0.0
        if signal_level == 'strong':
            base_position = 1.0
        elif signal_level == 'moderate':
            base_position = 0.6
        elif signal_level == 'weak':
            base_position = 0.3
        
        # 根据置信度调整
        position_size = base_position * confidence
        
        # 根据风险等级调整
        risk_multipliers = {'low': 1.0, 'medium': 0.8, 'high': 0.5}
        position_size *= risk_multipliers.get(risk_level, 0.8)
        
        # 限制最大仓位
        position_size = min(position_size, self.params['max_position_size'])
        
        return {
            'action': action,
            'price': price,
            'position_size': position_size,
            'signal_strength': signal_strength,
            'signal_level': signal_level,
            'confidence': confidence,
            'risk_level': risk_level,
            'expected_return': signals.get('expected_return', 0),
            'validity_period': signals.get('validity_period', 20)
        }
    
    def generate_portfolio_weights(self, signals_list, stock_codes):
        """
        生成组合权重
        
        Args:
            signals_list: 信号列表
            stock_codes: 股票代码列表
            
        Returns:
            weights: 组合权重字典
        """
        return self.fusion_strategy.generate_portfolio_weights(signals_list, stock_codes)


class StrategyManager:
    """策略管理器 - 统一管理所有策略"""
    def __init__(self, config=None):
        """初始化策略管理器"""
        self.config = config or {}
        self.strategies = {}
        self.active_strategy = None
    
    def add_strategy(self, name, strategy):
        """
        添加策略
        
        Args:
            name: 策略名称
            strategy: 策略对象
        """
        self.strategies[name] = strategy
        print(f"已添加策略: {name}")
    
    def set_active_strategy(self, name):
        """
        设置当前活跃策略
        
        Args:
            name: 策略名称
        """
        if name in self.strategies:
            self.active_strategy = self.strategies[name]
            print(f"当前活跃策略: {name}")
        else:
            print(f"策略不存在: {name}")
    
    def get_strategy(self, name):
        """
        获取策略
        
        Args:
            name: 策略名称
            
        Returns:
            strategy: 策略对象
        """
        return self.strategies.get(name)
    
    def generate_signals(self, strategy_name, *args, **kwargs):
        """
        使用指定策略生成信号
        
        Args:
            strategy_name: 策略名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            signals: 交易信号
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"策略不存在: {strategy_name}")
        
        strategy = self.strategies[strategy_name]
        return strategy.generate_signals(*args, **kwargs)
    
    def execute_trade(self, strategy_name, signals, price):
        """
        使用指定策略执行交易
        
        Args:
            strategy_name: 策略名称
            signals: 交易信号
            price: 当前价格
            
        Returns:
            trade: 交易信息
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"策略不存在: {strategy_name}")
        
        strategy = self.strategies[strategy_name]
        return strategy.execute_trade(signals, price)
    
    def backtest_strategy(self, strategy_name, data_dict, initial_capital=1000000):
        """
        回测策略
        
        Args:
            strategy_name: 策略名称
            data_dict: 数据字典
            initial_capital: 初始资金
            
        Returns:
            backtest_results: 回测结果
        """
        if strategy_name not in self.strategies:
            return None
        
        strategy = self.strategies[strategy_name]
        
        # 根据策略类型准备数据
        if isinstance(strategy, HighFrequencySentimentStrategy):
            tick_data = data_dict.get('tick_data')
            minute_data = data_dict.get('minute_data')
            if tick_data is None or minute_data is None:
                return None
            
            # 生成信号
            signals = strategy.generate_signals(tick_data, minute_data)
            
        elif isinstance(strategy, FundamentalValueStrategy):
            financial_data = data_dict.get('financial_data')
            price_data = data_dict.get('price_data')
            if financial_data is None or price_data is None:
                return None
            
            # 生成信号
            signals = strategy.generate_signals(financial_data, price_data)
            
        elif isinstance(strategy, MultiFrequencyFusionStrategy):
            tick_data = data_dict.get('tick_data')
            minute_data = data_dict.get('minute_data')
            financial_data = data_dict.get('financial_data')
            price_data = data_dict.get('price_data')
            
            if any(x is None for x in [tick_data, minute_data, financial_data, price_data]):
                return None
            
            # 生成信号
            signals = strategy.generate_signals(tick_data, minute_data, 
                                              financial_data, price_data)
        else:
            return None
        
        # 模拟回测
        # 这里简化处理，实际应该根据价格数据逐日回测
        backtest_results = {
            'strategy': strategy_name,
            'initial_capital': initial_capital,
            'signals': signals,
            'trades': []
        }
        
        return backtest_results
    
    def get_strategy_names(self):
        """
        获取策略名称列表
        
        Returns:
            strategy_names: 策略名称列表
        """
        return list(self.strategies.keys())
    
    def remove_strategy(self, name):
        """
        移除策略
        
        Args:
            name: 策略名称
        """
        if name in self.strategies:
            del self.strategies[name]
            print(f"已移除策略: {name}")
        else:
            print(f"策略不存在: {name}")
    
    def get_strategy_status(self):
        """
        获取所有策略状态
        
        Returns:
            status: 策略状态字典
        """
        status = {}
        for name, strategy in self.strategies.items():
            status[name] = {
                'is_trained': strategy.is_trained,
                'type': type(strategy).__name__
            }
        return status

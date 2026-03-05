# 多频段信号融合策略

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import warnings
import os
import threading
import time
from collections import deque
warnings.filterwarnings('ignore')

from models.high_frequency_sentiment import HighFrequencySentimentModel
from models.fundamental_value_v3 import FundamentalValueModel
from models.ai_signal_fusion import AISignalFusion
from models.dynamic_weight_allocator import DynamicWeightAllocator

class MultiFrequencySignalFusionStrategy:
    def __init__(self, config):
        """初始化多频段信号融合策略"""
        self.config = config
        
        # 初始化各个模型
        self.hf_model = HighFrequencySentimentModel(config)
        self.fd_model = FundamentalValueModel(config)
        self.fusion_model = AISignalFusion(config)
        self.weight_allocator = DynamicWeightAllocator(config)
        
        # 策略状态
        self.is_trained = False
        self.predictions_history = []
        
        # 策略参数
        self.rebalance_frequency = 'daily'  # 'daily', 'weekly', 'monthly'
        self.signal_threshold = 0.02  # 信号阈值
        self.max_position_size = 0.05  # 最大单只股票仓位
        
        # 模型版本控制
        self.model_registry = {
            'versions': [],
            'current_version': None,
            'performance_history': []
        }
        
        # 模型存储路径
        self.model_path = config.get('model_path', './models/saved/')
        os.makedirs(self.model_path, exist_ok=True)
        
        # 实时监控
        self.monitoring = {
            'enabled': config.get('enable_monitoring', False),
            'interval': config.get('monitoring_interval', 60),
            'alerts': deque(maxlen=1000),
            'last_signal': None,
            'signal_history': deque(maxlen=100),
            'monitoring_thread': None,
            'is_monitoring': False
        }
        
        # 报警阈值
        self.alert_thresholds = {
            'signal_strength': config.get('alert_signal_threshold', 0.05),
            'confidence': config.get('alert_confidence', 0.8),
            'risk_level': config.get('alert_risk_level', 'high'),
            'signal_reversal': config.get('alert_signal_reversal', True),
            'max_alerts_per_hour': config.get('max_alerts_per_hour', 10)
        }
        
        # 报警统计
        self.alert_stats = {
            'total_alerts': 0,
            'alert_types': {
                'strong_signal': 0,
                'high_confidence': 0,
                'high_risk': 0,
                'signal_reversal': 0
            },
            'last_alert_time': None
        }
        
        # 导入验证器
        try:
            from validation.model_validator import ModelValidator
            self.validator = ModelValidator(config)
            print("✅ 验证器初始化成功")
        except ImportError:
            print("⚠️ 未找到验证模块，验证功能将不可用")
            self.validator = None
        
        # 验证结果存储
        self.validation_results = {
            'strategy': None,
            'submodels': {},
            'backtest': None,
            'timestamp': None
        }
        
        print("多频段信号融合策略初始化完成")
    
    def train(self, train_data: Dict, val_data: Dict = None):
        """
        训练整个策略（使用训练/验证分离，避免数据泄露）
        
        Args:
            train_data: 训练数据，包含 {
                'tick': 逐笔交易数据列表,
                'minute': 分钟级数据列表,
                'financial': 财务数据列表,
                'price': 价格数据列表
            }
            val_data: 验证数据，格式同train_data，包含 'actual_returns'
        """
        print("="*60)
        print("训练多频段信号融合策略")
        print("="*60)
        
        # 1. 用训练数据训练各个基础模型
        print("\n【步骤1】训练基础模型")
        print("  训练高频市场情绪感知模型...")
        self.hf_model.train(train_data['tick'][0], train_data['minute'][0])
        
        print("  训练基本面价值评估模型...")
        self.fd_model.train(train_data['financial'][0], train_data['price'][0])
        
        # 2. 用验证数据生成预测（避免数据泄露）
        if val_data is None:
            print("\n⚠️ 警告：未提供验证数据，使用训练数据进行验证（可能导致过拟合）")
            val_data = train_data
        
        print("\n【步骤2】生成验证集预测")
        hf_predictions = []
        fd_predictions = []
        
        for i in range(len(val_data['tick'])):
            hf_pred = self.hf_model.predict(
                val_data['tick'][i],
                val_data['minute'][i]
            )
            fd_pred = self.fd_model.predict(
                val_data['financial'][i],
                val_data['price'][i]
            )
            
            hf_predictions.append(hf_pred)
            fd_predictions.append(fd_pred)
        
        # 3. 用验证集训练融合器
        print("\n【步骤3】训练AI信号融合器")
        if 'actual_returns' in val_data:
            self.fusion_model.train(
                hf_predictions,
                fd_predictions,
                val_data['actual_returns']
            )
        else:
            print("  ⚠️ 警告：验证数据中没有实际收益率，跳过融合器训练")
        
        # 4. 用验证集优化权重分配器参数
        print("\n【步骤4】优化权重分配器")
        self._optimize_weight_allocator(val_data)
        
        self.is_trained = True
        
        # 5. 在测试集上评估（如果提供）
        if 'test_data' in self.config:
            print("\n【步骤5】在测试集上评估")
            self._evaluate_on_test(self.config['test_data'])
        
        print("\n" + "="*60)
        print("多频段信号融合策略训练完成")
        print("="*60)
    
    def _optimize_weight_allocator(self, val_data: Dict):
        """
        优化权重分配器参数
        
        Args:
            val_data: 验证数据
        """
        print("  优化权重分配器参数...")
        
        # 这里可以实现权重分配器的参数优化
        # 简化版：使用默认参数
        # 实际应用中可以网格搜索最优参数
        
        # 计算不同市场环境下的最优权重
        if 'market_data' in val_data and len(val_data['market_data']) > 0:
            # 根据市场数据调整权重分配器的基准参数
            pass
        
        print("  权重分配器优化完成")
    
    def _evaluate_on_test(self, test_data: Dict):
        """
        在测试集上评估模型性能
        
        Args:
            test_data: 测试数据
        """
        print("\n  在测试集上评估...")
        
        predictions = []
        actuals = []
        
        for i in range(len(test_data['tick'])):
            # 生成信号
            signals = self.generate_signals(
                test_data['tick'][i],
                test_data['minute'][i],
                test_data['financial'][i],
                test_data['price'][i],
                test_data.get('market_data', [None])[i] if 'market_data' in test_data else None
            )
            
            predictions.append(signals['final_signal']['strength'])
            
            if 'actual_returns' in test_data:
                actuals.append(test_data['actual_returns'][i])
        
        # 计算评估指标
        if len(actuals) > 0:
            predictions_array = np.array(predictions)
            actuals_array = np.array(actuals)
            
            # IC（信息系数）
            ic = np.corrcoef(predictions_array, actuals_array)[0, 1]
            
            # 方向准确率
            direction_accuracy = np.mean(
                [1 if p * a > 0 else 0 for p, a in zip(predictions, actuals)]
            )
            
            print(f"  测试集IC: {ic:.4f}")
            print(f"  测试集方向准确率: {direction_accuracy:.2%}")
        else:
            print("  测试数据中没有实际收益率，跳过评估")
    
    def generate_signals(self, 
                       tick_data: pd.DataFrame,
                       minute_data: pd.DataFrame,
                       financial_data: pd.DataFrame,
                       price_data: pd.DataFrame,
                       market_data: pd.DataFrame = None,
                       signal_age: int = 0) -> Dict:
        """
        生成融合信号
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            financial_data: 财务数据
            price_data: 价格数据
            market_data: 市场数据（可选）
            signal_age: 信号年龄
            
        Returns:
            signals: 融合信号字典
        """
        if not self.is_trained:
            raise ValueError("策略未训练，请先调用train方法")
        
        print("="*60)
        print("生成融合信号")
        print("="*60)
        
        # 1. 高频市场情绪感知
        print("\n【高频信号】感知市场温度和情绪")
        hf_prediction = self.hf_model.predict(tick_data, minute_data)
        
        print(f"  市场温度: {hf_prediction['market_temperature']['level']} (得分: {hf_prediction['temperature_score']:.2f})")
        print(f"  市场情绪: {hf_prediction['market_sentiment']['level']} (得分: {hf_prediction['sentiment_score']:.2f})")
        print(f"  预测收益率: {hf_prediction['predicted_return']:.4f}")
        
        # 2. 基本面价值评估
        print("\n【基本面信号】评估公司体质和价值")
        fd_prediction = self.fd_model.predict(financial_data, price_data)
        
        print(f"  价值评分: {fd_prediction['value_score']:.2f}")
        print(f"  质量评级: {fd_prediction['value_assessment']['grade']}")
        print(f"  预测收益率: {fd_prediction['predicted_return']:.4f}")
        
        # 3. 动态权重分配
        print("\n【动态权重】根据市场环境分配权重")
        weights = self.weight_allocator.allocate_weights(
            market_data, hf_prediction, fd_prediction, signal_age
        )
        
        print(f"  高频信号权重: {weights['high_frequency']:.2%}")
        print(f"  基本面信号权重: {weights['fundamental']:.2%}")
        print(f"  市场制度: {weights['market_regime']}")
        
        # 4. AI信号融合（粘合剂）
        print("\n【AI融合】融合高频和基本面信号")
        fusion_prediction = self.fusion_model.predict(hf_prediction, fd_prediction)
        
        print(f"  融合预测收益率: {fusion_prediction['predicted_return']:.4f}")
        print(f"  信号类型: {fusion_prediction['fusion_signal']['type']}")
        print(f"  信号方向: {fusion_prediction['fusion_signal']['direction']}")
        print(f"  信号置信度: {fusion_prediction['fusion_signal']['confidence']:.2f}")
        
        # 5. 信号叠加
        print("\n【信号叠加】叠加融合信号")
        final_signal = self.overlay_signals(fusion_prediction, weights)
        
        print(f"  最终信号强度: {final_signal['strength']:.4f}")
        print(f"  最终信号方向: {final_signal['direction']}")
        print(f"  建议操作: {final_signal['action']}")
        
        # 6. 生成完整信号报告
        signals = {
            'high_frequency': hf_prediction,
            'fundamental': fd_prediction,
            'fusion': fusion_prediction,
            'weights': weights,
            'final_signal': final_signal,
            'timestamp': pd.Timestamp.now()
        }
        
        # 保存历史
        self.predictions_history.append(signals)
        
        print("\n" + "="*60)
        
        return signals
    
    def overlay_signals(self, fusion_prediction: Dict, weights: Dict) -> Dict:
        """
        信号叠加
        
        Args:
            fusion_prediction: 融合预测结果
            weights: 权重字典
            
        Returns:
            final_signal: 最终信号
        """
        fusion_signal = fusion_prediction['fusion_signal']
        reaction_path = fusion_prediction['reaction_path']
        
        # 1. 计算信号强度
        # 信号强度 = 融合预测收益率 * (高频权重 + 基本面权重)
        predicted_return = fusion_prediction['predicted_return']
        signal_strength = predicted_return * (weights['high_frequency'] + weights['fundamental'])
        
        # 2. 根据信号类型调整强度
        signal_type = fusion_signal['type']
        type_multiplier = {
            'strong_convergence': 1.5,
            'convergence': 1.2,
            'divergence': 0.8,
            'neutral': 1.0
        }
        
        signal_strength *= type_multiplier.get(signal_type, 1.0)
        
        # 3. 根据置信度调整强度
        confidence = fusion_signal['confidence']
        signal_strength *= confidence
        
        # 4. 信号方向
        signal_direction = 'positive' if signal_strength > 0 else 'negative'
        
        # 5. 信号等级
        abs_strength = abs(signal_strength)
        if abs_strength > 0.05:
            signal_level = 'strong'
        elif abs_strength > 0.02:
            signal_level = 'moderate'
        elif abs_strength > 0.01:
            signal_level = 'weak'
        else:
            signal_level = 'none'
        
        # 6. 建议操作
        action = self.get_action_recommendation(signal_strength, reaction_path)
        
        # 7. 信号时间框架
        time_frame = reaction_path.get('time_frame', 'medium_term')
        
        # 8. 信号有效期
        persistence = reaction_path.get('persistence', 1.0)
        validity_period = int(20 * persistence)  # 交易日
        
        final_signal = {
            'strength': signal_strength,
            'direction': signal_direction,
            'level': signal_level,
            'action': action,
            'time_frame': time_frame,
            'validity_period': validity_period,
            'confidence': confidence,
            'signal_type': signal_type,
            'expected_return': predicted_return,
            'risk_level': reaction_path.get('risk_level', 'medium')
        }
        
        return final_signal
    
    def get_action_recommendation(self, signal_strength: float, reaction_path: Dict) -> str:
        """
        获取操作建议
        
        Args:
            signal_strength: 信号强度
            reaction_path: 反应路径
            
        Returns:
            action: 操作建议
        """
        abs_strength = abs(signal_strength)
        risk_level = reaction_path.get('risk_level', 'medium')
        
        # 根据信号强度和风险等级给出建议
        if abs_strength > 0.05 and risk_level == 'low':
            return 'strong_buy' if signal_strength > 0 else 'strong_sell'
        elif abs_strength > 0.05 and risk_level == 'medium':
            return 'buy' if signal_strength > 0 else 'sell'
        elif abs_strength > 0.03:
            return 'buy' if signal_strength > 0 else 'sell'
        elif abs_strength > 0.02:
            return 'hold'
        elif abs_strength > 0.01:
            return 'hold'
        else:
            return 'no_action'
    
    def generate_portfolio_weights(self, 
                                  signals_list: List[Dict],
                                  stock_codes: List[str]) -> Dict[str, float]:
        """
        生成组合权重
        
        Args:
            signals_list: 信号列表
            stock_codes: 股票代码列表
            
        Returns:
            weights: 组合权重字典
        """
        print("="*60)
        print("生成组合权重")
        print("="*60)
        
        # 1. 根据信号强度排序
        stock_signals = []
        for i, signals in enumerate(signals_list):
            final_signal = signals['final_signal']
            stock_code = stock_codes[i]
            
            # 只考虑有效信号
            if final_signal['level'] != 'none':
                stock_signals.append({
                    'stock_code': stock_code,
                    'signal_strength': final_signal['strength'],
                    'signal_direction': final_signal['direction'],
                    'confidence': final_signal['confidence'],
                    'risk_level': final_signal['risk_level'],
                    'expected_return': final_signal['expected_return']
                })
        
        # 2. 按信号强度排序
        stock_signals.sort(key=lambda x: abs(x['signal_strength']), reverse=True)
        
        # 3. 选择前N只股票
        top_n = min(50, len(stock_signals))
        selected_stocks = stock_signals[:top_n]
        
        print(f"选择了 {top_n} 只股票")
        
        # 4. 计算权重
        weights = {}
        
        # 方法1：等权重
        equal_weight = 1.0 / len(selected_stocks) if selected_stocks else 0
        for stock in selected_stocks:
            weights[stock['stock_code']] = equal_weight
        
        # 方法2：按信号强度加权
        total_strength = sum(abs(s['signal_strength']) for s in selected_stocks)
        if total_strength > 0:
            for stock in selected_stocks:
                weight = abs(stock['signal_strength']) / total_strength
                # 限制最大权重
                weight = min(weight, self.max_position_size)
                weights[stock['stock_code']] = weight
        
        # 5. 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            for stock_code in weights:
                weights[stock_code] /= total_weight
        
        # 6. 打印前10大权重
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        print("\n前10大权重:")
        for stock_code, weight in sorted_weights[:10]:
            print(f"  {stock_code}: {weight:.4f}")
        
        print("="*60)
        
        return weights
    
    def generate_report(self, signals: Dict) -> str:
        """
        生成信号报告
        
        Args:
            signals: 信号字典
            
        Returns:
            report: 信号报告
        """
        hf_pred = signals['high_frequency']
        fd_pred = signals['fundamental']
        fusion_pred = signals['fusion']
        final_signal = signals['final_signal']
        weights = signals['weights']
        
        report = f"""
多频段信号融合策略报告
{'='*60}

【高频市场情绪感知】
市场温度: {hf_pred['market_temperature']['level']} (得分: {hf_pred['temperature_score']:.2f})
市场情绪: {hf_pred['market_sentiment']['level']} (得分: {hf_pred['sentiment_score']:.2f})
预测收益率: {hf_pred['predicted_return']:.4f}
反应速度: {hf_pred['reaction_path']['reaction_speed']:.2f}
反应幅度: {hf_pred['reaction_path']['reaction_magnitude']:.2f}

【基本面价值评估】
价值评分: {fd_pred['value_score']:.2f}
质量评级: {fd_pred['value_assessment']['grade']}
盈利能力: {fd_pred['value_assessment']['profitability_score']:.2f}
成长能力: {fd_pred['value_assessment']['growth_score']:.2f}
财务质量: {fd_pred['value_assessment']['quality_score']:.2f}
估值吸引力: {fd_pred['value_assessment']['valuation_score']:.2f}
预测收益率: {fd_pred['predicted_return']:.4f}

【AI信号融合（粘合剂）】
融合预测收益率: {fusion_pred['predicted_return']:.4f}
信号类型: {fusion_pred['fusion_signal']['type']}
信号方向: {fusion_pred['fusion_signal']['direction']}
信号置信度: {fusion_pred['fusion_signal']['confidence']:.2f}
信号一致性: {fusion_pred['fusion_signal']['alignment_score']:.2f}
温度价值匹配: {fusion_pred['fusion_signal']['temperature_value_match']:.2f}

【资金反应路径】
反应阶段: {fusion_pred['reaction_path']['phase']}
反应速度: {fusion_pred['reaction_path']['speed']} ({fusion_pred['reaction_path']['time_to_peak']})
反应幅度: {fusion_pred['reaction_path']['magnitude']:.4f} ({fusion_pred['reaction_path']['magnitude_level']})
反应持续性: {fusion_pred['reaction_path']['persistence']:.2f} ({fusion_pred['reaction_path']['persistence_level']})
反应形状: {fusion_pred['reaction_path']['shape']}
风险等级: {fusion_pred['reaction_path']['risk_level']}
风险因素: {', '.join(fusion_pred['reaction_path']['risk_factors']) if fusion_pred['reaction_path']['risk_factors'] else '无'}

【动态权重分配】
高频信号权重: {weights['high_frequency']:.2%}
基本面信号权重: {weights['fundamental']:.2%}
市场制度: {weights['market_regime']}
波动率得分: {weights['volatility_score']:.2f}
流动性得分: {weights['liquidity_score']:.2f}

【最终信号】
信号强度: {final_signal['strength']:.4f}
信号方向: {final_signal['direction']}
信号等级: {final_signal['level']}
建议操作: {final_signal['action']}
时间框架: {final_signal['time_frame']}
有效期: {final_signal['validity_period']} 交易日
预期收益率: {final_signal['expected_return']:.4f}

{'='*60}
"""
        
        return report
    
    def reset(self):
        """重置策略"""
        self.is_trained = False
        self.predictions_history = []
        self.weight_allocator.reset()
        print("多频段信号融合策略已重置")

    def save_version(self, version_name=None):
        """
        保存当前模型版本

        Args:
            version_name: 版本名称（可选，自动生成）

        Returns:
            version_name: 版本名称
        """
        try:
            import joblib
        except ImportError:
            print("❌ 未安装joblib，无法保存模型")
            return None

        if version_name is None:
            version_name = f"v{len(self.model_registry['versions']) + 1}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存各个子模型
        model_files = {
            'hf_model': f"{self.model_path}{version_name}_hf.pkl",
            'fd_model': f"{self.model_path}{version_name}_fd.pkl",
            'fusion_model': f"{self.model_path}{version_name}_fusion.pkl",
            'weight_allocator': f"{self.model_path}{version_name}_weight.pkl"
        }

        # 保存模型
        joblib.dump(self.hf_model, model_files['hf_model'])
        joblib.dump(self.fd_model, model_files['fd_model'])
        joblib.dump(self.fusion_model, model_files['fusion_model'])
        joblib.dump(self.weight_allocator, model_files['weight_allocator'])

        # 记录版本信息
        version_info = {
            'name': version_name,
            'timestamp': pd.Timestamp.now(),
            'files': model_files,
            'performance': self.model_registry['performance_history'][-1] if self.model_registry['performance_history'] else None
        }

        self.model_registry['versions'].append(version_info)
        self.model_registry['current_version'] = version_name

        print(f"✅ 模型版本 {version_name} 已保存")
        return version_name

    def load_version(self, version_name):
        """
        加载指定版本

        Args:
            version_name: 版本名称
        """
        try:
            import joblib
        except ImportError:
            print("❌ 未安装joblib，无法加载模型")
            return

        # 查找版本
        version_info = None
        for v in self.model_registry['versions']:
            if v['name'] == version_name:
                version_info = v
                break

        if version_info is None:
            raise ValueError(f"版本 {version_name} 不存在")

        # 加载模型
        self.hf_model = joblib.load(version_info['files']['hf_model'])
        self.fd_model = joblib.load(version_info['files']['fd_model'])
        self.fusion_model = joblib.load(version_info['files']['fusion_model'])
        self.weight_allocator = joblib.load(version_info['files']['weight_allocator'])

        self.model_registry['current_version'] = version_name
        self.is_trained = True

        print(f"✅ 已加载模型版本 {version_name}")

    def compare_versions(self, version_names=None):
        """
        比较不同版本的性能

        Args:
            version_names: 版本名称列表（可选，默认最近3个）

        Returns:
            comparison: 版本比较结果
        """
        if version_names is None:
            version_names = [v['name'] for v in self.model_registry['versions'][-3:]]

        comparison = []
        for version in version_names:
            for v_info in self.model_registry['versions']:
                if v_info['name'] == version:
                    comparison.append({
                        'version': version,
                        'timestamp': v_info['timestamp'],
                        'performance': v_info['performance']
                    })

        # 可视化比较
        if len(comparison) > 1:
            try:
                import matplotlib.pyplot as plt

                plt.figure(figsize=(10, 6))
                for c in comparison:
                    if c['performance'] and 'ic_series' in c['performance']:
                        plt.plot(c['performance']['ic_series'], label=c['version'])

                plt.xlabel('时间窗口')
                plt.ylabel('IC值')
                plt.title('模型版本性能对比')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.savefig(f"{self.model_path}version_comparison.png")
                print(f"✅ 版本对比图已保存到 {self.model_path}version_comparison.png")
                plt.close()
            except ImportError:
                print("⚠️ 未安装matplotlib，跳过可视化")

        return comparison

    def backtest(self, data_dict: Dict[str, Dict], initial_capital: float = 1000000) -> Dict:
        """
        回测策略（增强版）

        Args:
            data_dict: 数据字典
            initial_capital: 初始资金

        Returns:
            results: 回测结果
        """
        print("="*60)
        print("回测多频段信号融合策略（增强版）")
        print("="*60)

        # 导入回测工具
        try:
            from strategies.backtester import Backtester
        except ImportError:
            print("⚠️ 未找到Backtester模块，使用简化回测")
            return self._simple_backtest(data_dict, initial_capital)

        # 准备回测配置
        backtest_config = {
            'initial_capital': initial_capital,
            'commission': self.config.get('commission', 0.0003),  # 佣金
            'slippage': self.config.get('slippage', 0.001),      # 滑点
            'min_volume': self.config.get('min_volume', 10000),   # 最小成交量
            'lookback_period': self.config.get('lookback_period', 20)  # 回看期
        }

        # 创建回测器
        backtester = Backtester(backtest_config)

        # 准备信号生成函数
        def signal_generator(period_data):
            """生成信号的函数（供回测器调用）"""
            signals_list = []

            for stock_code, data in period_data.items():
                signals = self.generate_signals(
                    data['tick'],
                    data['minute'],
                    data['financial'],
                    data['price']
                )
                signals_list.append({
                    'stock_code': stock_code,
                    'signal': signals['final_signal']
                })

            return signals_list

        # 运行回测
        results = backtester.run(data_dict, signal_generator)

        # 详细输出
        print(f"\n回测结果:")
        print(f"  总收益率: {results['total_return']:.2%}")
        print(f"  年化收益率: {results['annual_return']:.2%}")
        print(f"  夏普比率: {results['sharpe_ratio']:.4f}")
        print(f"  最大回撤: {results['max_drawdown']:.2%}")
        print(f"  胜率: {results['win_rate']:.2%}")
        print(f"  交易次数: {results['trade_count']}")

        return results

    def _simple_backtest(self, data_dict: Dict[str, Dict], initial_capital: float = 1000000) -> Dict:
        """
        简化回测（当Backtester不可用时使用）

        Args:
            data_dict: 数据字典
            initial_capital: 初始资金

        Returns:
            results: 回测结果
        """
        print("使用简化回测...")

        backtest_results = {
            'dates': [],
            'portfolio_value': [],
            'weights': [],
            'returns': [],
            'signals': []
        }

        portfolio_value = initial_capital
        stock_codes = list(data_dict.keys())

        # 获取回测周期
        max_periods = min(len(data_dict[code]['price']) for code in stock_codes)

        for period in range(20, max_periods):
            # 生成信号
            signals_list = []
            for stock_code in stock_codes:
                data = data_dict[stock_code]
                tick_data = data['tick']
                minute_data = data['minute']
                financial_data = data['financial']
                price_data = data['price'].iloc[:period]

                signals = self.generate_signals(
                    tick_data, minute_data, financial_data, price_data
                )
                signals_list.append(signals)

            # 生成组合权重
            weights = self.generate_portfolio_weights(signals_list, stock_codes)

            # 计算组合收益
            portfolio_return = 0
            for stock_code, weight in weights.items():
                price_data = data_dict[stock_code]['price']
                if period < len(price_data):
                    stock_return = price_data['close'].pct_change().iloc[period]
                    portfolio_return += weight * stock_return

            # 更新组合价值
            portfolio_value *= (1 + portfolio_return)

            # 记录结果
            backtest_results['dates'].append(period)
            backtest_results['portfolio_value'].append(portfolio_value)
            backtest_results['weights'].append(weights)
            backtest_results['returns'].append(portfolio_return)
            backtest_results['signals'].append(signals_list)

        # 计算回测指标
        total_return = (portfolio_value / initial_capital) - 1
        returns = np.array(backtest_results['returns'])
        volatility = np.std(returns) * np.sqrt(252 / 20)
        sharpe_ratio = (np.mean(returns) * 252 / 20) / volatility if volatility > 0 else 0

        backtest_results['metrics'] = {
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'final_value': portfolio_value
        }

        print("\n" + "="*60)
        print("回测完成")
        print(f"总收益率: {total_return:.2%}")
        print(f"年化波动率: {volatility:.2%}")
        print(f"夏普比率: {sharpe_ratio:.4f}")
        print("="*60)

        return backtest_results
    
    def start_monitoring(self):
        """
        启动实时监控
        """
        if not self.monitoring['enabled']:
            print("⚠️ 监控未启用，请在配置中设置 enable_monitoring=True")
            return
        
        if self.monitoring['is_monitoring']:
            print("⚠️ 监控已在运行中")
            return
        
        if not self.is_trained:
            print("⚠️ 模型未训练，请先调用train方法")
            return
        
        def monitor_loop():
            while self.monitoring['is_monitoring']:
                try:
                    # 获取最新数据
                    latest_data = self._fetch_latest_data()
                    
                    if latest_data is None:
                        print("⚠️ 无法获取最新数据，等待下次尝试...")
                        time.sleep(self.monitoring['interval'])
                        continue
                    
                    # 生成信号
                    signals = self.generate_signals(
                        latest_data['tick'],
                        latest_data['minute'],
                        latest_data['financial'],
                        latest_data['price'],
                        latest_data.get('market_data')
                    )
                    
                    # 检查报警条件
                    self._check_alerts(signals)
                    
                    # 记录历史
                    self.monitoring['last_signal'] = signals
                    self.monitoring['signal_history'].append({
                        'timestamp': pd.Timestamp.now(),
                        'signal': signals['final_signal']
                    })
                    
                    # 打印监控状态
                    self._print_monitoring_status(signals)
                    
                    time.sleep(self.monitoring['interval'])
                    
                except Exception as e:
                    print(f"❌ 监控错误: {e}")
                    time.sleep(10)
        
        # 启动监控线程
        self.monitoring['is_monitoring'] = True
        self.monitoring['monitoring_thread'] = threading.Thread(
            target=monitor_loop, 
            daemon=True,
            name="MonitoringThread"
        )
        self.monitoring['monitoring_thread'].start()
        
        print(f"✅ 实时监控已启动（间隔: {self.monitoring['interval']}秒）")
    
    def _fetch_latest_data(self):
        """
        获取最新数据（需要根据实际数据源实现）
        
        Returns:
            data: 最新数据字典
        """
        # 这里需要根据实际数据源实现
        # 示例：从数据库或API获取最新数据
        
        # 暂时返回None，实际使用时需要实现
        print("⚠️ _fetch_latest_data方法需要根据实际数据源实现")
        return None
    
    def _check_alerts(self, signals):
        """
        检查是否需要报警
        
        Args:
            signals: 信号字典
        """
        final_signal = signals['final_signal']
        alerts = []
        
        # 检查报警频率限制
        if self._should_rate_limit_alerts():
            return
        
        # 信号强度报警
        if abs(final_signal['strength']) > self.alert_thresholds['signal_strength']:
            alerts.append({
                'type': 'strong_signal',
                'message': f"强信号出现: {final_signal['strength']:.2%} {final_signal['direction']}",
                'level': 'info',
                'timestamp': pd.Timestamp.now(),
                'details': {
                    'strength': final_signal['strength'],
                    'direction': final_signal['direction'],
                    'confidence': final_signal['confidence']
                }
            })
        
        # 高置信度报警
        if final_signal['confidence'] > self.alert_thresholds['confidence']:
            alerts.append({
                'type': 'high_confidence',
                'message': f"高置信度信号: {final_signal['confidence']:.1%}",
                'level': 'info',
                'timestamp': pd.Timestamp.now(),
                'details': {
                    'confidence': final_signal['confidence'],
                    'strength': final_signal['strength']
                }
            })
        
        # 高风险报警
        if final_signal['risk_level'] == self.alert_thresholds['risk_level']:
            alerts.append({
                'type': 'high_risk',
                'message': "高风险信号",
                'level': 'warning',
                'timestamp': pd.Timestamp.now(),
                'details': {
                    'risk_level': final_signal['risk_level'],
                    'action': final_signal['action']
                }
            })
        
        # 信号反转报警
        if self.alert_thresholds['signal_reversal'] and len(self.monitoring['signal_history']) > 0:
            last_signal = self.monitoring['signal_history'][-1]['signal']
            if last_signal['direction'] != final_signal['direction']:
                alerts.append({
                    'type': 'signal_reversal',
                    'message': f"信号反转: {last_signal['direction']} → {final_signal['direction']}",
                    'level': 'warning',
                    'timestamp': pd.Timestamp.now(),
                    'details': {
                        'previous_direction': last_signal['direction'],
                        'current_direction': final_signal['direction'],
                        'previous_strength': last_signal['strength'],
                        'current_strength': final_signal['strength']
                    }
                })
        
        # 记录和发送报警
        for alert in alerts:
            self.monitoring['alerts'].append(alert)
            self.alert_stats['total_alerts'] += 1
            self.alert_stats['alert_types'][alert['type']] += 1
            self.alert_stats['last_alert_time'] = pd.Timestamp.now()
            
            self._send_alert(alert)
    
    def _should_rate_limit_alerts(self):
        """
        检查是否需要限制报警频率
        
        Returns:
            bool: 是否限制
        """
        if self.alert_stats['last_alert_time'] is None:
            return False
        
        time_since_last_alert = (pd.Timestamp.now() - self.alert_stats['last_alert_time']).total_seconds()
        alerts_per_hour_limit = self.alert_thresholds['max_alerts_per_hour']
        min_interval = 3600 / alerts_per_hour_limit
        
        return time_since_last_alert < min_interval
    
    def _send_alert(self, alert):
        """
        发送报警（可以集成钉钉/微信/邮件）
        
        Args:
            alert: 报警字典
        """
        # 这里可以集成实际的报警通道
        # 例如：钉钉机器人、微信企业号、邮件等
        
        if alert['level'] == 'warning':
            print(f"⚠️ 报警: {alert['message']}")
        else:
            print(f"ℹ️ 提示: {alert['message']}")
        
        # 示例：钉钉机器人集成
        # self._send_dingtalk_alert(alert)
        
        # 示例：邮件集成
        # self._send_email_alert(alert)
    
    def _send_dingtalk_alert(self, alert):
        """
        发送钉钉报警（示例）
        
        Args:
            alert: 报警字典
        """
        import requests
        import json
        
        webhook_url = self.config.get('dingtalk_webhook_url')
        if not webhook_url:
            return
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"【多频段信号融合报警】\n{alert['message']}\n时间: {alert['timestamp']}"
            }
        }
        
        try:
            response = requests.post(webhook_url, json=message, timeout=5)
            if response.status_code == 200:
                print("✅ 钉钉报警发送成功")
            else:
                print(f"❌ 钉钉报警发送失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 钉钉报警发送异常: {e}")
    
    def _send_email_alert(self, alert):
        """
        发送邮件报警（示例）
        
        Args:
            alert: 报警字典
        """
        import smtplib
        from email.mime.text import MIMEText
        
        smtp_server = self.config.get('smtp_server')
        smtp_port = self.config.get('smtp_port', 587)
        smtp_username = self.config.get('smtp_username')
        smtp_password = self.config.get('smtp_password')
        recipient = self.config.get('alert_recipient')
        
        if not all([smtp_server, smtp_username, smtp_password, recipient]):
            return
        
        subject = f"【多频段信号融合报警】{alert['type']}"
        body = f"""
        报警类型: {alert['type']}
        报警级别: {alert['level']}
        报警消息: {alert['message']}
        报警时间: {alert['timestamp']}
        详细信息: {alert.get('details', {})}
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = recipient
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            print("✅ 邮件报警发送成功")
        except Exception as e:
            print(f"❌ 邮件报警发送异常: {e}")
    
    def _print_monitoring_status(self, signals):
        """
        打印监控状态
        
        Args:
            signals: 信号字典
        """
        final_signal = signals['final_signal']
        
        print("\n" + "="*60)
        print(f"📊 监控状态 - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"信号强度: {final_signal['strength']:.4f}")
        print(f"信号方向: {final_signal['direction']}")
        print(f"信号等级: {final_signal['level']}")
        print(f"置信度: {final_signal['confidence']:.2f}")
        print(f"风险等级: {final_signal['risk_level']}")
        print(f"建议操作: {final_signal['action']}")
        print(f"总报警数: {self.alert_stats['total_alerts']}")
        print("="*60)
    
    def stop_monitoring(self):
        """
        停止实时监控
        """
        if not self.monitoring['is_monitoring']:
            print("⚠️ 监控未在运行")
            return
        
        self.monitoring['is_monitoring'] = False
        
        if self.monitoring['monitoring_thread']:
            self.monitoring['monitoring_thread'].join(timeout=5)
        
        print("✅ 实时监控已停止")
    
    def get_monitoring_status(self):
        """
        获取监控状态
        
        Returns:
            status: 监控状态字典
        """
        status = {
            'is_monitoring': self.monitoring['is_monitoring'],
            'monitoring_enabled': self.monitoring['enabled'],
            'monitoring_interval': self.monitoring['interval'],
            'last_signal': self.monitoring['last_signal'],
            'signal_history_count': len(self.monitoring['signal_history']),
            'alerts_count': len(self.monitoring['alerts']),
            'alert_stats': self.alert_stats.copy()
        }
        
        return status
    
    def get_recent_alerts(self, n=10):
        """
        获取最近的报警
        
        Args:
            n: 获取最近n个报警
            
        Returns:
            alerts: 报警列表
        """
        alerts_list = list(self.monitoring['alerts'])
        return alerts_list[-n:]
    
    def clear_alerts(self):
        """
        清除所有报警
        """
        self.monitoring['alerts'].clear()
        self.alert_stats = {
            'total_alerts': 0,
            'alert_types': {
                'strong_signal': 0,
                'high_confidence': 0,
                'high_risk': 0,
                'signal_reversal': 0
            },
            'last_alert_time': None
        }
        print("✅ 报警已清除")
    
    def set_alert_threshold(self, threshold_name, value):
        """
        设置报警阈值
        
        Args:
            threshold_name: 阈值名称
            value: 阈值值
        """
        if threshold_name in self.alert_thresholds:
            self.alert_thresholds[threshold_name] = value
            print(f"✅ 报警阈值 {threshold_name} 已设置为 {value}")
        else:
            print(f"❌ 未知的阈值名称: {threshold_name}")
            print(f"可用的阈值: {list(self.alert_thresholds.keys())}")
    
    def get_alert_thresholds(self):
        """
        获取所有报警阈值
        
        Returns:
            thresholds: 阈值字典
        """
        return self.alert_thresholds.copy()
    
    def generate_monitoring_report(self):
        """
        生成监控报告
        
        Returns:
            report: 监控报告字典
        """
        report = {
            'timestamp': pd.Timestamp.now(),
            'status': self.get_monitoring_status(),
            'recent_alerts': self.get_recent_alerts(20),
            'alert_thresholds': self.get_alert_thresholds(),
            'signal_summary': self._summarize_signals()
        }
        
        return report
    
    def _summarize_signals(self):
        """
        总结信号历史
        
        Returns:
            summary: 信号总结
        """
        if len(self.monitoring['signal_history']) == 0:
            return {
                'total_signals': 0,
                'positive_signals': 0,
                'negative_signals': 0,
                'avg_strength': 0,
                'avg_confidence': 0
            }
        
        signals = [item['signal'] for item in self.monitoring['signal_history']]
        
        positive_count = sum(1 for s in signals if s['direction'] == 'positive')
        negative_count = sum(1 for s in signals if s['direction'] == 'negative')
        
        avg_strength = np.mean([abs(s['strength']) for s in signals])
        avg_confidence = np.mean([s['confidence'] for s in signals])
        
        return {
            'total_signals': len(signals),
            'positive_signals': positive_count,
            'negative_signals': negative_count,
            'avg_strength': avg_strength,
            'avg_confidence': avg_confidence
        }
    
    def validate_strategy(self, test_data: Dict, initial_capital: float = 1000000):
        """
        验证策略整体表现
        
        Args:
            test_data: 测试数据字典
            initial_capital: 初始资金
            
        Returns:
            validation_result: 验证结果
        """
        if self.validator is None:
            print("❌ 验证器未初始化，无法进行验证")
            return None
        
        if not self.is_trained:
            print("❌ 策略未训练，请先调用train方法")
            return None
        
        print("="*60)
        print("验证多频段信号融合策略")
        print("="*60)
        
        # 1. 运行回测
        print("\n【步骤1】运行回测")
        backtest_result = self.backtest(test_data, initial_capital)
        
        # 2. 收集预测和实际值
        print("\n【步骤2】收集预测和实际值")
        predictions = []
        actuals = []
        signals_strength = []
        
        stock_codes = list(test_data.keys())
        n_periods = len(list(test_data.values())[0]['price'])
        
        for period in range(20, n_periods, 20):
            for stock_code in stock_codes:
                data = test_data[stock_code]
                
                # 获取当前时期的数据
                tick_data = data['tick'].iloc[max(0, period-100):period]
                minute_data = data['minute'].iloc[max(0, period-60):period]
                financial_data = data['financial'].iloc[max(0, period-20):period]
                price_data = data['price'].iloc[max(0, period-20):period]
                
                # 生成信号
                signals = self.generate_signals(
                    tick_data, minute_data, financial_data, price_data
                )
                
                predictions.append(signals['final_signal']['expected_return'])
                signals_strength.append(signals['final_signal']['strength'])
                
                # 获取实际收益率
                if period < len(price_data):
                    actual_return = price_data['close'].pct_change().iloc[period]
                    actuals.append(actual_return)
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        signals_strength = np.array(signals_strength)
        
        # 3. 计算策略性能指标
        print("\n【步骤3】计算策略性能指标")
        strategy_metrics = self.validator.validate_strategy(signals_strength, actuals)
        
        # 4. 计算预测性能指标
        print("\n【步骤4】计算预测性能指标")
        mse = np.mean((predictions - actuals) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - actuals))
        r2 = 1 - np.sum((actuals - predictions) ** 2) / np.sum((actuals - np.mean(actuals)) ** 2)
        
        # 计算信息系数（IC）
        ic = np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0
        
        # 计算方向准确率
        direction_accuracy = np.mean(np.sign(predictions) == np.sign(actuals))
        
        prediction_metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'information_coefficient': ic,
            'direction_accuracy': direction_accuracy
        }
        
        print(f"  MSE: {mse:.6f}")
        print(f"  RMSE: {rmse:.6f}")
        print(f"  MAE: {mae:.6f}")
        print(f"  R²: {r2:.4f}")
        print(f"  信息系数: {ic:.4f}")
        print(f"  方向准确率: {direction_accuracy:.4f}")
        
        # 5. 分组测试（按信号强度分组）
        print("\n【步骤5】分组测试")
        if len(predictions) > 0:
            # 按信号强度分组
            strong_mask = np.abs(signals_strength) > 0.05
            moderate_mask = (np.abs(signals_strength) > 0.02) & (np.abs(signals_strength) <= 0.05)
            weak_mask = np.abs(signals_strength) <= 0.02
            
            group_results = {}
            
            for group_name, mask in [('strong', strong_mask), ('moderate', moderate_mask), ('weak', weak_mask)]:
                if np.sum(mask) > 0:
                    group_predictions = predictions[mask]
                    group_actuals = actuals[mask]
                    
                    group_ic = np.corrcoef(group_predictions, group_actuals)[0, 1] if len(group_predictions) > 1 else 0
                    group_direction_acc = np.mean(np.sign(group_predictions) == np.sign(group_actuals))
                    group_avg_return = np.mean(group_actuals)
                    
                    group_results[group_name] = {
                        'count': np.sum(mask),
                        'ic': group_ic,
                        'direction_accuracy': group_direction_acc,
                        'avg_return': group_avg_return
                    }
                    
                    print(f"  {group_name}组:")
                    print(f"    样本数: {np.sum(mask)}")
                    print(f"    IC: {group_ic:.4f}")
                    print(f"    方向准确率: {group_direction_acc:.4f}")
                    print(f"    平均收益率: {group_avg_return:.4f}")
        else:
            group_results = {}
        
        # 6. 保存验证结果
        self.validation_results = {
            'strategy': strategy_metrics,
            'prediction': prediction_metrics,
            'group_test': group_results,
            'backtest': backtest_result,
            'timestamp': pd.Timestamp.now()
        }
        
        print("\n" + "="*60)
        print("策略验证完成")
        print("="*60)
        
        return self.validation_results
    
    def validate_submodels(self, test_data: Dict):
        """
        验证子模型（高频模型、基本面模型、融合模型）
        
        Args:
            test_data: 测试数据字典
            
        Returns:
            submodel_results: 子模型验证结果
        """
        if self.validator is None:
            print("❌ 验证器未初始化，无法进行验证")
            return None
        
        if not self.is_trained:
            print("❌ 策略未训练，请先调用train方法")
            return None
        
        print("="*60)
        print("验证子模型")
        print("="*60)
        
        submodel_results = {}
        
        # 1. 验证高频模型
        print("\n【高频模型】")
        hf_predictions = []
        hf_actuals = []
        
        stock_codes = list(test_data.keys())
        for stock_code in stock_codes:
            data = test_data[stock_code]
            n_periods = len(data['price'])
            
            for period in range(20, n_periods, 20):
                tick_data = data['tick'].iloc[max(0, period-100):period]
                minute_data = data['minute'].iloc[max(0, period-60):period]
                
                hf_pred = self.hf_model.predict(tick_data, minute_data)
                hf_predictions.append(hf_pred['predicted_return'])
                
                if period < len(data['price']):
                    actual_return = data['price']['close'].pct_change().iloc[period]
                    hf_actuals.append(actual_return)
        
        if len(hf_predictions) > 0:
            hf_predictions = np.array(hf_predictions)
            hf_actuals = np.array(hf_actuals)
            
            hf_ic = np.corrcoef(hf_predictions, hf_actuals)[0, 1] if len(hf_predictions) > 1 else 0
            hf_direction_acc = np.mean(np.sign(hf_predictions) == np.sign(hf_actuals))
            hf_mse = np.mean((hf_predictions - hf_actuals) ** 2)
            
            submodel_results['high_frequency'] = {
                'ic': hf_ic,
                'direction_accuracy': hf_direction_acc,
                'mse': hf_mse,
                'sample_count': len(hf_predictions)
            }
            
            print(f"  IC: {hf_ic:.4f}")
            print(f"  方向准确率: {hf_direction_acc:.4f}")
            print(f"  MSE: {hf_mse:.6f}")
            print(f"  样本数: {len(hf_predictions)}")
        
        # 2. 验证基本面模型
        print("\n【基本面模型】")
        fd_predictions = []
        fd_actuals = []
        
        for stock_code in stock_codes:
            data = test_data[stock_code]
            n_periods = len(data['price'])
            
            for period in range(20, n_periods, 20):
                financial_data = data['financial'].iloc[max(0, period-20):period]
                price_data = data['price'].iloc[max(0, period-20):period]
                
                fd_pred = self.fd_model.predict(financial_data, price_data)
                fd_predictions.append(fd_pred['predicted_return'])
                
                if period < len(price_data):
                    actual_return = price_data['close'].pct_change().iloc[period]
                    fd_actuals.append(actual_return)
        
        if len(fd_predictions) > 0:
            fd_predictions = np.array(fd_predictions)
            fd_actuals = np.array(fd_actuals)
            
            fd_ic = np.corrcoef(fd_predictions, fd_actuals)[0, 1] if len(fd_predictions) > 1 else 0
            fd_direction_acc = np.mean(np.sign(fd_predictions) == np.sign(fd_actuals))
            fd_mse = np.mean((fd_predictions - fd_actuals) ** 2)
            
            submodel_results['fundamental'] = {
                'ic': fd_ic,
                'direction_accuracy': fd_direction_acc,
                'mse': fd_mse,
                'sample_count': len(fd_predictions)
            }
            
            print(f"  IC: {fd_ic:.4f}")
            print(f"  方向准确率: {fd_direction_acc:.4f}")
            print(f"  MSE: {fd_mse:.6f}")
            print(f"  样本数: {len(fd_predictions)}")
        
        # 3. 验证融合模型
        print("\n【融合模型】")
        fusion_predictions = []
        fusion_actuals = []
        
        for stock_code in stock_codes:
            data = test_data[stock_code]
            n_periods = len(data['price'])
            
            for period in range(20, n_periods, 20):
                tick_data = data['tick'].iloc[max(0, period-100):period]
                minute_data = data['minute'].iloc[max(0, period-60):period]
                financial_data = data['financial'].iloc[max(0, period-20):period]
                price_data = data['price'].iloc[max(0, period-20):period]
                
                hf_pred = self.hf_model.predict(tick_data, minute_data)
                fd_pred = self.fd_model.predict(financial_data, price_data)
                fusion_pred = self.fusion_model.predict(hf_pred, fd_pred)
                
                fusion_predictions.append(fusion_pred['predicted_return'])
                
                if period < len(price_data):
                    actual_return = price_data['close'].pct_change().iloc[period]
                    fusion_actuals.append(actual_return)
        
        if len(fusion_predictions) > 0:
            fusion_predictions = np.array(fusion_predictions)
            fusion_actuals = np.array(fusion_actuals)
            
            fusion_ic = np.corrcoef(fusion_predictions, fusion_actuals)[0, 1] if len(fusion_predictions) > 1 else 0
            fusion_direction_acc = np.mean(np.sign(fusion_predictions) == np.sign(fusion_actuals))
            fusion_mse = np.mean((fusion_predictions - fusion_actuals) ** 2)
            
            submodel_results['fusion'] = {
                'ic': fusion_ic,
                'direction_accuracy': fusion_direction_acc,
                'mse': fusion_mse,
                'sample_count': len(fusion_predictions)
            }
            
            print(f"  IC: {fusion_ic:.4f}")
            print(f"  方向准确率: {fusion_direction_acc:.4f}")
            print(f"  MSE: {fusion_mse:.6f}")
            print(f"  样本数: {len(fusion_predictions)}")
        
        # 4. 比较子模型
        print("\n【子模型比较】")
        if len(submodel_results) > 0:
            comparison_df = pd.DataFrame(submodel_results).T
            print(comparison_df)
            
            # 找出最佳模型
            best_ic_model = comparison_df['ic'].idxmax()
            best_direction_model = comparison_df['direction_accuracy'].idxmax()
            best_mse_model = comparison_df['mse'].idxmin()
            
            print(f"\n最佳IC模型: {best_ic_model}")
            print(f"最佳方向准确率模型: {best_direction_model}")
            print(f"最佳MSE模型: {best_mse_model}")
        
        # 5. 保存结果
        self.validation_results['submodels'] = submodel_results
        
        print("\n" + "="*60)
        print("子模型验证完成")
        print("="*60)
        
        return submodel_results
    
    def generate_validation_report(self):
        """
        生成验证报告
        
        Returns:
            report: 验证报告字典
        """
        if self.validation_results['timestamp'] is None:
            print("❌ 尚未进行验证，请先调用validate_strategy或validate_submodels")
            return None
        
        report = {
            'timestamp': pd.Timestamp.now(),
            'validation_timestamp': self.validation_results['timestamp'],
            'strategy_metrics': self.validation_results.get('strategy'),
            'prediction_metrics': self.validation_results.get('prediction'),
            'group_test': self.validation_results.get('group_test'),
            'submodels': self.validation_results.get('submodels'),
            'backtest_summary': None
        }
        
        # 回测摘要
        if self.validation_results.get('backtest'):
            backtest = self.validation_results['backtest']
            if 'metrics' in backtest:
                report['backtest_summary'] = backtest['metrics']
        
        # 生成文本报告
        text_report = self._generate_text_report(report)
        
        # 保存报告
        report_dir = './validation/'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = report_dir + f'multi_frequency_validation_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        print(f"✅ 验证报告已保存: {report_file}")
        
        return report
    
    def _generate_text_report(self, report: Dict) -> str:
        """
        生成文本格式的验证报告
        
        Args:
            report: 验证报告字典
            
        Returns:
            text_report: 文本报告
        """
        text_report = "="*80 + "\n"
        text_report += "多频段信号融合策略 - 验证报告\n"
        text_report += "="*80 + "\n\n"
        
        text_report += f"验证时间: {report['validation_timestamp']}\n"
        text_report += f"报告生成时间: {report['timestamp']}\n\n"
        
        # 策略性能
        if report['strategy_metrics']:
            text_report += "-"*80 + "\n"
            text_report += "策略性能指标\n"
            text_report += "-"*80 + "\n"
            for metric, value in report['strategy_metrics'].items():
                if isinstance(value, float):
                    text_report += f"{metric}: {value:.4f}\n"
                else:
                    text_report += f"{metric}: {value}\n"
            text_report += "\n"
        
        # 预测性能
        if report['prediction_metrics']:
            text_report += "-"*80 + "\n"
            text_report += "预测性能指标\n"
            text_report += "-"*80 + "\n"
            for metric, value in report['prediction_metrics'].items():
                if isinstance(value, float):
                    text_report += f"{metric}: {value:.4f}\n"
                else:
                    text_report += f"{metric}: {value}\n"
            text_report += "\n"
        
        # 分组测试
        if report['group_test']:
            text_report += "-"*80 + "\n"
            text_report += "分组测试结果\n"
            text_report += "-"*80 + "\n"
            for group_name, group_data in report['group_test'].items():
                text_report += f"\n{group_name}组:\n"
                for metric, value in group_data.items():
                    if isinstance(value, float):
                        text_report += f"  {metric}: {value:.4f}\n"
                    else:
                        text_report += f"  {metric}: {value}\n"
            text_report += "\n"
        
        # 子模型
        if report['submodels']:
            text_report += "-"*80 + "\n"
            text_report += "子模型验证结果\n"
            text_report += "-"*80 + "\n"
            for model_name, model_data in report['submodels'].items():
                text_report += f"\n{model_name}:\n"
                for metric, value in model_data.items():
                    if isinstance(value, float):
                        text_report += f"  {metric}: {value:.4f}\n"
                    else:
                        text_report += f"  {metric}: {value}\n"
            text_report += "\n"
        
        # 回测摘要
        if report['backtest_summary']:
            text_report += "-"*80 + "\n"
            text_report += "回测摘要\n"
            text_report += "-"*80 + "\n"
            for metric, value in report['backtest_summary'].items():
                if isinstance(value, float):
                    text_report += f"{metric}: {value:.4f}\n"
                else:
                    text_report += f"{metric}: {value}\n"
            text_report += "\n"
        
        text_report += "="*80 + "\n"
        text_report += "报告结束\n"
        text_report += "="*80 + "\n"
        
        return text_report
    
    def plot_validation_results(self):
        """
        绘制验证结果图表
        """
        if self.validator is None:
            print("❌ 验证器未初始化，无法绘制图表")
            return
        
        if self.validation_results['timestamp'] is None:
            print("❌ 尚未进行验证，请先调用validate_strategy或validate_submodels")
            return
        
        print("绘制验证结果图表...")
        
        # 创建图表目录
        plot_dir = './validation/plots/'
        os.makedirs(plot_dir, exist_ok=True)
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 绘制子模型比较图
        if self.validation_results.get('submodels'):
            self._plot_submodel_comparison(plot_dir, timestamp)
        
        # 2. 绘制分组测试结果图
        if self.validation_results.get('group_test'):
            self._plot_group_test_results(plot_dir, timestamp)
        
        # 3. 绘制策略性能图
        if self.validation_results.get('strategy'):
            self._plot_strategy_performance(plot_dir, timestamp)
        
        print(f"✅ 图表已保存到: {plot_dir}")
    
    def _plot_submodel_comparison(self, plot_dir: str, timestamp: str):
        """
        绘制子模型比较图
        
        Args:
            plot_dir: 图表保存目录
            timestamp: 时间戳
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        submodels = self.validation_results['submodels']
        
        # 准备数据
        model_names = list(submodels.keys())
        ic_values = [submodels[m]['ic'] for m in model_names]
        direction_acc_values = [submodels[m]['direction_accuracy'] for m in model_names]
        mse_values = [submodels[m]['mse'] for m in model_names]
        
        # 创建图表
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # IC对比
        axes[0].bar(model_names, ic_values, color=['skyblue', 'lightgreen', 'salmon'])
        axes[0].set_title('信息系数(IC)对比')
        axes[0].set_ylabel('IC')
        axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # 方向准确率对比
        axes[1].bar(model_names, direction_acc_values, color=['skyblue', 'lightgreen', 'salmon'])
        axes[1].set_title('方向准确率对比')
        axes[1].set_ylabel('方向准确率')
        axes[1].set_ylim([0, 1])
        
        # MSE对比
        axes[2].bar(model_names, mse_values, color=['skyblue', 'lightgreen', 'salmon'])
        axes[2].set_title('均方误差(MSE)对比')
        axes[2].set_ylabel('MSE')
        
        plt.tight_layout()
        plt.savefig(f'{plot_dir}submodel_comparison_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_group_test_results(self, plot_dir: str, timestamp: str):
        """
        绘制分组测试结果图
        
        Args:
            plot_dir: 图表保存目录
            timestamp: 时间戳
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        group_test = self.validation_results['group_test']
        
        # 准备数据
        group_names = list(group_test.keys())
        ic_values = [group_test[g]['ic'] for g in group_names]
        direction_acc_values = [group_test[g]['direction_accuracy'] for g in group_names]
        avg_return_values = [group_test[g]['avg_return'] for g in group_names]
        
        # 创建图表
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # IC对比
        axes[0].bar(group_names, ic_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[0].set_title('分组IC对比')
        axes[0].set_ylabel('IC')
        axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # 方向准确率对比
        axes[1].bar(group_names, direction_acc_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[1].set_title('分组方向准确率对比')
        axes[1].set_ylabel('方向准确率')
        axes[1].set_ylim([0, 1])
        
        # 平均收益率对比
        axes[2].bar(group_names, avg_return_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[2].set_title('分组平均收益率对比')
        axes[2].set_ylabel('平均收益率')
        axes[2].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(f'{plot_dir}group_test_results_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_strategy_performance(self, plot_dir: str, timestamp: str):
        """
        绘制策略性能图
        
        Args:
            plot_dir: 图表保存目录
            timestamp: 时间戳
        """
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            print("⚠️ 未安装matplotlib，无法绘制图表")
            return
        
        strategy_metrics = self.validation_results['strategy']
        
        # 准备数据
        metrics = ['年化收益率', '年化波动率', '夏普比率', '最大回撤', '胜率']
        values = [
            strategy_metrics.get('annualized_return', 0),
            strategy_metrics.get('volatility', 0),
            strategy_metrics.get('sharpe_ratio', 0),
            strategy_metrics.get('max_drawdown', 0),
            strategy_metrics.get('win_rate', 0)
        ]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(metrics, values, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B'])
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.4f}',
                   ha='center', va='bottom')
        
        ax.set_title('策略性能指标')
        ax.set_ylabel('值')
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{plot_dir}strategy_performance_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def get_validation_summary(self):
        """
        获取验证摘要
        
        Returns:
            summary: 验证摘要
        """
        if self.validation_results['timestamp'] is None:
            return {
                'status': 'not_validated',
                'message': '尚未进行验证'
            }
        
        summary = {
            'status': 'validated',
            'validation_time': self.validation_results['timestamp'],
            'strategy_ic': self.validation_results.get('prediction', {}).get('information_coefficient'),
            'strategy_direction_accuracy': self.validation_results.get('prediction', {}).get('direction_accuracy'),
            'strategy_sharpe': self.validation_results.get('strategy', {}).get('sharpe_ratio'),
            'best_submodel': None,
            'overall_assessment': None
        }
        
        # 找出最佳子模型
        if self.validation_results.get('submodels'):
            submodels = self.validation_results['submodels']
            best_model = max(submodels.items(), key=lambda x: x[1]['ic'])
            summary['best_submodel'] = best_model[0]
        
        # 整体评估
        if summary['strategy_ic'] is not None:
            if summary['strategy_ic'] > 0.05:
                summary['overall_assessment'] = 'excellent'
            elif summary['strategy_ic'] > 0.02:
                summary['overall_assessment'] = 'good'
            elif summary['strategy_ic'] > 0:
                summary['overall_assessment'] = 'acceptable'
            else:
                summary['overall_assessment'] = 'poor'
        
        return summary

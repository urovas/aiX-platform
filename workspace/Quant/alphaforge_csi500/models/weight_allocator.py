# 统一权重分配器 - 整合所有权重分配方法
# 整合：dynamic_weight_allocator + hybrid_weight_allocator + ppo_weight_allocator

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from typing import Dict, List, Tuple, Optional
from collections import deque
import warnings
warnings.filterwarnings('ignore')


class WeightAllocator:
    """
    统一权重分配器
    
    整合多种权重分配方法：
    - baseline: 基于规则的动态权重分配
    - ppo: 基于PPO强化学习的权重分配
    - hybrid: 混合模式（自动选择或强制指定）
    
    通过config配置启用/禁用特定方法
    """
    
    def __init__(self, config=None):
        """
        初始化权重分配器
        
        Args:
            config: 配置参数
                - weight_method: 权重分配方法 ('baseline', 'ppo', 'hybrid')
                - enable_ppo: 是否启用PPO
                - ppo_model_path: PPO模型路径
                - ... 其他配置参数
        """
        # 兼容Config对象和字典
        if config is not None and hasattr(config, '__dict__'):
            self.config = {k: v for k, v in config.__dict__.items() if not k.startswith('_')}
        else:
            self.config = config or {}
        
        # 权重分配方法
        self.weight_method = self.config.get('weight_method', 'baseline')
        
        # 初始化基线方法
        self.baseline = BaselineAllocator(self.config)
        
        # 初始化PPO方法
        self.enable_ppo = self.config.get('enable_ppo', False)
        self.ppo = PPOAllocator(self.config) if self.enable_ppo else None
        
        # 尝试加载PPO模型
        if self.enable_ppo and self.ppo:
            ppo_model_path = self.config.get('ppo_model_path', './models/saved/ppo_weight_allocator.pth')
            try:
                self.ppo.load_model(ppo_model_path)
                print("✅ PPO模型加载成功")
            except Exception as e:
                print(f"⚠️ PPO模型加载失败: {e}")
                print("   将使用基线方法")
                self.enable_ppo = False
        
        # 性能历史
        self.performance_history = {
            'baseline': [],
            'ppo': [],
        }
        
        # 权重历史
        self.weight_history = []
        
        print(f"权重分配器初始化完成")
        print(f"  方法: {self.weight_method}")
        print(f"  基线方法: 已启用")
        print(f"  PPO方法: {'已启用' if self.enable_ppo else '已禁用'}")
    
    def allocate_weights(self,
                        market_data: pd.DataFrame,
                        hf_prediction: Dict,
                        fd_prediction: Dict,
                        force_method: Optional[str] = None) -> Dict:
        """
        分配权重（统一入口）
        
        Args:
            market_data: 市场数据
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            force_method: 强制使用的方法 ('baseline', 'ppo', None=使用配置的方法）
            
        Returns:
            weights: 权重字典
                - high_frequency: 高频权重
                - fundamental: 基本面权重
                - method: 使用的方法
                - ... 其他信息
        """
        # 确定使用的方法
        method = force_method or self.weight_method
        
        # 根据方法选择分配策略
        if method == 'baseline':
            return self._allocate_baseline(market_data, hf_prediction, fd_prediction)
        
        elif method == 'ppo':
            if not self.enable_ppo or not self.ppo or not self.ppo.is_trained:
                print("⚠️ PPO未启用或未训练，使用基线方法")
                return self._allocate_baseline(market_data, hf_prediction, fd_prediction)
            return self._allocate_ppo(market_data, hf_prediction, fd_prediction)
        
        elif method == 'hybrid':
            # 混合模式：优先使用PPO（如果可用），否则使用基线
            if self.enable_ppo and self.ppo and self.ppo.is_trained:
                return self._allocate_ppo(market_data, hf_prediction, fd_prediction)
            else:
                return self._allocate_baseline(market_data, hf_prediction, fd_prediction)
        
        else:
            print(f"⚠️ 未知方法: {method}，使用基线方法")
            return self._allocate_baseline(market_data, hf_prediction, fd_prediction)
    
    def allocate_weights_fast(self, state: np.ndarray, method: Optional[str] = None) -> Dict:
        """
        快速分配权重（用于高频交易）
        
        Args:
            state: 状态向量（已提取）
            method: 使用的方法 ('baseline', 'ppo', None=自动选择）
            
        Returns:
            weights: 权重字典
        """
        method = method or self.weight_method
        
        if method == 'ppo' and self.enable_ppo and self.ppo and self.ppo.is_trained:
            return self.ppo.allocate_weights_fast(state)
        else:
            # 基线方法快速版本
            return self.baseline.allocate_weights_fast(state)
    
    def _allocate_baseline(self,
                          market_data: pd.DataFrame,
                          hf_prediction: Dict,
                          fd_prediction: Dict) -> Dict:
        """使用基线方法分配权重"""
        weights = self.baseline.allocate_weights(market_data, hf_prediction, fd_prediction)
        weights['method'] = 'baseline'
        self._save_weight_history(weights)
        return weights
    
    def _allocate_ppo(self,
                      market_data: pd.DataFrame,
                      hf_prediction: Dict,
                      fd_prediction: Dict) -> Dict:
        """使用PPO方法分配权重"""
        weights = self.ppo.allocate_weights(market_data, hf_prediction, fd_prediction)
        self._save_weight_history(weights)
        return weights
    
    def _save_weight_history(self, weights: Dict):
        """保存权重历史"""
        self.weight_history.append({
            'high_frequency': weights['high_frequency'],
            'fundamental': weights['fundamental'],
            'method': weights.get('method', 'unknown'),
            'timestamp': pd.Timestamp.now(),
        })
        
        # 限制历史长度
        if len(self.weight_history) > 100:
            self.weight_history.pop(0)
    
    def update_performance(self, actual_return: float, predicted_return: float, method: str = 'auto'):
        """更新性能历史"""
        if method == 'auto':
            method = self.weight_history[-1]['method'] if self.weight_history else 'baseline'
        
        self.performance_history[method].append({
            'actual_return': actual_return,
            'predicted_return': predicted_return,
            'error': abs(actual_return - predicted_return),
        })
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        report = {}
        
        for method in ['baseline', 'ppo']:
            if method in self.performance_history and self.performance_history[method]:
                errors = [p['error'] for p in self.performance_history[method]]
                report[method] = {
                    'count': len(errors),
                    'mean_error': np.mean(errors),
                    'std_error': np.std(errors),
                }
        
        return report


# ==================== 基线权重分配器 ====================

class BaselineAllocator:
    """基线权重分配器（基于规则）"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 基础权重
        self.base_weights = config.get('base_weights', {
            'high_frequency': 0.5,
            'fundamental': 0.5,
        })
        
        # 权重调整因子
        self.adjustment_factors = config.get('adjustment_factors', {
            'market_regime': 0.3,
            'signal_quality': 0.25,
            'volatility': 0.2,
            'liquidity': 0.15,
            'time_decay': 0.1,
        })
        
        # 市场制度配置
        self.market_regimes = config.get('market_regimes', {
            'bull': {'hf_weight': 0.6, 'fd_weight': 0.4},
            'bear': {'hf_weight': 0.4, 'fd_weight': 0.6},
            'sideways': {'hf_weight': 0.5, 'fd_weight': 0.5},
            'crisis': {'hf_weight': 0.7, 'fd_weight': 0.3},
        })
        
        # 平滑系数
        self.smoothing_factor = config.get('smoothing_factor', 0.7)
        
        # 权重历史
        self.weight_history = []
    
    def allocate_weights(self,
                        market_data: pd.DataFrame,
                        hf_prediction: Dict,
                        fd_prediction: Dict) -> Dict:
        """分配权重"""
        # 识别市场制度
        regime_info = self.identify_market_regime(market_data)
        
        # 评估信号质量
        quality = self.assess_signal_quality(hf_prediction, fd_prediction)
        
        # 评估波动率
        volatility_score = self.assess_volatility(market_data)
        
        # 评估流动性
        liquidity_score = self.assess_liquidity(market_data)
        
        # 计算权重
        weights = self.calculate_weights(
            regime_info, quality, volatility_score, liquidity_score
        )
        
        weights['regime'] = regime_info['regime']
        weights['regime_confidence'] = regime_info['confidence']
        weights['signal_quality'] = quality['overall']
        
        return weights
    
    def allocate_weights_fast(self, state: np.ndarray) -> Dict:
        """快速分配权重（简化版）"""
        # 从状态向量提取关键信息
        # 假设状态向量格式：[市场特征(10), 高频特征(5), 基本面特征(5)]
        
        hf_signal = state[10] if len(state) > 10 else 0  # 高频预测收益
        fd_signal = state[15] if len(state) > 15 else 0  # 基本面预测收益
        
        # 简单的权重分配逻辑
        if abs(hf_signal) > abs(fd_signal):
            hf_weight = 0.6
            fd_weight = 0.4
        else:
            hf_weight = 0.4
            fd_weight = 0.6
        
        return {
            'high_frequency': hf_weight,
            'fundamental': fd_weight,
            'method': 'baseline_fast',
        }
    
    def identify_market_regime(self, market_data: pd.DataFrame) -> Dict:
        """识别市场制度"""
        if market_data is None or market_data.empty:
            return {'regime': 'sideways', 'confidence': 0.5}
        
        close = market_data['close']
        returns = close.pct_change()
        
        # 计算趋势
        ma_short = close.rolling(20).mean().iloc[-1]
        ma_long = close.rolling(60).mean().iloc[-1]
        current_price = close.iloc[-1]
        
        # 计算波动率
        volatility = returns.rolling(20).std().iloc[-1]
        
        # 判断市场制度
        if current_price > ma_short > ma_long:
            regime = 'bull'
        elif current_price < ma_short < ma_long:
            regime = 'bear'
        elif volatility > returns.rolling(60).std().iloc[-1] * 1.5:
            regime = 'crisis'
        else:
            regime = 'sideways'
        
        return {
            'regime': regime,
            'confidence': 0.7,
        }
    
    def assess_signal_quality(self, hf_prediction: Dict, fd_prediction: Dict) -> Dict:
        """评估信号质量"""
        # 高频信号质量
        hf_confidence = hf_prediction.get('reaction_path', {}).get('confidence', 0.5)
        hf_quality = hf_confidence
        
        # 基本面信号质量
        fd_grade = fd_prediction.get('value_assessment', {}).get('grade', 'C')
        grade_scores = {'A+': 1.0, 'A': 0.9, 'B+': 0.8, 'B': 0.7, 'C+': 0.6, 'C': 0.5, 'D': 0.3}
        fd_quality = grade_scores.get(fd_grade, 0.5)
        
        return {
            'high_frequency': hf_quality,
            'fundamental': fd_quality,
            'overall': (hf_quality + fd_quality) / 2,
        }
    
    def assess_volatility(self, market_data: pd.DataFrame) -> float:
        """评估波动率"""
        if market_data is None or market_data.empty:
            return 0.5
        
        close = market_data['close']
        returns = close.pct_change()
        vol = returns.rolling(20).std().iloc[-1]
        
        # 归一化到0-1
        return min(vol * 10, 1.0)
    
    def assess_liquidity(self, market_data: pd.DataFrame) -> float:
        """评估流动性"""
        if market_data is None or 'volume' not in market_data.columns:
            return 0.5
        
        volume = market_data['volume']
        avg_volume = volume.rolling(20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        
        if avg_volume > 0:
            ratio = current_volume / avg_volume
            return min(ratio, 1.0)
        
        return 0.5
    
    def calculate_weights(self, regime_info: Dict, quality: Dict,
                         volatility_score: float, liquidity_score: float) -> Dict:
        """计算权重"""
        regime = regime_info['regime']
        regime_weights = self.market_regimes.get(regime, {'hf_weight': 0.5, 'fd_weight': 0.5})
        
        # 基础权重
        base_hf = regime_weights['hf_weight']
        base_fd = regime_weights['fd_weight']
        
        # 根据信号质量调整
        quality_adjustment = (quality['high_frequency'] - quality['fundamental']) * 0.1
        
        # 根据波动率调整
        vol_adjustment = (volatility_score - 0.5) * 0.1
        
        # 计算最终权重
        hf_weight = base_hf + quality_adjustment + vol_adjustment
        fd_weight = base_fd - quality_adjustment - vol_adjustment
        
        # 归一化
        total = hf_weight + fd_weight
        hf_weight = max(0.1, min(0.9, hf_weight / total))
        fd_weight = max(0.1, min(0.9, fd_weight / total))
        
        # 再次归一化确保总和为1
        total = hf_weight + fd_weight
        hf_weight /= total
        fd_weight /= total
        
        return {
            'high_frequency': hf_weight,
            'fundamental': fd_weight,
        }


# ==================== PPO权重分配器 ====================

class PPOAllocator:
    """PPO权重分配器（基于强化学习）"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # PPO超参数
        self.learning_rate = config.get('ppo_lr', 3e-4)
        self.gamma = config.get('ppo_gamma', 0.99)
        self.clip_epsilon = config.get('ppo_clip_epsilon', 0.2)
        
        # 状态空间维度
        self.state_dim = config.get('ppo_state_dim', 20)
        
        # 设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 初始化网络
        self.actor = ActorNetwork(self.state_dim, 1).to(self.device)
        self.critic = CriticNetwork(self.state_dim).to(self.device)
        
        # 训练状态
        self.is_trained = False
    
    def extract_state(self, market_data: pd.DataFrame,
                     hf_prediction: Dict,
                     fd_prediction: Dict) -> np.ndarray:
        """提取状态特征"""
        state = np.zeros(self.state_dim)
        idx = 0
        
        # 市场特征 (0-9)
        if market_data is not None and not market_data.empty:
            close = market_data['close']
            returns = close.pct_change()
            
            state[idx] = returns.iloc[-1] if len(returns) > 0 else 0
            idx += 1
            state[idx] = returns.rolling(5).mean().iloc[-1] if len(returns) >= 5 else 0
            idx += 1
            state[idx] = returns.rolling(20).std().iloc[-1] if len(returns) >= 20 else 0
            idx += 1
            
            if 'volume' in market_data.columns:
                volume = market_data['volume']
                state[idx] = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1] if len(volume) >= 20 else 1
                idx += 1
        
        # 高频信号特征 (10-14)
        state[idx] = hf_prediction.get('predicted_return', 0)
        idx += 1
        state[idx] = hf_prediction.get('temperature_score', 0.5)
        idx += 1
        state[idx] = hf_prediction.get('sentiment_score', 0.5)
        idx += 1
        state[idx] = hf_prediction.get('reaction_path', {}).get('confidence', 0.5)
        idx += 1
        state[idx] = hf_prediction.get('reaction_path', {}).get('reaction_speed', 0.5)
        idx += 1
        
        # 基本面信号特征 (15-19)
        state[idx] = fd_prediction.get('predicted_return', 0)
        idx += 1
        state[idx] = fd_prediction.get('value_score', 0.5)
        idx += 1
        state[idx] = 0.8 if fd_prediction.get('value_assessment', {}).get('grade', 'C') in ['A+', 'A', 'B+'] else 0.5
        idx += 1
        state[idx] = fd_prediction.get('value_assessment', {}).get('profitability_score', 0.5)
        idx += 1
        state[idx] = fd_prediction.get('value_assessment', {}).get('quality_score', 0.5)
        idx += 1
        
        return np.clip(state, -1, 1)
    
    def allocate_weights(self,
                        market_data: pd.DataFrame,
                        hf_prediction: Dict,
                        fd_prediction: Dict) -> Dict:
        """分配权重"""
        # 提取状态
        state = self.extract_state(market_data, hf_prediction, fd_prediction)
        
        # 选择动作
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs = self.actor(state_tensor)
            action = action_probs.argmax(dim=1).item()
        
        # 转换为权重
        hf_weight = action / 10.0
        fd_weight = 1.0 - hf_weight
        
        return {
            'high_frequency': hf_weight,
            'fundamental': fd_weight,
            'method': 'ppo',
            'is_trained': self.is_trained,
        }
    
    def allocate_weights_fast(self, state: np.ndarray) -> Dict:
        """快速分配权重"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs = self.actor.forward_fast(state_tensor)
            action = action_probs.argmax(dim=1).item()
        
        hf_weight = action / 10.0
        fd_weight = 1.0 - hf_weight
        
        return {
            'high_frequency': hf_weight,
            'fundamental': fd_weight,
            'method': 'ppo_fast',
            'is_trained': self.is_trained,
        }
    
    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            'actor_state_dict': self.actor.state_dict(),
            'critic_state_dict': self.critic.state_dict(),
        }, path)
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint['actor_state_dict'])
        self.critic.load_state_dict(checkpoint['critic_state_dict'])
        self.is_trained = True


# ==================== PPO网络架构 ====================

class ActorNetwork(nn.Module):
    """Actor网络 - 高频优化版"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 64):
        super().__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, 11)  # 11个离散动作
        
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = torch.softmax(self.fc3(x), dim=-1)
        return x
    
    def forward_fast(self, x):
        """快速前向传播"""
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.softmax(self.fc3(x), dim=-1)
        return x


class CriticNetwork(nn.Module):
    """Critic网络 - 高频优化版"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 64):
        super().__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, 1)
        
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
    def forward_fast(self, x):
        """快速前向传播"""
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

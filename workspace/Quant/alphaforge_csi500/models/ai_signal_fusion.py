# AI信号融合器（粘合剂）- 增强版 未来需要增加分离高低频模态、时序建模、多头注意力、自适应学习

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from collections import deque
import warnings
warnings.filterwarnings('ignore')

# 尝试导入深度学习框架
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 尝试导入LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class AISignalFusion:
    """
    AI信号融合器 - 增强版
    
    支持多种融合模型架构，引入时序上下文和在线学习机制
    """
    
    def __init__(self, config=None):
        """
        初始化AI信号融合器
        
        Args:
            config: 配置参数
        """
        # 兼容Config对象和字典
        if config is not None and hasattr(config, '__dict__'):
            self.config = {k: v for k, v in config.__dict__.items() if not k.startswith('_')}
        else:
            self.config = config or {}
        
        # 融合策略（支持多种架构）
        self.fusion_strategy = self.config.get('fusion_strategy', 'transformer')
        
        # 模型
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        
        # 信号权重（动态调整）
        self.signal_weights = {
            'high_frequency': 0.5,
            'fundamental': 0.5,
            'dynamic': True
        }
        
        # 信号历史缓冲区（用于时序建模）
        self.signal_history = {
            'hf': deque(maxlen=self.config.get('history_length', 20)),
            'fd': deque(maxlen=self.config.get('history_length', 20)),
            'fusion': deque(maxlen=self.config.get('history_length', 20))
        }
        
        # 性能历史（用于在线学习）
        self.performance_buffer = deque(maxlen=self.config.get('perf_buffer_size', 50))
        
        # 注意力权重历史
        self.attention_history = deque(maxlen=10)
        
        # 在线学习参数
        self.online_mode = self.config.get('online_mode', True)
        self.online_learning_rate = self.config.get('online_learning_rate', 0.01)
        self.update_frequency = self.config.get('update_frequency', 10)
        self.last_update_step = 0
        self.batch_size = self.config.get('batch_size', 32)
        
        # 模型版本控制
        self.model_version = 0
        self.update_count = 0
        
        # 性能监控
        self.performance_tracker = {
            'predictions': [],
            'actuals': [],
            'errors': [],
            'timestamps': []
        }
        
        # 导入验证器
        try:
            from validation.model_validator import ModelValidator
            self.validator = ModelValidator()
            self.validator_available = True
        except ImportError:
            self.validator = None
            self.validator_available = False
        
        # 融合特征（包含增强的交叉特征）
        self.fusion_features = [
            # 基础特征
            'hf_predicted_return',
            'hf_temperature_score',
            'hf_sentiment_score',
            'hf_reaction_speed',
            'hf_reaction_magnitude',
            'fd_predicted_return',
            'fd_value_score',
            'fd_profitability_score',
            'fd_growth_score',
            'fd_quality_score',
            'fd_valuation_score',
            # 基础交叉特征
            'hf_fd_alignment',
            'temperature_value_match',
            'sentiment_value_momentum',
            'reaction_timing_quality',
            'fundamental_grade_score',
            # 增强交叉特征
            'temperature_growth_match',
            'sentiment_valuation_match',
            'speed_quality_match',
            'divergence_level',
            'signal_strength_ratio',
            'temp_sentiment_interaction',
            'value_quality_interaction',
            'combined_confidence',
            'signal_stability',
        ]
        
        # 初始化模型
        self._init_model()
    
    def _init_model(self):
        """根据策略初始化模型"""
        if self.fusion_strategy == 'transformer' and TORCH_AVAILABLE:
            self.model = self._build_transformer_model()
        elif self.fusion_strategy == 'lstm' and TORCH_AVAILABLE:
            self.model = self._build_lstm_model()
        elif self.fusion_strategy == 'lightgbm' and LIGHTGBM_AVAILABLE:
            self.model = None
            self.lgb_params = {
                'objective': 'regression',
                'metric': 'mse',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.7,
                'bagging_freq': 5,
                'verbose': -1
            }
        else:
            # 默认使用MLP
            self.model = MLPRegressor(
                hidden_layer_sizes=[64, 32, 16],
                activation='relu',
                learning_rate_init=0.001,
                max_iter=500,
                batch_size=32,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2
            )
    
    def _build_transformer_model(self):
        """构建增强版Transformer融合模型"""
        if not TORCH_AVAILABLE:
            return None
        
        # 定义增强位置编码
        class EnhancedPositionalEncoding(nn.Module):
            """增强位置编码（包含相对位置信息）"""
            def __init__(self, d_model, max_len=5000):
                super().__init__()
                # 绝对位置编码
                pe = torch.zeros(max_len, d_model)
                position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
                div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
                pe[:, 0::2] = torch.sin(position * div_term[0::2])
                pe[:, 1::2] = torch.cos(position * div_term[1::2])
                self.register_buffer('pe', pe.unsqueeze(0))
                
                # 相对位置编码（用于学习局部依赖）
                self.relative_pe = nn.Parameter(torch.randn(max_len, max_len, d_model) * 0.02)
            
            def forward(self, x):
                batch_size, seq_len, d_model = x.shape
                # 添加绝对位置编码
                x = x + self.pe[:, :seq_len, :]
                return x
        
        # 定义模态编码
        class ModalityEncoding(nn.Module):
            """模态编码（区分高频和基本面信号）"""
            def __init__(self, d_model):
                super().__init__()
                # 高频模态嵌入
                self.hf_embedding = nn.Parameter(torch.randn(d_model) * 0.02)
                # 基本面模态嵌入
                self.fd_embedding = nn.Parameter(torch.randn(d_model) * 0.02)
            
            def forward(self, x, modality_mask):
                """
                Args:
                    x: 输入序列 [batch, seq_len, d_model]
                    modality_mask: 模态掩码 [batch, seq_len] (0=高频, 1=基本面）
                """
                batch_size, seq_len, d_model = x.shape
                
                # 扩展模态嵌入
                hf_emb = self.hf_embedding.unsqueeze(0).unsqueeze(0).expand(batch_size, seq_len, -1)
                fd_emb = self.fd_embedding.unsqueeze(0).unsqueeze(0).expand(batch_size, seq_len, -1)
                
                # 根据掩码选择模态嵌入
                modality_mask = modality_mask.unsqueeze(-1).float()
                modality_emb = modality_mask * fd_emb + (1 - modality_mask) * hf_emb
                
                return x + modality_emb
        
        # 定义交叉注意力模块
        class CrossAttention(nn.Module):
            """交叉注意力（学习高频和基本面之间的交互）"""
            def __init__(self, d_model, nhead=8):
                super().__init__()
                self.d_model = d_model
                self.nhead = nhead
                self.head_dim = d_model // nhead
                
                # 高频查询、键、值
                self.hf_q = nn.Linear(d_model, d_model)
                self.hf_k = nn.Linear(d_model, d_model)
                self.hf_v = nn.Linear(d_model, d_model)
                
                # 基本面查询、键、值
                self.fd_q = nn.Linear(d_model, d_model)
                self.fd_k = nn.Linear(d_model, d_model)
                self.fd_v = nn.Linear(d_model, d_model)
                
                # 输出投影
                self.out_proj = nn.Linear(d_model, d_model)
                
                # 门控机制
                self.gate = nn.Sequential(
                    nn.Linear(d_model * 2, d_model),
                    nn.Sigmoid()
                )
            
            def forward(self, hf_features, fd_features):
                """
                Args:
                    hf_features: 高频特征 [batch, seq_len, d_model]
                    fd_features: 基本面特征 [batch, seq_len, d_model]
                """
                # 高频查询基本面
                hf_q = self.hf_q(hf_features)
                fd_k = self.fd_k(fd_features)
                fd_v = self.fd_v(fd_features)
                
                # 计算注意力分数
                scores = torch.matmul(hf_q, fd_k.transpose(-2, -1)) / (self.head_dim ** 0.5)
                attn_weights = torch.softmax(scores, dim=-1)
                
                # 应用注意力
                hf_attended = torch.matmul(attn_weights, fd_v)
                
                # 基本面查询高频
                fd_q = self.fd_q(fd_features)
                hf_k = self.hf_k(hf_features)
                hf_v = self.hf_v(hf_features)
                
                scores = torch.matmul(fd_q, hf_k.transpose(-2, -1)) / (self.head_dim ** 0.5)
                attn_weights = torch.softmax(scores, dim=-1)
                
                fd_attended = torch.matmul(attn_weights, hf_v)
                
                # 门控融合
                gate = self.gate(torch.cat([hf_features, fd_features], dim=-1))
                hf_output = gate * hf_attended + (1 - gate) * hf_features
                fd_output = gate * fd_attended + (1 - gate) * fd_features
                
                # 输出投影
                output = self.out_proj(hf_output + fd_output)
                
                return output
        
        # 定义多尺度注意力（高频优化版）
        class MultiScaleAttention(nn.Module):
            """多尺度注意力（短期+长期）- 高频优化"""
            def __init__(self, d_model, nhead=8, short_window=5):
                super().__init__()
                self.d_model = d_model
                self.short_window = short_window  # 短期窗口大小
                
                # 短期注意力（局部，使用小窗口）
                self.short_attn = nn.MultiheadAttention(d_model, nhead, batch_first=True)
                
                # 长期注意力（全局）
                self.long_attn = nn.MultiheadAttention(d_model, nhead, batch_first=True)
                
                # 融合
                self.fusion = nn.Sequential(
                    nn.Linear(d_model * 2, d_model),
                    nn.ReLU(),
                    nn.Dropout(0.1)
                )
                
                # 高频优化：预分配缓冲区
                self._short_buffer = None
                self._long_buffer = None
            
            def forward(self, x):
                """
                Args:
                    x: 输入序列 [batch, seq_len, d_model]
                """
                batch_size, seq_len, _ = x.shape
                
                # 短期注意力（只使用最近short_window个时间步）
                if seq_len > self.short_window:
                    short_input = x[:, -self.short_window:, :]
                else:
                    short_input = x
                short_out, _ = self.short_attn(short_input, short_input, short_input)
                
                # 将短期输出填充回原始长度
                if seq_len > self.short_window:
                    short_out_full = torch.zeros_like(x)
                    short_out_full[:, -self.short_window:, :] = short_out
                    short_out = short_out_full
                
                # 长期注意力（使用全序列）
                long_out, _ = self.long_attn(x, x, x)
                
                # 融合
                output = self.fusion(torch.cat([short_out, long_out], dim=-1))
                
                return output
            
            def forward_fast(self, x):
                """快速前向传播（只计算最后一个时间步）"""
                batch_size, seq_len, _ = x.shape
                
                # 短期：只使用最后short_window个时间步
                if seq_len > self.short_window:
                    short_input = x[:, -self.short_window:, :]
                else:
                    short_input = x
                short_out, _ = self.short_attn(short_input, short_input, short_input)
                short_out = short_out[:, -1:, :]  # 只取最后一个
                
                # 长期：使用全序列，但只计算最后一个输出
                long_out, _ = self.long_attn(x, x, x)
                long_out = long_out[:, -1:, :]
                
                # 融合
                output = self.fusion(torch.cat([short_out, long_out], dim=-1))
                
                return output
        
        # 定义高频优化版Transformer模型
        class EnhancedTransformerFusionModel(nn.Module):
            def __init__(self, input_dim, d_model=128, nhead=8, num_layers=4):
                super().__init__()
                self.d_model = d_model
                
                # 输入投影
                self.input_proj = nn.Linear(input_dim, d_model)
                
                # 位置编码
                self.pos_encoder = EnhancedPositionalEncoding(d_model)
                
                # 模态编码
                self.modality_encoder = ModalityEncoding(d_model)
                
                # 交叉注意力（在编码器之前）
                self.cross_attn = CrossAttention(d_model, nhead)
                
                # 多尺度注意力
                self.multi_scale_attn = MultiScaleAttention(d_model, nhead)
                
                # Transformer编码器
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=d_model,
                    nhead=nhead,
                    dim_feedforward=512,
                    dropout=0.1,
                    batch_first=True
                )
                self.transformer = nn.TransformerEncoder(
                    encoder_layer,
                    num_layers=num_layers
                )
                
                # 输出投影
                self.output_proj = nn.Sequential(
                    nn.Linear(d_model, 64),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(64, 1)
                )
                
                # 特征重要性（可解释性）
                self.feature_importance = nn.Linear(d_model, 1)
                
                # 高频优化：预分配缓冲区，减少内存分配
                self._buffer = None
                self._cached_mask = None
            
            def forward(self, x, modality_mask=None):
                """
                Args:
                    x: 输入序列 [batch, seq_len, input_dim]
                    modality_mask: 模态掩码 [batch, seq_len] (可选）
                """
                # 输入投影
                x = self.input_proj(x)
                
                # 位置编码
                x = self.pos_encoder(x)
                
                # 模态编码（如果提供了模态掩码）
                if modality_mask is not None:
                    x = self.modality_encoder(x, modality_mask)
                
                # 多尺度注意力
                x = self.multi_scale_attn(x)
                
                # Transformer编码
                x = self.transformer(x)
                
                # 使用最后一个时间步
                x = x[:, -1, :]
                
                # 输出预测
                output = self.output_proj(x)
                
                return output
            
            def forward_fast(self, x_hf, x_fd):
                """
                高频快速前向传播（分离高频和基本面输入）- 使用快速多尺度注意力
                
                Args:
                    x_hf: 高频特征 [batch, seq_len, hf_dim]
                    x_fd: 基本面特征 [batch, seq_len, fd_dim]
                
                Returns:
                    output: 预测结果
                """
                batch_size = x_hf.size(0)
                seq_len = x_hf.size(1)
                
                # 分别投影
                hf_proj = self.input_proj(x_hf)
                fd_proj = self.input_proj(x_fd)
                
                # 添加位置编码
                hf_proj = self.pos_encoder(hf_proj)
                fd_proj = self.pos_encoder(fd_proj)
                
                # 交叉注意力（高频查询基本面）
                cross_out = self.cross_attn(hf_proj, fd_proj)
                
                # 多尺度注意力（使用快速版本，只计算最后一个时间步）
                x = self.multi_scale_attn.forward_fast(cross_out)
                
                # Transformer编码（只处理最后一个时间步）
                # 为了效率，我们只对最后一个时间步进行编码
                x_last = x[:, -1:, :]  # [batch, 1, d_model]
                x_encoded = self.transformer(x_last)
                x = x_encoded.squeeze(1)  # [batch, d_model]
                
                # 输出预测
                output = self.output_proj(x)
                
                return output
            
            def get_attention_weights(self, x):
                """获取注意力权重（用于可视化）"""
                x = self.input_proj(x)
                x = self.pos_encoder(x)
                x = self.multi_scale_attn(x)
                
                # 返回特征重要性
                importance = torch.softmax(self.feature_importance(x), dim=1)
                
                return importance
        
        return EnhancedTransformerFusionModel(
            input_dim=len(self.fusion_features),
            d_model=self.config.get('d_model', 128),
            nhead=self.config.get('nhead', 8),
            num_layers=self.config.get('num_layers', 4)
        )
    
    def _build_lstm_model(self):
        """构建LSTM融合模型"""
        if not TORCH_AVAILABLE:
            return None
        
        class LSTMFusionModel(nn.Module):
            def __init__(self, input_dim, hidden_size=128, num_layers=2):
                super().__init__()
                self.lstm = nn.LSTM(
                    input_dim,
                    hidden_size,
                    num_layers,
                    batch_first=True,
                    dropout=0.1
                )
                self.fc = nn.Sequential(
                    nn.Linear(hidden_size, 64),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(64, 1)
                )
            
            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                x = lstm_out[:, -1, :]
                return self.fc(x)
        
        return LSTMFusionModel(
            input_dim=len(self.fusion_features),
            hidden_size=self.config.get('hidden_size', 128),
            num_layers=self.config.get('num_layers', 2)
        )
    
    def update_history(self, hf_pred, fd_pred, fusion_result):
        """
        更新信号历史
        
        Args:
            hf_pred: 高频预测结果
            fd_pred: 基本面预测结果
            fusion_result: 融合结果
        """
        # 更新高频历史
        self.signal_history['hf'].append({
            'timestamp': pd.Timestamp.now(),
            'predicted_return': hf_pred.get('predicted_return', 0),
            'temperature': hf_pred.get('temperature_score', 0.5),
            'sentiment': hf_pred.get('sentiment_score', 0),
            'reaction_speed': hf_pred.get('reaction_path', {}).get('reaction_speed', 0.5),
            'reaction_magnitude': hf_pred.get('reaction_path', {}).get('reaction_magnitude', 0.5)
        })
        
        # 更新基本面历史
        self.signal_history['fd'].append({
            'timestamp': pd.Timestamp.now(),
            'predicted_return': fd_pred.get('predicted_return', 0),
            'value_score': fd_pred.get('value_score', 0.5),
            'grade': fd_pred.get('value_assessment', {}).get('grade', 'C'),
            'profitability': fd_pred.get('value_assessment', {}).get('profitability_score', 0.5),
            'quality': fd_pred.get('value_assessment', {}).get('quality_score', 0.5)
        })
        
        # 更新融合历史
        self.signal_history['fusion'].append(fusion_result)
    
    def prepare_sequence_features(self, hf_pred, fd_pred):
        """
        准备序列特征（包含历史信息）
        
        Args:
            hf_pred: 高频预测结果
            fd_pred: 基本面预测结果
            
        Returns:
            sequence_features: 序列特征
        """
        # 获取最近N个时间步的信号
        hf_history = list(self.signal_history['hf'])[-10:]
        fd_history = list(self.signal_history['fd'])[-10:]
        
        # 构建序列特征
        sequence = []
        
        # 对齐历史长度
        max_len = max(len(hf_history), len(fd_history))
        
        for i in range(max_len):
            hf_idx = -(i + 1) if i < len(hf_history) else -1
            fd_idx = -(i + 1) if i < len(fd_history) else -1
            
            step_features = []
            
            # 高频特征
            if hf_idx >= 0:
                hf = hf_history[hf_idx]
                step_features.extend([
                    hf['predicted_return'],
                    hf['temperature'],
                    hf['sentiment'],
                    hf['reaction_speed'],
                    hf['reaction_magnitude']
                ])
            else:
                step_features.extend([0, 0.5, 0, 0.5, 0.5])
            
            # 基本面特征
            if fd_idx >= 0:
                fd = fd_history[fd_idx]
                step_features.extend([
                    fd['predicted_return'],
                    fd['value_score'],
                    fd['profitability'],
                    fd['quality']
                ])
            else:
                step_features.extend([0, 0.5, 0.5, 0.5])
            
            sequence.append(step_features)
        
        # 添加当前时刻的特征
        current_features = self.prepare_fusion_features(hf_pred, fd_pred)
        current_values = [current_features.get(f, 0) for f in self.fusion_features]
        sequence.append(current_values)
        
        # 反转序列（最早的在前）
        sequence.reverse()
        
        return np.array(sequence)
    
    def _grade_to_score(self, grade):
        """
        将等级转换为分数
        
        Args:
            grade: 等级（如 'A+', 'B', 'C'）
            
        Returns:
            score: 分数
        """
        grade_score = {
            'A+': 1.0,
            'A': 0.9,
            'B+': 0.8,
            'B': 0.7,
            'C+': 0.6,
            'C': 0.5,
            'D': 0.3
        }
        return grade_score.get(grade, 0.5)
    
    def _compute_attention(self, sequence):
        """
        计算注意力权重
        
        Args:
            sequence: 序列特征
            
        Returns:
            attention_weights: 注意力权重
        """
        if len(sequence) == 0:
            return np.array([1.0])
        
        # 基于信号变化计算注意力权重
        # 最近的变化更重要
        n = len(sequence)
        weights = np.exp(np.linspace(-1, 0, n))
        weights = weights / weights.sum()
        
        return weights
    
    def _apply_attention(self, sequence, attention_weights):
        """
        应用注意力权重
        
        Args:
            sequence: 序列特征
            attention_weights: 注意力权重
            
        Returns:
            weighted_features: 加权后的特征
        """
        if len(sequence) == 0:
            return np.zeros(len(self.fusion_features))
        
        # 加权平均
        weighted_features = np.average(sequence, axis=0, weights=attention_weights)
        
        return weighted_features
    
    def predict_with_attention(self, hf_pred, fd_pred):
        """
        使用增强版注意力机制融合信号（考虑历史和模态）
        
        Args:
            hf_pred: 高频预测结果
            fd_pred: 基本面预测结果
            
        Returns:
            predicted_return: 预测收益率
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train方法")
        
        # 准备序列特征
        sequence = self.prepare_sequence_features(hf_pred, fd_pred)
        
        # 生成模态掩码
        seq_length = sequence.shape[0]
        feature_dim = sequence.shape[1]
        mask = np.zeros(feature_dim)
        mask[5:10] = 1  # 基本面特征
        seq_mask = np.tile(mask, seq_length)
        
        # 预测
        X = sequence.reshape(1, -1)
        X_scaled = self.scaler_X.transform(X)
        
        # 重塑为序列格式
        X_seq = X_scaled.reshape(-1, seq_length, feature_dim)
        X_tensor = torch.FloatTensor(X_seq)
        mask_tensor = torch.FloatTensor(seq_mask).unsqueeze(0)
        
        # 根据模型类型进行预测
        if self.fusion_strategy == 'transformer' and TORCH_AVAILABLE:
            self.model.eval()
            with torch.no_grad():
                # 使用增强版Transformer（支持模态掩码）
                y_pred_scaled = self.model(X_tensor, modality_mask=mask_tensor).numpy().flatten()
        elif self.fusion_strategy == 'lstm' and TORCH_AVAILABLE:
            self.model.eval()
            with torch.no_grad():
                y_pred_scaled = self.model(X_tensor).numpy().flatten()
        elif self.fusion_strategy == 'lightgbm' and LIGHTGBM_AVAILABLE:
            y_pred_scaled = self.model.predict(X_scaled)
        else:
            y_pred_scaled = self.model.predict(X_scaled)
        
        # 反标准化
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
        
        # 记录注意力
        self.attention_history.append({
            'timestamp': pd.Timestamp.now(),
            'weights': seq_mask.tolist()
        })
        
        return y_pred
    
    def predict_fast(self, hf_features, fd_features):
        """
        高频快速预测（分离高频和基本面特征输入）
        
        Args:
            hf_features: 高频特征数组 [seq_len, hf_feature_dim]
            fd_features: 基本面特征数组 [seq_len, fd_feature_dim]
            
        Returns:
            predicted_return: 预测收益率
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train方法")
        
        if self.fusion_strategy != 'transformer' or not TORCH_AVAILABLE:
            # 如果不是Transformer，使用普通预测
            return self.predict_with_attention(
                {'predicted_return': hf_features[-1, 0]},
                {'predicted_return': fd_features[-1, 0]}
            )
        
        # 转换为张量
        hf_tensor = torch.FloatTensor(hf_features).unsqueeze(0)  # [1, seq_len, hf_dim]
        fd_tensor = torch.FloatTensor(fd_features).unsqueeze(0)  # [1, seq_len, fd_dim]
        
        # 标准化
        # 注意：这里假设hf_features和fd_features已经标准化
        # 实际使用时需要保存标准化参数
        
        # 快速预测
        self.model.eval()
        with torch.no_grad():
            y_pred_scaled = self.model.forward_fast(hf_tensor, fd_tensor).numpy().flatten()
        
        # 反标准化
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
        
        return y_pred
    
    def calculate_cross_features(self, hf_prediction, fd_prediction):
        """
        计算交叉特征（增强版）
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            
        Returns:
            cross_features: 交叉特征字典
        """
        cross_features = {}
        
        # 1. 基础一致性（已有）
        hf_return = hf_prediction.get('predicted_return', 0)
        fd_return = fd_prediction.get('predicted_return', 0)
        
        direction_match = 1 if np.sign(hf_return) == np.sign(fd_return) else -1
        magnitude_ratio = abs(hf_return) / (abs(fd_return) + 1e-6)
        magnitude_ratio = np.clip(magnitude_ratio, 0, 2)
        
        cross_features['hf_fd_alignment'] = direction_match * magnitude_ratio
        
        # 2. 温度-价值匹配度（已有）
        temp_score = hf_prediction.get('temperature_score', 0.5)
        value_score = fd_prediction.get('value_score', 0.5)
        
        temp_value_match = temp_score * value_score
        cross_features['temperature_value_match'] = temp_value_match
        
        # 3. 情绪与价值动量（已有）
        sent_score = hf_prediction.get('sentiment_score', 0)
        sentiment_value_momentum = sent_score * value_score
        cross_features['sentiment_value_momentum'] = sentiment_value_momentum
        
        # 4. 反应时机质量（已有）
        reaction_path = hf_prediction.get('reaction_path', {})
        reaction_speed = reaction_path.get('reaction_speed', 0.5)
        reaction_magnitude = reaction_path.get('reaction_magnitude', 0.5)
        reaction_confidence = reaction_path.get('confidence', 0.5)
        
        timing_quality = reaction_speed * reaction_magnitude * reaction_confidence
        cross_features['reaction_timing_quality'] = timing_quality
        
        # 5. 基本面信号强度（已有）
        fd_assessment = fd_prediction.get('value_assessment', {})
        fd_grade = fd_assessment.get('grade', 'C')
        
        grade_score = {
            'A+': 1.0,
            'A': 0.9,
            'B+': 0.8,
            'B': 0.7,
            'C+': 0.6,
            'C': 0.5,
            'D': 0.3
        }
        
        cross_features['fundamental_grade_score'] = grade_score.get(fd_grade, 0.5)
        
        # 6. 新增：温度-成长匹配度
        growth_score = fd_assessment.get('growth_score', 0.5)
        cross_features['temperature_growth_match'] = temp_score * growth_score
        
        # 7. 新增：情绪-估值匹配度
        valuation_score = fd_assessment.get('valuation_score', 0.5)
        cross_features['sentiment_valuation_match'] = sent_score * valuation_score
        
        # 8. 新增：反应速度-质量匹配度
        quality_score = fd_assessment.get('quality_score', 0.5)
        cross_features['speed_quality_match'] = reaction_speed * quality_score
        
        # 9. 新增：分歧程度
        # 当信号冲突时，这个值很重要
        cross_features['divergence_level'] = abs(hf_return - fd_return) / (abs(hf_return + fd_return) + 1e-6)
        
        # 10. 新增：信号强度比
        cross_features['signal_strength_ratio'] = abs(hf_return) / (abs(fd_return) + 1e-6)
        
        # 11. 新增：温度-情绪交互
        cross_features['temp_sentiment_interaction'] = temp_score * sent_score
        
        # 12. 新增：价值-质量交互
        cross_features['value_quality_interaction'] = value_score * quality_score
        
        # 13. 新增：综合置信度
        cross_features['combined_confidence'] = (reaction_confidence + value_score) / 2
        
        # 14. 新增：信号稳定性（基于历史）
        cross_features['signal_stability'] = self._calculate_signal_stability()
        
        return cross_features
    
    def _calculate_signal_stability(self, window=10):
        """
        计算信号稳定性
        
        Args:
            window: 计算窗口大小
            
        Returns:
            stability: 稳定性分数（0-1）
        """
        if len(self.signal_history['fusion']) < window:
            return 0.5
        
        recent_signals = [s['predicted_return'] for s in list(self.signal_history['fusion'])[-window:]]
        
        if len(recent_signals) < 2:
            return 0.5
        
        # 稳定性 = 1 - 变异系数
        cv = np.std(recent_signals) / (abs(np.mean(recent_signals)) + 1e-6)
        stability = 1 / (1 + cv)
        
        return np.clip(stability, 0, 1)
    
    def prepare_fusion_features(self, hf_prediction, fd_prediction):
        """
        准备融合特征
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            
        Returns:
            features: 融合特征向量
        """
        features = {}
        
        # 高频特征
        features['hf_predicted_return'] = hf_prediction.get('predicted_return', 0)
        features['hf_temperature_score'] = hf_prediction.get('temperature_score', 0.5)
        features['hf_sentiment_score'] = hf_prediction.get('sentiment_score', 0)
        
        # 反应路径特征
        reaction_path = hf_prediction.get('reaction_path', {})
        features['hf_reaction_speed'] = reaction_path.get('reaction_speed', 0.5)
        features['hf_reaction_magnitude'] = reaction_path.get('reaction_magnitude', 0.5)
        
        # 基本面特征
        features['fd_predicted_return'] = fd_prediction.get('predicted_return', 0)
        features['fd_value_score'] = fd_prediction.get('value_score', 0.5)
        
        # 基本面评估特征
        fd_assessment = fd_prediction.get('value_assessment', {})
        features['fd_profitability_score'] = fd_assessment.get('profitability_score', 0.5)
        features['fd_growth_score'] = fd_assessment.get('growth_score', 0.5)
        features['fd_quality_score'] = fd_assessment.get('quality_score', 0.5)
        features['fd_valuation_score'] = fd_assessment.get('valuation_score', 0.5)
        
        # 计算交叉特征
        cross_features = self.calculate_cross_features(hf_prediction, fd_prediction)
        features.update(cross_features)
        
        return features
    
    def prepare_training_data(self, hf_predictions_list, fd_predictions_list, actual_returns):
        """
        准备训练数据（增强版，包含模态掩码）
        
        Args:
            hf_predictions_list: 高频预测结果列表
            fd_predictions_list: 基本面预测结果列表
            actual_returns: 实际收益率列表
            
        Returns:
            X: 特征矩阵
            y: 标签向量
            modality_masks: 模态掩码列表
        """
        X_list = []
        modality_masks = []
        
        for hf_pred, fd_pred in zip(hf_predictions_list, fd_predictions_list):
            features = self.prepare_fusion_features(hf_pred, fd_pred)
            
            # 处理NaN值
            feature_values = []
            for val in features.values():
                if pd.isna(val):
                    feature_values.append(0)
                else:
                    feature_values.append(val)
            
            X_list.append(feature_values)
            
            # 生成模态掩码（0=高频特征，1=基本面特征）
            # 高频特征索引: 0-4 (5个）
            # 基本面特征索引: 5-9 (5个）
            # 交叉特征: 10-23 (14个，默认为0）
            mask = np.zeros(len(feature_values))
            mask[5:10] = 1  # 基本面特征
            modality_masks.append(mask)
        
        X = np.array(X_list)
        y = np.array(actual_returns)
        modality_masks = np.array(modality_masks)
        
        return X, y, modality_masks
    
    def train(self, hf_predictions_list, fd_predictions_list, actual_returns, 
              use_sequence=False, online_learning=False):
        """
        训练AI信号融合器
        
        Args:
            hf_predictions_list: 高频预测结果列表
            fd_predictions_list: 基本面预测结果列表
            actual_returns: 实际收益率列表
            use_sequence: 是否使用序列特征（时序建模）
            online_learning: 是否使用在线学习
        """
        print("="*60)
        print("训练AI信号融合器（粘合剂）- 增强版")
        print("="*60)
        
        # 准备数据
        if use_sequence and len(self.signal_history['hf']) > 0:
            # 使用序列特征
            X_list = []
            modality_masks_list = []
            for hf_pred, fd_pred in zip(hf_predictions_list, fd_predictions_list):
                sequence = self.prepare_sequence_features(hf_pred, fd_pred)
                X_list.append(sequence.flatten())
                
                # 为序列生成模态掩码
                seq_length = sequence.shape[0]
                feature_dim = sequence.shape[1]
                # 假设每个时间步的特征结构相同
                mask = np.zeros(feature_dim)
                mask[5:10] = 1  # 基本面特征
                seq_mask = np.tile(mask, seq_length)
                modality_masks_list.append(seq_mask)
            
            X = np.array(X_list)
            modality_masks = np.array(modality_masks_list)
        else:
            # 使用普通特征
            X, y, modality_masks = self.prepare_training_data(hf_predictions_list, 
                                                             fd_predictions_list, 
                                                             actual_returns)
        
        if X is None or len(X) == 0:
            print("无法准备训练数据")
            return None
        
        print(f"训练数据量: {len(X)}")
        print(f"特征数量: {X.shape[1]}")
        print(f"融合策略: {self.fusion_strategy}")
        print(f"使用序列特征: {use_sequence}")
        print(f"在线学习: {online_learning}")
        
        # 标准化特征
        self.scaler_X = StandardScaler()
        X_scaled = self.scaler_X.fit_transform(X)
        
        # 标准化标签
        self.scaler_y = StandardScaler()
        y = np.array(actual_returns)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_scaled, 
            test_size=0.2, 
            random_state=42
        )
        
        # 划分模态掩码
        mask_train, mask_test = train_test_split(
            modality_masks, 
            test_size=0.2, 
            random_state=42
        )
        
        # 根据融合策略选择模型
        if self.fusion_strategy == 'transformer' and TORCH_AVAILABLE:
            self._train_transformer(X_train, y_train, X_test, y_test, mask_train, mask_test)
        elif self.fusion_strategy == 'lstm' and TORCH_AVAILABLE:
            self._train_lstm(X_train, y_train, X_test, y_test)
        elif self.fusion_strategy == 'lightgbm' and LIGHTGBM_AVAILABLE:
            self._train_lightgbm(X_train, y_train, X_test, y_test)
        else:
            # 使用传统模型
            self._train_traditional(X_train, y_train, X_test, y_test)
        
        # 更新模型版本
        self.model_version += 1
        
        print("="*60)
        
        return self.model
    
    def _train_traditional(self, X_train, y_train, X_test, y_test):
        """训练传统模型"""
        if self.fusion_strategy == 'neural_network':
            self.model = MLPRegressor(
                hidden_layer_sizes=[64, 32, 16],
                activation='relu',
                learning_rate_init=0.001,
                max_iter=500,
                batch_size=32,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2
            )
        elif self.fusion_strategy == 'gbdt':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        
        # 训练模型
        print(f"使用模型: {self.fusion_strategy}")
        self.model.fit(X_train, y_train)
        
        # 评估模型
        self._evaluate_model(X_train, y_train, X_test, y_test)
    
    def _train_lightgbm(self, X_train, y_train, X_test, y_test):
        """训练LightGBM模型"""
        print("使用模型: lightgbm")
        
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test)
        
        self.model = lgb.train(
            self.lgb_params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=100,
            early_stopping_rounds=10,
            verbose_eval=False
        )
        
        # 评估模型
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        y_train_original = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_train_original = self.scaler_y.inverse_transform(y_pred_train.reshape(-1, 1)).flatten()
        y_pred_test_original = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).flatten()
        
        train_mse = mean_squared_error(y_train_original, y_pred_train_original)
        test_mse = mean_squared_error(y_test_original, y_pred_test_original)
        train_r2 = r2_score(y_train_original, y_pred_train_original)
        test_r2 = r2_score(y_test_original, y_pred_test_original)
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
    
    def _train_transformer(self, X_train, y_train, X_test, y_test, mask_train=None, mask_test=None):
        """训练增强版Transformer模型"""
        print("使用模型: transformer (增强版）")
        
        # 重塑数据为序列格式
        seq_length = 11  # 10个历史 + 1个当前
        feature_dim = len(self.fusion_features)
        
        X_train_seq = X_train.reshape(-1, seq_length, feature_dim)
        X_test_seq = X_test.reshape(-1, seq_length, feature_dim)
        
        # 重塑模态掩码
        if mask_train is not None:
            mask_train_seq = mask_train.reshape(-1, seq_length, feature_dim)
            mask_test_seq = mask_test.reshape(-1, seq_length, feature_dim)
        else:
            mask_train_seq = None
            mask_test_seq = None
        
        # 转换为PyTorch张量
        X_train_tensor = torch.FloatTensor(X_train_seq)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1)
        X_test_tensor = torch.FloatTensor(X_test_seq)
        y_test_tensor = torch.FloatTensor(y_test).reshape(-1, 1)
        
        # 转换模态掩码为张量
        if mask_train_seq is not None:
            mask_train_tensor = torch.FloatTensor(mask_train_seq)
            mask_test_tensor = torch.FloatTensor(mask_test_seq)
        else:
            mask_train_tensor = None
            mask_test_tensor = None
        
        # 创建数据加载器
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        # 训练
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        num_epochs = 50
        for epoch in range(num_epochs):
            self.model.train()
            total_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                
                # 使用模态掩码（如果有）
                if mask_train_tensor is not None:
                    # 获取当前batch的掩码
                    batch_mask = mask_train_tensor[:batch_X.size(0)]
                    outputs = self.model(batch_X, modality_mask=batch_mask)
                else:
                    outputs = self.model(batch_X)
                
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(train_loader)
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.6f}")
        
        # 评估
        self.model.eval()
        with torch.no_grad():
            if mask_test_tensor is not None:
                y_pred_train = self.model(X_train_tensor, modality_mask=mask_train_tensor).numpy().flatten()
                y_pred_test = self.model(X_test_tensor, modality_mask=mask_test_tensor).numpy().flatten()
            else:
                y_pred_train = self.model(X_train_tensor).numpy().flatten()
                y_pred_test = self.model(X_test_tensor).numpy().flatten()
        
        y_train_original = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_train_original = self.scaler_y.inverse_transform(y_pred_train.reshape(-1, 1)).flatten()
        y_pred_test_original = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).flatten()
        
        train_mse = mean_squared_error(y_train_original, y_pred_train_original)
        test_mse = mean_squared_error(y_test_original, y_pred_test_original)
        train_r2 = r2_score(y_train_original, y_pred_train_original)
        test_r2 = r2_score(y_test_original, y_pred_test_original)
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
    
    def _train_lstm(self, X_train, y_train, X_test, y_test):
        """训练LSTM模型"""
        print("使用模型: lstm")
        
        # 重塑数据为序列格式
        seq_length = 11  # 10个历史 + 1个当前
        feature_dim = len(self.fusion_features)
        
        X_train_seq = X_train.reshape(-1, seq_length, feature_dim)
        X_test_seq = X_test.reshape(-1, seq_length, feature_dim)
        
        # 转换为PyTorch张量
        X_train_tensor = torch.FloatTensor(X_train_seq)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1)
        X_test_tensor = torch.FloatTensor(X_test_seq)
        y_test_tensor = torch.FloatTensor(y_test).reshape(-1, 1)
        
        # 创建数据加载器
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        # 训练
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        num_epochs = 50
        for epoch in range(num_epochs):
            self.model.train()
            total_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(train_loader)
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.6f}")
        
        # 评估
        self.model.eval()
        with torch.no_grad():
            y_pred_train = self.model(X_train_tensor).numpy().flatten()
            y_pred_test = self.model(X_test_tensor).numpy().flatten()
        
        y_train_original = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_train_original = self.scaler_y.inverse_transform(y_pred_train.reshape(-1, 1)).flatten()
        y_pred_test_original = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).flatten()
        
        train_mse = mean_squared_error(y_train_original, y_pred_train_original)
        test_mse = mean_squared_error(y_test_original, y_pred_test_original)
        train_r2 = r2_score(y_train_original, y_pred_train_original)
        test_r2 = r2_score(y_test_original, y_pred_test_original)
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
    
    def _evaluate_model(self, X_train, y_train, X_test, y_test):
        """评估模型"""
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # 反标准化
        y_pred_train_original = self.scaler_y.inverse_transform(y_pred_train.reshape(-1, 1)).flatten()
        y_pred_test_original = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).flatten()
        y_train_original = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        train_mse = mean_squared_error(y_train_original, y_pred_train_original)
        test_mse = mean_squared_error(y_test_original, y_pred_test_original)
        train_r2 = r2_score(y_train_original, y_pred_train_original)
        test_r2 = r2_score(y_test_original, y_pred_test_original)
        
        print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
        
        # 特征重要性（如果模型支持）
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_names = self.fusion_features + ['fundamental_grade_score']
            
            print("\n特征重要性:")
            for name, importance in sorted(zip(feature_names, importances), 
                                         key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {name}: {importance:.4f}")
    
    def predict(self, hf_prediction, fd_prediction, use_sequence=False):
        """
        融合预测（AI粘合剂的核心功能）
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            use_sequence: 是否使用序列特征
            
        Returns:
            fusion_prediction: 融合预测结果
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train方法")
        
        # 准备融合特征
        if use_sequence and len(self.signal_history['hf']) > 0:
            # 使用序列特征
            sequence = self.prepare_sequence_features(hf_prediction, fd_prediction)
            X = sequence.flatten().reshape(1, -1)
        else:
            # 使用普通特征
            features = self.prepare_fusion_features(hf_prediction, fd_prediction)
            
            # 转换为特征向量，处理NaN值
            feature_values = []
            for val in features.values():
                if pd.isna(val):
                    feature_values.append(0)
                else:
                    feature_values.append(val)
            
            X = np.array(feature_values).reshape(1, -1)
        
        # 标准化
        X_scaled = self.scaler_X.transform(X)
        
        # 预测
        if self.fusion_strategy in ['transformer', 'lstm'] and TORCH_AVAILABLE:
            # 深度学习模型
            seq_length = 11
            feature_dim = len(self.fusion_features)
            X_seq = X_scaled.reshape(-1, seq_length, feature_dim)
            X_tensor = torch.FloatTensor(X_seq)
            
            self.model.eval()
            with torch.no_grad():
                y_pred_scaled = self.model(X_tensor).numpy().flatten()
        elif self.fusion_strategy == 'lightgbm' and LIGHTGBM_AVAILABLE:
            # LightGBM模型
            y_pred_scaled = self.model.predict(X_scaled)
        else:
            # 传统模型
            y_pred_scaled = self.model.predict(X_scaled)
        
        # 反标准化
        if self.fusion_strategy in ['transformer', 'lstm']:
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
        else:
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
        
        # 计算融合信号
        fusion_signal = self.calculate_fusion_signal(hf_prediction, fd_prediction, y_pred)
        
        # 预测资金反应路径
        reaction_path = self.predict_reaction_path(hf_prediction, fd_prediction, fusion_signal)
        
        fusion_prediction = {
            'predicted_return': y_pred,
            'fusion_signal': fusion_signal,
            'reaction_path': reaction_path,
            'fusion_features': features,
            'high_frequency_prediction': hf_prediction,
            'fundamental_prediction': fd_prediction
        }
        
        # 更新历史
        self.update_history(hf_prediction, fd_prediction, fusion_prediction)
        
        return fusion_prediction
    
    def online_update(self, hf_pred, fd_pred, actual_return):
        """
        在线更新模型（实际收益发生后）
        
        Args:
            hf_pred: 高频预测结果
            fd_pred: 基本面预测结果
            actual_return: 实际收益率
        """
        if not self.online_mode:
            return
        
        # 记录性能
        fusion_result = self.predict(hf_pred, fd_pred)
        error = actual_return - fusion_result['predicted_return']
        
        self.performance_tracker['predictions'].append(fusion_result['predicted_return'])
        self.performance_tracker['actuals'].append(actual_return)
        self.performance_tracker['errors'].append(error)
        self.performance_tracker['timestamps'].append(pd.Timestamp.now())
        
        # 准备更新数据
        features = self.prepare_fusion_features(hf_pred, fd_pred)
        X = np.array(list(features.values())).reshape(1, -1)
        X_scaled = self.scaler_X.transform(X)
        
        # 根据不同模型类型进行在线更新
        if self.fusion_strategy == 'neural_network' and hasattr(self.model, 'partial_fit'):
            # MLP支持partial_fit
            y_scaled = self.scaler_y.transform([[actual_return]])
            self.model.partial_fit(X_scaled, y_scaled.ravel())
            
        elif self.fusion_strategy == 'lightgbm':
            # LightGBM在线更新需要特殊处理
            self._update_lightgbm(X_scaled, actual_return)
            
        elif self.fusion_strategy == 'transformer' or self.fusion_strategy == 'lstm':
            # PyTorch模型的在线更新
            self._update_pytorch_model(X_scaled, actual_return)
        
        # 更新计数器
        self.update_count += 1
        
        # 定期评估性能
        if self.update_count % 100 == 0:
            self._evaluate_performance()
    
    def _update_lightgbm(self, X, y):
        """
        更新LightGBM模型
        
        Args:
            X: 特征
            y: 标签
        """
        if not LIGHTGBM_AVAILABLE:
            return
        
        # LightGBM支持增量学习
        y_scaled = self.scaler_y.transform([[y]])
        train_data = lgb.Dataset(X, label=y_scaled.ravel())
        
        # 使用init_model参数进行增量训练
        self.model = lgb.train(
            self.lgb_params,
            train_data,
            num_boost_round=10,
            init_model=self.model,
            verbose_eval=False
        )
    
    def _update_pytorch_model(self, X, y):
        """
        更新PyTorch模型
        
        Args:
            X: 特征
            y: 标签
        """
        if not TORCH_AVAILABLE:
            return
        
        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=self.online_learning_rate)
        
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor([y])
        
        optimizer.zero_grad()
        y_pred = self.model(X_tensor.unsqueeze(0))  # 添加batch维度
        loss = nn.MSELoss()(y_pred, y_tensor)
        loss.backward()
        optimizer.step()
    
    def _evaluate_performance(self):
        """
        评估近期性能
        """
        recent_errors = self.performance_tracker['errors'][-100:]
        
        if len(recent_errors) < 10:
            return
        
        mae = np.mean(np.abs(recent_errors))
        rmse = np.sqrt(np.mean(np.array(recent_errors) ** 2))
        
        # 计算方向准确率
        recent_preds = self.performance_tracker['predictions'][-100:]
        recent_actuals = self.performance_tracker['actuals'][-100:]
        
        direction_accuracy = np.mean(
            [1 if p * a > 0 else 0 for p, a in zip(recent_preds, recent_actuals)]
        )
        
        print(f"\n📊 在线学习性能报告（最近{len(recent_errors)}个样本）")
        print(f"  MAE: {mae:.6f}")
        print(f"  RMSE: {rmse:.6f}")
        print(f"  方向准确率: {direction_accuracy:.2%}")
        
        # 如果性能下降，调整学习率
        if direction_accuracy < 0.5:
            self.online_learning_rate *= 0.9
            print(f"  ⚠️ 方向准确率低于50%，降低学习率至 {self.online_learning_rate:.4f}")
    
    def calculate_fusion_signal(self, hf_prediction, fd_prediction, fusion_return):
        """
        计算融合信号
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            fusion_return: 融合预测收益率
            
        Returns:
            signal: 融合信号
        """
        # 获取交叉特征
        cross_features = self.calculate_cross_features(hf_prediction, fd_prediction)
        
        # 信号强度
        signal_strength = fusion_return
        
        # 信号方向
        signal_direction = 'positive' if signal_strength > 0 else 'negative'
        
        # 信号置信度
        hf_confidence = hf_prediction.get('reaction_path', {}).get('confidence', 0.5)
        fd_confidence = fd_prediction.get('value_score', 0.5)
        alignment = abs(cross_features.get('hf_fd_alignment', 0))
        
        signal_confidence = (hf_confidence * 0.4 + fd_confidence * 0.4 + alignment * 0.2)
        
        # 信号类型
        alignment_score = cross_features.get('hf_fd_alignment', 0)
        temp_value_match = cross_features.get('temperature_value_match', 0)
        
        if alignment_score > 0.5 and temp_value_match > 0.5:
            signal_type = 'strong_convergence'
        elif alignment_score > 0:
            signal_type = 'convergence'
        elif alignment_score < -0.5:
            signal_type = 'divergence'
        else:
            signal_type = 'neutral'
        
        # 信号时间框架
        reaction_speed = hf_prediction.get('reaction_path', {}).get('reaction_speed', 0.5)
        if reaction_speed > 0.7:
            time_frame = 'short_term'
        elif reaction_speed > 0.4:
            time_frame = 'medium_term'
        else:
            time_frame = 'long_term'
        
        signal = {
            'strength': signal_strength,
            'direction': signal_direction,
            'confidence': signal_confidence,
            'type': signal_type,
            'time_frame': time_frame,
            'alignment_score': alignment_score,
            'temperature_value_match': temp_value_match
        }
        
        return signal
    
    def predict_reaction_path(self, hf_prediction, fd_prediction, fusion_signal):
        """
        预测资金反应路径（AI粘合剂的核心价值）
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            fusion_signal: 融合信号
            
        Returns:
            reaction_path: 反应路径
        """
        # 获取基本面信号
        fd_return = fd_prediction.get('predicted_return', 0)
        fd_grade = fd_prediction.get('value_assessment', {}).get('grade', 'C')
        
        # 获取高频信号
        hf_temp = hf_prediction.get('temperature_score', 0.5)
        hf_sent = hf_prediction.get('sentiment_score', 0)
        
        # 获取融合信号
        fusion_strength = fusion_signal.get('strength', 0)
        fusion_type = fusion_signal.get('type', 'neutral')
        
        # 计算反应路径
        reaction_path = {}
        
        # 1. 反应阶段
        if fusion_type == 'strong_convergence':
            reaction_path['phase'] = 'immediate'
        elif fusion_type == 'convergence':
            reaction_path['phase'] = 'gradual'
        elif fusion_type == 'divergence':
            reaction_path['phase'] = 'delayed'
        else:
            reaction_path['phase'] = 'uncertain'
        
        # 2. 反应速度（基于市场温度）
        if hf_temp > 0.7:
            reaction_path['speed'] = 'fast'
            reaction_path['speed_value'] = 0.8
            reaction_path['time_to_peak'] = '1-3天'
        elif hf_temp > 0.4:
            reaction_path['speed'] = 'moderate'
            reaction_path['speed_value'] = 0.5
            reaction_path['time_to_peak'] = '3-7天'
        else:
            reaction_path['speed'] = 'slow'
            reaction_path['speed_value'] = 0.3
            reaction_path['time_to_peak'] = '7-14天'
        
        # 3. 反应幅度（基于基本面强度和市场情绪）
        fd_strength = abs(fd_return)
        sentiment_magnitude = abs(hf_sent)
        
        expected_magnitude = fd_strength * (1 + sentiment_magnitude)
        reaction_path['magnitude'] = expected_magnitude
        reaction_path['magnitude_level'] = 'high' if expected_magnitude > 0.05 else 'medium' if expected_magnitude > 0.02 else 'low'
        
        # 4. 反应持续性（基于基本面质量）
        grade_multiplier = {
            'A+': 1.5,
            'A': 1.3,
            'B+': 1.1,
            'B': 1.0,
            'C+': 0.9,
            'C': 0.8,
            'D': 0.6
        }
        
        persistence = grade_multiplier.get(fd_grade, 1.0)
        reaction_path['persistence'] = persistence
        reaction_path['persistence_level'] = 'long' if persistence > 1.2 else 'medium' if persistence > 0.9 else 'short'
        
        # 5. 反应路径形状
        if fusion_type == 'strong_convergence' and hf_temp > 0.7:
            reaction_path['shape'] = 'spike'
        elif fusion_type == 'convergence':
            reaction_path['shape'] = 'smooth'
        elif fusion_type == 'divergence':
            reaction_path['shape'] = 'oscillating'
        else:
            reaction_path['shape'] = 'flat'
        
        # 6. 风险评估
        risk_factors = []
        if fusion_type == 'divergence':
            risk_factors.append('signal_divergence')
        if hf_temp > 0.8:
            risk_factors.append('high_temperature')
        if hf_sent < -0.5:
            risk_factors.append('negative_sentiment')
        if fd_grade in ['C', 'D']:
            risk_factors.append('low_fundamental_quality')
        
        reaction_path['risk_factors'] = risk_factors
        reaction_path['risk_level'] = 'high' if len(risk_factors) >= 2 else 'medium' if len(risk_factors) == 1 else 'low'
        
        # 7. 交易建议
        if fusion_signal['confidence'] > 0.7 and fusion_type == 'strong_convergence':
            reaction_path['action'] = 'strong_buy' if fusion_signal['direction'] == 'positive' else 'strong_sell'
        elif fusion_signal['confidence'] > 0.5:
            reaction_path['action'] = 'buy' if fusion_signal['direction'] == 'positive' else 'sell'
        elif fusion_signal['confidence'] > 0.3:
            reaction_path['action'] = 'hold'
        else:
            reaction_path['action'] = 'no_action'
        
        return reaction_path
    
    def predict_reaction_path_quantitative(self, hf_prediction, fd_prediction, fusion_signal):
        """
        量化预测反应路径（返回数值而非文本）
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            fusion_signal: 融合信号
            
        Returns:
            quantitative_path: 量化反应路径
        """
        # 基础参数
        fd_return = abs(fd_prediction.get('predicted_return', 0))
        temp_score = hf_prediction.get('temperature_score', 0.5)
        sent_score = abs(hf_prediction.get('sentiment_score', 0))
        grade_score = self._grade_to_score(
            fd_prediction.get('value_assessment', {}).get('grade', 'C')
        )
        
        # 1. 预测峰值时间（交易日）
        # 温度高 → 反应快 → 峰值时间短
        base_time = 5  # 基础5天
        temp_factor = 1 - temp_score * 0.5  # 温度高时因子变小
        sent_factor = 1 - sent_score * 0.3  # 情绪强时因子变小
        
        peak_time = base_time * temp_factor * sent_factor
        peak_time = np.clip(peak_time, 1, 20)  # 限制在1-20天
        
        # 2. 预测峰值幅度
        # 基本面强度 * 情绪放大 * 质量持续
        magnitude = fd_return * (1 + sent_score) * grade_score
        magnitude = np.clip(magnitude, 0, 0.2)  # 最大20%
        
        # 3. 预测反应曲线形状参数
        # 使用logistic函数参数化
        shape_params = {
            'growth_rate': temp_score * 2,  # 增长速率
            'midpoint': peak_time,  # 中点
            'asymmetry': sent_score  # 不对称性
        }
        
        # 4. 预测各个时间点的累积反应
        time_points = [1, 3, 5, 10, 20, 30]  # 交易日
        cumulative_reactions = {}
        
        for t in time_points:
            if t <= peak_time:
                # 上升阶段
                progress = t / peak_time
                cumulative = magnitude * (1 - np.exp(-progress * 3))
            else:
                # 衰减阶段
                decay = np.exp(-(t - peak_time) / (peak_time * grade_score))
                cumulative = magnitude * decay
            
            cumulative_reactions[f'day_{t}'] = cumulative
        
        return {
            'peak_time': peak_time,
            'peak_magnitude': magnitude,
            'cumulative_reactions': cumulative_reactions,
            'total_expected_return': magnitude * grade_score,
            'half_life': peak_time * 0.7,  # 半衰期
            'reaction_efficiency': magnitude / peak_time,  # 效率：单位时间的回报
            'shape_params': shape_params
        }
    
    def dynamic_weight_adjustment(self, hf_prediction, fd_prediction):
        """
        动态权重调整
        
        Args:
            hf_prediction: 高频预测结果
            fd_prediction: 基本面预测结果
            
        Returns:
            weights: 调整后的权重
        """
        if not self.signal_weights['dynamic']:
            return self.signal_weights
        
        # 获取市场温度
        temp_score = hf_prediction.get('temperature_score', 0.5)
        
        # 获取基本面质量
        value_score = fd_prediction.get('value_score', 0.5)
        
        # 动态调整逻辑
        if temp_score > 0.7:
            hf_weight = 0.7
            fd_weight = 0.3
        elif temp_score > 0.4:
            hf_weight = 0.5
            fd_weight = 0.5
        else:
            hf_weight = 0.3
            fd_weight = 0.7
        
        # 根据基本面质量微调
        if value_score > 0.7:
            fd_weight = min(fd_weight + 0.1, 0.8)
            hf_weight = max(hf_weight - 0.1, 0.2)
        elif value_score < 0.3:
            fd_weight = max(fd_weight - 0.1, 0.2)
            hf_weight = min(hf_weight + 0.1, 0.8)
        
        weights = {
            'high_frequency': hf_weight,
            'fundamental': fd_weight,
            'dynamic': True
        }
        
        return weights
    
    def get_fusion_report(self, fusion_prediction):
        """
        生成融合报告
        
        Args:
            fusion_prediction: 融合预测结果
            
        Returns:
            report: 融合报告
        """
        fusion_signal = fusion_prediction['fusion_signal']
        reaction_path = fusion_prediction['reaction_path']
        
        report = {
            'summary': {
                'predicted_return': fusion_prediction['predicted_return'],
                'signal_direction': fusion_signal['direction'],
                'signal_strength': fusion_signal['strength'],
                'confidence': fusion_signal['confidence'],
                'signal_type': fusion_signal['type'],
            },
            'reaction_path': {
                'phase': reaction_path['phase'],
                'speed': reaction_path['speed'],
                'time_to_peak': reaction_path['time_to_peak'],
                'magnitude': reaction_path['magnitude'],
                'magnitude_level': reaction_path['magnitude_level'],
                'persistence': reaction_path['persistence'],
                'persistence_level': reaction_path['persistence_level'],
                'shape': reaction_path['shape'],
                'action': reaction_path['action'],
            },
            'risk_assessment': {
                'risk_level': reaction_path['risk_level'],
                'risk_factors': reaction_path['risk_factors'],
            },
            'signal_analysis': {
                'high_frequency_contribution': fusion_signal['strength'] * self.signal_weights['high_frequency'],
                'fundamental_contribution': fusion_signal['strength'] * self.signal_weights['fundamental'],
                'alignment_score': fusion_signal['alignment_score'],
                'temperature_value_match': fusion_signal['temperature_value_match'],
            }
        }
        
        return report
    
    def get_model_info(self):
        """
        获取模型信息
        
        Returns:
            info: 模型信息
        """
        return {
            'fusion_strategy': self.fusion_strategy,
            'model_version': self.model_version,
            'update_count': self.update_count,
            'history_length': len(self.signal_history['hf']),
            'performance_buffer_size': len(self.performance_buffer),
            'torch_available': TORCH_AVAILABLE,
            'lightgbm_available': LIGHTGBM_AVAILABLE,
            'validator_available': self.validator_available
        }
    
    def validate_model(self, test_data):
        """
        验证模型性能
        
        Args:
            test_data: 测试数据列表，格式为 [(hf_pred, fd_pred, actual_return), ...]
            
        Returns:
            validation_result: 验证结果
        """
        if not self.validator_available or self.validator is None:
            print("验证器不可用，跳过验证")
            return None
        
        print("\n" + "=" * 60)
        print("验证AI信号融合器性能")
        print("=" * 60)
        
        results = {}
        
        # 分组测试
        predictions = []
        actuals = []
        
        for hf_pred, fd_pred, actual in test_data:
            fusion = self.predict(hf_pred, fd_pred)
            predictions.append(fusion['predicted_return'])
            actuals.append(actual)
        
        # 使用验证器
        group_result = self.validator.group_test(
            np.array(predictions),
            np.array(actuals),
            model_name="AI信号融合器"
        )
        
        results['group_test'] = group_result
        
        # 计算额外指标
        predictions_array = np.array(predictions)
        actuals_array = np.array(actuals)
        
        # 方向准确率
        direction_accuracy = np.mean(
            [1 if p * a > 0 else 0 for p, a in zip(predictions, actuals)]
        )
        
        # IC（信息系数）
        ic = np.corrcoef(predictions_array, actuals_array)[0, 1]
        
        # 年化收益率（假设每个预测对应一个周期）
        annual_return = np.mean(predictions_array) * 252
        
        results['metrics'] = {
            'direction_accuracy': direction_accuracy,
            'ic': ic,
            'annual_return': annual_return,
            'num_samples': len(predictions)
        }
        
        print(f"\n验证结果:")
        print(f"  方向准确率: {direction_accuracy:.2%}")
        print(f"  IC: {ic:.4f}")
        print(f"  年化收益率: {annual_return:.2%}")
        print(f"  样本数: {len(predictions)}")
        
        # 可视化
        try:
            self.validator.plot_results([group_result], 'group_returns')
            print("\n可视化结果已保存")
        except Exception as e:
            print(f"\n可视化失败: {e}")
        
        print("=" * 60)
        
        return results


# 测试代码
if __name__ == "__main__":
    print("\nAI信号融合器测试（增强版）")
    print("=" * 60)
    
    # 创建配置
    config = {
        'fusion_strategy': 'neural_network',
        'history_length': 20,
        'perf_buffer_size': 50,
        'online_learning_rate': 0.01,
        'update_frequency': 10
    }
    
    # 初始化融合器
    fusion = AISignalFusion(config)
    
    # 模拟数据
    np.random.seed(42)
    n_samples = 100
    
    hf_predictions = []
    fd_predictions = []
    actual_returns = []
    
    for i in range(n_samples):
        hf_pred = {
            'predicted_return': np.random.randn() * 0.02,
            'temperature_score': np.random.uniform(0.3, 0.8),
            'sentiment_score': np.random.uniform(-0.5, 0.5),
            'reaction_path': {
                'confidence': np.random.uniform(0.4, 0.9),
                'reaction_speed': np.random.uniform(0.3, 0.8),
                'reaction_magnitude': np.random.uniform(0.3, 0.8)
            }
        }
        
        fd_pred = {
            'predicted_return': np.random.randn() * 0.015,
            'value_score': np.random.uniform(0.3, 0.8),
            'value_assessment': {
                'grade': np.random.choice(['A+', 'A', 'B+', 'B', 'C', 'D']),
                'profitability_score': np.random.uniform(0.3, 0.9),
                'growth_score': np.random.uniform(0.3, 0.9),
                'quality_score': np.random.uniform(0.3, 0.9),
                'valuation_score': np.random.uniform(0.3, 0.9)
            }
        }
        
        actual_return = (hf_pred['predicted_return'] + fd_pred['predicted_return']) / 2 + np.random.randn() * 0.01
        
        hf_predictions.append(hf_pred)
        fd_predictions.append(fd_pred)
        actual_returns.append(actual_return)
    
    # 训练模型
    fusion.train(hf_predictions, fd_predictions, actual_returns, use_sequence=False)
    
    # 测试预测
    test_hf_pred = hf_predictions[0]
    test_fd_pred = fd_predictions[0]
    
    fusion_result = fusion.predict(test_hf_pred, test_fd_pred, use_sequence=False)
    
    print("\n融合预测结果:")
    print(f"预测收益率: {fusion_result['predicted_return']:.4f}")
    print(f"信号方向: {fusion_result['fusion_signal']['direction']}")
    print(f"信号强度: {fusion_result['fusion_signal']['strength']:.4f}")
    print(f"置信度: {fusion_result['fusion_signal']['confidence']:.4f}")
    print(f"信号类型: {fusion_result['fusion_signal']['type']}")
    
    print("\n反应路径:")
    print(f"阶段: {fusion_result['reaction_path']['phase']}")
    print(f"速度: {fusion_result['reaction_path']['speed']}")
    print(f"时间到峰值: {fusion_result['reaction_path']['time_to_peak']}")
    print(f"幅度: {fusion_result['reaction_path']['magnitude']:.4f}")
    print(f"持续性: {fusion_result['reaction_path']['persistence']:.2f}")
    print(f"形状: {fusion_result['reaction_path']['shape']}")
    print(f"行动: {fusion_result['reaction_path']['action']}")
    
    print("\n测试完成！")

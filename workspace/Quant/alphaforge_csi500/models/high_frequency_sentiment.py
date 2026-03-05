# 高频市场情绪感知模型（微观结构）

import pandas as pd
import numpy as np
from collections import deque
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
except ImportError:
    Sequential = None

class HighFrequencySentimentModel:
    def __init__(self, config):
        """初始化高频市场情绪感知模型"""
        # 兼容Config对象和字典
        if hasattr(config, '__dict__'):
            self.config = {k: v for k, v in config.__dict__.items() if not k.startswith('_')}
        else:
            self.config = config or {}
        
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        
        # 微观结构参数
        self.lookback_periods = {
            'tick': self.config.get('tick_lookback', 100),      # 逐笔数据回溯期
            'minute': self.config.get('minute_lookback', 60),   # 分钟级数据回溯期
            'hour': self.config.get('hour_lookback', 24),       # 小时级数据回溯期
            'daily': self.config.get('daily_lookback', 20)      # 日级数据回溯期
        }
    
        # 模型参数
        self.model_type = self.config.get('model_type', 'lightgbm')  # 默认为LightGBM
        self.n_estimators = self.config.get('n_estimators', 100)
        self.max_depth = self.config.get('max_depth', 5)
        self.random_state = self.config.get('random_state', 42)
        
        # 流处理缓冲区
        self.tick_buffer = deque(maxlen=10000)  # 环形缓冲区
        self.minute_buffer = deque(maxlen=1440)  # 保存全天分钟数据
        
        # 特征缓存
        self.feature_store = {}  # 特征缓存，避免重复计算
        
        # 市场温度指标
        self.temperature_indicators = [
            'order_flow_imbalance',    # 订单流不平衡
            'spread_pressure',         # 买卖价差压力
            'volume_surge',            # 成交量激增
            'price_impact',            # 价格冲击
            'volatility_spike',        # 波动率飙升
            'liquidity_stress',        # 流动性压力
            'depth_imbalance',         # 订单簿深度不平衡
            'market_impact',           # 市场冲击成本
            'book_slope',              # 订单簿斜率
            'imbalance_level_1',       # 订单簿1档不平衡
            'imbalance_level_5',       # 订单簿5档不平衡
            'imbalance_level_10',      # 订单簿10档不平衡
            'buy_aggression',          # 买入吃单力度
            'sell_aggression',         # 卖出吃单力度
            'sector_relative_strength', # 行业相对强度
            'ofi_correlation',         # 订单流相关性
            'large_trade_flow',        # 大单资金流向
            'medium_trade_flow',       # 中单资金流向
            'small_trade_flow',        # 小单资金流向
            'cross_sectional_strength', # 横截面相对强度
            'liquidity_momentum',      # 流动性动量
        ]
        
        # 市场情绪指标
        self.sentiment_indicators = [
            'momentum_burst',          # 动量爆发
            'reversal_signal',         # 反转信号
            'trend_strength',          # 趋势强度
            'market_participation',    # 市场参与度
            'noise_level',             # 噪声水平
            'cross_sectional_strength', # 横截面相对强度
            'liquidity_momentum',      # 流动性动量
        ]
    
    def calculate_microstructure_features_efficient(self, tick_data, order_book=None, market_data=None):
        """
        高效计算微观结构特征（使用EWMA替代rolling）
        
        Args:
            tick_data: 逐笔交易数据
            order_book: 订单簿数据（可选）
            market_data: 市场数据（可选）
            
        Returns:
            features: 微观结构特征字典
        """
        features = {}
        
        if tick_data is None or tick_data.empty:
            return features
        
        # 使用衰减因子，计算效率更高
        decay_factor = 0.94  # 相当于半衰期约11个tick
        
        # 1. 订单流不平衡（Order Flow Imbalance）
        if 'buy_volume' in tick_data.columns and 'sell_volume' in tick_data.columns:
            # 在线更新订单流不平衡
            current_ofi = (tick_data['buy_volume'] - tick_data['sell_volume']) / (tick_data['buy_volume'] + tick_data['sell_volume'] + 1e-6)
            # 使用ewm替代rolling，计算更快
            features['order_flow_imbalance'] = current_ofi.ewm(span=self.lookback_periods['tick'], adjust=False).mean()
        
        # 2. 买卖价差压力（Spread Pressure）
        if 'ask_price' in tick_data.columns and 'bid_price' in tick_data.columns:
            spread = tick_data['ask_price'] - tick_data['bid_price']
            mid_price = (tick_data['ask_price'] + tick_data['bid_price']) / 2
            features['spread_pressure'] = spread / (mid_price + 1e-6)
        
        # 3. 成交量激增（Volume Surge）
        if 'volume' in tick_data.columns:
            # 使用EWMA计算平均成交量
            avg_volume = tick_data['volume'].ewm(span=self.lookback_periods['minute'], adjust=False).mean()
            features['volume_surge'] = tick_data['volume'] / (avg_volume + 1e-6)
        
        # 4. 价格冲击（Price Impact）
        if 'trade_price' in tick_data.columns and 'mid_price' in tick_data.columns:
            price_change = tick_data['trade_price'] - tick_data['mid_price']
            features['price_impact'] = price_change / (tick_data['mid_price'] + 1e-6)
        
        # 5. 波动率飙升（Volatility Spike）
        if 'trade_price' in tick_data.columns:
            returns = tick_data['trade_price'].pct_change()
            # 使用EWMA计算波动率
            rolling_std = returns.ewm(span=self.lookback_periods['minute'], adjust=False).std()
            features['volatility_spike'] = rolling_std / (rolling_std.ewm(span=200, adjust=False).mean() + 1e-6)
        
        # 6. 流动性压力（Liquidity Stress）
        if 'bid_volume' in tick_data.columns and 'ask_volume' in tick_data.columns:
            depth = tick_data['bid_volume'] + tick_data['ask_volume']
            features['liquidity_stress'] = 1 / (depth + 1e-6)
        
        # 7. 订单簿深度不平衡
        if 'bid_volume' in tick_data.columns and 'ask_volume' in tick_data.columns:
            depth_imbalance = (tick_data['bid_volume'] - tick_data['ask_volume']) / (tick_data['bid_volume'] + tick_data['ask_volume'] + 1e-6)
            features['depth_imbalance'] = depth_imbalance
        
        # 8. 市场冲击成本
        if 'trade_price' in tick_data.columns and 'volume' in tick_data.columns:
            returns = tick_data['trade_price'].pct_change()
            volume_normalized = tick_data['volume'] / (tick_data['volume'].ewm(span=100, adjust=False).mean() + 1e-6)
            features['market_impact'] = abs(returns) * volume_normalized
        
        # 9. 高级微观结构特征（如果有订单簿数据）
        if order_book:
            advanced_features = self.calculate_advanced_micro_features(order_book)
            features.update(advanced_features)
        
        # 10. 横截面特征（如果有市场数据）
        if market_data:
            cross_sectional_features = self.add_cross_sectional_features(tick_data, market_data)
            features.update(cross_sectional_features)
        
        return features
    
    def update_streaming(self, new_tick, new_minute, order_book=None, market_data=None):
        """
        流式更新，而不是每次都重新计算全部
        
        Args:
            new_tick: 新的逐笔数据
            new_minute: 新的分钟数据
            order_book: 订单簿数据（可选）
            market_data: 市场数据（可选）
            
        Returns:
            prediction: 预测结果（仅在分钟闭合时返回）
        """
        # 增量更新滚动特征
        self._update_rolling_features(new_tick, new_minute, order_book, market_data)
        
        # 只在分钟闭合时触发预测
        if self._is_minute_closed(new_tick):
            return self.predict_streaming()
        
        return None
    
    def _update_rolling_features(self, new_tick, new_minute=None, order_book=None, market_data=None):
        """
        增量更新滚动特征
        
        Args:
            new_tick: 新的逐笔数据
            new_minute: 新的分钟数据
            order_book: 订单簿数据（可选）
            market_data: 市场数据（可选）
        """
        # 将新数据添加到缓冲区
        self.tick_buffer.append(new_tick)
        
        # 更新分钟缓冲区
        if new_minute:
            self.minute_buffer.append(new_minute)
        
        # 更新特征缓存
        if len(self.tick_buffer) > self.lookback_periods['tick']:
            # 计算最新的特征
            recent_ticks = list(self.tick_buffer)[-self.lookback_periods['tick']:]
            tick_df = pd.DataFrame(recent_ticks)
            
            # 计算微观结构特征（包含高级特征和横截面特征）
            micro_features = self.calculate_microstructure_features_efficient(tick_df, order_book, market_data)
            
            # 计算情绪特征（如果有分钟数据）
            sentiment_features = {}
            if len(self.minute_buffer) > self.lookback_periods['minute']:
                recent_minutes = list(self.minute_buffer)[-self.lookback_periods['minute']:]
                minute_df = pd.DataFrame(recent_minutes)
                sentiment_features = self.calculate_sentiment_features(minute_df)
            
            # 合并特征
            all_features = {}
            all_features.update(micro_features)
            all_features.update(sentiment_features)
            
            # 缓存特征
            self.feature_store['micro_features'] = micro_features
            self.feature_store['sentiment_features'] = sentiment_features
            self.feature_store['all_features'] = all_features
    
    def _is_minute_closed(self, new_tick):
        """
        判断分钟是否闭合
        
        Args:
            new_tick: 新的逐笔数据
            
        Returns:
            bool: 是否为分钟闭合
        """
        # 简单实现：假设数据按时间排序，每分钟的最后一笔为闭合
        # 实际实现需要根据时间戳判断
        return True  # 简化实现
    
    def predict_streaming(self):
        """
        流式预测
        
        Returns:
            prediction: 预测结果
        """
        # 从缓存中获取特征
        all_features = self.feature_store.get('all_features', {})
        micro_features = self.feature_store.get('micro_features', {})
        sentiment_features = self.feature_store.get('sentiment_features', {})
        
        # 构建特征向量
        feature_values = []
        all_indicators = list(self.temperature_indicators) + list(self.sentiment_indicators)
        
        for indicator in all_indicators:
            if indicator in all_features:
                val = all_features[indicator].iloc[-1] if isinstance(all_features[indicator], pd.Series) else all_features[indicator]
                feature_values.append(val if not pd.isna(val) else 0)
            else:
                feature_values.append(0)
        
        # 标准化并预测
        if self.model and self.scaler_X:
            X = np.array(feature_values).reshape(1, -1)
            X_scaled = self.scaler_X.transform(X)
            
            # 处理LSTM模型
            if self.model_type == 'lstm' and Sequential:
                X_scaled_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
                y_pred_scaled = self.model.predict(X_scaled_lstm).flatten()
            else:
                y_pred_scaled = self.model.predict(X_scaled)
            
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
            
            # 计算市场温度和情绪指标
            temperature = self.calculate_market_temperature(micro_features)
            sentiment = self.calculate_market_sentiment(sentiment_features)
            
            # 计算反应路径
            reaction_path = self.get_reaction_path({'temperature_score': temperature['overall_score'], 
                                                  'sentiment_score': sentiment['overall_score']})
            
            return {
                'predicted_return': y_pred,
                'market_temperature': temperature,
                'market_sentiment': sentiment,
                'temperature_score': temperature['overall_score'],
                'sentiment_score': sentiment['overall_score'],
                'reaction_path': reaction_path,
                'microstructure_features': micro_features,
                'sentiment_features': sentiment_features
            }
        
        return None
    
    def _winsorize(self, series, limits):
        """
        截尾均值平滑
        
        Args:
            series: 输入序列
            limits: 上下限百分比
            
        Returns:
            平滑后的序列
        """
        if series is None or series.empty:
            return series
        
        lower_bound = series.quantile(limits[0])
        upper_bound = series.quantile(1 - limits[1])
        
        return series.clip(lower=lower_bound, upper=upper_bound)
    
    def calculate_sentiment_features(self, minute_data):
        """
        计算情绪特征（市场情绪）
        
        Args:
            minute_data: 分钟级数据
            
        Returns:
            features: 情绪特征字典
        """
        features = {}
        
        if minute_data is None or minute_data.empty:
            return features
        
        # 1. 动量爆发（Momentum Burst）
        if 'close' in minute_data.columns:
            returns = minute_data['close'].pct_change()
            momentum_5m = returns.rolling(5).sum()
            momentum_20m = returns.rolling(20).sum()
            features['momentum_burst'] = momentum_5m / (abs(momentum_20m) + 1e-6)
        
        # 2. 反转信号（Reversal Signal）
        if 'close' in minute_data.columns:
            returns = minute_data['close'].pct_change()
            # RSI计算
            gains = returns.where(returns > 0, 0)
            losses = -returns.where(returns < 0, 0)
            avg_gains = gains.rolling(14).mean()
            avg_losses = losses.rolling(14).mean()
            rs = avg_gains / (avg_losses + 1e-6)
            rsi = 100 - (100 / (1 + rs))
            features['reversal_signal'] = (rsi - 50) / 50
        
        # 3. 趋势强度（Trend Strength）
        if 'close' in minute_data.columns:
            # 使用ADX思想计算趋势强度
            high = minute_data['high'] if 'high' in minute_data.columns else minute_data['close']
            low = minute_data['low'] if 'low' in minute_data.columns else minute_data['close']
            close = minute_data['close']
            
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            
            plus_dm = high.diff()
            minus_dm = -low.diff()
            plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
            minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)
            
            atr = tr.rolling(14).mean()
            plus_di = 100 * (plus_dm.rolling(14).mean() / (atr + 1e-6))
            minus_di = 100 * (minus_dm.rolling(14).mean() / (atr + 1e-6))
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-6)
            features['trend_strength'] = dx.rolling(14).mean() / 100
        
        # 4. 市场参与度（Market Participation）
        if 'volume' in minute_data.columns:
            total_volume = minute_data['volume'].rolling(self.lookback_periods['hour']).sum()
            avg_volume = total_volume / self.lookback_periods['hour']
            features['market_participation'] = minute_data['volume'] / (avg_volume + 1e-6)
        
        # 5. 噪声水平（Noise Level）
        if 'close' in minute_data.columns:
            returns = minute_data['close'].pct_change()
            signal = returns.rolling(self.lookback_periods['hour']).mean()
            noise = returns.rolling(self.lookback_periods['hour']).std()
            features['noise_level'] = noise / (abs(signal) + 1e-6)
        
        # 6. 横截面相对强度
        # 注意：实际实现需要全市场数据
        features['cross_sectional_strength'] = 0.5  # 占位符
        
        # 7. 流动性动量
        if 'volume' in minute_data.columns:
            volume_change = minute_data['volume'].pct_change()
            features['liquidity_momentum'] = volume_change.rolling(self.lookback_periods['minute']).mean()
        
        return features
    
    def calculate_advanced_micro_features(self, order_book):
        """
        计算高级微观结构特征
        
        Args:
            order_book: 订单簿数据
            
        Returns:
            features: 高级微观结构特征字典
        """
        features = {}
        
        if order_book is None:
            return features
        
        # 1. 订单簿斜率（Book Slope）
        # 衡量不同档位的挂单压力
        if 'bid_prices' in order_book and 'bid_volumes' in order_book and 'ask_prices' in order_book and 'ask_volumes' in order_book:
            bid_prices = order_book['bid_prices'][:10]  # 前10档
            bid_volumes = order_book['bid_volumes'][:10]
            ask_prices = order_book['ask_prices'][:10]
            ask_volumes = order_book['ask_volumes'][:10]
            
            # 计算加权价格
            weighted_bid = np.sum(bid_prices * bid_volumes) / (np.sum(bid_volumes) + 1e-6)
            weighted_ask = np.sum(ask_prices * ask_volumes) / (np.sum(ask_volumes) + 1e-6)
            features['book_slope'] = (weighted_ask - weighted_bid) / (weighted_bid + 1e-6)
        
        # 2. 订单簿不平衡的深度分解
        for level in [1, 5, 10]:
            if f'bid_volumes' in order_book and f'ask_volumes' in order_book:
                bid_depth = np.sum(order_book[f'bid_volumes'][:level])
                ask_depth = np.sum(order_book[f'ask_volumes'][:level])
                features[f'imbalance_level_{level}'] = (bid_depth - ask_depth) / (bid_depth + ask_depth + 1e-6)
        
        # 3. 成交与挂单的交互
        # 例如：吃单力度（Aggression）
        if 'trades' in order_book and 'ask_price' in order_book and 'bid_price' in order_book:
            trades = order_book['trades']
            if not trades.empty:
                aggressive_buy = trades[trades['price'] >= order_book['ask_price'][0]]
                aggressive_sell = trades[trades['price'] <= order_book['bid_price'][0]]
                
                features['buy_aggression'] = len(aggressive_buy) / (len(trades) + 1e-6)
                features['sell_aggression'] = len(aggressive_sell) / (len(trades) + 1e-6)
        
        return features
    
    def _calculate_trade_flow(self, stock_data, size='large'):
        """
        计算不同规模的资金流向
        
        Args:
            stock_data: 股票数据
            size: 交易规模（'large', 'medium', 'small'）
            
        Returns:
            trade_flow: 资金流向
        """
        if 'trade_size' not in stock_data or 'trade_price' not in stock_data:
            return 0
        
        # 定义不同规模的阈值（单位：股）
        thresholds = {
            'large': 100000,
            'medium': 10000,
            'small': 1000
        }
        
        threshold = thresholds.get(size, 1000)
        
        # 计算资金流向
        large_trades = stock_data[stock_data['trade_size'] >= threshold]
        if large_trades.empty:
            return 0
        
        # 假设价格上涨为资金流入，下跌为资金流出
        price_change = large_trades['trade_price'].pct_change()
        trade_value = large_trades['trade_size'] * large_trades['trade_price']
        
        return np.sum(price_change * trade_value) / (np.sum(trade_value) + 1e-6)
    
    def add_cross_sectional_features(self, stock_data, market_data):
        """
        加入市场整体信息
        
        Args:
            stock_data: 股票数据
            market_data: 市场数据
            
        Returns:
            features: 横截面特征字典
        """
        features = {}
        
        if stock_data is None or market_data is None:
            return features
        
        # 1. 行业相对强度
        if 'return' in stock_data and 'sector_return' in market_data:
            features['sector_relative_strength'] = stock_data['return'] - market_data['sector_return']
        
        # 2. 市场微观结构一致性
        # 计算股票与市场在订单流上的相关性
        if 'order_flow_imbalance' in stock_data and 'market_order_flow_imbalance' in market_data:
            stock_ofi = stock_data['order_flow_imbalance']
            market_ofi = market_data['market_order_flow_imbalance']
            features['ofi_correlation'] = stock_ofi.rolling(60).corr(market_ofi)
        
        # 3. 资金流向分解
        # 大单、中单、小单的资金流向
        features['large_trade_flow'] = self._calculate_trade_flow(stock_data, size='large')
        features['medium_trade_flow'] = self._calculate_trade_flow(stock_data, size='medium')
        features['small_trade_flow'] = self._calculate_trade_flow(stock_data, size='small')
        
        return features
    
    def prepare_training_data_improved(self, tick_data, minute_data):
        """
        多尺度标签构造
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            
        Returns:
            labels_short: 短期标签
            labels_medium: 中期标签
        """
        # 1. 短期标签（1-5分钟）- 捕捉瞬时反应
        labels_short = {
            'return_1min': minute_data['close'].pct_change(1).shift(-1),
            'return_3min': minute_data['close'].pct_change(3).shift(-3),
            'return_5min': minute_data['close'].pct_change(5).shift(-5)
        }
        
        # 2. 中期标签（10-30分钟）- 捕捉情绪扩散
        labels_medium = {
            'return_10min': minute_data['close'].pct_change(10).shift(-10),
            'return_20min': minute_data['close'].pct_change(20).shift(-20)
        }
        
        # 3. 标签平滑处理
        for name, label in labels_short.items():
            # 使用截尾均值平滑，去除极端噪声
            labels_short[name] = self._winsorize(label, limits=[0.01, 0.01])
        
        for name, label in labels_medium.items():
            labels_medium[name] = self._winsorize(label, limits=[0.01, 0.01])
        
        # 4. 分层学习策略
        # 我们可以训练多个模型分别预测不同时间尺度
        # 或者让一个模型输出多个头
        return labels_short, labels_medium
    
    def prepare_training_data(self, tick_data, minute_data, future_return_horizon=60):
        """
        准备训练数据
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            future_return_horizon: 未来收益率预测期（分钟）
            
        Returns:
            X: 特征矩阵
            y: 标签向量
        """
        # 计算微观结构特征
        micro_features = self.calculate_microstructure_features_efficient(tick_data)
        sentiment_features = self.calculate_sentiment_features(minute_data)
        
        # 合并特征
        all_features = {}
        all_features.update(micro_features)
        all_features.update(sentiment_features)
        
        # 转换为DataFrame
        feature_df = pd.DataFrame(all_features)
        
        # 计算未来收益率
        if 'close' in minute_data.columns:
            minute_data = minute_data.copy()
            minute_data['future_return'] = minute_data['close'].pct_change(future_return_horizon).shift(-future_return_horizon)
            
            # 对齐数据长度
            min_length = min(len(feature_df), len(minute_data))
            feature_df = feature_df.iloc[:min_length]
            minute_data = minute_data.iloc[:min_length]
            
            feature_df['future_return'] = minute_data['future_return'].values
        
        # 去除空值
        feature_df = feature_df.dropna()
        
        if feature_df.empty:
            return None, None
        
        # 提取特征和标签
        feature_cols = [col for col in feature_df.columns if col != 'future_return']
        X = feature_df[feature_cols].values
        y = feature_df['future_return'].values
        
        return X, y
    
    def train(self, tick_data, minute_data, future_return_horizon=60, multi_scale=False):
        """
        训练高频市场情绪感知模型
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            future_return_horizon: 未来收益率预测期（分钟）
            multi_scale: 是否使用多尺度标签
        """
        print("="*60)
        print("训练高频市场情绪感知模型")
        print("="*60)
        
        if multi_scale:
            # 使用多尺度标签
            labels_short, labels_medium = self.prepare_training_data_improved(tick_data, minute_data)
            
            # 计算特征
            micro_features = self.calculate_microstructure_features_efficient(tick_data)
            sentiment_features = self.calculate_sentiment_features(minute_data)
            
            # 合并特征
            all_features = {}
            all_features.update(micro_features)
            all_features.update(sentiment_features)
            
            # 转换为DataFrame
            feature_df = pd.DataFrame(all_features)
            
            # 合并标签
            for name, label in labels_short.items():
                feature_df[name] = label.values
            
            for name, label in labels_medium.items():
                feature_df[name] = label.values
            
            # 去除空值
            feature_df = feature_df.dropna()
            
            if feature_df.empty:
                print("无法准备训练数据")
                return None
            
            # 提取特征和标签
            feature_cols = [col for col in feature_df.columns if col not in list(labels_short.keys()) + list(labels_medium.keys())]
            X = feature_df[feature_cols].values
            
            # 训练多个模型分别预测不同时间尺度
            self.models = {}
            all_labels = {**labels_short, **labels_medium}
            
            # 标准化特征
            self.scaler_X = StandardScaler()
            X_scaled = self.scaler_X.fit_transform(X)
            
            for label_name in all_labels.keys():
                print(f"\n训练 {label_name} 模型:")
                y = feature_df[label_name].values
                
                # 标准化标签
                scaler_y = StandardScaler()
                y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
                
                # 划分训练集和测试集
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y_scaled, 
                    test_size=0.2, 
                    random_state=42
                )
                
                # 根据模型类型选择训练方法
                if self.model_type == 'lightgbm' and LGBMRegressor:
                    model = LGBMRegressor(
                        n_estimators=self.n_estimators,
                        max_depth=self.max_depth,
                        learning_rate=0.01,
                        subsample=0.8,
                        random_state=self.random_state,
                        n_jobs=-1
                    )
                    model.fit(X_train, y_train)
                elif self.model_type == 'lstm' and Sequential:
                    # 重塑数据用于LSTM
                    X_train_lstm = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
                    X_test_lstm = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
                    
                    model = Sequential()
                    model.add(LSTM(64, input_shape=(1, X_train.shape[1]), return_sequences=True))
                    model.add(Dropout(0.2))
                    model.add(LSTM(32))
                    model.add(Dropout(0.2))
                    model.add(Dense(1))
                    
                    model.compile(optimizer='adam', loss='mse')
                    model.fit(X_train_lstm, y_train, epochs=20, batch_size=32, validation_data=(X_test_lstm, y_test), verbose=0)
                else:
                    model = RandomForestRegressor(
                        n_estimators=self.n_estimators,
                        max_depth=self.max_depth,
                        min_samples_split=10,
                        min_samples_leaf=5,
                        random_state=self.random_state,
                        n_jobs=-1
                    )
                    model.fit(X_train, y_train)
                
                # 评估模型
                if self.model_type == 'lstm' and Sequential:
                    y_pred_train = model.predict(X_train_lstm).flatten()
                    y_pred_test = model.predict(X_test_lstm).flatten()
                else:
                    y_pred_train = model.predict(X_train)
                    y_pred_test = model.predict(X_test)
                
                train_mse = np.mean((y_train - y_pred_train) ** 2)
                test_mse = np.mean((y_test - y_pred_test) ** 2)
                train_r2 = 1 - (np.sum((y_train - y_pred_train) ** 2) / 
                               np.sum((y_train - np.mean(y_train)) ** 2))
                test_r2 = 1 - (np.sum((y_test - y_pred_test) ** 2) / 
                              np.sum((y_test - np.mean(y_test)) ** 2))
                
                print(f"  训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
                print(f"  测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
                
                # 保存模型和scaler
                self.models[label_name] = {
                    'model': model,
                    'scaler_y': scaler_y
                }
            
            print("\n多尺度模型训练完成！")
            return self.models
        else:
            # 使用传统单尺度标签
            X, y = self.prepare_training_data(tick_data, minute_data, future_return_horizon)
            
            if X is None or len(X) == 0:
                print("无法准备训练数据")
                return None
            
            print(f"训练数据量: {len(X)}")
            print(f"特征数量: {X.shape[1]}")
            
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
            
            # 根据模型类型选择训练方法
            if self.model_type == 'lightgbm' and LGBMRegressor:
                print("使用 LightGBM 模型")
                self.model = LGBMRegressor(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=0.01,
                    subsample=0.8,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                self.model.fit(X_train, y_train)
            elif self.model_type == 'lstm' and Sequential:
                print("使用 LSTM 模型")
                # 重塑数据用于LSTM
                X_train_lstm = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
                X_test_lstm = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
                
                self.model = Sequential()
                self.model.add(LSTM(64, input_shape=(1, X_train.shape[1]), return_sequences=True))
                self.model.add(Dropout(0.2))
                self.model.add(LSTM(32))
                self.model.add(Dropout(0.2))
                self.model.add(Dense(1))
                
                self.model.compile(optimizer='adam', loss='mse')
                self.model.fit(X_train_lstm, y_train, epochs=50, batch_size=32, validation_data=(X_test_lstm, y_test), verbose=1)
            else:
                print("使用 RandomForest 模型")
                self.model = RandomForestRegressor(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    min_samples_split=10,
                    min_samples_leaf=5,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                self.model.fit(X_train, y_train)
            
            # 评估模型
            if self.model_type == 'lstm' and Sequential:
                y_pred_train = self.model.predict(X_train_lstm).flatten()
                y_pred_test = self.model.predict(X_test_lstm).flatten()
            else:
                y_pred_train = self.model.predict(X_train)
                y_pred_test = self.model.predict(X_test)
            
            train_mse = np.mean((y_train - y_pred_train) ** 2)
            test_mse = np.mean((y_test - y_pred_test) ** 2)
            train_r2 = 1 - (np.sum((y_train - y_pred_train) ** 2) / 
                           np.sum((y_train - np.mean(y_train)) ** 2))
            test_r2 = 1 - (np.sum((y_test - y_pred_test) ** 2) / 
                          np.sum((y_test - np.mean(y_test)) ** 2))
            
            print(f"训练集 MSE: {train_mse:.6f}, R²: {train_r2:.4f}")
            print(f"测试集 MSE: {test_mse:.6f}, R²: {test_r2:.4f}")
            
            # 特征重要性（仅对树模型）
            if hasattr(self.model, 'feature_importances_'):
                feature_names = list(self.temperature_indicators) + list(self.sentiment_indicators)
                importances = self.model.feature_importances_
                
                print("\n特征重要性:")
                for name, importance in sorted(zip(feature_names, importances), 
                                             key=lambda x: x[1], reverse=True)[:10]:
                    print(f"  {name}: {importance:.4f}")
            
            print("="*60)
            
            return self.model
    
    def predict(self, tick_data, minute_data, multi_scale=False, order_book=None, market_data=None):
        """
        预测市场情绪和温度
        
        Args:
            tick_data: 逐笔交易数据
            minute_data: 分钟级数据
            multi_scale: 是否使用多尺度预测
            order_book: 订单簿数据（可选）
            market_data: 市场数据（可选）
            
        Returns:
            prediction: 预测结果字典
        """
        if not multi_scale and self.model is None:
            raise ValueError("模型未训练，请先调用train方法")
        
        if multi_scale and not hasattr(self, 'models'):
            raise ValueError("多尺度模型未训练，请先调用train方法并设置multi_scale=True")
        
        # 计算特征
        micro_features = self.calculate_microstructure_features_efficient(tick_data, order_book, market_data)
        sentiment_features = self.calculate_sentiment_features(minute_data)
        
        # 合并特征
        all_features = {}
        all_features.update(micro_features)
        all_features.update(sentiment_features)
        
        # 转换为DataFrame
        feature_df = pd.DataFrame(all_features)
        
        # 提取最新特征
        feature_values = []
        for col in feature_df.columns:
            if isinstance(feature_df[col], pd.Series):
                val = feature_df[col].iloc[-1]
            else:
                val = feature_df[col]
            
            # 处理NaN值
            if pd.isna(val):
                val = 0
            feature_values.append(val)
        
        X = np.array(feature_values).reshape(1, -1)
        
        # 标准化
        X_scaled = self.scaler_X.transform(X)
        
        if multi_scale:
            # 多尺度预测
            predictions = {}
            for label_name, model_info in self.models.items():
                model = model_info['model']
                scaler_y = model_info['scaler_y']
                
                # 预测
                if self.model_type == 'lstm' and Sequential:
                    # 重塑数据用于LSTM
                    X_scaled_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
                    y_pred_scaled = model.predict(X_scaled_lstm).flatten()
                else:
                    y_pred_scaled = model.predict(X_scaled)
                
                y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
                predictions[label_name] = y_pred
            
            # 计算市场温度和情绪指标
            temperature = self.calculate_market_temperature(micro_features)
            sentiment = self.calculate_market_sentiment(sentiment_features)
            
            # 计算反应路径
            reaction_path = self.get_reaction_path({'temperature_score': temperature['overall_score'], 
                                                  'sentiment_score': sentiment['overall_score']})
            
            prediction = {
                'predicted_returns': predictions,
                'market_temperature': temperature,
                'market_sentiment': sentiment,
                'temperature_score': temperature['overall_score'],
                'sentiment_score': sentiment['overall_score'],
                'reaction_path': reaction_path,
                'microstructure_features': micro_features,
                'sentiment_features': sentiment_features
            }
        else:
            # 传统单尺度预测
            # 预测
            if self.model_type == 'lstm' and Sequential:
                # 重塑数据用于LSTM
                X_scaled_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
                y_pred_scaled = self.model.predict(X_scaled_lstm).flatten()
            else:
                y_pred_scaled = self.model.predict(X_scaled)
            
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()[0]
            
            # 计算市场温度和情绪指标
            temperature = self.calculate_market_temperature(micro_features)
            sentiment = self.calculate_market_sentiment(sentiment_features)
            
            # 计算反应路径
            reaction_path = self.get_reaction_path({'temperature_score': temperature['overall_score'], 
                                                  'sentiment_score': sentiment['overall_score']})
            
            prediction = {
                'predicted_return': y_pred,
                'market_temperature': temperature,
                'market_sentiment': sentiment,
                'temperature_score': temperature['overall_score'],
                'sentiment_score': sentiment['overall_score'],
                'reaction_path': reaction_path,
                'microstructure_features': micro_features,
                'sentiment_features': sentiment_features
            }
        
        return prediction


class HighFrequencyBacktest:
    """
    高频回测框架
    """
    def __init__(self, model):
        self.model = model
        self.trades = []
        self.performance = {}
        self.trading_days = 0
    
    def run_walk_forward(self, data, train_window=20, test_window=5):
        """
        滚动窗口验证（Walk-Forward Analysis）
        这是量化实战中最可靠的验证方法
        
        Args:
            data: 回测数据
            train_window: 训练窗口大小
            test_window: 测试窗口大小
            
        Returns:
            results: 回测结果
        """
        results = []
        
        for i in range(0, len(data) - train_window - test_window, test_window):
            # 训练期
            train_data = data.iloc[i:i+train_window]
            self.model.train(train_data)
            
            # 测试期
            test_data = data.iloc[i+train_window:i+train_window+test_window]
            pred = self.model.predict(test_data)
            
            # 记录结果
            results.append({
                'train_period': (i, i+train_window),
                'test_period': (i+train_window, i+train_window+test_window),
                'predictions': pred,
                'actual': test_data['return']
            })
        
        return self._analyze_results(results)
    
    def _analyze_results(self, results):
        """
        分析回测结果
        
        Args:
            results: 回测结果
            
        Returns:
            analysis: 分析结果
        """
        # 计算各种指标
        predictions = []
        actuals = []
        
        for result in results:
            predictions.extend(result['predictions'])
            actuals.extend(result['actual'].values)
        
        # 计算相关性
        correlation = np.corrcoef(predictions, actuals)[0, 1]
        
        # 计算MSE
        mse = np.mean((np.array(predictions) - np.array(actuals)) ** 2)
        
        # 计算胜率
        correct = 0
        for pred, actual in zip(predictions, actuals):
            if pred * actual > 0:
                correct += 1
        win_rate = correct / len(predictions)
        
        return {
            'correlation': correlation,
            'mse': mse,
            'win_rate': win_rate,
            'total_trades': len(predictions)
        }
    
    def calculate_high_frequency_metrics(self, trades):
        """
        高频交易特有的评价指标
        
        Args:
            trades: 交易记录
            
        Returns:
            metrics: 评价指标
        """
        metrics = {}
        
        if not trades:
            return metrics
        
        # 1. 胜率（但要注意高频交易胜率天然高）
        metrics['win_rate'] = len([t for t in trades if t['pnl'] > 0]) / len(trades)
        
        # 2. 赔率（盈亏比）
        winning_trades = [t['pnl'] for t in trades if t['pnl'] > 0]
        losing_trades = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
        
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 1
        metrics['profit_loss_ratio'] = avg_win / avg_loss if avg_loss > 0 else np.inf
        
        # 3. 交易频率
        metrics['trades_per_day'] = len(trades) / self.trading_days if self.trading_days > 0 else 0
        
        # 4. 滑点冲击
        metrics['avg_slippage'] = np.mean([t.get('slippage', 0) for t in trades])
        
        # 5. 容量估计
        metrics['estimated_capacity'] = self._estimate_capacity(trades)
        
        return metrics
    
    def _estimate_capacity(self, trades):
        """
        估计策略容量
        
        Args:
            trades: 交易记录
            
        Returns:
            capacity: 估计容量
        """
        # 简化实现：基于平均交易量的倍数
        avg_trade_size = np.mean([t.get('size', 0) for t in trades])
        return avg_trade_size * 1000  # 假设可以处理1000倍的平均交易量


class HighFrequencySentimentSystem:
    """
    这不是一个模型，这是一个生态系统
    """
    def __init__(self):
        # 多时间尺度模型
        self.tick_model = HighFrequencySentimentModel({'model_type': 'lightgbm'})    # 毫秒级反应
        self.minute_model = HighFrequencySentimentModel({'model_type': 'lightgbm'})    # 分钟级判断
        self.hour_model = HighFrequencySentimentModel({'model_type': 'lightgbm'})         # 趋势把握
        
        # 风险管理器
        self.risk_manager = RiskManager(
            max_position=1e6,  # 最大持仓
            max_trade_rate=0.1,  # 最大交易速率
            circuit_breaker=CircuitBreaker()  # 熔断机制
        )
        
        # 执行优化器
        self.execution_optimizer = ExecutionOptimizer(
            algo='twap',  # 或vwap、iceberg等
            urgency='low'  # 根据信号强度动态调整
        )
        
        # 实时监控
        self.monitor = RealTimeMonitor()
    
    async def run(self):
        """
        异步实时运行
        """
        async for market_data in self.data_feed:
            # 并行计算多个模型
            tick_signal = await self.tick_model.predict_async(market_data.tick)
            min_signal = await self.minute_model.predict_async(market_data.minute)
            
            # 信号融合
            combined_signal = self.signal_fusion(tick_signal, min_signal)
            
            # 风险检查
            if self.risk_manager.check(combined_signal):
                # 执行优化
                execution_plan = self.execution_optimizer.optimize(combined_signal)
                
                # 发送订单
                await self.order_sender.send(execution_plan)
            
            # 监控记录
            self.monitor.record(market_data, combined_signal)
    
    def signal_fusion(self, tick_signal, minute_signal):
        """
        信号融合
        
        Args:
            tick_signal:  tick级信号
            minute_signal: 分钟级信号
            
        Returns:
            combined_signal: 融合后的信号
        """
        # 简单加权融合
        weight_tick = 0.7  # tick级信号权重更高
        weight_minute = 0.3
        
        combined_signal = {
            'predicted_return': weight_tick * tick_signal['predicted_return'] + weight_minute * minute_signal['predicted_return'],
            'confidence': min(tick_signal.get('confidence', 0.5) + minute_signal.get('confidence', 0.5), 1.0)
        }
        
        return combined_signal


class RiskManager:
    """
    风险管理器
    """
    def __init__(self, max_position, max_trade_rate, circuit_breaker):
        self.max_position = max_position
        self.max_trade_rate = max_trade_rate
        self.circuit_breaker = circuit_breaker
    
    def check(self, signal):
        """
        检查风险
        
        Args:
            signal: 交易信号
            
        Returns:
            bool: 是否通过风险检查
        """
        # 检查熔断机制
        if not self.circuit_breaker.check():
            return False
        
        # 检查仓位限制
        if abs(signal.get('position', 0)) > self.max_position:
            return False
        
        # 检查交易速率
        if signal.get('trade_rate', 0) > self.max_trade_rate:
            return False
        
        return True


class CircuitBreaker:
    """
    熔断机制
    """
    def check(self):
        """
        检查是否触发熔断
        
        Returns:
            bool: 是否可以交易
        """
        # 简化实现：总是返回True
        return True


class ExecutionOptimizer:
    """
    执行优化器
    """
    def __init__(self, algo, urgency):
        self.algo = algo
        self.urgency = urgency
    
    def optimize(self, signal):
        """
        优化执行计划
        
        Args:
            signal: 交易信号
            
        Returns:
            execution_plan: 执行计划
        """
        # 简化实现
        return {
            'size': signal.get('size', 0),
            'price': signal.get('price', 0),
            'algo': self.algo,
            'urgency': self.urgency
        }


class RealTimeMonitor:
    """
    实时监控
    """
    def record(self, market_data, signal):
        """
        记录市场数据和信号
        
        Args:
            market_data: 市场数据
            signal: 交易信号
        """
        # 简化实现：打印日志
        print(f"[{pd.Timestamp.now()}] Signal: {signal['predicted_return']:.6f}, Confidence: {signal.get('confidence', 0.5):.2f}")
    
    def calculate_market_temperature(self, micro_features):
        """
        计算市场温度
        
        Args:
            micro_features: 微观结构特征
            
        Returns:
            temperature: 市场温度字典
        """
        temperature = {}
        
        # 计算各项温度指标
        if 'order_flow_imbalance' in micro_features:
            ofi = micro_features['order_flow_imbalance']
            if isinstance(ofi, pd.Series):
                ofi = ofi.iloc[-1]
            temperature['order_flow_temp'] = abs(ofi)
        
        if 'spread_pressure' in micro_features:
            sp = micro_features['spread_pressure']
            if isinstance(sp, pd.Series):
                sp = sp.iloc[-1]
            temperature['spread_temp'] = sp
        
        if 'volume_surge' in micro_features:
            vs = micro_features['volume_surge']
            if isinstance(vs, pd.Series):
                vs = vs.iloc[-1]
            temperature['volume_temp'] = min(vs, 3.0) / 3.0
        
        if 'volatility_spike' in micro_features:
            vs = micro_features['volatility_spike']
            if isinstance(vs, pd.Series):
                vs = vs.iloc[-1]
            temperature['volatility_temp'] = min(vs, 3.0) / 3.0
        
        if 'liquidity_stress' in micro_features:
            ls = micro_features['liquidity_stress']
            if isinstance(ls, pd.Series):
                ls = ls.iloc[-1]
            temperature['liquidity_temp'] = min(ls, 1.0)
        
        # 计算综合温度
        temp_values = [v for v in temperature.values() if not pd.isna(v)]
        if temp_values:
            temperature['overall_score'] = np.mean(temp_values)
        else:
            temperature['overall_score'] = 0.5
        
        # 温度等级
        if temperature['overall_score'] > 0.7:
            temperature['level'] = '高温'
        elif temperature['overall_score'] > 0.4:
            temperature['level'] = '中温'
        else:
            temperature['level'] = '低温'
        
        return temperature
    
    def calculate_market_sentiment(self, sentiment_features):
        """
        计算市场情绪
        
        Args:
            sentiment_features: 情绪特征
            
        Returns:
            sentiment: 市场情绪字典
        """
        sentiment = {}
        
        # 计算各项情绪指标
        if 'momentum_burst' in sentiment_features:
            mb = sentiment_features['momentum_burst']
            if isinstance(mb, pd.Series):
                mb = mb.iloc[-1]
            sentiment['momentum_sentiment'] = np.tanh(mb)
        
        if 'reversal_signal' in sentiment_features:
            rs = sentiment_features['reversal_signal']
            if isinstance(rs, pd.Series):
                rs = rs.iloc[-1]
            sentiment['reversal_sentiment'] = rs
        
        if 'trend_strength' in sentiment_features:
            ts = sentiment_features['trend_strength']
            if isinstance(ts, pd.Series):
                ts = ts.iloc[-1]
            sentiment['trend_sentiment'] = ts
        
        if 'market_participation' in sentiment_features:
            mp = sentiment_features['market_participation']
            if isinstance(mp, pd.Series):
                mp = mp.iloc[-1]
            sentiment['participation_sentiment'] = min(mp, 2.0) / 2.0
        
        if 'noise_level' in sentiment_features:
            nl = sentiment_features['noise_level']
            if isinstance(nl, pd.Series):
                nl = nl.iloc[-1]
            sentiment['noise_sentiment'] = 1 - min(nl, 2.0) / 2.0
        
        # 计算综合情绪
        sent_values = [v for v in sentiment.values() if not pd.isna(v)]
        if sent_values:
            sentiment['overall_score'] = np.mean(sent_values)
        else:
            sentiment['overall_score'] = 0
        
        # 情绪等级
        if sentiment['overall_score'] > 0.3:
            sentiment['level'] = '乐观'
        elif sentiment['overall_score'] > -0.3:
            sentiment['level'] = '中性'
        else:
            sentiment['level'] = '悲观'
        
        return sentiment
    
    def get_signal_strength(self, prediction):
        """
        获取信号强度
        
        Args:
            prediction: 预测结果
            
        Returns:
            strength: 信号强度
        """
        # 综合考虑预测收益率、市场温度和情绪
        pred_return = prediction['predicted_return']
        temp_score = prediction['temperature_score']
        sent_score = prediction['sentiment_score']
        
        # 信号强度 = 预测收益率 * (温度权重 + 情绪权重)
        strength = pred_return * (temp_score + abs(sent_score))
        
        return strength
    
    def get_reaction_path(self, prediction, time_horizon=60):
        """
        预测资金反应路径
        
        Args:
            prediction: 预测结果
            time_horizon: 时间范围（分钟）
            
        Returns:
            path: 反应路径
        """
        # 基于市场温度和情绪预测资金反应路径
        temp_score = prediction.get('temperature_score', 0.5)
        sent_score = prediction.get('sentiment_score', 0)
        pred_return = prediction.get('predicted_return', 0)
        
        # 反应速度（温度越高，反应越快）
        reaction_speed = 0.5 + temp_score * 0.5
        
        # 反应幅度（情绪越极端，反应幅度越大）
        reaction_magnitude = abs(sent_score)
        
        # 反应持续时间
        reaction_duration = int(time_horizon * reaction_speed)
        
        # 反应路径
        path = {
            'reaction_speed': reaction_speed,
            'reaction_magnitude': reaction_magnitude,
            'reaction_duration': reaction_duration,
            'expected_return': pred_return * reaction_magnitude,
            'confidence': min(temp_score + abs(sent_score), 1.0)
        }
        
        return path

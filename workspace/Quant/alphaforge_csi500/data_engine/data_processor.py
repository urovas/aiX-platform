# 数据预处理模块

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import warnings
from datetime import datetime, timedelta
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer

warnings.filterwarnings('ignore')


class DataProcessor:
    """
    数据预处理模块
    支持数据清洗、特征工程、数据转换等功能
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据处理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 预处理器
        self.scalers = {}
        self.imputers = {}
        
        # 数据质量统计
        self.quality_stats = {}
        
        print("✅ 数据处理器初始化完成")
    
    def clean_data(self, 
                   data: pd.DataFrame, 
                   data_type: str = 'default') -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            data: 原始数据
            data_type: 数据类型 ('tick', 'minute', 'daily', 'financial')
            
        Returns:
            cleaned_data: 清洗后的数据
        """
        print(f"清洗{data_type}数据...")
        
        if data.empty:
            print("  ⚠️ 数据为空")
            return data
        
        original_len = len(data)
        
        # 1. 处理重复数据
        data = self._remove_duplicates(data)
        
        # 2. 处理缺失值
        data = self._handle_missing_values(data, data_type)
        
        # 3. 处理异常值
        data = self._handle_outliers(data, data_type)
        
        # 4. 数据类型转换
        data = self._convert_dtypes(data, data_type)
        
        # 5. 数据排序
        data = self._sort_data(data, data_type)
        
        # 6. 数据重置索引
        data = data.reset_index(drop=True)
        
        cleaned_len = len(data)
        print(f"  ✅ 清洗完成: {original_len} -> {cleaned_len} 条记录")
        
        return data
    
    def _remove_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """移除重复数据"""
        # 识别时间列
        time_cols = ['datetime', 'timestamp', 'date', 'time']
        subset = None
        
        for col in time_cols:
            if col in data.columns:
                subset = [col]
                break
        
        # 移除重复
        if subset:
            duplicates = data.duplicated(subset=subset, keep='first').sum()
            if duplicates > 0:
                data = data.drop_duplicates(subset=subset, keep='first')
                print(f"    移除重复数据: {duplicates} 条")
        
        return data
    
    def _handle_missing_values(self, 
                               data: pd.DataFrame, 
                               data_type: str) -> pd.DataFrame:
        """处理缺失值"""
        missing_count = data.isnull().sum().sum()
        
        if missing_count == 0:
            return data
        
        print(f"    处理缺失值: {missing_count} 个")
        
        # 根据数据类型选择不同的填充策略
        if data_type == 'tick':
            # 逐笔数据：删除缺失值
            data = data.dropna()
            
        elif data_type == 'minute':
            # 分钟数据：前向填充
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            data[numeric_cols] = data[numeric_cols].fillna(method='ffill')
            data = data.dropna()
            
        elif data_type == 'financial':
            # 财务数据：使用中位数填充
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if data[col].isnull().sum() > 0:
                    median_val = data[col].median()
                    data[col] = data[col].fillna(median_val)
        
        else:
            # 默认：删除缺失值
            data = data.dropna()
        
        return data
    
    def _handle_outliers(self, 
                        data: pd.DataFrame, 
                        data_type: str) -> pd.DataFrame:
        """处理异常值"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['volume', 'amount', 'turnover']:
                continue
            
            # 使用IQR方法检测异常值
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            # 标记异常值
            outliers_mask = (data[col] < lower_bound) | (data[col] > upper_bound)
            outliers_count = outliers_mask.sum()
            
            if outliers_count > 0:
                # 使用边界值替换异常值
                data.loc[data[col] < lower_bound, col] = lower_bound
                data.loc[data[col] > upper_bound, col] = upper_bound
        
        return data
    
    def _convert_dtypes(self, 
                       data: pd.DataFrame, 
                       data_type: str) -> pd.DataFrame:
        """数据类型转换"""
        # 时间列转换
        time_cols = ['datetime', 'timestamp', 'date', 'time', 'trade_time']
        for col in time_cols:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col], errors='coerce')
        
        # 价格列转换
        price_cols = ['open', 'high', 'low', 'close', 'price', 'bid_price', 'ask_price']
        for col in price_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 成交量列转换
        volume_cols = ['volume', 'amount', 'turnover', 'bid_volume', 'ask_volume']
        for col in volume_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        return data
    
    def _sort_data(self, 
                  data: pd.DataFrame, 
                  data_type: str) -> pd.DataFrame:
        """数据排序"""
        time_cols = ['datetime', 'timestamp', 'date', 'time', 'trade_time']
        
        for col in time_cols:
            if col in data.columns:
                data = data.sort_values(col)
                break
        
        return data
    
    def engineer_features(self, 
                         data: pd.DataFrame, 
                         data_type: str) -> pd.DataFrame:
        """
        特征工程
        
        Args:
            data: 原始数据
            data_type: 数据类型
            
        Returns:
            featured_data: 特征工程后的数据
        """
        print(f"特征工程: {data_type}")
        
        if data.empty:
            return data
        
        if data_type == 'tick':
            data = self._engineer_tick_features(data)
        elif data_type == 'minute':
            data = self._engineer_minute_features(data)
        elif data_type == 'daily':
            data = self._engineer_daily_features(data)
        elif data_type == 'financial':
            data = self._engineer_financial_features(data)
        
        print(f"  ✅ 特征工程完成: {data.shape[1]} 列")
        return data
    
    def _engineer_tick_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """逐笔数据特征工程"""
        df = data.copy()
        
        # 价格变化
        if 'price' in df.columns:
            df['price_change'] = df['price'].diff()
            df['price_change_pct'] = df['price'].pct_change()
            
            # 成交量加权平均价格
            if 'volume' in df.columns:
                df['vwap'] = (df['price'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # 订单不平衡
        if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
            df['order_imbalance'] = (df['bid_volume'] - df['ask_volume']) / (df['bid_volume'] + df['ask_volume'] + 1e-8)
        
        # 价差
        if 'bid_price' in df.columns and 'ask_price' in df.columns:
            df['spread'] = df['ask_price'] - df['bid_price']
            df['spread_pct'] = df['spread'] / df['price']
        
        # 成交方向
        if 'direction' not in df.columns and 'price' in df.columns:
            df['direction'] = np.sign(df['price_change'])
        
        return df
    
    def _engineer_minute_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """分钟数据特征工程"""
        df = data.copy()
        
        # 价格特征
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # 收益率
            df['return'] = df['close'].pct_change()
            
            # 波动率
            df['volatility'] = df['return'].rolling(window=20).std()
            
            # 价格范围
            df['price_range'] = (df['high'] - df['low']) / df['close']
            
            # 实体大小
            df['body_size'] = abs(df['close'] - df['open']) / df['close']
            
            # 上下影线
            df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
            df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # 成交量特征
        if 'volume' in df.columns:
            df['volume_ma5'] = df['volume'].rolling(window=5).mean()
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma5']
            
            # 成交量变化率
            df['volume_change'] = df['volume'].pct_change()
        
        # 成交额特征
        if 'amount' in df.columns:
            df['amount_ma5'] = df['amount'].rolling(window=5).mean()
            df['amount_ratio'] = df['amount'] / df['amount_ma5']
        
        return df
    
    def _engineer_daily_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """日线数据特征工程"""
        df = data.copy()
        
        # 基础价格特征
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # 多周期收益率
            for period in [1, 5, 10, 20]:
                df[f'return_{period}d'] = df['close'].pct_change(period)
            
            # 多周期波动率
            for period in [5, 10, 20, 60]:
                df[f'volatility_{period}d'] = df['return_1d'].rolling(window=period).std()
            
            # 移动平均线
            for period in [5, 10, 20, 60, 120]:
                df[f'ma{period}'] = df['close'].rolling(window=period).mean()
                df[f'close_to_ma{period}'] = df['close'] / df[f'ma{period}'] - 1
            
            # MACD
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 布林带
            df['boll_mid'] = df['close'].rolling(window=20).mean()
            df['boll_std'] = df['close'].rolling(window=20).std()
            df['boll_upper'] = df['boll_mid'] + 2 * df['boll_std']
            df['boll_lower'] = df['boll_mid'] - 2 * df['boll_std']
            df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_mid']
        
        # 成交量特征
        if 'volume' in df.columns:
            # 成交量移动平均
            for period in [5, 10, 20]:
                df[f'volume_ma{period}'] = df['volume'].rolling(window=period).mean()
            
            # 成交量比率
            df['volume_ratio_5'] = df['volume'] / df['volume_ma5']
            df['volume_ratio_20'] = df['volume'] / df['volume_ma20']
            
            # OBV
            df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        
        # 换手率特征
        if 'turnover' in df.columns:
            df['turnover_ma5'] = df['turnover'].rolling(window=5).mean()
            df['turnover_ma20'] = df['turnover'].rolling(window=20).mean()
        
        return df
    
    def _engineer_financial_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """财务数据特征工程"""
        df = data.copy()
        
        # 盈利能力指标
        if 'net_profit' in df.columns and 'revenue' in df.columns:
            df['net_profit_margin'] = df['net_profit'] / df['revenue']
        
        if 'gross_profit' in df.columns and 'revenue' in df.columns:
            df['gross_profit_margin'] = df['gross_profit'] / df['revenue']
        
        if 'operating_profit' in df.columns and 'revenue' in df.columns:
            df['operating_margin'] = df['operating_profit'] / df['revenue']
        
        # ROE和ROA
        if 'net_profit' in df.columns:
            if 'total_equity' in df.columns:
                df['roe'] = df['net_profit'] / df['total_equity']
            if 'total_assets' in df.columns:
                df['roa'] = df['net_profit'] / df['total_assets']
        
        # 偿债能力指标
        if 'total_assets' in df.columns and 'total_liabilities' in df.columns:
            df['debt_ratio'] = df['total_liabilities'] / df['total_assets']
            df['equity_ratio'] = 1 - df['debt_ratio']
        
        if 'current_assets' in df.columns and 'current_liabilities' in df.columns:
            df['current_ratio'] = df['current_assets'] / df['current_liabilities']
        
        # 运营能力指标
        if 'revenue' in df.columns:
            if 'total_assets' in df.columns:
                df['asset_turnover'] = df['revenue'] / df['total_assets']
            if 'inventory' in df.columns:
                df['inventory_turnover'] = df['revenue'] / df['inventory']
        
        # 成长性指标
        numeric_cols = ['revenue', 'net_profit', 'total_assets', 'total_equity']
        for col in numeric_cols:
            if col in df.columns:
                df[f'{col}_yoy'] = df[col].pct_change(4)  # 同比增长
                df[f'{col}_qoq'] = df[col].pct_change(1)  # 环比增长
        
        return df
    
    def normalize_data(self,
                      data: pd.DataFrame,
                      method: str = 'standard',
                      columns: List[str] = None,
                      fit: bool = True) -> pd.DataFrame:
        """
        数据标准化
        
        Args:
            data: 原始数据
            method: 标准化方法 ('standard', 'minmax', 'robust')
            columns: 需要标准化的列，None表示所有数值列
            fit: 是否拟合预处理器
            
        Returns:
            normalized_data: 标准化后的数据
        """
        print(f"数据标准化: {method}")
        
        df = data.copy()
        
        # 选择需要标准化的列
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not columns:
            return df
        
        # 选择预处理器
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            raise ValueError(f"未知的标准化方法: {method}")
        
        # 拟合和转换
        if fit:
            df[columns] = scaler.fit_transform(df[columns])
            self.scalers[method] = scaler
        else:
            if method not in self.scalers:
                raise ValueError(f"预处理器未拟合: {method}")
            df[columns] = self.scalers[method].transform(df[columns])
        
        print(f"  ✅ 标准化完成: {len(columns)} 列")
        return df
    
    def resample_data(self,
                     data: pd.DataFrame,
                     target_freq: str,
                     time_col: str = 'datetime') -> pd.DataFrame:
        """
        数据重采样
        
        Args:
            data: 原始数据
            target_freq: 目标频率 ('1min', '5min', '15min', '30min', '1h', '1d')
            time_col: 时间列名
            
        Returns:
            resampled_data: 重采样后的数据
        """
        print(f"数据重采样: -> {target_freq}")
        
        df = data.copy()
        
        if time_col not in df.columns:
            print(f"  ⚠️ 时间列 {time_col} 不存在")
            return df
        
        # 设置时间索引
        df = df.set_index(time_col)
        
        # 定义聚合规则
        agg_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'amount': 'sum',
            'turnover': 'sum',
            'bid_price': 'last',
            'ask_price': 'last',
            'bid_volume': 'sum',
            'ask_volume': 'sum'
        }
        
        # 只保留存在的列
        existing_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
        
        # 重采样
        resampled = df.resample(target_freq).agg(existing_rules)
        
        # 删除空行
        resampled = resampled.dropna(how='all')
        
        # 重置索引
        resampled = resampled.reset_index()
        
        print(f"  ✅ 重采样完成: {len(data)} -> {len(resampled)} 条记录")
        return resampled
    
    def align_data(self,
                  data_dict: Dict[str, pd.DataFrame],
                  time_col: str = 'datetime') -> Dict[str, pd.DataFrame]:
        """
        对齐多个数据集的时间
        
        Args:
            data_dict: 数据字典 {name: DataFrame}
            time_col: 时间列名
            
        Returns:
            aligned_dict: 对齐后的数据字典
        """
        print("对齐数据时间...")
        
        if not data_dict:
            return data_dict
        
        # 获取所有时间点
        all_times = []
        for name, df in data_dict.items():
            if time_col in df.columns:
                all_times.extend(df[time_col].tolist())
        
        if not all_times:
            print("  ⚠️ 没有找到时间列")
            return data_dict
        
        # 找到共同时间范围
        all_times = pd.to_datetime(all_times)
        common_start = all_times.min()
        common_end = all_times.max()
        
        # 过滤每个数据集
        aligned_dict = {}
        for name, df in data_dict.items():
            if time_col in df.columns:
                df = df[(df[time_col] >= common_start) & (df[time_col] <= common_end)]
            aligned_dict[name] = df
        
        print(f"  ✅ 时间对齐完成: {common_start} ~ {common_end}")
        return aligned_dict
    
    def split_data(self,
                  data: pd.DataFrame,
                  train_ratio: float = 0.7,
                  val_ratio: float = 0.15,
                  test_ratio: float = 0.15,
                  time_col: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        划分训练集、验证集、测试集
        
        Args:
            data: 原始数据
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            time_col: 时间列名（用于时间序列划分）
            
        Returns:
            train_data, val_data, test_data: 划分后的数据
        """
        print(f"划分数据集: {train_ratio:.0%} / {val_ratio:.0%} / {test_ratio:.0%}")
        
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例之和必须为1"
        
        n = len(data)
        
        if time_col and time_col in data.columns:
            # 按时间顺序划分
            data = data.sort_values(time_col)
            
            train_end = int(n * train_ratio)
            val_end = int(n * (train_ratio + val_ratio))
            
            train_data = data.iloc[:train_end]
            val_data = data.iloc[train_end:val_end]
            test_data = data.iloc[val_end:]
        else:
            # 随机划分
            train_data = data.sample(frac=train_ratio, random_state=42)
            remaining = data.drop(train_data.index)
            
            val_data = remaining.sample(frac=val_ratio/(val_ratio+test_ratio), random_state=42)
            test_data = remaining.drop(val_data.index)
        
        print(f"  ✅ 划分完成: {len(train_data)} / {len(val_data)} / {len(test_data)}")
        return train_data, val_data, test_data
    
    def create_sequences(self,
                        data: pd.DataFrame,
                        feature_cols: List[str],
                        target_col: str,
                        sequence_length: int = 20,
                        horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建时间序列样本
        
        Args:
            data: 原始数据
            feature_cols: 特征列名
            target_col: 目标列名
            sequence_length: 序列长度
            horizon: 预测步长
            
        Returns:
            X, y: 特征序列和目标值
        """
        print(f"创建时间序列样本: 序列长度={sequence_length}, 预测步长={horizon}")
        
        feature_data = data[feature_cols].values
        target_data = data[target_col].values
        
        X, y = [], []
        
        for i in range(len(data) - sequence_length - horizon + 1):
            X.append(feature_data[i:i+sequence_length])
            y.append(target_data[i+sequence_length+horizon-1])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"  ✅ 创建完成: X.shape={X.shape}, y.shape={y.shape}")
        return X, y
    
    def generate_labels(self,
                       data: pd.DataFrame,
                       price_col: str = 'close',
                       horizons: List[int] = [1, 5, 10, 20]) -> pd.DataFrame:
        """
        生成多尺度标签
        
        Args:
            data: 原始数据
            price_col: 价格列名
            horizons: 预测周期列表
            
        Returns:
            labeled_data: 带标签的数据
        """
        print(f"生成多尺度标签: {horizons}")
        
        df = data.copy()
        
        for horizon in horizons:
            # 未来收益率
            df[f'label_return_{horizon}'] = df[price_col].pct_change(horizon).shift(-horizon)
            
            # 未来方向
            df[f'label_direction_{horizon}'] = np.sign(df[f'label_return_{horizon}'])
            
            # 未来波动率
            df[f'label_volatility_{horizon}'] = df[price_col].pct_change().rolling(window=horizon).std().shift(-horizon)
        
        print(f"  ✅ 标签生成完成")
        return df
    
    def get_data_quality_report(self, data: pd.DataFrame) -> Dict:
        """
        生成数据质量报告
        
        Args:
            data: 数据DataFrame
            
        Returns:
            report: 质量报告
        """
        report = {
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
            'missing_values': {
                'total': data.isnull().sum().sum(),
                'by_column': data.isnull().sum().to_dict()
            },
            'duplicates': data.duplicated().sum(),
            'numeric_stats': {},
            'data_types': data.dtypes.to_dict()
        }
        
        # 数值列统计
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            report['numeric_stats'][col] = {
                'mean': data[col].mean(),
                'std': data[col].std(),
                'min': data[col].min(),
                'max': data[col].max(),
                'median': data[col].median(),
                'skewness': data[col].skew(),
                'kurtosis': data[col].kurtosis()
            }
        
        return report
    
    def print_quality_report(self, data: pd.DataFrame):
        """打印数据质量报告"""
        report = self.get_data_quality_report(data)
        
        print("\n" + "="*60)
        print("数据质量报告")
        print("="*60)
        print(f"总行数: {report['total_rows']}")
        print(f"总列数: {report['total_columns']}")
        print(f"内存使用: {report['memory_usage_mb']:.2f} MB")
        print(f"缺失值总数: {report['missing_values']['total']}")
        print(f"重复行数: {report['duplicates']}")
        print("="*60)

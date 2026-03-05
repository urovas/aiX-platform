#!/usr/bin/env python3
# 量化选股模型训练算法（专家级设计）

import sys
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/stock_selection')

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

class AdvancedStockSelectionTrainer:
    def __init__(self):
        """初始化训练器"""
        print("="*80)
        print("量化选股模型训练算法（专家级设计）")
        print("="*80)
        print()
        
        self.data_dir = Path("/home/xcc/openclaw-platform/workspace/quant/stock_selection/data")
        self.clean_dir = self.data_dir / "cleaned"
        
    def load_data(self):
        """加载清洗后的数据"""
        print("1. 加载清洗后的数据")
        print("-"*80)
        
        quote_files = list(self.clean_dir.glob("quote_*.csv"))
        print(f"找到 {len(quote_files)} 个清洗后的文件")
        
        all_data = []
        
        for file in quote_files[:100]:
            try:
                df = pd.read_csv(file)
                if not df.empty:
                    filename = file.name
                    ts_code = filename.split('_')[1].replace('.csv', '')
                    df['ts_code'] = ts_code
                    all_data.append(df)
            except Exception as e:
                continue
        
        if all_data:
            full_data = pd.concat(all_data, ignore_index=True)
            print(f"加载完成，总数据量: {len(full_data):,} 条")
            return full_data
        else:
            print("无法加载清洗后的数据")
            return None
    
    def advanced_feature_engineering(self, data):
        """高级特征工程"""
        print("2. 高级特征工程")
        print("-"*80)
        
        if data is None:
            return None
        
        # 基础收益率因子
        data['return_1d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change())
        data['return_3d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(3))
        data['return_5d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(5))
        data['return_10d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(10))
        data['return_20d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(20))
        
        # 成交量因子
        data['volume_change'] = data.groupby('ts_code')['volume'].transform(lambda x: x.pct_change())
        data['volume_ma5'] = data.groupby('ts_code')['volume'].transform(lambda x: x.rolling(5).mean())
        data['volume_ma20'] = data.groupby('ts_code')['volume'].transform(lambda x: x.rolling(20).mean())
        data['volume_ratio'] = data['volume'] / data['volume_ma20']
        
        # 成交额因子
        data['amount_change'] = data.groupby('ts_code')['amount'].transform(lambda x: x.pct_change())
        data['amount_ma5'] = data.groupby('ts_code')['amount'].transform(lambda x: x.rolling(5).mean())
        data['amount_ma20'] = data.groupby('ts_code')['amount'].transform(lambda x: x.rolling(20).mean())
        data['amount_ratio'] = data['amount'] / data['amount_ma20']
        
        # 技术指标因子
        data['ma5'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(5).mean())
        data['ma10'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(10).mean())
        data['ma20'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(20).mean())
        data['ma5_10_diff'] = (data['ma5'] - data['ma10']) / data['ma10']
        data['ma10_20_diff'] = (data['ma10'] - data['ma20']) / data['ma20']
        data['ma5_20_diff'] = (data['ma5'] - data['ma20']) / data['ma20']
        
        # 波动率因子
        data['price_volatility_5'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(5).std())
        data['price_volatility_10'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(10).std())
        data['price_volatility_20'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(20).std())
        data['volatility_ratio'] = data['price_volatility_5'] / data['price_volatility_20']
        
        # 动量因子
        data['momentum_5'] = data.groupby('ts_code')['close'].transform(lambda x: x / x.shift(5) - 1)
        data['momentum_10'] = data.groupby('ts_code')['close'].transform(lambda x: x / x.shift(10) - 1)
        data['momentum_20'] = data.groupby('ts_code')['close'].transform(lambda x: x / x.shift(20) - 1)
        
        # 相对强弱因子
        data['rs_5'] = data.groupby('ts_code')['close'].transform(lambda x: (x - x.rolling(5).min()) / (x.rolling(5).max() - x.rolling(5).min()))
        data['rs_10'] = data.groupby('ts_code')['close'].transform(lambda x: (x - x.rolling(10).min()) / (x.rolling(10).max() - x.rolling(10).min()))
        data['rs_20'] = data.groupby('ts_code')['close'].transform(lambda x: (x - x.rolling(20).min()) / (x.rolling(20).max() - x.rolling(20).min()))
        
        # 去除空值
        data = data.dropna()
        
        if len(data) == 0:
            print("数据清洗后为空")
            return None
        
        print(f"特征工程完成，数据量: {len(data):,} 条")
        
        return data
    
    def select_features(self, data):
        """特征选择"""
        print("3. 特征选择")
        print("-"*80)
        
        if data is None:
            return None, None
        
        # 选择特征列
        feature_cols = [
            'return_3d', 'return_5d', 'return_10d', 'return_20d',
            'volume_change', 'volume_ratio',
            'amount_change', 'amount_ratio',
            'ma5_10_diff', 'ma10_20_diff', 'ma5_20_diff',
            'price_volatility_5', 'price_volatility_10', 'volatility_ratio',
            'momentum_5', 'momentum_10', 'momentum_20',
            'rs_5', 'rs_10', 'rs_20'
        ]
        
        # 确保所有特征列都存在
        feature_cols = [col for col in feature_cols if col in data.columns]
        
        # 计算特征相关性
        feature_data = data[feature_cols]
        correlation_matrix = feature_data.corr().abs()
        
        # 移除高度相关的特征
        to_remove = set()
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                if correlation_matrix.iloc[i, j] > 0.95:
                    to_remove.add(correlation_matrix.columns[j])
        
        feature_cols = [col for col in feature_cols if col not in to_remove]
        
        print(f"特征数量: {len(feature_cols)}")
        print(f"移除高度相关特征: {len(to_remove)}")
        
        return data, feature_cols
    
    def prepare_training_data(self, data, feature_cols):
        """准备训练数据"""
        print("4. 准备训练数据")
        print("-"*80)
        
        if data is None or feature_cols is None:
            return None, None, None, None
        
        target_col = 'return_1d'
        
        X = data[feature_cols]
        y = data[target_col]
        
        # 时间序列划分
        data_sorted = data.sort_values('date')
        split_idx = int(len(data_sorted) * 0.8)
        
        train_data = data_sorted.iloc[:split_idx]
        test_data = data_sorted.iloc[split_idx:]
        
        X_train = train_data[feature_cols]
        y_train = train_data[target_col]
        X_test = test_data[feature_cols]
        y_test = test_data[target_col]
        
        # 特征标准化
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print(f"训练数据: {len(X_train):,} 条, 测试数据: {len(X_test):,} 条")
        print(f"特征标准化完成")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_linear_models(self, X_train, y_train, X_test, y_test):
        """训练线性模型"""
        print("5. 训练线性模型")
        print("-"*80)
        
        models = {}
        results = {}
        
        # 线性回归
        print("训练线性回归...")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        models['linear'] = lr
        
        y_pred_train = lr.predict(X_train)
        y_pred_test = lr.predict(X_test)
        results['linear'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # Ridge回归
        print("训练Ridge回归...")
        ridge = Ridge(alpha=1.0)
        ridge.fit(X_train, y_train)
        models['ridge'] = ridge
        
        y_pred_train = ridge.predict(X_train)
        y_pred_test = ridge.predict(X_test)
        results['ridge'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # Lasso回归
        print("训练Lasso回归...")
        lasso = Lasso(alpha=0.01)
        lasso.fit(X_train, y_train)
        models['lasso'] = lasso
        
        y_pred_train = lasso.predict(X_train)
        y_pred_test = lasso.predict(X_test)
        results['lasso'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # ElasticNet
        print("训练ElasticNet...")
        enet = ElasticNet(alpha=0.01, l1_ratio=0.5)
        enet.fit(X_train, y_train)
        models['elasticnet'] = enet
        
        y_pred_train = enet.predict(X_train)
        y_pred_test = enet.predict(X_test)
        results['elasticnet'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        return models, results
    
    def train_tree_models(self, X_train, y_train, X_test, y_test):
        """训练树模型"""
        print("\n6. 训练树模型")
        print("-"*80)
        
        models = {}
        results = {}
        
        # 随机森林（保守参数）
        print("训练随机森林（保守参数）...")
        rf = RandomForestRegressor(
            n_estimators=20,
            max_depth=3,
            min_samples_split=20,
            min_samples_leaf=10,
            max_features='sqrt',
            random_state=42
        )
        rf.fit(X_train, y_train)
        models['rf'] = rf
        
        y_pred_train = rf.predict(X_train)
        y_pred_test = rf.predict(X_test)
        results['rf'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # 梯度提升树
        print("训练梯度提升树...")
        gb = GradientBoostingRegressor(
            n_estimators=20,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        gb.fit(X_train, y_train)
        models['gb'] = gb
        
        y_pred_train = gb.predict(X_train)
        y_pred_test = gb.predict(X_test)
        results['gb'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # AdaBoost
        print("训练AdaBoost...")
        ada = AdaBoostRegressor(
            n_estimators=20,
            learning_rate=0.1,
            random_state=42
        )
        ada.fit(X_train, y_train)
        models['adaboost'] = ada
        
        y_pred_train = ada.predict(X_train)
        y_pred_test = ada.predict(X_test)
        results['adaboost'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        return models, results
    
    def train_boosting_models(self, X_train, y_train, X_test, y_test):
        """训练Boosting模型"""
        print("\n7. 训练Boosting模型")
        print("-"*80)
        
        models = {}
        results = {}
        
        # XGBoost（保守参数）
        print("训练XGBoost（保守参数）...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=20,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42
        )
        xgb_model.fit(X_train, y_train)
        models['xgb'] = xgb_model
        
        y_pred_train = xgb_model.predict(X_train)
        y_pred_test = xgb_model.predict(X_test)
        results['xgb'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        # LightGBM（保守参数）
        print("训练LightGBM（保守参数）...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=20,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        models['lgb'] = lgb_model
        
        y_pred_train = lgb_model.predict(X_train)
        y_pred_test = lgb_model.predict(X_test)
        results['lgb'] = self.evaluate_model(y_train, y_pred_train, y_test, y_pred_test)
        
        return models, results
    
    def evaluate_model(self, y_train, y_pred_train, y_test, y_pred_test):
        """评估模型"""
        return {
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_mse': mean_squared_error(y_train, y_pred_train),
            'test_mse': mean_squared_error(y_test, y_pred_test),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'overfitting': r2_score(y_train, y_pred_train) - r2_score(y_test, y_pred_test)
        }
    
    def model_ensemble(self, models, X_train, y_train, X_test, y_test):
        """模型集成"""
        print("\n8. 模型集成")
        print("-"*80)
        
        # 简单平均
        predictions_train = []
        predictions_test = []
        
        for model in models.values():
            predictions_train.append(model.predict(X_train))
            predictions_test.append(model.predict(X_test))
        
        ensemble_train = np.mean(predictions_train, axis=0)
        ensemble_test = np.mean(predictions_test, axis=0)
        
        results = self.evaluate_model(y_train, ensemble_train, y_test, ensemble_test)
        
        print(f"集成模型:")
        print(f"训练集 R²: {results['train_r2']:.4f}")
        print(f"测试集 R²: {results['test_r2']:.4f}")
        print(f"训练集 MSE: {results['train_mse']:.4f}")
        print(f"测试集 MSE: {results['test_mse']:.4f}")
        print(f"过拟合程度: {results['overfitting']:.4f}")
        
        return results
    
    def compare_all_models(self, all_results):
        """比较所有模型"""
        print("\n9. 模型对比")
        print("="*80)
        
        comparison_df = pd.DataFrame(all_results).T
        comparison_df = comparison_df.sort_values('test_r2', ascending=False)
        
        print(comparison_df.to_string())
        
        print("\n推荐模型:", comparison_df.index[0])
        print(f"测试集 R²: {comparison_df.loc[comparison_df.index[0], 'test_r2']:.4f}")
        print(f"过拟合程度: {comparison_df.loc[comparison_df.index[0], 'overfitting']:.4f}")
        
        return comparison_df
    
    def predict_stocks(self, data, models, feature_cols):
        """预测股票"""
        print("\n10. 预测股票")
        print("-"*80)
        
        latest_data = data.groupby('ts_code').tail(1).copy()
        
        if len(latest_data) == 0:
            print("没有最新数据")
            return
        
        # 准备特征
        X_pred = latest_data[feature_cols]
        
        # 预测
        for model_name, model in models.items():
            latest_data[f'predicted_return_{model_name}'] = model.predict(X_pred)
        
        # 综合预测
        model_names = list(models.keys())
        latest_data['predicted_return_ensemble'] = latest_data[[f'predicted_return_{name}' for name in model_names]].mean(axis=1)
        
        print("按综合预测收益率排序的前20只股票:")
        top_stocks_ensemble = latest_data.sort_values('predicted_return_ensemble', ascending=False).head(20)
        for i, (_, row) in enumerate(top_stocks_ensemble.iterrows(), 1):
            print(f"{i}. {row['ts_code']}: {row['predicted_return_ensemble']:.4f}")
    
    def run_full_training(self):
        """完整训练流程"""
        # 加载数据
        data = self.load_data()
        if data is None:
            return
        
        # 高级特征工程
        data_with_features = self.advanced_feature_engineering(data)
        if data_with_features is None:
            return
        
        # 特征选择
        data_selected, feature_cols = self.select_features(data_with_features)
        if data_selected is None:
            return
        
        # 准备训练数据
        X_train, X_test, y_train, y_test = self.prepare_training_data(data_selected, feature_cols)
        if X_train is None:
            return
        
        # 训练线性模型
        linear_models, linear_results = self.train_linear_models(X_train, y_train, X_test, y_test)
        
        # 训练树模型
        tree_models, tree_results = self.train_tree_models(X_train, y_train, X_test, y_test)
        
        # 训练Boosting模型
        boosting_models, boosting_results = self.train_boosting_models(X_train, y_train, X_test, y_test)
        
        # 合并所有模型
        all_models = {**linear_models, **tree_models, **boosting_models}
        all_results = {**linear_results, **tree_results, **boosting_results}
        
        # 模型集成
        ensemble_results = self.model_ensemble(all_models, X_train, y_train, X_test, y_test)
        all_results['ensemble'] = ensemble_results
        
        # 比较所有模型
        self.compare_all_models(all_results)
        
        # 预测股票
        self.predict_stocks(data_selected, all_models, feature_cols)
        
        print()
        print("="*80)
        print("训练完成")
        print("="*80)

if __name__ == "__main__":
    try:
        trainer = AdvancedStockSelectionTrainer()
        trainer.run_full_training()
    except KeyboardInterrupt:
        print("\n训练被用户中断")
    except Exception as e:
        print(f"\n训练出错: {e}")
        import traceback
        traceback.print_exc()

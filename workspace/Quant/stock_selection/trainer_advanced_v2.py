#!/usr/bin/env python3
# 量化选股模型训练脚本（使用XGBoost和LightGBM）

import sys
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/stock_selection')

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb

class StockSelectionTrainer:
    def __init__(self):
        """初始化训练器"""
        print("="*80)
        print("量化选股模型训练（使用XGBoost和LightGBM）")
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
        
        for file in quote_files[:100]:  # 处理100个文件
            try:
                df = pd.read_csv(file)
                if not df.empty:
                    # 提取股票代码
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
    
    def calculate_simple_factors(self, data):
        """计算简单因子"""
        print("2. 计算因子")
        print("-"*80)
        
        if data is None:
            return None
        
        # 计算基本因子
        data['return_1d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change())
        data['return_5d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(5))
        data['return_20d'] = data.groupby('ts_code')['close'].transform(lambda x: x.pct_change(20))
        
        data['volume_change'] = data.groupby('ts_code')['volume'].transform(lambda x: x.pct_change())
        data['amount_change'] = data.groupby('ts_code')['amount'].transform(lambda x: x.pct_change())
        
        # 计算技术因子
        data['ma5'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(5).mean())
        data['ma20'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(20).mean())
        data['ma5_20_diff'] = (data['ma5'] - data['ma20']) / data['ma20']
        
        data['price_volatility'] = data.groupby('ts_code')['close'].transform(lambda x: x.rolling(20).std())
        data['price_volatility_ratio'] = data['price_volatility'] / data['close']
        
        # 去除空值
        data = data.dropna()
        
        if len(data) == 0:
            print("数据清洗后为空")
            return None
        
        print(f"因子计算完成，数据量: {len(data):,} 条")
        
        return data
    
    def train_models(self, data):
        """训练多个模型"""
        print("3. 训练模型")
        print("-"*80)
        
        if data is None:
            return None
        
        # 选择特征和目标变量
        feature_cols = [
            'return_5d', 'return_20d', 'volume_change', 'amount_change',
            'ma5_20_diff', 'price_volatility_ratio'
        ]
        
        # 确保所有特征列都存在
        feature_cols = [col for col in feature_cols if col in data.columns]
        
        if len(feature_cols) == 0:
            print("没有有效的特征列")
            return None
        
        # 目标变量：1日收益率
        target_col = 'return_1d'
        
        if target_col not in data.columns:
            print("目标变量不存在")
            return None
        
        X = data[feature_cols]
        y = data[target_col]
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"训练数据: {len(X_train):,} 条, 测试数据: {len(X_test):,} 条")
        
        models = {}
        results = {}
        
        # 1. 线性回归模型
        print("\n1. 训练线性回归模型...")
        linear_model = LinearRegression()
        linear_model.fit(X_train, y_train)
        
        y_pred_train = linear_model.predict(X_train)
        y_pred_test = linear_model.predict(X_test)
        
        results['linear'] = {
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_mse': mean_squared_error(y_train, y_pred_train),
            'test_mse': mean_squared_error(y_test, y_pred_test)
        }
        
        print(f"线性回归模型:")
        print(f"训练集 R²: {results['linear']['train_r2']:.4f}")
        print(f"测试集 R²: {results['linear']['test_r2']:.4f}")
        print(f"训练集 MSE: {results['linear']['train_mse']:.4f}")
        print(f"测试集 MSE: {results['linear']['test_mse']:.4f}")
        
        models['linear'] = linear_model
        
        # 2. 随机森林模型
        print("\n2. 训练随机森林模型...")
        rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        rf_model.fit(X_train, y_train)
        
        y_pred_train_rf = rf_model.predict(X_train)
        y_pred_test_rf = rf_model.predict(X_test)
        
        results['rf'] = {
            'train_r2': r2_score(y_train, y_pred_train_rf),
            'test_r2': r2_score(y_test, y_pred_test_rf),
            'train_mse': mean_squared_error(y_train, y_pred_train_rf),
            'test_mse': mean_squared_error(y_test, y_pred_test_rf)
        }
        
        print(f"随机森林模型:")
        print(f"训练集 R²: {results['rf']['train_r2']:.4f}")
        print(f"测试集 R²: {results['rf']['test_r2']:.4f}")
        print(f"训练集 MSE: {results['rf']['train_mse']:.4f}")
        print(f"测试集 MSE: {results['rf']['test_mse']:.4f}")
        print(f"过拟合程度: {results['rf']['train_r2'] - results['rf']['test_r2']:.4f}")
        
        models['rf'] = rf_model
        
        # 2.1 优化随机森林模型
        print("\n2.1 训练优化随机森林模型...")
        rf_optimized = RandomForestRegressor(
            n_estimators=30,
            max_depth=4,
            max_features='sqrt',
            min_samples_split=15,
            min_samples_leaf=8,
            bootstrap=True,
            random_state=42
        )
        rf_optimized.fit(X_train, y_train)
        
        y_pred_train_rf_opt = rf_optimized.predict(X_train)
        y_pred_test_rf_opt = rf_optimized.predict(X_test)
        
        results['rf_optimized'] = {
            'train_r2': r2_score(y_train, y_pred_train_rf_opt),
            'test_r2': r2_score(y_test, y_pred_test_rf_opt),
            'train_mse': mean_squared_error(y_train, y_pred_train_rf_opt),
            'test_mse': mean_squared_error(y_test, y_pred_test_rf_opt)
        }
        
        print(f"优化随机森林模型:")
        print(f"训练集 R²: {results['rf_optimized']['train_r2']:.4f}")
        print(f"测试集 R²: {results['rf_optimized']['test_r2']:.4f}")
        print(f"训练集 MSE: {results['rf_optimized']['train_mse']:.4f}")
        print(f"测试集 MSE: {results['rf_optimized']['test_mse']:.4f}")
        print(f"过拟合程度: {results['rf_optimized']['train_r2'] - results['rf_optimized']['test_r2']:.4f}")
        
        models['rf_optimized'] = rf_optimized
        
        # 3. XGBoost模型
        print("\n3. 训练XGBoost模型...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
        xgb_model.fit(X_train, y_train)
        
        y_pred_train_xgb = xgb_model.predict(X_train)
        y_pred_test_xgb = xgb_model.predict(X_test)
        
        results['xgb'] = {
            'train_r2': r2_score(y_train, y_pred_train_xgb),
            'test_r2': r2_score(y_test, y_pred_test_xgb),
            'train_mse': mean_squared_error(y_train, y_pred_train_xgb),
            'test_mse': mean_squared_error(y_test, y_pred_test_xgb)
        }
        
        print(f"XGBoost模型:")
        print(f"训练集 R²: {results['xgb']['train_r2']:.4f}")
        print(f"测试集 R²: {results['xgb']['test_r2']:.4f}")
        print(f"训练集 MSE: {results['xgb']['train_mse']:.4f}")
        print(f"测试集 MSE: {results['xgb']['test_mse']:.4f}")
        
        models['xgb'] = xgb_model
        
        # 4. LightGBM模型
        print("\n4. 训练LightGBM模型...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
        lgb_model.fit(X_train, y_train)
        
        y_pred_train_lgb = lgb_model.predict(X_train)
        y_pred_test_lgb = lgb_model.predict(X_test)
        
        results['lgb'] = {
            'train_r2': r2_score(y_train, y_pred_train_lgb),
            'test_r2': r2_score(y_test, y_pred_test_lgb),
            'train_mse': mean_squared_error(y_train, y_pred_train_lgb),
            'test_mse': mean_squared_error(y_test, y_pred_test_lgb)
        }
        
        print(f"LightGBM模型:")
        print(f"训练集 R²: {results['lgb']['train_r2']:.4f}")
        print(f"测试集 R²: {results['lgb']['test_r2']:.4f}")
        print(f"训练集 MSE: {results['lgb']['train_mse']:.4f}")
        print(f"测试集 MSE: {results['lgb']['test_mse']:.4f}")
        
        models['lgb'] = lgb_model
        
        # 显示因子重要性（XGBoost）
        if 'xgb' in models:
            print("\nXGBoost因子重要性:")
            importance = models['xgb'].feature_importances_
            feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': importance
            }).sort_values('importance', ascending=False)
            print(feature_importance)
        
        # 显示因子重要性（LightGBM）
        if 'lgb' in models:
            print("\nLightGBM因子重要性:")
            importance = models['lgb'].feature_importances_
            feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': importance
            }).sort_values('importance', ascending=False)
            print(feature_importance)
        
        return models, results, feature_cols
    
    def predict_stocks(self, data, models, feature_cols):
        """预测股票"""
        print("4. 预测股票")
        print("-"*80)
        
        if data is None or models is None:
            return
        
        # 获取最新数据
        latest_data = data.groupby('ts_code').tail(1).copy()
        
        if len(latest_data) == 0:
            print("没有最新数据")
            return
        
        # 准备特征
        X_pred = latest_data[feature_cols]
        
        # 预测
        for model_name, model in models.items():
            latest_data[f'predicted_return_{model_name}'] = model.predict(X_pred)
        
        # 按各个模型的预测收益率排序
        for model_name in models.keys():
            print(f"\n按{model_name}预测收益率排序的前10只股票:")
            top_stocks = latest_data.sort_values(f'predicted_return_{model_name}', ascending=False).head(10)
            for i, (_, row) in enumerate(top_stocks.iterrows(), 1):
                print(f"{i}. {row['ts_code']}: {row[f'predicted_return_{model_name}']:.4f}")
        
        # 综合预测（平均所有模型的预测）
        model_names = list(models.keys())
        latest_data['predicted_return_ensemble'] = latest_data[[f'predicted_return_{name}' for name in model_names]].mean(axis=1)
        
        print("\n按综合预测收益率排序的前20只股票:")
        top_stocks_ensemble = latest_data.sort_values('predicted_return_ensemble', ascending=False).head(20)
        for i, (_, row) in enumerate(top_stocks_ensemble.iterrows(), 1):
            print(f"{i}. {row['ts_code']}: {row['predicted_return_ensemble']:.4f}")
    
    def run_full_training(self):
        """完整训练流程"""
        # 加载数据
        data = self.load_data()
        if data is None:
            return
        
        # 计算因子
        data_with_factors = self.calculate_simple_factors(data)
        if data_with_factors is None:
            return
        
        # 训练模型
        models, results, feature_cols = self.train_models(data_with_factors)
        if models is None:
            return
        
        # 模型对比
        self.compare_models(results)
        
        # 预测股票
        self.predict_stocks(data_with_factors, models, feature_cols)
        
        print()
        print("="*80)
        print("训练完成")
        print("="*80)
    
    def compare_models(self, results):
        """比较所有模型"""
        print("\n模型对比")
        print("="*80)
        
        comparison_df = pd.DataFrame(results).T
        comparison_df['overfitting'] = comparison_df['train_r2'] - comparison_df['test_r2']
        comparison_df = comparison_df.sort_values('test_r2', ascending=False)
        
        print(comparison_df.to_string())
        
        print("\n推荐模型:", comparison_df.index[0])
        print(f"测试集 R²: {comparison_df.loc[comparison_df.index[0], 'test_r2']:.4f}")
        print(f"过拟合程度: {comparison_df.loc[comparison_df.index[0], 'overfitting']:.4f}")

if __name__ == "__main__":
    try:
        trainer = StockSelectionTrainer()
        trainer.run_full_training()
    except KeyboardInterrupt:
        print("\n训练被用户中断")
    except Exception as e:
        print(f"\n训练出错: {e}")
        import traceback
        traceback.print_exc()

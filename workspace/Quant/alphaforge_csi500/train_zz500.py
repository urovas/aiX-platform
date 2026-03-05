#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中证500指数增强模型训练脚本
使用现有模型: FundamentalValueModel, HighFrequencySentimentModel, AISignalFusion, DynamicWeightAllocator
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from models.fundamental_value_v3 import FundamentalValueModel
from models.high_frequency_sentiment import HighFrequencySentimentModel
from models.ai_signal_fusion import AISignalFusion
from models.dynamic_weight_allocator import DynamicWeightAllocator
from data_engine.data_enhancer import DataEnhancer


class ZZ500Trainer:
    """中证500指增模型训练器"""
    
    def __init__(self):
        """初始化训练器"""
        print("="*60)
        print("中证500指数增强模型训练")
        print("="*60)
        
        self.data_dir = './data/zz500/'
        self.train_dir = './data/zz500/train/'
        self.val_dir = './data/zz500/val/'
        self.test_dir = './data/zz500/test/'
        
        self.models = {}
        self.enhancer = DataEnhancer(self.data_dir)
        
    def get_stock_codes(self, data_dir: str) -> list:
        """获取股票代码列表"""
        files = glob.glob(os.path.join(data_dir, '*.csv'))
        stock_files = [f for f in files if 'index' not in os.path.basename(f)]
        codes = []
        for f in stock_files:
            basename = os.path.basename(f)
            code = basename.replace('.csv', '')
            if code:
                codes.append(code)
        return list(set(codes))
    
    def prepare_data(self):
        """
        准备训练数据
        1. 获取财务数据
        2. 获取分钟数据(可选)
        3. 整合数据
        """
        print("\n" + "="*60)
        print("1. 准备数据")
        print("="*60)
        
        stock_codes = self.get_stock_codes(self.train_dir)
        print(f"训练集股票数: {len(stock_codes)}")
        
        # 1. 获取财务数据
        print("\n获取财务数据...")
        financial_dir = os.path.join(self.data_dir, 'financial')
        if not os.path.exists(financial_dir) or len(os.listdir(financial_dir)) < 10:
            self.enhancer.batch_fetch_financial(stock_codes[:50], use_akshare=True)
        else:
            print(f"  财务数据已存在: {len(os.listdir(financial_dir))} 个文件")
        
        # 2. 获取行业分类
        print("\n获取行业分类...")
        industry_file = os.path.join(self.data_dir, 'industry', 'industry_classification.csv')
        if not os.path.exists(industry_file):
            self.enhancer.fetch_industry_data_akshare()
        else:
            print(f"  行业分类已存在")
        
        return stock_codes
    
    def train_fundamental_model(self, stock_codes: list):
        """
        训练基本面价值模型
        
        Args:
            stock_codes: 股票代码列表
        """
        print("\n" + "="*60)
        print("2. 训练基本面价值模型")
        print("="*60)
        
        model = FundamentalValueModel(config)
        
        all_financial = []
        all_price = []
        
        for i, code in enumerate(stock_codes[:30]):
            if (i+1) % 10 == 0:
                print(f"  加载进度: {i+1}/{len(stock_codes[:30])}")
            
            financial_file = os.path.join(self.data_dir, 'financial', f"{code}.csv")
            if os.path.exists(financial_file):
                financial_df = pd.read_csv(financial_file)
                financial_df['stock_code'] = code
                all_financial.append(financial_df)
            
            price_files = glob.glob(os.path.join(self.train_dir, f'{code}.csv'))
            if price_files:
                price_df = pd.read_csv(price_files[0])
                price_df['date'] = pd.to_datetime(price_df['date'])
                price_df = price_df.set_index('date')
                all_price.append(price_df)
        
        if not all_financial or not all_price:
            print("  ⚠️ 数据不足，跳过训练")
            return None
        
        financial_data = pd.concat(all_financial, ignore_index=True)
        price_data = pd.concat(all_price)
        
        print(f"  财务数据: {len(financial_data)} 条")
        print(f"  价格数据: {len(price_data)} 条")
        
        try:
            model.train(financial_data, price_data, future_return_horizon=20)
            self.models['fundamental'] = model
            print("  ✅ 基本面模型训练完成")
        except Exception as e:
            print(f"  ⚠️ 训练失败: {e}")
        
        return model
    
    def train_sentiment_model(self, stock_codes: list):
        """
        训练高频情绪模型
        使用分钟数据，如果没有则跳过
        
        Args:
            stock_codes: 股票代码列表
        """
        print("\n" + "="*60)
        print("3. 训练高频情绪模型")
        print("="*60)
        
        minute_dir = os.path.join(self.data_dir, 'minute')
        minute_files = glob.glob(os.path.join(minute_dir, '*.csv'))
        
        if len(minute_files) < 5:
            print("  ⚠️ 分钟数据不足，尝试获取...")
            for code in stock_codes[:10]:
                try:
                    self.enhancer.fetch_minute_data_akshare(code, period='5')
                except:
                    pass
            minute_files = glob.glob(os.path.join(minute_dir, '*.csv'))
        
        if len(minute_files) < 5:
            print("  ⚠️ 分钟数据仍然不足，跳过训练")
            return None
        
        model = HighFrequencySentimentModel(config)
        
        all_minute = []
        for f in minute_files[:20]:
            df = pd.read_csv(f)
            all_minute.append(df)
        
        if all_minute:
            minute_data = pd.concat(all_minute, ignore_index=True)
            print(f"  分钟数据: {len(minute_data)} 条")
            
            try:
                model.train(pd.DataFrame(), minute_data, future_return_horizon=60)
                self.models['sentiment'] = model
                print("  ✅ 情绪模型训练完成")
            except Exception as e:
                print(f"  ⚠️ 训练失败: {e}")
        
        return model if 'sentiment' in self.models else None
    
    def train_fusion_model(self, stock_codes: list):
        """
        训练信号融合模型
        
        Args:
            stock_codes: 股票代码列表
        """
        print("\n" + "="*60)
        print("4. 训练信号融合模型")
        print("="*60)
        
        model = AISignalFusion(config)
        
        # 准备训练数据
        signals = []
        returns = []
        
        for code in stock_codes[:50]:
            price_files = glob.glob(os.path.join(self.train_dir, f'{code}.csv'))
            if not price_files:
                continue
            
            price_df = pd.read_csv(price_files[0])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # 计算简单信号
            price_df['return_5d'] = price_df['close'].pct_change(5)
            price_df['return_10d'] = price_df['close'].pct_change(10)
            price_df['volatility'] = price_df['close'].pct_change().rolling(20).std()
            price_df['volume_ratio'] = price_df['volume'] / price_df['volume'].rolling(20).mean()
            price_df['target'] = price_df['close'].pct_change(5).shift(-5)
            
            df = price_df.dropna()
            if len(df) > 50:
                signals.append(df[['return_5d', 'return_10d', 'volatility', 'volume_ratio']].values)
                returns.append(df['target'].values)
        
        if signals:
            X = np.vstack(signals)
            y = np.concatenate(returns)
            
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=-0.0)
            y = np.clip(y, -0.5, 0.5)
            
            print(f"  训练样本: {len(X)}")
            
            try:
                model.train(X, y)
                self.models['fusion'] = model
                print("  ✅ 融合模型训练完成")
            except Exception as e:
                print(f"  ⚠️ 训练失败: {e}")
        
        return model if 'fusion' in self.models else None
    
    def validate_models(self, stock_codes: list):
        """
        验证模型
        
        Args:
            stock_codes: 股票代码列表
        """
        print("\n" + "="*60)
        print("5. 验证模型")
        print("="*60)
        
        val_codes = self.get_stock_codes(self.val_dir)
        print(f"验证集股票数: {len(val_codes)}")
        
        if 'fusion' in self.models:
            model = self.models['fusion']
            
            predictions = []
            actuals = []
            
            for code in val_codes[:50]:
                price_files = glob.glob(os.path.join(self.val_dir, f'{code}.csv'))
                if not price_files:
                    continue
                
                price_df = pd.read_csv(price_files[0])
                price_df['date'] = pd.to_datetime(price_df['date'])
                
                price_df['return_5d'] = price_df['close'].pct_change(5)
                price_df['return_10d'] = price_df['close'].pct_change(10)
                price_df['volatility'] = price_df['close'].pct_change().rolling(20).std()
                price_df['volume_ratio'] = price_df['volume'] / price_df['volume'].rolling(20).mean()
                price_df['target'] = price_df['close'].pct_change(5).shift(-5)
                
                df = price_df.dropna()
                if len(df) > 20:
                    X = df[['return_5d', 'return_10d', 'volatility', 'volume_ratio']].values
                    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
                    
                    try:
                        pred = model.predict(X)
                        predictions.extend(pred.flatten().tolist())
                        actuals.extend(df['target'].values.tolist())
                    except:
                        pass
            
            if predictions and actuals:
                min_len = min(len(predictions), len(actuals))
                predictions = predictions[:min_len]
                actuals = actuals[:min_len]
                
                corr = np.corrcoef(predictions, actuals)[0, 1]
                print(f"\n验证结果:")
                print(f"  预测与实际相关性: {corr:.4f}")
                
                predictions_arr = np.array(predictions)
                actuals_arr = np.array(actuals)
                top_idx = np.argsort(predictions_arr)[-20:]
                bottom_idx = np.argsort(predictions_arr)[:20]
                
                top_return = actuals_arr[top_idx].mean()
                bottom_return = actuals_arr[bottom_idx].mean()
                print(f"  Top20平均收益: {top_return:.4f}")
                print(f"  Bottom20平均收益: {bottom_return:.4f}")
                print(f"  多空收益差: {top_return - bottom_return:.4f}")
    
    def save_models(self):
        """保存模型"""
        print("\n" + "="*60)
        print("6. 保存模型")
        print("="*60)
        
        import joblib
        
        model_dir = './models/saved/'
        os.makedirs(model_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for name, model in self.models.items():
            model_path = os.path.join(model_dir, f'zz500_{name}_{timestamp}.pkl')
            try:
                joblib.dump(model, model_path)
                print(f"  ✅ {name}模型保存到: {model_path}")
            except Exception as e:
                print(f"  ⚠️ {name}模型保存失败: {e}")
    
    def run(self):
        """运行完整训练流程"""
        print("\n开始训练流程...")
        
        # 1. 准备数据
        stock_codes = self.prepare_data()
        
        if not stock_codes:
            print("❌ 没有找到训练数据")
            return
        
        # 2. 训练各模型
        self.train_fundamental_model(stock_codes)
        self.train_sentiment_model(stock_codes)
        self.train_fusion_model(stock_codes)
        
        # 3. 验证
        self.validate_models(stock_codes)
        
        # 4. 保存
        self.save_models()
        
        print("\n" + "="*60)
        print("✅ 训练完成！")
        print("="*60)


def main():
    trainer = ZZ500Trainer()
    trainer.run()


if __name__ == '__main__':
    main()

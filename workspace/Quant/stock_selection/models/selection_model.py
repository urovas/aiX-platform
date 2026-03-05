# 量化选股模型
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

class StockSelectionModel:
    def __init__(self, config, data_fetcher, factor_calculator):
        """初始化选股模型"""
        self.config = config
        self.data_fetcher = data_fetcher
        self.factor_calculator = factor_calculator
        self.models = {}
    
    def prepare_training_data(self, start_date, end_date):
        """准备训练数据"""
        # 获取股票基本信息
        stock_basic = self.data_fetcher.get_stock_basic()
        if stock_basic.empty:
            print("无法获取股票基本信息")
            return None
        
        # 限制股票数量（避免计算量过大）
        if len(stock_basic) > 1000:
            stock_basic = stock_basic.sample(1000)
        
        training_data = []
        success_count = 0
        fail_count = 0
        
        # 遍历股票
        for i, (_, stock) in enumerate(stock_basic.iterrows()):
            try:
                ts_code = stock.get('ts_code', '')
                if not ts_code:
                    continue
                
                # 获取价格数据
                price_df = self.data_fetcher.get_stock_quote(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if price_df.empty:
                    fail_count += 1
                    continue
                
                # 计算因子
                factors = {}
                
                # 价值因子
                value_factors = self.factor_calculator.calculate_value_factors(price_df)
                factors.update(value_factors)
                
                # 动量因子
                momentum_factors = self.factor_calculator.calculate_momentum_factors(price_df)
                factors.update(momentum_factors)
                
                # 技术因子
                technical_factors = self.factor_calculator.calculate_technical_factors(price_df)
                factors.update(technical_factors)
                
                # 计算未来收益率（标签）
                price_df['future_return'] = price_df['close'].pct_change(20).shift(-20)
                
                # 合并数据
                factor_df = pd.DataFrame(factors)
                factor_df['future_return'] = price_df['future_return'].values
                factor_df['ts_code'] = ts_code
                if 'date' in price_df.columns:
                    factor_df['date'] = price_df['date'].values
                else:
                    factor_df['date'] = price_df.index
                
                # 删除大部分为空的列（非空数据少于50%的列）
                for col in factor_df.columns:
                    if col not in ['ts_code', 'date', 'future_return']:
                        non_null_ratio = factor_df[col].notna().sum() / len(factor_df)
                        if non_null_ratio < 0.5:
                            factor_df.drop(col, axis=1, inplace=True)
                
                # 去除空值
                factor_df = factor_df.dropna()
                
                if not factor_df.empty:
                    training_data.append(factor_df)
                    success_count += 1
                else:
                    fail_count += 1
                        
                # 每50只股票打印一次进度
                if (i + 1) % 50 == 0:
                    print(f"处理进度: {i + 1}/{len(stock_basic)}, 成功: {success_count}, 失败: {fail_count}")
                    
            except Exception as e:
                fail_count += 1
                if fail_count <= 10:  # 只打印前10个错误
                    print(f"处理股票 {ts_code} 时出错: {e}")
                continue
        
        print(f"训练数据准备完成，成功: {success_count}, 失败: {fail_count}")
        
        if not training_data:
            print("无法准备训练数据")
            return None
        
        # 合并所有数据
        full_data = pd.concat(training_data, ignore_index=True)
        return full_data
    
    def train_model(self, X, y, model_type="linear"):
        """训练模型"""
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 训练模型
        if model_type == "linear":
            model = LinearRegression()
        elif model_type == "rf":
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        train_mse = mean_squared_error(y_train, y_pred_train)
        test_mse = mean_squared_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        print(f"模型评估结果 ({model_type}):")
        print(f"训练集 MSE: {train_mse:.4f}, R²: {train_r2:.4f}")
        print(f"测试集 MSE: {test_mse:.4f}, R²: {test_r2:.4f}")
        
        return model
    
    def build_factor_model(self, start_date, end_date):
        """构建因子模型"""
        # 准备训练数据
        training_data = self.prepare_training_data(start_date, end_date)
        if training_data is None:
            return None
        
        # 选择特征列
        feature_cols = [col for col in training_data.columns 
                      if col not in ['future_return', 'ts_code', 'date']]
        
        X = training_data[feature_cols]
        y = training_data['future_return']
        
        # 训练线性回归模型
        linear_model = self.train_model(X, y, model_type="linear")
        self.models['linear'] = linear_model
        
        # 训练随机森林模型
        rf_model = self.train_model(X, y, model_type="rf")
        self.models['rf'] = rf_model
        
        # 保存因子重要性
        if 'rf' in self.models:
            importances = self.models['rf'].feature_importances_
            feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            print("\n因子重要性:")
            print(feature_importance.head(10))
        
        return self.models
    
    def predict_stocks(self, stock_codes, model_type="linear"):
        """预测股票收益率"""
        if model_type not in self.models:
            print(f"模型 {model_type} 未训练")
            return None
        
        model = self.models[model_type]
        predictions = []
        
        for ts_code in stock_codes:
            try:
                # 获取最新价格数据
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
                
                price_df = self.data_fetcher.get_stock_quote(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if price_df.empty:
                    continue
                
                # 计算因子
                factors = {}
                
                # 价值因子
                value_factors = self.factor_calculator.calculate_value_factors(price_df)
                factors.update(value_factors)
                
                # 动量因子
                momentum_factors = self.factor_calculator.calculate_momentum_factors(price_df)
                factors.update(momentum_factors)
                
                # 技术因子
                technical_factors = self.factor_calculator.calculate_technical_factors(price_df)
                factors.update(technical_factors)
                
                # 准备特征
                factor_df = pd.DataFrame(factors)
                factor_df = factor_df.dropna()
                
                if factor_df.empty:
                    continue
                
                # 获取最新因子值
                latest_factors = factor_df.iloc[-1:]
                feature_cols = [col for col in latest_factors.columns]
                X = latest_factors[feature_cols]
                
                # 预测
                predicted_return = model.predict(X)[0]
                
                predictions.append({
                    'ts_code': ts_code,
                    'predicted_return': predicted_return
                })
                
            except Exception as e:
                continue
        
        return predictions
    
    def select_stocks(self, stock_universe, top_n=50, model_type="linear"):
        """选择股票"""
        # 预测收益率
        predictions = self.predict_stocks(stock_universe, model_type=model_type)
        
        if not predictions:
            print("无法预测股票收益率")
            return []
        
        # 按预测收益率排序
        predictions.sort(key=lambda x: x['predicted_return'], reverse=True)
        
        # 选择前N只股票
        selected_stocks = predictions[:top_n]
        
        return selected_stocks
    
    def backtest_strategy(self, start_date, end_date, stock_pool, top_n=50):
        """回测策略"""
        # 获取价格数据
        all_price_data = {}
        for ts_code in stock_pool:
            price_df = self.data_fetcher.get_stock_quote(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if not price_df.empty:
                all_price_data[ts_code] = price_df
        
        if not all_price_data:
            print("无法获取回测数据")
            return None
        
        # 按月回测
        backtest_results = []
        
        # 生成回测日期
        test_dates = pd.date_range(start=start_date, end=end_date, freq='M')
        
        for test_date in test_dates:
            try:
                # 构建训练数据的日期范围
                train_end = test_date - timedelta(days=1)
                train_start = train_end - timedelta(days=365)
                
                # 准备训练数据
                training_data = self.prepare_training_data(
                    start_date=train_start.strftime("%Y%m%d"),
                    end_date=train_end.strftime("%Y%m%d")
                )
                
                if training_data is None:
                    continue
                
                # 训练模型
                feature_cols = [col for col in training_data.columns 
                              if col not in ['future_return', 'ts_code', 'date']]
                X = training_data[feature_cols]
                y = training_data['future_return']
                
                model = LinearRegression()
                model.fit(X, y)
                
                # 预测
                predictions = []
                for ts_code in stock_pool:
                    try:
                        price_df = all_price_data.get(ts_code, None)
                        if price_df is None:
                            continue
                        
                        # 计算因子
                        factors = {}
                        value_factors = self.factor_calculator.calculate_value_factors(price_df)
                        factors.update(value_factors)
                        momentum_factors = self.factor_calculator.calculate_momentum_factors(price_df)
                        factors.update(momentum_factors)
                        technical_factors = self.factor_calculator.calculate_technical_factors(price_df)
                        factors.update(technical_factors)
                        
                        # 准备特征
                        factor_df = pd.DataFrame(factors)
                        factor_df = factor_df.dropna()
                        
                        if factor_df.empty:
                            continue
                        
                        latest_factors = factor_df.iloc[-1:]
                        X_pred = latest_factors[feature_cols]
                        
                        # 预测
                        predicted_return = model.predict(X_pred)[0]
                        predictions.append({
                            'ts_code': ts_code,
                            'predicted_return': predicted_return
                        })
                        
                    except Exception as e:
                        continue
                
                if not predictions:
                    continue
                
                # 选择股票
                predictions.sort(key=lambda x: x['predicted_return'], reverse=True)
                selected_stocks = [p['ts_code'] for p in predictions[:top_n]]
                
                # 计算组合收益率
                portfolio_return = 0
                count = 0
                
                for ts_code in selected_stocks:
                    price_df = all_price_data.get(ts_code, None)
                    if price_df is None:
                        continue
                    
                    # 计算月度收益率
                    monthly_return = price_df['close'].pct_change(20)
                    if not monthly_return.empty:
                        portfolio_return += monthly_return.iloc[-1]
                        count += 1
                
                if count > 0:
                    portfolio_return /= count
                    backtest_results.append({
                        'date': test_date,
                        'return': portfolio_return,
                        'stocks': selected_stocks
                    })
                    
            except Exception as e:
                continue
        
        return backtest_results

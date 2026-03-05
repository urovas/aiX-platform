# 策略执行模块
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ExecutionStrategy:
    def __init__(self, config, data_fetcher, selection_model):
        """初始化执行策略"""
        self.config = config
        self.data_fetcher = data_fetcher
        self.selection_model = selection_model
        
        # 结果目录
        self.result_dir = os.path.join(config.DATA_DIR, "results")
        os.makedirs(self.result_dir, exist_ok=True)
    
    def get_stock_pool(self, universe="CSI300"):
        """获取股票池"""
        # 根据指数获取成分股
        index_map = {
            "CSI300": "000300.SH",
            "CSI500": "000905.SH",
            "CSI1000": "000852.SH",
            "SH50": "000016.SH",
            "SZ50": "399001.SZ"
        }
        
        index_code = index_map.get(universe, "000300.SH")
        
        # 获取指数成分股
        components = self.data_fetcher.get_index_components(index_code)
        
        if components.empty:
            # 如果无法获取指数成分股，使用全市场股票
            stock_basic = self.data_fetcher.get_stock_basic()
            if not stock_basic.empty:
                stock_pool = stock_basic.get('ts_code', stock_basic.get('代码', [])).tolist()
            else:
                stock_pool = []
        else:
            # 从成分股中提取股票代码
            if 'ts_code' in components.columns:
                stock_pool = components['ts_code'].tolist()
            elif '成分券代码' in components.columns:
                # 处理AkShare格式
                stock_pool = []
                for code in components['成分券代码']:
                    # 转换代码格式
                    if str(code).startswith('6'):
                        stock_pool.append(f"{code}.SH")
                    else:
                        stock_pool.append(f"{code}.SZ")
            elif '品种代码' in components.columns:
                # 处理AkShare新格式
                stock_pool = []
                for code in components['品种代码']:
                    # 转换代码格式
                    code_str = str(code)
                    if code_str.startswith('6'):
                        stock_pool.append(f"{code_str}.SH")
                    else:
                        stock_pool.append(f"{code_str}.SZ")
            else:
                stock_pool = []
        
        # 限制股票池大小
        if len(stock_pool) > 500:
            stock_pool = stock_pool[:500]
        
        return stock_pool
    
    def generate_selection(self, universe="CSI300", top_n=50, model_type="linear"):
        """生成选股结果"""
        # 获取股票池
        stock_pool = self.get_stock_pool(universe)
        
        if not stock_pool:
            print("无法获取股票池")
            return None
        
        # 选择股票
        selected_stocks = self.selection_model.select_stocks(
            stock_universe=stock_pool,
            top_n=top_n,
            model_type=model_type
        )
        
        if not selected_stocks:
            print("无法选择股票")
            return None
        
        # 获取股票基本信息
        stock_basic = self.data_fetcher.get_stock_basic()
        
        # 丰富选股结果
        selection_results = []
        for stock in selected_stocks:
            ts_code = stock['ts_code']
            info = {}
            
            # 查找股票基本信息
            if not stock_basic.empty:
                stock_info = stock_basic[stock_basic.get('ts_code', stock_basic.get('代码', '')) == ts_code]
                if not stock_info.empty:
                    info['name'] = stock_info.get('name', stock_info.get('名称', '')).iloc[0]
                    info['industry'] = stock_info.get('industry', stock_info.get('行业', '')).iloc[0]
                    info['area'] = stock_info.get('area', stock_info.get('地区', '')).iloc[0]
            
            # 获取市值
            market_cap = self.data_fetcher.get_market_cap(ts_code)
            if not market_cap.empty:
                info['total_mv'] = market_cap.get('total_mv', market_cap.get('总市值', 0)).iloc[0] / 10000  # 转换为亿
            
            # 合并信息
            selection_results.append({
                'ts_code': ts_code,
                'name': info.get('name', ''),
                'industry': info.get('industry', ''),
                'area': info.get('area', ''),
                'total_mv': info.get('total_mv', 0),
                'predicted_return': stock['predicted_return']
            })
        
        # 转换为DataFrame
        result_df = pd.DataFrame(selection_results)
        
        # 按预测收益率排序
        result_df.sort_values('predicted_return', ascending=False, inplace=True)
        
        # 添加排名
        result_df['rank'] = range(1, len(result_df) + 1)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.result_dir, f"stock_selection_{universe}_{timestamp}.csv")
        result_df.to_csv(file_path, index=False)
        
        print(f"选股结果已保存至: {file_path}")
        return result_df
    
    def create_portfolio(self, selection_results, weight_method="equal"):
        """创建投资组合"""
        if selection_results is None:
            return None
        
        # 计算权重
        if weight_method == "equal":
            # 等权分配
            weight = 1.0 / len(selection_results)
            portfolio = []
            for _, stock in selection_results.iterrows():
                portfolio.append({
                    'ts_code': stock['ts_code'],
                    'name': stock['name'],
                    'weight': weight,
                    'predicted_return': stock['predicted_return']
                })
        elif weight_method == "market_cap":
            # 市值加权
            total_mv = selection_results['total_mv'].sum()
            portfolio = []
            for _, stock in selection_results.iterrows():
                weight = stock['total_mv'] / total_mv if total_mv > 0 else 0
                portfolio.append({
                    'ts_code': stock['ts_code'],
                    'name': stock['name'],
                    'weight': weight,
                    'predicted_return': stock['predicted_return']
                })
        elif weight_method == "return_based":
            # 基于预测收益率加权
            total_pred_return = selection_results['predicted_return'].abs().sum()
            portfolio = []
            for _, stock in selection_results.iterrows():
                weight = abs(stock['predicted_return']) / total_pred_return if total_pred_return > 0 else 0
                portfolio.append({
                    'ts_code': stock['ts_code'],
                    'name': stock['name'],
                    'weight': weight,
                    'predicted_return': stock['predicted_return']
                })
        else:
            # 默认等权
            weight = 1.0 / len(selection_results)
            portfolio = []
            for _, stock in selection_results.iterrows():
                portfolio.append({
                    'ts_code': stock['ts_code'],
                    'name': stock['name'],
                    'weight': weight,
                    'predicted_return': stock['predicted_return']
                })
        
        # 转换为DataFrame
        portfolio_df = pd.DataFrame(portfolio)
        
        # 保存投资组合
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.result_dir, f"portfolio_{timestamp}.csv")
        portfolio_df.to_csv(file_path, index=False)
        
        print(f"投资组合已保存至: {file_path}")
        return portfolio_df
    
    def analyze_industry_distribution(self, selection_results):
        """分析行业分布"""
        if selection_results is None:
            return None
        
        # 计算行业分布
        industry_dist = selection_results['industry'].value_counts()
        
        # 转换为DataFrame
        industry_df = pd.DataFrame({
            'industry': industry_dist.index,
            'count': industry_dist.values,
            'percentage': (industry_dist.values / len(selection_results) * 100).round(2)
        })
        
        # 按数量排序
        industry_df.sort_values('count', ascending=False, inplace=True)
        
        # 保存行业分布
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.result_dir, f"industry_distribution_{timestamp}.csv")
        industry_df.to_csv(file_path, index=False)
        
        print(f"行业分布已保存至: {file_path}")
        return industry_df
    
    def analyze_market_cap_distribution(self, selection_results):
        """分析市值分布"""
        if selection_results is None:
            return None
        
        # 计算市值分布
        selection_results['market_cap_group'] = pd.cut(
            selection_results['total_mv'],
            bins=[0, 100, 300, 500, 1000, float('inf')],
            labels=['<100亿', '100-300亿', '300-500亿', '500-1000亿', '>1000亿']
        )
        
        market_cap_dist = selection_results['market_cap_group'].value_counts()
        
        # 转换为DataFrame
        market_cap_df = pd.DataFrame({
            'market_cap_group': market_cap_dist.index,
            'count': market_cap_dist.values,
            'percentage': (market_cap_dist.values / len(selection_results) * 100).round(2)
        })
        
        # 按市值排序
        market_cap_df = market_cap_df.reindex(['<100亿', '100-300亿', '300-500亿', '500-1000亿', '>1000亿'])
        
        # 保存市值分布
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.result_dir, f"market_cap_distribution_{timestamp}.csv")
        market_cap_df.to_csv(file_path, index=False)
        
        print(f"市值分布已保存至: {file_path}")
        return market_cap_df
    
    def run_full_strategy(self, universe="CSI300", top_n=50, model_type="linear", weight_method="equal"):
        """运行完整策略"""
        print(f"开始运行量化选股策略")
        print(f"股票池: {universe}")
        print(f"选股数量: {top_n}")
        print(f"模型类型: {model_type}")
        print(f"加权方法: {weight_method}")
        print("=" * 60)
        
        # 1. 生成选股结果
        print("1. 生成选股结果...")
        selection_results = self.generate_selection(
            universe=universe,
            top_n=top_n,
            model_type=model_type
        )
        
        if selection_results is None:
            print("选股失败")
            return None
        
        print(f"✓ 选股完成，共选择 {len(selection_results)} 只股票")
        print("\n前10只股票:")
        print(selection_results[['rank', 'name', 'ts_code', 'industry', 'predicted_return']].head(10))
        print()
        
        # 2. 分析行业分布
        print("2. 分析行业分布...")
        industry_dist = self.analyze_industry_distribution(selection_results)
        if industry_dist is not None:
            print("行业分布前10:")
            print(industry_dist.head(10))
            print()
        
        # 3. 分析市值分布
        print("3. 分析市值分布...")
        market_cap_dist = self.analyze_market_cap_distribution(selection_results)
        if market_cap_dist is not None:
            print("市值分布:")
            print(market_cap_dist)
            print()
        
        # 4. 创建投资组合
        print("4. 创建投资组合...")
        portfolio = self.create_portfolio(
            selection_results=selection_results,
            weight_method=weight_method
        )
        
        if portfolio is not None:
            print("投资组合前10:")
            print(portfolio[['name', 'weight', 'predicted_return']].head(10))
            print()
        
        print("=" * 60)
        print("策略运行完成！")
        
        return {
            'selection_results': selection_results,
            'industry_distribution': industry_dist,
            'market_cap_distribution': market_cap_dist,
            'portfolio': portfolio
        }

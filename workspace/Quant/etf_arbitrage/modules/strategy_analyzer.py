#!/usr/bin/env python3
"""
策略分析模块
负责分析ETF溢价/折价套利机会
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class StrategyAnalyzer:
    """
    策略分析类
    """

    def __init__(self, config):
        """
        初始化策略分析器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.strategies = {}

    def calculate_arbitrage_cost(self, operation: str = 'premium') -> float:
        """
        计算套利成本
        
        Args:
            operation: 操作类型 ('premium'溢价套利 或 'discount'折价套利)
            
        Returns:
            float: 套利成本率
        """
        if operation == 'premium':
            cost = self.config.TRADING_FEE_RATE * 2 + self.config.STAMP_DUTY_RATE
        else:
            cost = self.config.TRADING_FEE_RATE * 2
        
        self.logger.debug(f"{operation}套利成本: {cost:.4f}")
        return cost

    def estimate_profit(self, premium_rate: float, operation: str = 'premium') -> float:
        """
        预估套利收益
        
        Args:
            premium_rate: 溢价率（百分比）
            operation: 操作类型
            
        Returns:
            float: 预估收益率
        """
        cost = self.calculate_arbitrage_cost(operation)
        profit = premium_rate / 100 - cost
        
        return profit

    def identify_opportunities(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        识别套利机会
        
        Args:
            data: ETF数据
            
        Returns:
            DataFrame: 套利机会列表
        """
        self.logger.info("识别套利机会...")
        
        opportunities = []
        
        for idx, row in data.iterrows():
            premium_rate = row['premium_rate']
            
            if pd.isna(premium_rate):
                continue
            
            if premium_rate > self.config.PREMIUM_THRESHOLD * 100:
                profit = self.estimate_profit(premium_rate, 'premium')
                
                if profit > self.config.MIN_PROFIT_THRESHOLD:
                    opportunities.append({
                        'date': row['date'],
                        'etf_price': row['close'],
                        'nav': row['nav'],
                        'premium_rate': premium_rate,
                        'operation': 'premium',
                        'estimated_profit': profit,
                        'volume': row['volume'],
                        'amount': row['amount']
                    })
            
            elif premium_rate < -self.config.DISCOUNT_THRESHOLD * 100:
                profit = self.estimate_profit(premium_rate, 'discount')
                
                if profit > self.config.MIN_PROFIT_THRESHOLD:
                    opportunities.append({
                        'date': row['date'],
                        'etf_price': row['close'],
                        'nav': row['nav'],
                        'premium_rate': premium_rate,
                        'operation': 'discount',
                        'estimated_profit': profit,
                        'volume': row['volume'],
                        'amount': row['amount']
                    })
        
        opp_df = pd.DataFrame(opportunities)
        
        if len(opp_df) > 0:
            self.logger.info(f"发现 {len(opp_df)} 个套利机会")
            self.logger.info(f"溢价套利: {len(opp_df[opp_df['operation']=='premium'])} 个")
            self.logger.info(f"折价套利: {len(opp_df[opp_df['operation']=='discount'])} 个")
            self.logger.info(f"平均预估收益: {opp_df['estimated_profit'].mean():.4f}")
        else:
            self.logger.warning("未发现套利机会")
        
        return opp_df

    def calculate_position_size(self, opportunity: Dict) -> float:
        """
        计算持仓规模
        
        Args:
            opportunity: 套利机会信息
            
        Returns:
            float: 持仓规模
        """
        nav = opportunity['nav']
        volume = opportunity['volume']
        amount = opportunity['amount']
        
        max_by_capital = self.config.MAX_POSITION
        max_by_single_trade = self.config.MAX_SINGLE_TRADE
        
        max_by_liquidity = amount * 0.1
        
        position_size = min(max_by_capital, max_by_single_trade, max_by_liquidity)
        
        return position_size

    def generate_trading_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: ETF数据
            
        Returns:
            DataFrame: 包含交易信号的数据
        """
        self.logger.info("生成交易信号...")
        
        data = data.copy()
        
        data['signal'] = 0
        data['position_size'] = 0.0
        data['estimated_profit'] = 0.0
        
        for idx in range(len(data)):
            row = data.iloc[idx]
            
            if row['premium_signal'] == 1:
                profit = self.estimate_profit(row['premium_rate'], 'premium')
                if profit > self.config.MIN_PROFIT_THRESHOLD:
                    data.at[idx, 'signal'] = 1
                    data.at[idx, 'estimated_profit'] = profit
            
            elif row['discount_signal'] == 1:
                profit = self.estimate_profit(row['premium_rate'], 'discount')
                if profit > self.config.MIN_PROFIT_THRESHOLD:
                    data.at[idx, 'signal'] = -1
                    data.at[idx, 'estimated_profit'] = profit
        
        signal_count = (data['signal'] != 0).sum()
        self.logger.info(f"生成 {signal_count} 个交易信号")
        
        return data

    def optimize_thresholds(self, data: pd.DataFrame, 
                         premium_range: Tuple[float, float] = (0.003, 0.02),
                         discount_range: Tuple[float, float] = (0.003, 0.02),
                         steps: int = 10) -> Dict:
        """
        优化套利阈值
        
        Args:
            data: ETF数据
            premium_range: 溢价阈值范围
            discount_range: 折价阈值范围
            steps: 优化步数
            
        Returns:
            Dict: 最优参数
        """
        self.logger.info("开始参数优化...")
        
        best_params = None
        best_sharpe = -float('inf')
        results = []
        
        premium_thresholds = np.linspace(premium_range[0], premium_range[1], steps)
        discount_thresholds = np.linspace(discount_range[0], discount_range[1], steps)
        
        for premium_th in premium_thresholds:
            for discount_th in discount_thresholds:
                self.config.PREMIUM_THRESHOLD = premium_th
                self.config.DISCOUNT_THRESHOLD = discount_th
                
                opp_df = self.identify_opportunities(data)
                
                if len(opp_df) > 0:
                    total_profit = opp_df['estimated_profit'].sum()
                    avg_profit = opp_df['estimated_profit'].mean()
                    std_profit = opp_df['estimated_profit'].std()
                    
                    if std_profit > 0:
                        sharpe = avg_profit / std_profit * np.sqrt(252)
                    else:
                        sharpe = 0
                    
                    results.append({
                        'premium_threshold': premium_th,
                        'discount_threshold': discount_th,
                        'opportunity_count': len(opp_df),
                        'total_profit': total_profit,
                        'avg_profit': avg_profit,
                        'sharpe_ratio': sharpe
                    })
                    
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = {
                            'premium_threshold': premium_th,
                            'discount_threshold': discount_th,
                            'opportunity_count': len(opp_df),
                            'total_profit': total_profit,
                            'avg_profit': avg_profit,
                            'sharpe_ratio': sharpe
                        }
        
        results_df = pd.DataFrame(results)
        
        if best_params is not None:
            self.logger.info(f"最优参数: 溢价阈值={best_params['premium_threshold']:.4f}, "
                         f"折价阈值={best_params['discount_threshold']:.4f}")
            self.logger.info(f"最优夏普比率: {best_params['sharpe_ratio']:.4f}")
            self.logger.info(f"套利机会数: {best_params['opportunity_count']}")
            self.logger.info(f"总收益: {best_params['total_profit']:.4f}")
        else:
            self.logger.warning("参数优化失败，未找到有效参数")
        
        return best_params, results_df

    def analyze_strategy_performance(self, opportunities: pd.DataFrame) -> Dict:
        """
        分析策略性能
        
        Args:
            opportunities: 套利机会数据
            
        Returns:
            Dict: 性能指标
        """
        if len(opportunities) == 0:
            return {}
        
        premium_ops = opportunities[opportunities['operation'] == 'premium']
        discount_ops = opportunities[opportunities['operation'] == 'discount']
        
        metrics = {
            'total_opportunities': len(opportunities),
            'premium_opportunities': len(premium_ops),
            'discount_opportunities': len(discount_ops),
            'avg_estimated_profit': opportunities['estimated_profit'].mean(),
            'total_estimated_profit': opportunities['estimated_profit'].sum(),
            'max_estimated_profit': opportunities['estimated_profit'].max(),
            'min_estimated_profit': opportunities['estimated_profit'].min(),
            'profit_std': opportunities['estimated_profit'].std(),
            'avg_premium_rate': opportunities['premium_rate'].mean(),
            'max_premium_rate': opportunities['premium_rate'].max(),
            'min_premium_rate': opportunities['premium_rate'].min(),
        }
        
        if len(premium_ops) > 0:
            metrics['premium_avg_profit'] = premium_ops['estimated_profit'].mean()
            metrics['premium_avg_rate'] = premium_ops['premium_rate'].mean()
        
        if len(discount_ops) > 0:
            metrics['discount_avg_profit'] = discount_ops['estimated_profit'].mean()
            metrics['discount_avg_rate'] = discount_ops['premium_rate'].mean()
        
        self.logger.info("策略性能分析完成:")
        for key, value in metrics.items():
            self.logger.info(f"  {key}: {value:.4f}")
        
        return metrics

    def save_opportunities(self, opportunities: pd.DataFrame, filename: str = None):
        """
        保存套利机会
        
        Args:
            opportunities: 套利机会数据
            filename: 保存文件名
        """
        if filename is None:
            filename = os.path.join(
                self.config.RESULTS_DIR,
                f'{self.config.ETF_CODE}_opportunities.csv'
            )
        
        try:
            opportunities.to_csv(filename, index=False)
            self.logger.info(f"套利机会已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存套利机会失败: {e}")
    
    def calculate_t0_arbitrage_cost(self) -> float:
        """
        计算T+0折套利成本
        
        Returns:
            float: T+0折套利成本率
        """
        # T+0折套利成本：ETF买入费用 + 成分股卖出费用（含印花税）
        cost = self.config.TRADING_FEE_RATE + (self.config.TRADING_FEE_RATE + self.config.STAMP_DUTY_RATE)
        
        self.logger.debug(f"T+0折套利成本: {cost:.4f}")
        return cost
    
    def identify_t0_arbitrage_opportunities(self, realtime_data: Dict) -> Optional[Dict]:
        """
        识别T+0折套利机会
        
        Args:
            realtime_data: 实时数据
            
        Returns:
            Dict: T+0折套利机会数据
        """
        try:
            if 't0_opportunity' not in realtime_data:
                return None
            
            t0_opportunity = realtime_data['t0_opportunity']
            etf_quote = realtime_data['etf_quote']
            
            # 计算套利成本
            arbitrage_cost = self.calculate_t0_arbitrage_cost()
            
            # 检查是否有套利机会
            if t0_opportunity['profit_rate'] > self.config.MIN_PROFIT_THRESHOLD:
                opportunity = {
                    'date': datetime.now(),
                    'etf_code': etf_quote['code'],
                    'etf_name': etf_quote['name'],
                    'etf_price': etf_quote['price'],
                    'theoretical_nav': t0_opportunity['theoretical_nav'],
                    'discount_rate': t0_opportunity['discount_rate'],
                    'profit_rate': t0_opportunity['profit_rate'],
                    'arbitrage_cost': arbitrage_cost,
                    'stock_coverage': t0_opportunity['stock_coverage'],
                    'volume': etf_quote['volume'],
                    'amount': etf_quote['amount'],
                    'operation': 't0_arbitrage',
                    'timestamp': datetime.now()
                }
                
                self.logger.info(f"发现T+0折套利机会: {etf_quote['code']}, 收益率: {opportunity['profit_rate']:.4f}")
                return opportunity
            else:
                self.logger.info(f"无显著T+0折套利机会: {etf_quote['code']}, 收益率: {t0_opportunity['profit_rate']:.4f}")
                return None
                
        except Exception as e:
            self.logger.error(f"识别T+0折套利机会失败: {e}")
            return None
    
    def analyze_t0_arbitrage_performance(self, opportunities: List[Dict]) -> Dict:
        """
        分析T+0折套利策略性能
        
        Args:
            opportunities: T+0折套利机会列表
            
        Returns:
            Dict: 性能指标
        """
        if not opportunities:
            return {}
        
        metrics = {
            'total_opportunities': len(opportunities),
            'avg_profit_rate': np.mean([opp['profit_rate'] for opp in opportunities]),
            'max_profit_rate': np.max([opp['profit_rate'] for opp in opportunities]),
            'min_profit_rate': np.min([opp['profit_rate'] for opp in opportunities]),
            'profit_std': np.std([opp['profit_rate'] for opp in opportunities]),
            'avg_stock_coverage': np.mean([opp['stock_coverage'] for opp in opportunities]),
            'total_estimated_profit': sum([opp['profit_rate'] for opp in opportunities])
        }
        
        self.logger.info(f"T+0折套利策略分析: 机会数={metrics['total_opportunities']}, 平均收益率={metrics['avg_profit_rate']:.4f}")
        
        return metrics


if __name__ == '__main__':
    import sys
    sys.path.append('..')
    from config import config
    from modules.data_collector import DataCollector
    
    collector = DataCollector(config)
    data = collector.process_all()
    
    if data is not None:
        analyzer = StrategyAnalyzer(config)
        opportunities = analyzer.identify_opportunities(data)
        
        if len(opportunities) > 0:
            analyzer.save_opportunities(opportunities)
            analyzer.analyze_strategy_performance(opportunities)
            
            print("\n套利机会预览:")
            print(opportunities.head(20))

#!/usr/bin/env python3
"""
T+0 ETF 第一批10个因子测试系统
基于13只ETF的日线数据生成模拟15分钟K线，计算因子IC
文件名: t0_10_factor_test.py (修复版)
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import logging
from concurrent.futures import ProcessPoolExecutor
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('t0_10_factor_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class T0FactorTester:
    """T+0第一批10个因子测试器"""
    
    def __init__(self, data_dir='./t0_etf_data'):
        self.data_dir = data_dir
        
        # 13只ETF列表
        self.etf_list = [
            {'code': '513100', 'name': '纳指ETF', 'type': 'cross_border'},
            {'code': '513050', 'name': '中概互联ETF', 'type': 'cross_border'},
            {'code': '513500', 'name': '标普500ETF', 'type': 'cross_border'},
            {'code': '513030', 'name': '德国30ETF', 'type': 'cross_border'},
            {'code': '513880', 'name': '恒生ETF', 'type': 'cross_border'},
            {'code': '518880', 'name': '黄金ETF', 'type': 'gold'},
            {'code': '518800', 'name': '黄金ETF', 'type': 'gold'},
            {'code': '159937', 'name': '黄金ETF', 'type': 'gold'},
            {'code': '518660', 'name': '黄金ETF', 'type': 'gold'},
            {'code': '511010', 'name': '国债ETF', 'type': 'bond'},
            {'code': '511380', 'name': '可转债ETF', 'type': 'bond'},
            {'code': '511220', 'name': '城投债ETF', 'type': 'bond'},
            {'code': '511030', 'name': '国开ETF', 'type': 'bond'},
        ]
        
        # 第一批10个因子定义
        self.factors = self.define_priority_factors()
        
    def define_priority_factors(self):
        """定义第一批10个测试因子"""
        factors = []
        
        # 1. rev_5 - 5日反转
        factors.append({
            'name': 'rev_5',
            'type': 'reversal',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_rev_factor
        })
        
        # 2. rev_10 - 10日反转
        factors.append({
            'name': 'rev_10',
            'type': 'reversal',
            'period_days': 10,
            'period_15min': 160,
            'func': self.calc_rev_factor
        })
        
        # 3. trend_score - 趋势评分
        factors.append({
            'name': 'trend_score',
            'type': 'trend',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_trend_score
        })
        
        # 4. price_reversal - 价格反转因子
        factors.append({
            'name': 'price_reversal',
            'type': 'reversal',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_price_reversal
        })
        
        # 5. volume_ratio - 成交量比率
        factors.append({
            'name': 'volume_ratio',
            'type': 'volume',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_volume_ratio
        })
        
        # 6. WQAlpha1 - WorldQuant Alpha#1
        factors.append({
            'name': 'WQAlpha1',
            'type': 'worldquant',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_wq_alpha1
        })
        
        # 7. WQAlpha4 - WorldQuant Alpha#4
        factors.append({
            'name': 'WQAlpha4',
            'type': 'worldquant',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_wq_alpha4
        })
        
        # 8. fangzheng_vol_price_corr - 量价相关性
        factors.append({
            'name': 'fangzheng_vol_price_corr',
            'type': 'vp',
            'period_days': 10,
            'period_15min': 160,
            'func': self.calc_volume_price_corr
        })
        
        # 9. donghai_money_flow_5 - 5日资金流
        factors.append({
            'name': 'donghai_money_flow_5',
            'type': 'moneyflow',
            'period_days': 5,
            'period_15min': 80,
            'func': self.calc_money_flow
        })
        
        # 10. momentum_factor - 动量因子
        factors.append({
            'name': 'momentum_factor',
            'type': 'momentum',
            'period_days': 6,
            'period_15min': 96,
            'func': self.calc_momentum
        })
        
        return factors
    
    def generate_15min_from_daily(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据生成模拟的15分钟数据
        """
        if daily_df is None or daily_df.empty:
            return None
        
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        daily_df = daily_df.sort_values('date')
        
        periods_per_day = 16  # 每天16个15分钟
        all_15min = []
        
        for idx, row in daily_df.iterrows():
            date = row['date']
            open_price = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            volume = row['volume']
            
            # 生成日内价格路径
            t = np.linspace(0, 1, periods_per_day + 1)
            random_walk = np.cumsum(np.random.randn(periods_per_day + 1) * 0.1)
            price_path = open_price + (close - open_price) * t + random_walk * (high - low) * 0.2
            
            # 成交量分配
            volume_pattern = np.array([1.3, 1.2, 1.1, 1.0, 0.9, 0.9, 1.0, 1.1,
                                       1.2, 1.3, 1.1, 0.9, 0.8, 0.7, 0.7, 0.8])
            volume_pattern = volume_pattern / volume_pattern.sum()
            volume_15min = volume * volume_pattern
            
            # 构建15分钟K线
            for i in range(periods_per_day):
                time_stamp = date + timedelta(hours=9.5 + i * 0.25)
                
                segment_prices = price_path[i:i+2]
                
                row_15min = {
                    'date': time_stamp,
                    'open': segment_prices[0],
                    'high': max(segment_prices),
                    'low': min(segment_prices),
                    'close': segment_prices[1],
                    'volume': volume_15min[i],
                    'amount': segment_prices[1] * volume_15min[i]
                }
                all_15min.append(row_15min)
        
        df_15min = pd.DataFrame(all_15min)
        df_15min['return'] = df_15min['close'].pct_change()
        df_15min['log_return'] = np.log(df_15min['close'] / df_15min['close'].shift(1))
        
        return df_15min
    
    # ============= 因子计算函数 =============
    
    def calc_rev_factor(self, df, period):
        """计算反转因子"""
        return -df['close'].pct_change(period)
    
    def calc_trend_score(self, df, period):
        """计算趋势评分"""
        ma_short = df['close'].rolling(period//2).mean()
        ma_long = df['close'].rolling(period).mean()
        return (ma_short - ma_long) / ma_long
    
    def calc_price_reversal(self, df, period):
        """计算价格反转因子"""
        ret = df['close'].pct_change(period)
        volume_ratio = df['volume'] / df['volume'].rolling(period).mean()
        return -ret * volume_ratio
    
    def calc_volume_ratio(self, df, period):
        """计算成交量比率"""
        return df['volume'] / df['volume'].rolling(period).mean()
    
    def calc_wq_alpha1(self, df, period):
        """WorldQuant Alpha#1"""
        def ts_argmax(x):
            if len(x) < period:
                return np.nan
            return np.argmax(x)
        rolling_max_pos = df['close'].rolling(period).apply(ts_argmax, raw=False)
        return rolling_max_pos / period
    
    def calc_wq_alpha4(self, df, period):
        """WorldQuant Alpha#4"""
        low_rank = df['low'].rank(pct=True)
        ts_rank = low_rank.rolling(period).mean()
        return -ts_rank
    
    def calc_volume_price_corr(self, df, period):
        """计算量价相关性"""
        def rolling_corr(x):
            if len(x) < period:
                return np.nan
            price_change = x['close'].pct_change().dropna()
            volume_change = x['volume'].pct_change().dropna()
            if len(price_change) < 5 or len(volume_change) < 5:
                return np.nan
            return price_change.corr(volume_change)
        
        return df.rolling(period).apply(rolling_corr)
    
    def calc_money_flow(self, df, period):
        """计算资金流因子"""
        money_flow = df['volume'] * (df['close'] - df['open']) / df['close']
        return money_flow.rolling(period).mean()
    
    def calc_momentum(self, df, period):
        """计算动量因子"""
        return df['close'].pct_change(period)
    
    # ============= IC测试函数 =============
    
    def calculate_factor_ic(self, df_15min: pd.DataFrame, factor_def: dict) -> dict:
        """
        计算单个因子的IC值
        """
        try:
            period = factor_def['period_15min']
            
            # 计算因子值
            factor_values = factor_def['func'](df_15min, period)
            
            # 计算未来收益（预测未来1小时 = 4个15分钟）
            pred_period = 4
            future_returns = df_15min['close'].pct_change(pred_period).shift(-pred_period)
            
            # 对齐数据
            valid_mask = ~(factor_values.isna() | future_returns.isna())
            factor_values = factor_values[valid_mask]
            future_returns = future_returns[valid_mask]
            
            if len(factor_values) < 30:
                return {
                    'factor_name': factor_def['name'],
                    'factor_type': factor_def['type'],
                    'period_days': factor_def['period_days'],
                    'ic': 0.0,
                    'p_value': 1.0,
                    'valid_count': len(factor_values),
                    'ic_sharpe': 0.0
                }
            
            # 计算Spearman相关性（IC）
            ic, p_value = spearmanr(factor_values, future_returns)
            
            # 计算IC的稳定性
            ic_values = []
            window = min(100, len(factor_values) // 4)
            for i in range(0, len(factor_values) - window, window//2):
                if i + window <= len(factor_values):
                    ic_win, _ = spearmanr(
                        factor_values[i:i+window], 
                        future_returns[i:i+window]
                    )
                    ic_values.append(ic_win)
            
            ic_sharpe = np.mean(ic_values) / np.std(ic_values) if len(ic_values) > 1 else 0.0
            
            return {
                'factor_name': factor_def['name'],
                'factor_type': factor_def['type'],
                'period_days': factor_def['period_days'],
                'ic': ic,
                'p_value': p_value,
                'valid_count': len(factor_values),
                'ic_sharpe': ic_sharpe
            }
            
        except Exception as e:
            logger.error(f"计算因子{factor_def['name']} IC失败: {e}")
            return {
                'factor_name': factor_def['name'],
                'factor_type': factor_def['type'],
                'period_days': factor_def['period_days'],
                'ic': 0.0,
                'p_value': 1.0,
                'valid_count': 0,
                'ic_sharpe': 0.0
            }
    
    def test_etf_factors(self, etf_info: dict) -> pd.DataFrame:
        """
        测试单只ETF的所有因子
        """
        code = etf_info['code']
        logger.info(f"开始测试 {code} {etf_info['name']}")
        
        # 加载日线数据
        daily_file = f"{self.data_dir}/{code}_daily.csv"
        if not os.path.exists(daily_file):
            logger.warning(f"{code} 日线文件不存在")
            return None
        
        daily_df = pd.read_csv(daily_file)
        
        # 生成15分钟数据
        df_15min = self.generate_15min_from_daily(daily_df)
        if df_15min is None or len(df_15min) < 100:
            logger.warning(f"{code} 生成15分钟数据失败")
            return None
        
        logger.info(f"{code} 生成15分钟数据 {len(df_15min)} 条")
        
        # 计算每个因子的IC
        results = []
        for factor in self.factors:
            ic_result = self.calculate_factor_ic(df_15min, factor)
            
            results.append({
                'etf_code': code,
                'etf_name': etf_info['name'],
                'etf_type': etf_info['type'],
                **ic_result
            })
        
        df_results = pd.DataFrame(results)
        valid_ics = df_results[df_results['ic'].abs() > 0.03]
        logger.info(f"{code} 测试完成，有效因子数: {len(valid_ics)}/{len(self.factors)}")
        
        return df_results
    
    def test_all_etfs(self, max_workers: int = 8):
        """
        并行测试所有ETF
        """
        all_results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_etf = {
                executor.submit(self.test_etf_factors, etf): etf 
                for etf in self.etf_list
            }
            
            for future in future_to_etf:
                etf = future_to_etf[future]
                try:
                    result = future.result(timeout=300)
                    if result is not None and not result.empty:
                        all_results.append(result)
                        logger.info(f"✅ {etf['code']} 测试完成")
                except Exception as e:
                    logger.error(f"测试{etf['code']}异常: {e}")
        
        # 合并结果
        if all_results:
            final_results = pd.concat(all_results, ignore_index=True)
            return final_results
        else:
            return None
    
    def analyze_results(self, results: pd.DataFrame):
        """
        分析测试结果
        """
        logger.info("\n" + "="*70)
        logger.info("T+0第一批10个因子测试结果分析")
        logger.info("="*70)
        
        # 1. 整体统计
        logger.info(f"\n📊 整体统计:")
        logger.info(f"总测试样本: {len(results)}")
        logger.info(f"有效因子样本 (|IC|>0.03): {(results['ic'].abs() > 0.03).sum()}")
        logger.info(f"显著因子 (p<0.05): {(results['p_value'] < 0.05).sum()}")
        
        # 2. 按ETF类型统计
        logger.info(f"\n📈 按ETF类型统计平均IC:")
        for etf_type in results['etf_type'].unique():
            type_results = results[results['etf_type'] == etf_type]
            if len(type_results) > 0:
                mean_ic = type_results['ic'].mean()
                std_ic = type_results['ic'].std()
                pos_ratio = (type_results['ic'] > 0).mean()
                logger.info(f"  {etf_type:15s}: 平均IC={mean_ic:.4f}±{std_ic:.4f}, 正向比率={pos_ratio:.2%}")
        
        # 3. 按因子统计
        logger.info(f"\n🏆 各因子表现:")
        factor_summary = results.groupby(['factor_name', 'factor_type']).agg({
            'ic': ['mean', 'std'],
            'etf_code': 'count',
            'p_value': lambda x: (x < 0.05).mean(),
            'ic_sharpe': 'mean'
        }).round(4)
        
        factor_summary.columns = ['ic_mean', 'ic_std', 'etf_count', 'sig_ratio', 'ic_sharpe']
        factor_summary = factor_summary.sort_values('ic_mean', ascending=False)
        
        for idx, (factor_name, row) in enumerate(factor_summary.iterrows()):
            star = "⭐" if abs(row['ic_mean']) > 0.05 else ""
            logger.info(f"  {idx+1:2d}. {factor_name[0]:25s} IC={row['ic_mean']:.4f}±{row['ic_std']:.4f} "
                       f"出现在{int(row['etf_count']):2d}只ETF中 {star}")
        
        # 4. 找出跨ETF稳定的因子
        logger.info(f"\n🎯 推荐用于T+0的因子:")
        good_factors = factor_summary[
            (factor_summary['ic_mean'].abs() > 0.04) & 
            (factor_summary['etf_count'] >= 5)
        ]
        
        if not good_factors.empty:
            for factor_name, row in good_factors.iterrows():
                logger.info(f"  ✅ {factor_name[0]}: IC={row['ic_mean']:.4f}, "
                           f"{int(row['etf_count'])}只ETF有效, IC夏普={row['ic_sharpe']:.2f}")
        else:
            logger.info("  没有找到符合条件的推荐因子")
        
        # 5. 保存结果
        results.to_csv('t0_10_factor_results.csv', index=False)
        factor_summary.to_csv('t0_10_factor_ranking.csv')
        
        logger.info(f"\n📁 结果已保存:")
        logger.info(f"  - t0_10_factor_results.csv (全部结果)")
        logger.info(f"  - t0_10_factor_ranking.csv (因子排名)")
        
        return factor_summary


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("T+0 ETF 第一批10个因子测试系统启动")
    logger.info("="*70)
    
    # 创建测试器
    tester = T0FactorTester(data_dir='./t0_etf_data')
    
    # 并行测试所有ETF
    logger.info("\n开始并行测试13只ETF...")
    results = tester.test_all_etfs(max_workers=8)
    
    if results is not None:
        # 分析结果
        factor_ranking = tester.analyze_results(results)
        
        # 输出最终推荐
        logger.info("\n" + "="*70)
        logger.info("✅ 测试完成！推荐用于T+0策略的因子：")
        logger.info("="*70)
        
        good_factors = factor_ranking[
            (factor_ranking['ic_mean'].abs() > 0.04) & 
            (factor_ranking['etf_count'] >= 5)
        ]
        
        if not good_factors.empty:
            for factor_name, row in good_factors.iterrows():
                logger.info(f"{factor_name[0]:25s} | IC={row['ic_mean']:.4f} | "
                           f"出现在{int(row['etf_count']):2d}只ETF | IC夏普={row['ic_sharpe']:.2f}")
        else:
            logger.info("没有找到符合条件的推荐因子")
    else:
        logger.error("❌ 测试失败，未获得结果")


if __name__ == "__main__":
    main()
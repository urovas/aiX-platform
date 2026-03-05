#!/usr/bin/env python3
"""
T+0 ETF 策略回测系统(修复版2)
修复了绘图时的日期格式问题
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('t0_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class T0StrategyBacktest:
    """T+0策略回测器"""
    
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
        
        # 6个有效因子权重（基于测试结果）
        self.factor_weights = {
            'donghai_money_flow_5': 0.30,  # IC=0.1123
            'WQAlpha1': 0.25,               # IC=0.1028
            'WQAlpha4': 0.20,                # IC=0.0622, 最稳定
            'momentum_factor': 0.15,          # IC=0.0569
            'rev_5': -0.05,                    # IC=-0.0674 (反向信号)
            'rev_10': -0.05                     # IC=-0.0458 (反向信号)
        }
        
        # 策略参数
        self.params = {
            'lookback_15min': 80,        # 80个15分钟 = 5天
            'holding_period': 4,           # 持有4个15分钟 = 1小时
            'top_n': 3,                     # 每天选前3只ETF
            'stop_loss': 0.005,              # 止损线0.5%
            'take_profit': 0.01,             # 止盈线1.0%
            'commission': 0.00005,            # 佣金万0.5
            'initial_capital': 1000000,       # 初始资金100万
        }
        
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
            
            # 日内波动模式
            morning_vol = 1.2
            afternoon_vol = 0.8
            vol_pattern = np.concatenate([
                np.ones(9) * morning_vol,
                np.ones(8) * afternoon_vol
            ])
            
            random_walk = np.cumsum(np.random.randn(periods_per_day + 1) * 0.1 * vol_pattern)
            
            # 确保价格在high/low范围内
            price_path = open_price + (close - open_price) * t + random_walk * (high - low) * 0.15
            price_path = np.clip(price_path, low * 0.99, high * 1.01)
            
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
                    'amount': segment_prices[1] * volume_15min[i],
                    'code': row.get('code', ''),
                    'name': row.get('name', '')
                }
                all_15min.append(row_15min)
        
        df_15min = pd.DataFrame(all_15min)
        
        # 计算基础指标
        df_15min['return'] = df_15min['close'].pct_change()
        df_15min['log_return'] = np.log(df_15min['close'] / df_15min['close'].shift(1))
        df_15min['vwap'] = (df_15min['close'] * df_15min['volume']).rolling(48).sum() / df_15min['volume'].rolling(48).sum()
        
        return df_15min
    
    # ============= 因子计算函数 =============
    
    def calc_donghai_money_flow_5(self, df, period=80):
        """5日资金流因子"""
        money_flow = df['volume'] * (df['close'] - df['open']) / df['close']
        return money_flow.rolling(period).mean()
    
    def calc_wq_alpha1(self, df, period=80):
        """WorldQuant Alpha#1"""
        def ts_argmax(x):
            if len(x) < period:
                return np.nan
            result = np.argmax(x)
            return result if not np.isnan(result) else np.nan
        rolling_max_pos = df['close'].rolling(period).apply(ts_argmax, raw=False)
        return rolling_max_pos / period
    
    def calc_wq_alpha4(self, df, period=80):
        """WorldQuant Alpha#4"""
        low_rank = df['low'].rank(pct=True)
        ts_rank = low_rank.rolling(period).mean()
        return -ts_rank
    
    def calc_momentum_factor(self, df, period=96):
        """动量因子"""
        return df['close'].pct_change(period)
    
    def calc_rev_5(self, df, period=80):
        """5日反转因子"""
        return -df['close'].pct_change(period)
    
    def calc_rev_10(self, df, period=160):
        """10日反转因子"""
        return -df['close'].pct_change(period)
    
    def calculate_all_factors(self, df_15min: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有6个因子
        """
        df = df_15min.copy()
        
        # 计算每个因子
        df['donghai_money_flow_5'] = self.calc_donghai_money_flow_5(df, self.params['lookback_15min'])
        df['WQAlpha1'] = self.calc_wq_alpha1(df, self.params['lookback_15min'])
        df['WQAlpha4'] = self.calc_wq_alpha4(df, self.params['lookback_15min'])
        df['momentum_factor'] = self.calc_momentum_factor(df, 96)
        df['rev_5'] = self.calc_rev_5(df, self.params['lookback_15min'])
        df['rev_10'] = self.calc_rev_10(df, 160)
        
        # 标准化因子
        factor_cols = ['donghai_money_flow_5', 'WQAlpha1', 'WQAlpha4', 
                      'momentum_factor', 'rev_5', 'rev_10']
        
        for col in factor_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val > 0 and not np.isnan(std_val):
                df[col] = (df[col] - mean_val) / std_val
        
        # 计算综合得分
        df['composite_score'] = 0
        for factor, weight in self.factor_weights.items():
            if factor in df.columns:
                df['composite_score'] += df[factor].fillna(0) * weight
        
        return df
    
    # ============= 回测核心逻辑 =============
    
    def backtest_single_etf(self, etf_info: dict) -> pd.DataFrame:
        """
        回测单只ETF
        """
        code = etf_info['code']
        logger.info(f"开始回测 {code} {etf_info['name']}")
        
        # 加载日线数据
        daily_file = f"{self.data_dir}/{code}_daily.csv"
        if not os.path.exists(daily_file):
            logger.warning(f"{code} 日线文件不存在")
            return None
        
        daily_df = pd.read_csv(daily_file)
        
        # 生成15分钟数据
        df_15min = self.generate_15min_from_daily(daily_df)
        if df_15min is None or len(df_15min) < 500:
            logger.warning(f"{code} 生成15分钟数据失败")
            return None
        
        # 计算因子
        df = self.calculate_all_factors(df_15min)
        
        # 生成交易信号
        df['signal'] = 0
        score_mean = df['composite_score'].rolling(240).mean()
        score_std = df['composite_score'].rolling(240).std()
        df.loc[df['composite_score'] > score_mean + score_std, 'signal'] = 1
        df.loc[df['composite_score'] < score_mean - score_std, 'signal'] = -1
        
        # 回测
        df['position'] = 0
        df['entry_price'] = 0.0
        df['exit_price'] = 0.0
        df['trade_return'] = 0.0
        
        in_position = False
        entry_idx = 0
        entry_price = 0
        
        for i in range(1, len(df)):
            if not in_position and df.loc[i, 'signal'] == 1:
                # 开仓
                in_position = True
                entry_idx = i
                entry_price = df.loc[i, 'close']
                df.loc[i, 'position'] = 1
                df.loc[i, 'entry_price'] = entry_price
            
            elif in_position:
                # 检查平仓条件
                close_signal = False
                current_price = df.loc[i, 'close']
                current_return = (current_price - entry_price) / entry_price
                
                # 条件1：信号反转
                if df.loc[i, 'signal'] == -1:
                    close_signal = True
                
                # 条件2：止损
                if current_return < -self.params['stop_loss']:
                    close_signal = True
                
                # 条件3：止盈
                if current_return > self.params['take_profit']:
                    close_signal = True
                
                # 条件4：最大持有时间
                if i - entry_idx >= self.params['holding_period']:
                    close_signal = True
                
                if close_signal:
                    # 平仓
                    in_position = False
                    df.loc[i, 'position'] = -1
                    df.loc[i, 'exit_price'] = current_price
                    df.loc[i, 'trade_return'] = current_return - self.params['commission'] * 2
        
        # 计算累计收益
        df['strategy_return'] = df['trade_return'].cumsum()
        df['buy_hold_return'] = (df['close'] / df['close'].iloc[0] - 1)
        
        return df
    
    def backtest_all_etfs(self, max_workers: int = 8) -> dict:
        """
        并行回测所有ETF
        """
        all_results = {}
        
        for etf in self.etf_list:
            df = self.backtest_single_etf(etf)
            if df is not None:
                all_results[etf['code']] = {
                    'data': df,
                    'info': etf
                }
                logger.info(f"✅ {etf['code']} 回测完成")
        
        return all_results
    
    def analyze_results(self, all_results: dict):
        """
        分析回测结果
        """
        logger.info("\n" + "="*70)
        logger.info("T+0策略回测结果分析")
        logger.info("="*70)
        
        summary = []
        
        for code, result in all_results.items():
            df = result['data']
            etf_info = result['info']
            
            # 提取交易记录
            trades = df[df['position'] != 0].copy()
            sell_trades = trades[trades['position'] == -1]
            
            if len(sell_trades) == 0:
                continue
            
            # 计算绩效
            total_trades = len(sell_trades)
            win_trades = len(sell_trades[sell_trades['trade_return'] > 0])
            loss_trades = len(sell_trades[sell_trades['trade_return'] <= 0])
            
            win_rate = win_trades / total_trades if total_trades > 0 else 0
            avg_win = sell_trades[sell_trades['trade_return'] > 0]['trade_return'].mean() if win_trades > 0 else 0
            avg_loss = sell_trades[sell_trades['trade_return'] <= 0]['trade_return'].mean() if loss_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            total_return = df['strategy_return'].iloc[-1]
            buy_hold_return = df['buy_hold_return'].iloc[-1]
            
            # 夏普比率
            daily_returns = df.set_index('date')['trade_return'].resample('1D').sum()
            if len(daily_returns) > 1 and daily_returns.std() > 0:
                sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
            else:
                sharpe = 0
            
            # 最大回撤
            cumulative = (1 + df['strategy_return']).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            summary.append({
                'code': code,
                'name': etf_info['name'],
                'type': etf_info['type'],
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'total_return': total_return,
                'buy_hold_return': buy_hold_return,
                'excess_return': total_return - buy_hold_return,
                'sharpe': sharpe,
                'max_drawdown': max_drawdown
            })
            
            # 保存单只ETF的回测图表
            self.plot_etf_results(code, etf_info['name'], df)
        
        # 汇总统计
        df_summary = pd.DataFrame(summary)
        if not df_summary.empty:
            df_summary = df_summary.sort_values('total_return', ascending=False)
            
            logger.info(f"\n📊 各ETF表现汇总:")
            logger.info(f"\n{df_summary.to_string()}")
            
            # 按类型统计
            logger.info(f"\n📈 按ETF类型统计:")
            for etf_type in df_summary['type'].unique():
                type_df = df_summary[df_summary['type'] == etf_type]
                if len(type_df) > 0:
                    logger.info(f"\n{etf_type}:")
                    logger.info(f"  平均收益率: {type_df['total_return'].mean():.2%}")
                    logger.info(f"  平均胜率: {type_df['win_rate'].mean():.2%}")
                    logger.info(f"  平均夏普: {type_df['sharpe'].mean():.2f}")
                    logger.info(f"  平均回撤: {type_df['max_drawdown'].mean():.2%}")
            
            # 保存汇总结果
            df_summary.to_csv('t0_backtest_summary.csv', index=False)
            logger.info(f"\n📁 汇总结果已保存: t0_backtest_summary.csv")
            
            # 绘制总体对比图
            self.plot_overall_comparison(all_results)
        
        return df_summary
    
    def plot_etf_results(self, code, name, df):
        """
        绘制单只ETF的回测结果（修复版）
        """
        try:
            fig, axes = plt.subplots(3, 1, figsize=(14, 10))
            
            # 使用数值索引代替日期，避免日期格式问题
            x = range(len(df))
            
            # 1. 策略收益 vs 买入持有
            cumulative_strategy = (1 + df['strategy_return']).cumprod()
            cumulative_bh = (1 + df['buy_hold_return']).cumprod()
            
            axes[0].plot(x, cumulative_strategy, label='策略收益', linewidth=2)
            axes[0].plot(x, cumulative_bh, label='买入持有', linewidth=2, alpha=0.7)
            axes[0].set_title(f'{code} {name} - T+0策略回测')
            axes[0].set_ylabel('净值')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # 2. 因子综合得分
            axes[1].plot(x, df['composite_score'], label='因子综合得分', color='orange', linewidth=1)
            axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[1].fill_between(x, 0, df['composite_score'], 
                                 where=df['composite_score']>0, color='green', alpha=0.3, interpolate=True)
            axes[1].fill_between(x, 0, df['composite_score'], 
                                 where=df['composite_score']<0, color='red', alpha=0.3, interpolate=True)
            axes[1].set_ylabel('因子得分')
            axes[1].grid(True, alpha=0.3)
            
            # 3. 回撤曲线
            cumulative = (1 + df['strategy_return']).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            axes[2].fill_between(x, 0, drawdown, color='red', alpha=0.3)
            axes[2].set_ylabel('回撤')
            axes[2].set_ylim(drawdown.min() * 1.1, 0)
            axes[2].grid(True, alpha=0.3)
            
            # 只在最后一个图上显示x轴标签
            axes[2].set_xlabel('时间 (15分钟K线)')
            
            plt.tight_layout()
            plt.savefig(f't0_backtest_{code}.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"  图表已保存: t0_backtest_{code}.png")
            
        except Exception as e:
            logger.error(f"  绘制{code}图表失败: {e}")
    
    def plot_overall_comparison(self, all_results):
        """
        绘制所有ETF的对比图（修复版）
        """
        try:
            plt.figure(figsize=(14, 8))
            
            for code, result in all_results.items():
                df = result['data']
                cumulative = (1 + df['strategy_return']).cumprod()
                # 使用数值索引
                plt.plot(range(len(df)), cumulative, label=code, linewidth=1.5, alpha=0.8)
            
            plt.title('所有ETF策略收益对比')
            plt.ylabel('净值')
            plt.xlabel('时间 (15分钟K线)')
            plt.legend(loc='upper left', ncol=2)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('t0_backtest_all.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 总体对比图已保存: t0_backtest_all.png")
            
        except Exception as e:
            logger.error(f"绘制总体对比图失败: {e}")
    
    def optimize_parameters(self, etf_code='518880'):
        """
        参数优化
        """
        logger.info(f"\n🔧 开始参数优化: {etf_code}")
        
        # 获取ETF数据
        etf_info = next((e for e in self.etf_list if e['code'] == etf_code), None)
        if not etf_info:
            return None
        
        daily_file = f"{self.data_dir}/{etf_code}_daily.csv"
        if not os.path.exists(daily_file):
            logger.warning(f"{etf_code} 日线文件不存在")
            return None
        
        daily_df = pd.read_csv(daily_file)
        df_15min = self.generate_15min_from_daily(daily_df)
        if df_15min is None:
            return None
        
        # 待优化的参数
        lookback_range = [40, 60, 80, 100, 120]
        holding_range = [2, 4, 6, 8]
        stop_loss_range = [0.003, 0.005, 0.007, 0.01]
        
        results = []
        total_combinations = len(lookback_range) * len(holding_range) * len(stop_loss_range)
        count = 0
        
        for lookback in lookback_range:
            for holding in holding_range:
                for stop_loss in stop_loss_range:
                    count += 1
                    if count % 10 == 0:
                        logger.info(f"  参数优化进度: {count}/{total_combinations}")
                    
                    # 临时修改参数
                    self.params['lookback_15min'] = lookback
                    self.params['holding_period'] = holding
                    self.params['stop_loss'] = stop_loss
                    
                    # 计算因子
                    df = self.calculate_all_factors(df_15min)
                    
                    # 简化回测
                    df['signal'] = 0
                    score_mean = df['composite_score'].rolling(240).mean()
                    score_std = df['composite_score'].rolling(240).std()
                    df.loc[df['composite_score'] > score_mean + score_std, 'signal'] = 1
                    
                    # 模拟收益
                    returns = []
                    for i in range(len(df) - holding):
                        if df.loc[i, 'signal'] == 1:
                            ret = (df.loc[i+holding, 'close'] - df.loc[i, 'close']) / df.loc[i, 'close']
                            returns.append(ret)
                    
                    if len(returns) > 10:
                        results.append({
                            'lookback': lookback,
                            'holding': holding,
                            'stop_loss': stop_loss,
                            'avg_return': np.mean(returns),
                            'win_rate': np.mean(np.array(returns) > 0),
                            'sharpe': np.mean(returns) / np.std(returns) * np.sqrt(252 * 16) if np.std(returns) > 0 else 0,
                            'trade_count': len(returns)
                        })
        
        if results:
            df_results = pd.DataFrame(results)
            best_idx = df_results['sharpe'].idxmax()
            best = df_results.loc[best_idx]
            
            logger.info(f"\n✅ 最优参数:")
            logger.info(f"  lookback_15min: {int(best['lookback'])}")
            logger.info(f"  holding_period: {int(best['holding'])}")
            logger.info(f"  stop_loss: {best['stop_loss']:.3f}")
            logger.info(f"  预期夏普: {best['sharpe']:.2f}")
            logger.info(f"  胜率: {best['win_rate']:.2%}")
            logger.info(f"  交易次数: {int(best['trade_count'])}")
            
            return best
        else:
            logger.warning("参数优化未获得有效结果")
            return None


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("T+0 ETF 策略回测系统启动")
    logger.info("="*70)
    
    # 创建回测器
    backtester = T0StrategyBacktest(data_dir='./t0_etf_data')
    
    # 1. 参数优化（可选）
    logger.info("\n🔍 步骤1: 参数优化")
    best_params = backtester.optimize_parameters('518880')
    if best_params is not None:
        # 更新参数
        backtester.params['lookback_15min'] = int(best_params['lookback'])
        backtester.params['holding_period'] = int(best_params['holding'])
        backtester.params['stop_loss'] = float(best_params['stop_loss'])
        logger.info(f"\n✅ 使用优化后的参数:")
        logger.info(f"  lookback_15min: {backtester.params['lookback_15min']}")
        logger.info(f"  holding_period: {backtester.params['holding_period']}")
        logger.info(f"  stop_loss: {backtester.params['stop_loss']:.3f}")
    else:
        logger.info("\n⚠️ 使用默认参数继续回测")
    
    # 2. 回测所有ETF
    logger.info("\n📊 步骤2: 开始回测所有ETF")
    all_results = backtester.backtest_all_etfs(max_workers=8)
    
    if all_results:
        # 3. 分析结果
        logger.info("\n📈 步骤3: 分析回测结果")
        summary = backtester.analyze_results(all_results)
        
        logger.info("\n" + "="*70)
        logger.info("✅ 回测完成！")
        logger.info("="*70)
    else:
        logger.error("❌ 回测失败，未获得任何结果")


if __name__ == "__main__":
    main()
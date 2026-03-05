#!/usr/bin/env python3
"""
ETF套利主程序
实时监控ETF溢价/折价套利机会
"""

import sys
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage')

from config import config
from modules.realtime_data_collector import RealtimeDataCollector
from modules.strategy_analyzer import StrategyAnalyzer
from datetime import datetime
import pandas as pd
import time

class ETFArbitrageRunner:
    """
    ETF套利运行器
    """
    
    def __init__(self):
        """初始化运行器"""
        print("="*80)
        print("ETF套利监控系统")
        print("="*80)
        print()
        
        self.collector = RealtimeDataCollector(config)
        self.analyzer = StrategyAnalyzer(config)
        
    def check_market_time(self):
        """检查是否在交易时间"""
        now = datetime.now()
        current_time = now.time()
        
        # 上午交易时间: 9:30-11:30
        # 下午交易时间: 13:00-15:00
        from datetime import time as t
        morning_start = t(9, 30)
        morning_end = t(11, 30)
        afternoon_start = t(13, 0)
        afternoon_end = t(15, 0)
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return is_morning or is_afternoon
    
    def get_etf_realtime_data(self, etf_code):
        """获取ETF实时数据"""
        try:
            # 获取ETF行情（使用akshare）
            quote = self.collector.get_etf_quote_akshare(etf_code)
            
            if quote is None:
                # 尝试使用sina
                quote = self.collector.get_etf_quote_sina(etf_code)
            
            if quote is None:
                return None
            
            # 获取IOPV（使用东方财富）
            iopv = self.collector.get_iopv_eastmoney(etf_code)
            
            if iopv is None:
                # 尝试使用腾讯
                iopv = self.collector.get_iopv_tencent(etf_code)
            
            if iopv is None:
                return None
            
            # 计算溢价率
            premium_rate = (quote['close'] - iopv) / iopv * 100
            
            return {
                'code': etf_code,
                'name': quote.get('name', ''),
                'price': quote['close'],
                'iopv': iopv,
                'premium_rate': premium_rate,
                'volume': quote.get('volume', 0),
                'amount': quote.get('amount', 0),
                'time': datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            print(f"获取{etf_code}数据失败: {e}")
            return None
    
    def analyze_opportunities(self, etf_data):
        """分析套利机会"""
        if etf_data is None:
            return None
        
        premium_rate = etf_data['premium_rate']
        
        # 溢价套利机会
        if premium_rate > config.PREMIUM_THRESHOLD * 100:
            profit = premium_rate / 100 - config.TRADING_FEE_RATE * 2
            return {
                'type': '溢价套利',
                'premium_rate': premium_rate,
                'profit': profit * 100,
                'action': '买入成分股，赎回ETF',
                'profitable': profit > config.MIN_PROFIT_THRESHOLD
            }
        
        # 折价套利机会
        if premium_rate < -config.DISCOUNT_THRESHOLD * 100:
            profit = -premium_rate / 100 - config.TRADING_FEE_RATE * 2
            return {
                'type': '折价套利',
                'premium_rate': premium_rate,
                'profit': profit * 100,
                'action': '买入ETF，赎回成分股',
                'profitable': profit > config.MIN_PROFIT_THRESHOLD
            }
        
        return None
    
    def run_single_scan(self):
        """单次扫描"""
        print(f"\n{'='*80}")
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        opportunities = []
        
        for etf in config.MONITORED_ETFS:
            etf_code = etf['code']
            etf_name = etf['name']
            etf_type = etf['type']
            
            print(f"检查 {etf_name} ({etf_code})...")
            
            # 获取实时数据
            etf_data = self.get_etf_realtime_data(etf_code)
            
            if etf_data is None:
                print(f"  无法获取数据")
                continue
            
            # 显示数据
            print(f"  价格: {etf_data['price']:.3f}")
            print(f"  IOPV: {etf_data['iopv']:.3f}")
            print(f"  溢价率: {etf_data['premium_rate']:.3f}%")
            
            # 分析机会
            opportunity = self.analyze_opportunities(etf_data)
            
            if opportunity:
                print(f"  *** 发现{opportunity['type']}机会! ***")
                print(f"  操作: {opportunity['action']}")
                print(f"  预估收益: {opportunity['profit']:.3f}%")
                
                if opportunity['profitable']:
                    print(f"  >>> 建议执行! <<<")
                    opportunities.append({
                        'code': etf_code,
                        'name': etf_name,
                        'type': etf_type,
                        **etf_data,
                        **opportunity
                    })
            
            print()
        
        # 汇总结果
        print(f"\n{'='*80}")
        print("扫描结果汇总")
        print(f"{'='*80}\n")
        
        if opportunities:
            print(f"发现 {len(opportunities)} 个套利机会:\n")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"{i}. {opp['name']} ({opp['code']})")
                print(f"   类型: {opp['type']}")
                print(f"   溢价率: {opp['premium_rate']:.3f}%")
                print(f"   预估收益: {opp['profit']:.3f}%")
                print(f"   操作: {opp['action']}")
                print()
        else:
            print("未发现套利机会")
        
        return opportunities
    
    def run_continuous(self, interval=5):
        """持续监控"""
        print(f"启动持续监控模式，扫描间隔: {interval}秒")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while True:
                # 检查是否在交易时间
                if not self.check_market_time():
                    print("当前不在交易时间，等待...")
                    time.sleep(60)
                    continue
                
                # 执行扫描
                self.run_single_scan()
                
                # 等待下一次扫描
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n监控已停止")
    
    def run(self, mode='single'):
        """运行"""
        print(f"运行模式: {mode}")
        print()
        
        if mode == 'single':
            return self.run_single_scan()
        elif mode == 'continuous':
            return self.run_continuous()
        else:
            print(f"未知模式: {mode}")
            return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF套利监控系统')
    parser.add_argument('--mode', type=str, default='single', 
                       choices=['single', 'continuous'],
                       help='运行模式: single(单次扫描) 或 continuous(持续监控)')
    parser.add_argument('--interval', type=int, default=5,
                       help='持续监控模式的扫描间隔(秒)')
    
    args = parser.parse_args()
    
    runner = ETFArbitrageRunner()
    
    if args.mode == 'continuous':
        runner.run_continuous(args.interval)
    else:
        runner.run_single_scan()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ETF套利监控(使用东方财富接口)
"""

import sys
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage')

from config import config
from datetime import datetime
import pandas as pd
import requests
import json

class ETFArbitrageEastMoney:
    """
    ETF套利监控(使用东方财富接口)
    """
    
    def __init__(self):
        """初始化"""
        print("="*80)
        print("ETF套利监控系统(东方财富接口)")
        print("="*80)
        print()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_etf_quote(self, etf_code):
        """获取ETF实时行情"""
        try:
            # 判断市场
            if etf_code.startswith('5'):
                secid = f"1.{etf_code}"
            else:
                secid = f"0.{etf_code}"
            
            url = f"http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': secid,
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f55,f57,f58,f60,f170,f171',
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if data and 'data' in data and data['data']:
                d = data['data']
                return {
                    'code': etf_code,
                    'name': d.get('f58', ''),
                    'price': d.get('f43', 0) / 100 if d.get('f43') else 0,
                    'open': d.get('f46', 0) / 100 if d.get('f46') else 0,
                    'high': d.get('f44', 0) / 100 if d.get('f44') else 0,
                    'low': d.get('f45', 0) / 100 if d.get('f45') else 0,
                    'volume': d.get('f47', 0),
                    'amount': d.get('f48', 0),
                    'change_pct': d.get('f170', 0) / 100 if d.get('f170') else 0
                }
            return None
        except Exception as e:
            print(f"获取ETF行情失败: {e}")
            return None
    
    def get_etf_iopv(self, etf_code):
        """获取ETF实时IOPV（估算净值）"""
        try:
            # 判断市场
            if etf_code.startswith('5'):
                secid = f"1.{etf_code}"
            else:
                secid = f"0.{etf_code}"
            
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': secid,
                'fields': 'f51,f52',
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if data and 'data' in data and data['data']:
                d = data['data']
                iopv = d.get('f51', 0) / 100 if d.get('f51') else None
                return iopv
            return None
        except Exception as e:
            print(f"获取IOPV失败: {e}")
            return None
    
    def analyze_opportunity(self, etf_data, iopv):
        """分析套利机会"""
        if etf_data is None or iopv is None:
            return None
        
        price = etf_data['price']
        premium_rate = (price - iopv) / iopv * 100
        
        print(f"  ETF代码: {etf_data['code']}")
        print(f"  ETF名称: {etf_data['name']}")
        print(f"  最新价: {price:.3f}")
        print(f"  IOPV: {iopv:.3f}")
        print(f"  溢价率: {premium_rate:.3f}%")
        print(f"  开盘价: {etf_data['open']:.3f}")
        print(f"  最高价: {etf_data['high']:.3f}")
        print(f"  最低价: {etf_data['low']:.3f}")
        print(f"  成交量: {etf_data['volume']:,.0f}")
        print(f"  成交额: {etf_data['amount']:,.0f}")
        print(f"  日内涨跌: {etf_data['change_pct']:.2f}%")
        
        # 分析套利机会
        if premium_rate > config.PREMIUM_THRESHOLD * 100:
            profit = premium_rate / 100 - config.TRADING_FEE_RATE * 2
            print(f"\n  *** 发现溢价套利机会! ***")
            print(f"  操作: 买入成分股，赎回ETF")
            print(f"  预估收益: {profit*100:.3f}%")
            
            if profit > config.MIN_PROFIT_THRESHOLD:
                print(f"  >>> 建议执行! <<<")
                return {
                    'type': '溢价套利',
                    'premium_rate': premium_rate,
                    'profit': profit * 100,
                    'action': '买入成分股，赎回ETF'
                }
        
        elif premium_rate < -config.DISCOUNT_THRESHOLD * 100:
            profit = -premium_rate / 100 - config.TRADING_FEE_RATE * 2
            print(f"\n  *** 发现折价套利机会! ***")
            print(f"  操作: 买入ETF，赎回成分股")
            print(f"  预估收益: {profit*100:.3f}%")
            
            if profit > config.MIN_PROFIT_THRESHOLD:
                print(f"  >>> 建议执行! <<<")
                return {
                    'type': '折价套利',
                    'premium_rate': premium_rate,
                    'profit': profit * 100,
                    'action': '买入ETF，赎回成分股'
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
            
            print(f"检查 {etf_name} ({etf_code})...")
            
            # 获取ETF行情
            etf_data = self.get_etf_quote(etf_code)
            
            if etf_data is None:
                print(f"  无法获取行情数据")
                print()
                continue
            
            # 获取IOPV
            iopv = self.get_etf_iopv(etf_code)
            
            if iopv is None:
                print(f"  无法获取IOPV数据")
                print()
                continue
            
            # 分析机会
            opportunity = self.analyze_opportunity(etf_data, iopv)
            
            if opportunity:
                opportunities.append({
                    'code': etf_code,
                    'name': etf_name,
                    **etf_data,
                    'iopv': iopv,
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

def main():
    """主函数"""
    runner = ETFArbitrageEastMoney()
    runner.run_single_scan()

if __name__ == "__main__":
    main()

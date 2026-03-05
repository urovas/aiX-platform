#!/usr/bin/env python3
"""
ETF套利监控(使用新浪接口)
"""

import sys
sys.path.append('/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage')

from config import config
from datetime import datetime
import urllib.request
import ssl

class ETFArbitrageSina:
    """
    ETF套利监控(使用新浪接口)
    """
    
    def __init__(self):
        """初始化"""
        print("="*80)
        print("ETF套利监控系统(新浪接口)")
        print("="*80)
        print()
        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
    
    def get_etf_quote_sina(self, etf_code):
        """使用新浪接口获取ETF行情"""
        try:
            # 判断市场
            if etf_code.startswith('5'):
                market = "sh"
            else:
                market = "sz"
            
            url = f"http://hq.sinajs.cn/list={market}{etf_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'http://finance.sina.com.cn'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as response:
                data = response.read().decode('gbk')
            
            # 解析数据
            if '=' not in data or '"' not in data:
                return None
            
            content = data.split('=')[1].strip().strip(';').strip('"')
            fields = content.split(',')
            
            if len(fields) < 32:
                return None
            
            return {
                'code': etf_code,
                'name': fields[0],
                'open': float(fields[1]) if fields[1] else 0,
                'close': float(fields[3]) if fields[3] else 0,
                'high': float(fields[4]) if fields[4] else 0,
                'low': float(fields[5]) if fields[5] else 0,
                'volume': float(fields[8]) if fields[8] else 0,
                'amount': float(fields[9]) if fields[9] else 0,
                'change_pct': float(fields[3]) / float(fields[2]) * 100 - 100 if fields[2] and float(fields[2]) > 0 else 0
            }
        except Exception as e:
            print(f"获取行情失败: {e}")
            return None
    
    def get_etf_iopv(self, etf_code):
        """获取ETF实时IOPV"""
        try:
            if etf_code.startswith('5'):
                secid = f"1.{etf_code}"
            else:
                secid = f"0.{etf_code}"
            
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f51"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            import json
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data and 'data' in data and data['data']:
                iopv = data['data'].get('f51', 0) / 100 if data['data'].get('f51') else None
                return iopv
            return None
        except Exception as e:
            return None
    
    def get_index_quote(self, index_code):
        """获取指数行情(使用新浪接口)"""
        try:
            # 使用新浪接口获取指数行情
            # 中证500指数代码: sh000905
            url = f"http://hq.sinajs.cn/list=sh{index_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'http://finance.sina.com.cn'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as response:
                data = response.read().decode('gbk')
            
            # 解析数据
            if '=' not in data or '"' not in data:
                return None
            
            content = data.split('=')[1].strip().strip(';').strip('"')
            fields = content.split(',')
            
            if len(fields) < 32:
                return None
            
            # 指数当前价格
            price = float(fields[3]) if fields[3] else 0
            
            return {
                'code': index_code,
                'name': fields[0],
                'price': price
            }
        except Exception as e:
            print(f"  获取指数行情失败: {e}")
            return None
    
    def calculate_iopv_local(self, etf_code):
        """本地计算IOPV(通过指数价格估算)"""
        try:
            # 中证500ETF跟踪中证500指数(000905)
            if etf_code == '510500':
                index_data = self.get_index_quote('000905')
                if index_data and index_data['price'] > 0:
                    # 中证500ETF的净值与指数价格有一定比例关系
                    # 简化计算: 使用指数价格/1000作为估算
                    iopv = index_data['price'] / 1000
                    return iopv, index_data['price']
            
            return None, None
        except Exception as e:
            return None, None
    
    def analyze_arbitrage(self, etf_data, iopv, index_price=None):
        """分析套利机会"""
        if etf_data is None:
            return None
        
        price = etf_data['close']
        
        print(f"  ETF代码: {etf_data['code']}")
        print(f"  ETF名称: {etf_data['name']}")
        print(f"  最新价: {price:.3f}")
        
        if iopv and iopv > 0:
            premium_rate = (price - iopv) / iopv * 100
            print(f"  IOPV(估算): {iopv:.3f}")
            if index_price:
                print(f"  中证500指数: {index_price:.2f}")
            print(f"  溢价率: {premium_rate:.3f}%")
            
            # 分析套利机会
            if premium_rate > config.PREMIUM_THRESHOLD * 100:
                profit = premium_rate / 100 - config.TRADING_FEE_RATE * 2
                print(f"\n  *** 发现溢价套利机会! ***")
                print(f"  操作: 买入成分股, 赎回ETF")
                print(f"  预估收益: {profit*100:.3f}%")
                
                if profit > config.MIN_PROFIT_THRESHOLD:
                    print(f"  >>> 建议执行! <<<")
                    return {
                        'type': '溢价套利',
                        'premium_rate': premium_rate,
                        'profit': profit * 100
                    }
            
            elif premium_rate < -config.DISCOUNT_THRESHOLD * 100:
                profit = -premium_rate / 100 - config.TRADING_FEE_RATE * 2
                print(f"\n  *** 发现折价套利机会! ***")
                print(f"  操作: 买入ETF, 赎回成分股")
                print(f"  预估收益: {profit*100:.3f}%")
                
                if profit > config.MIN_PROFIT_THRESHOLD:
                    print(f"  >>> 建议执行! <<<")
                    return {
                        'type': '折价套利',
                        'premium_rate': premium_rate,
                        'profit': profit * 100
                    }
        else:
            print(f"  IOPV: 无法获取")
        
        print(f"  开盘价: {etf_data['open']:.3f}")
        print(f"  最高价: {etf_data['high']:.3f}")
        print(f"  最低价: {etf_data['low']:.3f}")
        print(f"  成交量: {etf_data['volume']:,.0f}")
        print(f"  成交额: {etf_data['amount']:,.0f}")
        print(f"  日内涨跌: {etf_data['change_pct']:.2f}%")
        
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
            etf_data = self.get_etf_quote_sina(etf_code)
            
            if etf_data is None:
                print(f"  无法获取行情数据")
                print()
                continue
            
            # 获取IOPV(先尝试接口, 再本地计算)
            iopv = self.get_etf_iopv(etf_code)
            index_price = None
            
            if iopv is None:
                # 本地计算IOPV
                iopv, index_price = self.calculate_iopv_local(etf_code)
            
            # 分析套利机会
            opportunity = self.analyze_arbitrage(etf_data, iopv, index_price)
            
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
                print()
        else:
            print("未发现套利机会")
        
        print("="*80)
        print("扫描完成")
        print("="*80)
        
        return opportunities

def main():
    """主函数"""
    runner = ETFArbitrageSina()
    runner.run_single_scan()

if __name__ == "__main__":
    main()

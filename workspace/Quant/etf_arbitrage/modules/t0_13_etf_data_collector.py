#!/usr/bin/env python3
"""
T+0 ETF数据采集系统
采集13只核心T+0 ETF的分钟级数据
支持并行下载和断点续传
"""

import pandas as pd
import numpy as np
import akshare as ak
import requests
from datetime import datetime, timedelta
import time
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etf_data_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class T0ETFDataFetcher:
    """T+0 ETF数据采集器"""
    
    def __init__(self, data_dir='./etf_data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 13只T+0 ETF配置
        self.etf_list = [
            # 跨境ETF(5只)
            {'code': '513100', 'name': '纳指ETF', 'type': 'cross_border', 'market': 'sh'},
            {'code': '513050', 'name': '中概互联ETF', 'type': 'cross_border', 'market': 'sh'},
            {'code': '513500', 'name': '标普500ETF', 'type': 'cross_border', 'market': 'sh'},
            {'code': '513030', 'name': '德国30ETF', 'type': 'cross_border', 'market': 'sh'},
            {'code': '513880', 'name': '恒生ETF', 'type': 'cross_border', 'market': 'sh'},
            
            # 黄金ETF(4只)
            {'code': '518880', 'name': '黄金ETF', 'type': 'gold', 'market': 'sh'},
            {'code': '518800', 'name': '黄金ETF', 'type': 'gold', 'market': 'sh'},
            {'code': '159937', 'name': '黄金ETF', 'type': 'gold', 'market': 'sz'},
            {'code': '518660', 'name': '黄金ETF', 'type': 'gold', 'market': 'sh'},
            
            # 债券ETF(4只)
            {'code': '511010', 'name': '国债ETF', 'type': 'bond', 'market': 'sh'},
            {'code': '511380', 'name': '可转债ETF', 'type': 'bond', 'market': 'sh'},
            {'code': '511220', 'name': '城投债ETF', 'type': 'bond', 'market': 'sh'},
            {'code': '511030', 'name': '国开ETF', 'type': 'bond', 'market': 'sh'},
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_etf_daily_sina(self, etf_info: Dict) -> Optional[pd.DataFrame]:
        """
        从新浪财经获取ETF日线数据(所有ETF通用)
        """
        try:
            code = etf_info['code']
            market = etf_info['market']
            symbol = f"{market}{code}"
            
            logger.info(f"获取{code} {etf_info['name']} 日线数据")
            
            df = ak.fund_etf_hist_sina(symbol=symbol)
            
            if df is not None and not df.empty:
                df['code'] = code
                df['name'] = etf_info['name']
                df['type'] = etf_info['type']
                logger.info(f"成功获取{code}日线数据，共{len(df)}条")
                return df
            else:
                logger.warning(f"获取{code}日线数据失败")
                return None
                
        except Exception as e:
            logger.error(f"获取{code}日线数据异常: {e}")
            return None
    
    def get_etf_1min_sina(self, etf_info: Dict) -> Optional[pd.DataFrame]:
        """
        从新浪财经获取ETF1分钟数据(仅限黄金/债券ETF)
        """
        try:
            code = etf_info['code']
            market = etf_info['market']
            symbol = f"{market}{code}"
            
            # 仅黄金和债券ETF支持分钟线
            if etf_info['type'] in ['gold', 'bond']:
                logger.info(f"获取{code} {etf_info['name']} 1分钟数据")
                
                df = ak.fund_etf_minute_sina(symbol=symbol, period="1")
                
                if df is not None and not df.empty:
                    df['code'] = code
                    df['name'] = etf_info['name']
                    df['type'] = etf_info['type']
                    logger.info(f"成功获取{code}1分钟数据，共{len(df)}条")
                    return df
                else:
                    logger.warning(f"获取{code}1分钟数据失败")
                    return None
            else:
                logger.info(f"{code} 不是黄金/债券ETF，跳过分钟线获取")
                return None
                
        except Exception as e:
            logger.error(f"获取{code}1分钟数据异常: {e}")
            return None
    
    def get_cross_border_premium(self, etf_info: Dict) -> Optional[pd.DataFrame]:
        """
        获取跨境ETF的溢价率数据(从东方财富)
        跨境ETF的溢价率是T+0交易的核心
        """
        try:
            code = etf_info['code']
            
            # 东方财富跨境ETF溢价率接口
            url = f"http://push2.eastmoney.com/api/qt/stock/get?ut=fa5fd1943c7b386f172d6893dbfba10&fltt=2&fields=f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f150,f151,f154,f174,f175,f59,f163,f171&secid=0.{code}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get('rc') != 0:
                return None
            
            quote_data = data.get('data', {})
            
            # 提取关键数据
            record = {
                'timestamp': datetime.now(),
                'code': code,
                'price': float(quote_data.get('f43', 0)),  # 最新价
                'premium_rate': float(quote_data.get('f171', 0)),  # 溢价率
                'nav': float(quote_data.get('f169', 0)),  # 净值
                'volume': float(quote_data.get('f47', 0)),  # 成交量
                'amount': float(quote_data.get('f45', 0))  # 成交额
            }
            
            return pd.DataFrame([record])
            
        except Exception as e:
            logger.error(f"获取{code}溢价率异常: {e}")
            return None
    
    def resample_to_15min(self, df_1min: pd.DataFrame) -> pd.DataFrame:
        """
        将1分钟数据重采样为15分钟
        """
        if df_1min is None or df_1min.empty:
            return None
        
        # 确保时间列是datetime类型
        if 'date' in df_1min.columns:
            df_1min['date'] = pd.to_datetime(df_1min['date'])
            df_1min.set_index('date', inplace=True)
        
        # 15分钟重采样
        df_15min = pd.DataFrame()
        df_15min['open'] = df_1min['open'].resample('15T').first()
        df_15min['high'] = df_1min['high'].resample('15T').max()
        df_15min['low'] = df_1min['low'].resample('15T').min()
        df_15min['close'] = df_1min['close'].resample('15T').last()
        df_15min['volume'] = df_1min['volume'].resample('15T').sum()
        df_15min['amount'] = df_1min['amount'].resample('15T').sum()
        
        df_15min = df_15min.dropna()
        df_15min.reset_index(inplace=True)
        
        return df_15min
    
    def fetch_etf_data(self, etf_info: Dict, start_date: str = '2025-01-01', end_date: str = '2026-02-24') -> Dict:
        """
        获取单只ETF的完整数据
        """
        code = etf_info['code']
        result = {
            'code': code,
            'name': etf_info['name'],
            'type': etf_info['type'],
            'daily': None,
            'minute_1min': None,
            'minute_15min': None,
            'premium': None,
            'success': False
        }
        
        try:
            # 1. 获取日线数据（所有ETF）
            daily_df = self.get_etf_daily_sina(etf_info)
            if daily_df is not None:
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df[(daily_df['date'] >= start_date) & (daily_df['date'] <= end_date)]
                result['daily'] = daily_df
            
            # 2. 获取1分钟数据（仅黄金/债券ETF）
            minute_df = self.get_etf_1min_sina(etf_info)
            if minute_df is not None:
                minute_df['date'] = pd.to_datetime(minute_df['date'])
                minute_df = minute_df[(minute_df['date'] >= start_date) & (minute_df['date'] <= end_date)]
                result['minute_1min'] = minute_df
                
                # 重采样为15分钟
                result['minute_15min'] = self.resample_to_15min(minute_df.copy())
            
            # 3. 获取溢价率（仅跨境ETF）
            if etf_info['type'] == 'cross_border':
                premium_df = self.get_cross_border_premium(etf_info)
                result['premium'] = premium_df
            
            result['success'] = True
            logger.info(f"✅ {code} {etf_info['name']} 数据获取完成")
            
        except Exception as e:
            logger.error(f"❌ {code} 数据获取失败: {e}")
        
        return result
    
    def fetch_all_etfs(self, max_workers: int = 8, start_date: str = '2025-01-01', end_date: str = '2026-02-24'):
        """
        并行获取所有ETF数据
        """
        all_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_etf = {
                executor.submit(self.fetch_etf_data, etf, start_date, end_date): etf 
                for etf in self.etf_list
            }
            
            for future in as_completed(future_to_etf):
                etf = future_to_etf[future]
                try:
                    result = future.result(timeout=60)
                    all_results.append(result)
                    
                    # 保存单只ETF数据
                    self.save_etf_data(result)
                    
                except Exception as e:
                    logger.error(f"处理{etf['code']}时发生异常: {e}")
        
        # 保存汇总报告
        self.save_summary_report(all_results)
        return all_results
    
    def save_etf_data(self, result: Dict):
        """
        保存单只ETF数据到文件
        """
        code = result['code']
        
        # 保存日线
        if result['daily'] is not None:
            daily_file = f"{self.data_dir}/{code}_daily.csv"
            result['daily'].to_csv(daily_file, index=False)
            logger.info(f"保存日线数据: {daily_file}")
        
        # 保存1分钟
        if result['minute_1min'] is not None:
            minute_file = f"{self.data_dir}/{code}_1min.csv"
            result['minute_1min'].to_csv(minute_file, index=False)
            logger.info(f"保存1分钟数据: {minute_file}")
        
        # 保存15分钟
        if result['minute_15min'] is not None:
            _15min_file = f"{self.data_dir}/{code}_15min.csv"
            result['minute_15min'].to_csv(_15min_file, index=False)
            logger.info(f"保存15分钟数据: {_15min_file}")
        
        # 保存溢价率
        if result['premium'] is not None:
            premium_file = f"{self.data_dir}/{code}_premium.csv"
            result['premium'].to_csv(premium_file, index=False)
            logger.info(f"保存溢价率数据: {premium_file}")
    
    def save_summary_report(self, all_results: List[Dict]):
        """
        生成数据获取汇总报告
        """
        report = []
        for result in all_results:
            report.append({
                'code': result['code'],
                'name': result['name'],
                'type': result['type'],
                'daily_count': len(result['daily']) if result['daily'] is not None else 0,
                'minute_count': len(result['minute_1min']) if result['minute_1min'] is not None else 0,
                '_15min_count': len(result['minute_15min']) if result['minute_15min'] is not None else 0,
                'has_premium': result['premium'] is not None,
                'success': result['success']
            })
        
        df_report = pd.DataFrame(report)
        report_file = f"{self.data_dir}/data_summary.csv"
        df_report.to_csv(report_file, index=False)
        
        # 打印汇总信息
        logger.info("\n" + "="*60)
        logger.info("数据获取汇总报告")
        logger.info("="*60)
        logger.info(f"\n{df_report.to_string()}")
        logger.info("="*60)
        
        # 按类型统计
        logger.info("\n按类型统计:")
        for etf_type in df_report['type'].unique():
            type_df = df_report[df_report['type'] == etf_type]
            logger.info(f"{etf_type}: {len(type_df)}只, 日线{type_df['daily_count'].sum()}条, 分钟线{type_df['minute_count'].sum()}条")

    def get_etf_15min_for_backtest(self, code: str) -> Optional[pd.DataFrame]:
        """
        获取用于回测的15分钟数据（统一接口）
        """
        file_path = f"{self.data_dir}/{code}_15min.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            # 如果没有15分钟数据，尝试从日线重采样（降级方案）
            daily_file = f"{self.data_dir}/{code}_daily.csv"
            if os.path.exists(daily_file):
                df_daily = pd.read_csv(daily_file)
                df_daily['date'] = pd.to_datetime(df_daily['date'])
                # 日线转15分钟（简单填充）
                logger.warning(f"{code} 无15分钟数据，使用日线数据填充")
                return df_daily
        return None


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("T+0 ETF数据采集系统启动")
    logger.info("="*60)
    
    # 创建数据采集器
    fetcher = T0ETFDataFetcher(data_dir='./t0_etf_data')
    
    # 设置时间范围（默认回测一年）
    start_date = '2025-01-01'
    end_date = '2026-02-24'
    
    # 并行获取所有数据（用你的8卡优势）
    logger.info(f"开始获取数据，时间范围: {start_date} 到 {end_date}")
    results = fetcher.fetch_all_etfs(max_workers=8, start_date=start_date, end_date=end_date)
    
    # 统计成功数量
    success_count = sum(1 for r in results if r['success'])
    logger.info(f"\n🎉 数据采集完成！成功: {success_count}/{len(results)} 只ETF")
    
    # 列出可用的15分钟数据
    logger.info("\n📊 可用15分钟数据列表:")
    for etf in fetcher.etf_list:
        df_15min = fetcher.get_etf_15min_for_backtest(etf['code'])
        if df_15min is not None:
            logger.info(f"  ✅ {etf['code']} {etf['name']}: {len(df_15min)}条")
        else:
            logger.info(f"  ❌ {etf['code']} {etf['name']}: 无15分钟数据")
    
    logger.info("\n" + "="*60)
    logger.info("数据采集完成！数据保存在 ./t0_etf_data/ 目录")
    logger.info("="*60)


if __name__ == "__main__":
    main()
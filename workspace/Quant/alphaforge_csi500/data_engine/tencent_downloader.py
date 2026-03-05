# 腾讯数据源下载器
# 使用腾讯财经API下载股票数据

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
import time
import requests
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')


class TencentDownloader:
    """
    腾讯数据源下载器
    使用腾讯财经API获取股票数据
    """
    
    def __init__(self, data_dir: str = './data/'):
        """
        初始化下载器
        
        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print("✅ 腾讯数据源下载器初始化完成")
    
    def download_daily(self, 
                      stock_code: str, 
                      start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        下载日线数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            df: 日线数据
        """
        # 转换股票代码格式
        tencent_code = self._to_tencent_code(stock_code)
        
        # 腾讯API接口
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        
        # 腾讯API最多返回500条，需要分段下载
        all_klines = []
        periods = [
            ('2020-01-01', '2021-12-31'),
            ('2022-01-01', '2023-12-31'),
            ('2024-01-01', '2025-12-31')
        ]
        
        try:
            for start, end in periods:
                params = {
                    'param': f"{tencent_code},day,{start},{end},500,qfq"
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=30)
                data = response.json()
                
                # 解析数据
                stock_data = data.get('data', {})
                if isinstance(stock_data, dict) and tencent_code in stock_data:
                    klines = stock_data[tencent_code].get('qfqday', [])
                    if klines:
                        all_klines.extend(klines)
                
                time.sleep(0.1)  # 限速
            
            if not all_klines:
                return pd.DataFrame()
            
            # 去重（同一日期可能出现在多个时间段）
            seen_dates = set()
            unique_klines = []
            for kline in all_klines:
                date = kline[0]
                if date not in seen_dates:
                    seen_dates.add(date)
                    unique_klines.append(kline)
            
            # 转换为DataFrame - 使用数据实际列数
            df = pd.DataFrame(unique_klines)
            
            # 根据实际列数设置列名
            if df.shape[1] == 6:
                df.columns = ['date', 'open', 'close', 'low', 'high', 'volume']
            elif df.shape[1] == 7:
                df.columns = ['date', 'open', 'close', 'low', 'high', 'volume', 'amount']
            else:
                # 如果列数不对，返回空
                return pd.DataFrame()
            
            # 数据类型转换
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'close', 'low', 'high', 'volume']:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            
            # 计算其他字段
            df['change_pct'] = df['close'].pct_change() * 100
            if 'amount' not in df.columns:
                df['amount'] = df['close'] * df['volume']
            df['stock_code'] = stock_code
            
            # 过滤日期
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            
            # 去重
            df = df.drop_duplicates(subset=['date'], keep='first')
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            return pd.DataFrame()
    
    def download_batch(self,
                      stock_codes: List[str],
                      start_date: str = None,
                      end_date: str = None,
                      save: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量下载股票数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            
        Returns:
            data_dict: 数据字典
        """
        print(f"\n批量下载 {len(stock_codes)} 只股票")
        print(f"时间范围: {start_date or '2020-01-01'} ~ {end_date or '2025-12-31'}")
        print("-" * 60)
        
        data_dict = {}
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(stock_codes, 1):
            if i % 100 == 0 or i == 1:
                print(f"\n进度: [{i}/{len(stock_codes)}] 成功: {success_count} 失败: {fail_count}")
            
            df = self.download_daily(code, start_date, end_date)
            
            if not df.empty and len(df) > 100:  # 至少100条数据才算成功
                data_dict[code] = df
                success_count += 1
                
                # 保存数据
                if save:
                    self._save_daily_data(df, code)
            else:
                fail_count += 1
            
            # 限速 - 每10只休息1秒
            if i % 10 == 0:
                time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"批量下载完成: 成功 {success_count}/{len(stock_codes)}")
        print(f"{'='*60}")
        return data_dict
    
    def download_index(self,
                      index_code: str,
                      start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        下载指数数据
        
        Args:
            index_code: 指数代码 (如: 000300)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            df: 指数数据
        """
        print(f"下载指数数据: {index_code}")
        
        # 转换指数代码
        if index_code.startswith('0') or index_code.startswith('3'):
            tencent_code = f"sh{index_code}"
        else:
            tencent_code = f"sz{index_code}"
        
        url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        
        all_klines = []
        periods = [
            ('2020-01-01', '2021-12-31'),
            ('2022-01-01', '2023-12-31'),
            ('2024-01-01', '2025-12-31')
        ]
        
        try:
            for start, end in periods:
                params = {
                    'param': f"{tencent_code},day,{start},{end},500"
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=30)
                data = response.json()
                
                stock_data = data.get('data', {})
                if isinstance(stock_data, dict) and tencent_code in stock_data:
                    klines = stock_data[tencent_code].get('day', [])
                    if klines:
                        all_klines.extend(klines)
                
                time.sleep(0.1)
            
            if not all_klines:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 去重
            seen_dates = set()
            unique_klines = []
            for kline in all_klines:
                date = kline[0]
                if date not in seen_dates:
                    seen_dates.add(date)
                    unique_klines.append(kline)
            
            df = pd.DataFrame(unique_klines)
            if df.shape[1] >= 6:
                df.columns = ['date', 'open', 'close', 'low', 'high', 'volume'] + [f'col_{i}' for i in range(6, df.shape[1])]
            
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'close', 'low', 'high', 'volume']:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            
            df['change_pct'] = df['close'].pct_change() * 100
            df['index_code'] = index_code
            
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            
            df = df.drop_duplicates(subset=['date'], keep='first')
            df = df.sort_values('date').reset_index(drop=True)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            
            # 保存
            output_path = os.path.join(self.data_dir, f"index_{index_code}_{start_date or '2020-01-01'}_{end_date or '2025-12-31'}.csv")
            df.to_csv(output_path, index=False)
            
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def _to_tencent_code(self, stock_code: str) -> str:
        """
        转换为腾讯股票代码格式
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            
        Returns:
            tencent_code: 腾讯格式 (如: sz000001)
        """
        if '.' in stock_code:
            code, exchange = stock_code.split('.')
            if exchange == 'SZ':
                return f"sz{code}"
            elif exchange == 'SH':
                return f"sh{code}"
            elif exchange == 'BJ':
                return f"bj{code}"
        return stock_code
    
    def _save_daily_data(self, df: pd.DataFrame, stock_code: str):
        """保存日线数据"""
        if df.empty:
            return
        
        start_date = df['date'].min().strftime('%Y-%m-%d')
        end_date = df['date'].max().strftime('%Y-%m-%d')
        
        output_path = os.path.join(self.data_dir, f"stock_quote_{stock_code}_{start_date}_{end_date}.csv")
        
        # 添加原始列名映射
        df_save = df.copy()
        df_save['code'] = df_save['stock_code'].apply(lambda x: x.split('.')[0] if '.' in x else x)
        df_save['trade_date'] = df_save['date']
        df_save['preclose'] = df_save['close'].shift(1)
        df_save['pctChg'] = df_save['change_pct']
        df_save['turn'] = 0.0  # 腾讯数据没有换手率
        df_save['tradestatus'] = 1
        df_save['adjustflag'] = 3
        
        # 估值指标（腾讯数据没有，设为0）
        df_save['peTTM'] = 0.0
        df_save['pbMRQ'] = 0.0
        df_save['psTTM'] = 0.0
        df_save['pcfNcfTTM'] = 0.0
        
        df_save.to_csv(output_path, index=False)


# 便捷函数
def download_stock(stock_code: str, 
                  start_date: str = '2020-01-01',
                  end_date: str = '2025-12-31',
                  data_dir: str = './data/') -> pd.DataFrame:
    """
    便捷函数：下载单只股票
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        df: 股票数据
    """
    downloader = TencentDownloader(data_dir)
    return downloader.download_daily(stock_code, start_date, end_date)


def download_stocks(stock_codes: List[str],
                   start_date: str = '2020-01-01',
                   end_date: str = '2025-12-31',
                   data_dir: str = './data/') -> Dict[str, pd.DataFrame]:
    """
    便捷函数：批量下载股票
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        data_dict: 数据字典
    """
    downloader = TencentDownloader(data_dir)
    return downloader.download_batch(stock_codes, start_date, end_date)

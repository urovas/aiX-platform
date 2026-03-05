# 数据获取模块

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import os
import json
import warnings
from datetime import datetime, timedelta
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings('ignore')


class DataLoader:
    """
    统一数据获取模块
    支持多种数据源：数据库、API、文件、缓存
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据加载器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 数据源配置
        self.data_sources = {
            'database': self.config.get('database', {}),
            'api': self.config.get('api', {}),
            'file': self.config.get('file', {}),
            'cache': self.config.get('cache', {})
        }
        
        # 数据库连接池
        self.db_connections = {}
        
        # API会话
        self.api_session = None
        
        # 数据缓存
        self.cache = {}
        
        # 数据目录
        self.data_dir = self.config.get('data_dir', './data/')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4))
        
        print("✅ 数据加载器初始化完成")
    
    def load_tick_data(self, 
                       stock_code: str, 
                       start_date: str, 
                       end_date: str,
                       source: str = 'file') -> pd.DataFrame:
        """
        加载逐笔交易数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            source: 数据源 ('database', 'api', 'file', 'cache')
            
        Returns:
            tick_data: 逐笔交易数据
        """
        print(f"加载逐笔交易数据: {stock_code} ({start_date} ~ {end_date})")
        
        # 检查缓存
        cache_key = f"tick_{stock_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        # 根据数据源加载
        if source == 'file':
            data = self._load_from_file('tick', stock_code, start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('tick', stock_code, start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('tick', stock_code, start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        # 缓存数据
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_minute_data(self,
                        stock_code: str,
                        start_date: str,
                        end_date: str,
                        source: str = 'file') -> pd.DataFrame:
        """
        加载分钟级数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            minute_data: 分钟级数据
        """
        print(f"加载分钟级数据: {stock_code} ({start_date} ~ {end_date})")
        
        cache_key = f"minute_{stock_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('minute', stock_code, start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('minute', stock_code, start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('minute', stock_code, start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_daily_data(self,
                       stock_code: str,
                       start_date: str,
                       end_date: str,
                       source: str = 'file') -> pd.DataFrame:
        """
        加载日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            daily_data: 日线数据
        """
        print(f"加载日线数据: {stock_code} ({start_date} ~ {end_date})")
        
        cache_key = f"daily_{stock_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('daily', stock_code, start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('daily', stock_code, start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('daily', stock_code, start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_financial_data(self,
                           stock_code: str,
                           start_date: str,
                           end_date: str,
                           source: str = 'file') -> pd.DataFrame:
        """
        加载财务数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            financial_data: 财务数据
        """
        print(f"加载财务数据: {stock_code} ({start_date} ~ {end_date})")
        
        cache_key = f"financial_{stock_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('financial', stock_code, start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('financial', stock_code, start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('financial', stock_code, start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_order_book_data(self,
                            stock_code: str,
                            start_date: str,
                            end_date: str,
                            source: str = 'file') -> pd.DataFrame:
        """
        加载订单簿数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            order_book_data: 订单簿数据
        """
        print(f"加载订单簿数据: {stock_code} ({start_date} ~ {end_date})")
        
        cache_key = f"order_book_{stock_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('order_book', stock_code, start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('order_book', stock_code, start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('order_book', stock_code, start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_market_data(self,
                        start_date: str,
                        end_date: str,
                        source: str = 'file') -> pd.DataFrame:
        """
        加载市场整体数据（指数、板块等）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            market_data: 市场数据
        """
        print(f"加载市场数据: ({start_date} ~ {end_date})")
        
        cache_key = f"market_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('market', 'market', start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('market', 'market', start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('market', 'market', start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def load_industry_data(self,
                          start_date: str,
                          end_date: str,
                          source: str = 'file') -> pd.DataFrame:
        """
        加载行业数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            industry_data: 行业数据
        """
        print(f"加载行业数据: ({start_date} ~ {end_date})")
        
        cache_key = f"industry_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"  从缓存加载")
            return self.cache[cache_key]
        
        if source == 'file':
            data = self._load_from_file('industry', 'industry', start_date, end_date)
        elif source == 'database':
            data = self._load_from_database('industry', 'industry', start_date, end_date)
        elif source == 'api':
            data = self._load_from_api('industry', 'industry', start_date, end_date)
        else:
            raise ValueError(f"未知的数据源: {source}")
        
        if data is not None and len(data) > 0:
            self.cache[cache_key] = data
        
        return data
    
    def _load_from_file(self, 
                        data_type: str, 
                        stock_code: str, 
                        start_date: str, 
                        end_date: str) -> pd.DataFrame:
        """
        从文件加载数据
        
        Args:
            data_type: 数据类型
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            data: 数据DataFrame
        """
        # 构建文件路径
        file_path = os.path.join(self.data_dir, data_type, f"{stock_code}.parquet")
        
        if not os.path.exists(file_path):
            # 尝试CSV格式
            file_path = os.path.join(self.data_dir, data_type, f"{stock_code}.csv")
            
            if not os.path.exists(file_path):
                print(f"  ⚠️ 文件不存在: {file_path}")
                return pd.DataFrame()
        
        try:
            if file_path.endswith('.parquet'):
                data = pd.read_parquet(file_path)
            else:
                data = pd.read_csv(file_path)
            
            # 过滤日期范围
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
            elif 'datetime' in data.columns:
                data['datetime'] = pd.to_datetime(data['datetime'])
                data = data[(data['datetime'] >= start_date) & (data['datetime'] <= end_date)]
            elif 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]
            
            print(f"  ✅ 从文件加载: {len(data)} 条记录")
            return data
            
        except Exception as e:
            print(f"  ❌ 加载文件失败: {e}")
            return pd.DataFrame()
    
    def _load_from_database(self,
                           data_type: str,
                           stock_code: str,
                           start_date: str,
                           end_date: str) -> pd.DataFrame:
        """
        从数据库加载数据
        
        Args:
            data_type: 数据类型
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            data: 数据DataFrame
        """
        db_config = self.data_sources['database']
        
        if not db_config:
            print("  ⚠️ 数据库配置不存在")
            return pd.DataFrame()
        
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
            
            # 创建数据库连接
            db_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            engine = create_engine(db_url)
            
            # 表名映射
            table_map = {
                'tick': 'tick_data',
                'minute': 'minute_data',
                'daily': 'daily_data',
                'financial': 'financial_data',
                'order_book': 'order_book_data',
                'market': 'market_data',
                'industry': 'industry_data'
            }
            
            table_name = table_map.get(data_type, data_type)
            
            # 构建SQL查询
            if stock_code in ['market', 'industry']:
                query = f"""
                SELECT * FROM {table_name}
                WHERE date >= '{start_date}' AND date <= '{end_date}'
                """
            else:
                query = f"""
                SELECT * FROM {table_name}
                WHERE stock_code = '{stock_code}'
                AND date >= '{start_date}' AND date <= '{end_date}'
                """
            
            # 执行查询
            data = pd.read_sql(text(query), engine)
            
            print(f"  ✅ 从数据库加载: {len(data)} 条记录")
            return data
            
        except Exception as e:
            print(f"  ❌ 从数据库加载失败: {e}")
            return pd.DataFrame()
    
    def _load_from_api(self,
                       data_type: str,
                       stock_code: str,
                       start_date: str,
                       end_date: str) -> pd.DataFrame:
        """
        从API加载数据
        
        Args:
            data_type: 数据类型
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            data: 数据DataFrame
        """
        api_config = self.data_sources['api']
        
        if not api_config:
            print("  ⚠️ API配置不存在")
            return pd.DataFrame()
        
        try:
            import requests
            
            # API端点映射
            endpoint_map = {
                'tick': '/api/tick',
                'minute': '/api/minute',
                'daily': '/api/daily',
                'financial': '/api/financial',
                'order_book': '/api/order_book',
                'market': '/api/market',
                'industry': '/api/industry'
            }
            
            endpoint = endpoint_map.get(data_type, f'/api/{data_type}')
            url = f"{api_config['base_url']}{endpoint}"
            
            # 构建请求参数
            params = {
                'stock_code': stock_code,
                'start_date': start_date,
                'end_date': end_date,
                'token': api_config.get('token', '')
            }
            
            # 发送请求
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = pd.DataFrame(response.json()['data'])
                print(f"  ✅ 从API加载: {len(data)} 条记录")
                return data
            else:
                print(f"  ❌ API请求失败: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"  ❌ 从API加载失败: {e}")
            return pd.DataFrame()
    
    def load_multiple_stocks(self,
                            stock_codes: List[str],
                            data_type: str,
                            start_date: str,
                            end_date: str,
                            source: str = 'file') -> Dict[str, pd.DataFrame]:
        """
        批量加载多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            data_type: 数据类型
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            data_dict: 数据字典 {stock_code: DataFrame}
        """
        print(f"批量加载 {len(stock_codes)} 只股票的{data_type}数据")
        
        data_dict = {}
        
        # 方法映射
        load_method_map = {
            'tick': self.load_tick_data,
            'minute': self.load_minute_data,
            'daily': self.load_daily_data,
            'financial': self.load_financial_data,
            'order_book': self.load_order_book_data
        }
        
        load_method = load_method_map.get(data_type)
        if load_method is None:
            raise ValueError(f"未知的数据类型: {data_type}")
        
        # 并行加载
        for stock_code in stock_codes:
            data = load_method(stock_code, start_date, end_date, source)
            data_dict[stock_code] = data
        
        print(f"  ✅ 批量加载完成: {len(data_dict)} 只股票")
        return data_dict
    
    async def load_multiple_stocks_async(self,
                                         stock_codes: List[str],
                                         data_type: str,
                                         start_date: str,
                                         end_date: str,
                                         source: str = 'api') -> Dict[str, pd.DataFrame]:
        """
        异步批量加载多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            data_type: 数据类型
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            data_dict: 数据字典
        """
        print(f"异步批量加载 {len(stock_codes)} 只股票的{data_type}数据")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for stock_code in stock_codes:
                task = self._load_from_api_async(session, data_type, stock_code, start_date, end_date)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        data_dict = dict(zip(stock_codes, results))
        print(f"  ✅ 异步批量加载完成")
        return data_dict
    
    async def _load_from_api_async(self,
                                   session,
                                   data_type: str,
                                   stock_code: str,
                                   start_date: str,
                                   end_date: str) -> pd.DataFrame:
        """
        异步从API加载数据
        """
        api_config = self.data_sources['api']
        
        endpoint_map = {
            'tick': '/api/tick',
            'minute': '/api/minute',
            'daily': '/api/daily',
            'financial': '/api/financial',
            'order_book': '/api/order_book'
        }
        
        endpoint = endpoint_map.get(data_type, f'/api/{data_type}')
        url = f"{api_config['base_url']}{endpoint}"
        
        params = {
            'stock_code': stock_code,
            'start_date': start_date,
            'end_date': end_date,
            'token': api_config.get('token', '')
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return pd.DataFrame(json_data['data'])
                else:
                    return pd.DataFrame()
        except Exception as e:
            print(f"  ❌ 异步加载失败 {stock_code}: {e}")
            return pd.DataFrame()
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        print("✅ 缓存已清除")
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存信息
        
        Returns:
            info: 缓存信息
        """
        info = {
            'cache_count': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'cache_size_mb': sum(df.memory_usage(deep=True).sum() for df in self.cache.values()) / 1024 / 1024
        }
        return info
    
    def save_to_cache(self, 
                      data: pd.DataFrame, 
                      data_type: str, 
                      stock_code: str, 
                      start_date: str, 
                      end_date: str):
        """
        手动保存数据到缓存
        
        Args:
            data: 数据DataFrame
            data_type: 数据类型
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        cache_key = f"{data_type}_{stock_code}_{start_date}_{end_date}"
        self.cache[cache_key] = data
        print(f"✅ 数据已缓存: {cache_key}")
    
    def export_data(self,
                   data: pd.DataFrame,
                   file_path: str,
                   format: str = 'parquet'):
        """
        导出数据到文件
        
        Args:
            data: 数据DataFrame
            file_path: 文件路径
            format: 文件格式 ('parquet', 'csv', 'pickle')
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if format == 'parquet':
            data.to_parquet(file_path, index=False)
        elif format == 'csv':
            data.to_csv(file_path, index=False)
        elif format == 'pickle':
            data.to_pickle(file_path)
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        print(f"✅ 数据已导出: {file_path}")
    
    def close(self):
        """关闭数据加载器，释放资源"""
        # 关闭数据库连接
        for conn in self.db_connections.values():
            try:
                conn.close()
            except:
                pass
        
        # 关闭API会话
        if self.api_session:
            try:
                self.api_session.close()
            except:
                pass
        
        # 关闭线程池
        self.executor.shutdown(wait=False)
        
        # 清除缓存
        self.clear_cache()
        
        print("✅ 数据加载器已关闭")

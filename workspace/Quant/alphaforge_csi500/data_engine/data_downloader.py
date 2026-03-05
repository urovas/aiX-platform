# 数据下载模块
# 集成AKShare和Tushare数据源

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import os
import time
import warnings
from datetime import datetime, timedelta
import logging

warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataDownloader:
    """
    数据下载管理器
    支持AKShare和Tushare数据源
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据下载器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 数据源配置
        self.data_sources = {
            'akshare': self.config.get('akshare', {'enabled': True}),
            'tushare': self.config.get('tushare', {'enabled': False, 'token': ''})
        }
        
        # 数据保存目录
        self.data_dir = self.config.get('data_dir', './data/')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 创建子目录
        for subdir in ['daily', 'minute', 'tick', 'financial', 'index', 'industry']:
            os.makedirs(os.path.join(self.data_dir, subdir), exist_ok=True)
        
        # 下载限速（秒）
        self.rate_limit = self.config.get('rate_limit', 0.5)
        
        # 初始化数据源
        self._init_data_sources()
        
        print("✅ 数据下载器初始化完成")
        print(f"  数据目录: {self.data_dir}")
        print(f"  AKShare: {'启用' if self.data_sources['akshare']['enabled'] else '禁用'}")
        print(f"  Tushare: {'启用' if self.data_sources['tushare']['enabled'] else '禁用'}")
    
    def _init_data_sources(self):
        """初始化数据源"""
        # AKShare
        if self.data_sources['akshare']['enabled']:
            try:
                import akshare as ak
                self.ak = ak
                print("  ✅ AKShare 初始化成功")
            except ImportError:
                print("  ⚠️ AKShare 未安装，请运行: pip install akshare")
                self.data_sources['akshare']['enabled'] = False
        
        # Tushare
        if self.data_sources['tushare']['enabled']:
            try:
                import tushare as ts
                self.ts = ts
                token = self.data_sources['tushare'].get('token', '')
                if token:
                    ts.set_token(token)
                    self.pro = ts.pro_api()
                    print("  ✅ Tushare 初始化成功")
                else:
                    print("  ⚠️ Tushare token 未设置")
                    self.data_sources['tushare']['enabled'] = False
            except ImportError:
                print("  ⚠️ Tushare 未安装，请运行: pip install tushare")
                self.data_sources['tushare']['enabled'] = False
    
    # ==================== AKShare 数据下载 ====================
    
    def download_daily_akshare(self,
                               stock_code: str,
                               start_date: str,
                               end_date: str,
                               save: bool = True) -> pd.DataFrame:
        """
        使用AKShare下载日线数据
        
        Args:
            stock_code: 股票代码 (如: 000001)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            save: 是否保存到文件
            
        Returns:
            daily_data: 日线数据
        """
        if not self.data_sources['akshare']['enabled']:
            print("❌ AKShare 未启用")
            return pd.DataFrame()
        
        print(f"使用AKShare下载日线数据: {stock_code}")
        
        try:
            # 转换日期格式
            start = start_date.replace('-', '')
            end = end_date.replace('-', '')
            
            # 下载数据
            df = self.ak.stock_zh_a_hist(
                symbol=stock_code[:6],
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_daily_columns(df, stock_code)
            
            # 保存数据
            if save:
                self._save_daily_data(df, stock_code)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_minute_akshare(self,
                                stock_code: str,
                                period: str = '1',
                                save: bool = True) -> pd.DataFrame:
        """
        使用AKShare下载分钟数据
        
        Args:
            stock_code: 股票代码
            period: 周期 ('1', '5', '15', '30', '60')
            save: 是否保存
            
        Returns:
            minute_data: 分钟数据
        """
        if not self.data_sources['akshare']['enabled']:
            print("❌ AKShare 未启用")
            return pd.DataFrame()
        
        print(f"使用AKShare下载{period}分钟数据: {stock_code}")
        
        try:
            # 下载数据
            df = self.ak.stock_zh_a_minute(
                symbol=stock_code[:6],
                period=period,
                adjust="qfq"
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_minute_columns(df, stock_code)
            
            # 保存数据
            if save:
                self._save_minute_data(df, stock_code, period)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_financial_akshare(self,
                                   stock_code: str,
                                   save: bool = True) -> pd.DataFrame:
        """
        使用AKShare下载财务数据
        
        Args:
            stock_code: 股票代码
            save: 是否保存
            
        Returns:
            financial_data: 财务数据
        """
        if not self.data_sources['akshare']['enabled']:
            print("❌ AKShare 未启用")
            return pd.DataFrame()
        
        print(f"使用AKShare下载财务数据: {stock_code}")
        
        try:
            # 下载主要财务指标
            df = self.ak.stock_financial_report_sina(
                stock=stock_code[:6],
                symbol="财务指标"
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_financial_columns(df, stock_code)
            
            # 保存数据
            if save:
                self._save_financial_data(df, stock_code)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_index_akshare(self,
                               index_code: str = 'sh000001',
                               start_date: str = None,
                               end_date: str = None,
                               save: bool = True) -> pd.DataFrame:
        """
        使用AKShare下载指数数据
        
        Args:
            index_code: 指数代码 (如: sh000001)
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            
        Returns:
            index_data: 指数数据
        """
        if not self.data_sources['akshare']['enabled']:
            print("❌ AKShare 未启用")
            return pd.DataFrame()
        
        print(f"使用AKShare下载指数数据: {index_code}")
        
        try:
            # 下载数据
            df = self.ak.index_zh_a_hist(
                symbol=index_code,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20230101",
                end_date=end_date.replace('-', '') if end_date else datetime.now().strftime('%Y%m%d')
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_daily_columns(df, index_code)
            
            # 保存数据
            if save:
                self._save_index_data(df, index_code)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_stock_list_akshare(self) -> pd.DataFrame:
        """
        使用AKShare获取A股股票列表
        
        Returns:
            stock_list: 股票列表
        """
        if not self.data_sources['akshare']['enabled']:
            print("❌ AKShare 未启用")
            return pd.DataFrame()
        
        print("使用AKShare获取A股股票列表")
        
        try:
            df = self.ak.stock_zh_a_spot_em()
            print(f"  ✅ 获取完成: {len(df)} 只股票")
            return df
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return pd.DataFrame()
    
    # ==================== Tushare 数据下载 ====================
    
    def download_daily_tushare(self,
                               stock_code: str,
                               start_date: str,
                               end_date: str,
                               save: bool = True) -> pd.DataFrame:
        """
        使用Tushare下载日线数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            save: 是否保存
            
        Returns:
            daily_data: 日线数据
        """
        if not self.data_sources['tushare']['enabled']:
            print("❌ Tushare 未启用")
            return pd.DataFrame()
        
        print(f"使用Tushare下载日线数据: {stock_code}")
        
        try:
            # 下载数据
            df = self.pro.daily(
                ts_code=stock_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_tushare_daily(df, stock_code)
            
            # 保存数据
            if save:
                self._save_daily_data(df, stock_code)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_financial_tushare(self,
                                   stock_code: str,
                                   save: bool = True) -> pd.DataFrame:
        """
        使用Tushare下载财务数据
        
        Args:
            stock_code: 股票代码
            save: 是否保存
            
        Returns:
            financial_data: 财务数据
        """
        if not self.data_sources['tushare']['enabled']:
            print("❌ Tushare 未启用")
            return pd.DataFrame()
        
        print(f"使用Tushare下载财务数据: {stock_code}")
        
        try:
            # 下载利润表
            income_df = self.pro.income(
                ts_code=stock_code,
                fields='ts_code,ann_date,f_ann_date,end_date,total_revenue,operate_profit,n_income'
            )
            
            # 下载资产负债表
            balance_df = self.pro.balancesheet(
                ts_code=stock_code,
                fields='ts_code,ann_date,f_ann_date,end_date,total_assets,total_liabilities,total_hldr_eqy_exc_min_int'
            )
            
            # 合并数据
            df = pd.merge(income_df, balance_df, on=['ts_code', 'end_date'], how='outer')
            
            if df.empty:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_tushare_financial(df, stock_code)
            
            # 保存数据
            if save:
                self._save_financial_data(df, stock_code)
            
            print(f"  ✅ 下载完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return pd.DataFrame()
    
    def download_stock_list_tushare(self) -> pd.DataFrame:
        """
        使用Tushare获取A股股票列表
        
        Returns:
            stock_list: 股票列表
        """
        if not self.data_sources['tushare']['enabled']:
            print("❌ Tushare 未启用")
            return pd.DataFrame()
        
        print("使用Tushare获取A股股票列表")
        
        try:
            df = self.pro.stock_basic(exchange='', list_status='L')
            print(f"  ✅ 获取完成: {len(df)} 只股票")
            return df
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return pd.DataFrame()
    
    # ==================== 批量下载功能 ====================
    
    def batch_download_daily(self,
                            stock_codes: List[str],
                            start_date: str,
                            end_date: str,
                            source: str = 'akshare',
                            save: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量下载日线数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源 ('akshare', 'tushare')
            save: 是否保存
            
        Returns:
            data_dict: 数据字典
        """
        print(f"\n批量下载 {len(stock_codes)} 只股票的日线数据")
        print(f"数据源: {source}")
        
        data_dict = {}
        failed_codes = []
        
        for i, code in enumerate(stock_codes):
            print(f"\n[{i+1}/{len(stock_codes)}] {code}")
            
            try:
                if source == 'akshare':
                    df = self.download_daily_akshare(code, start_date, end_date, save)
                elif source == 'tushare':
                    df = self.download_daily_tushare(code, start_date, end_date, save)
                else:
                    print(f"  ❌ 未知数据源: {source}")
                    continue
                
                if not df.empty:
                    data_dict[code] = df
                else:
                    failed_codes.append(code)
                
                # 限速
                time.sleep(self.rate_limit)
                
            except Exception as e:
                print(f"  ❌ 下载失败: {e}")
                failed_codes.append(code)
        
        print(f"\n✅ 批量下载完成: {len(data_dict)}/{len(stock_codes)} 成功")
        if failed_codes:
            print(f"  ⚠️ 失败: {failed_codes}")
        
        return data_dict
    
    def download_all_data(self,
                         stock_codes: List[str],
                         start_date: str,
                         end_date: str,
                         source: str = 'akshare') -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        下载所有类型的数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            
        Returns:
            all_data: 所有数据字典
        """
        print("="*60)
        print("下载所有数据")
        print("="*60)
        
        all_data = {}
        
        for stock_code in stock_codes:
            print(f"\n下载 {stock_code} 数据...")
            
            stock_data = {}
            
            # 下载日线数据
            if source == 'akshare':
                stock_data['daily'] = self.download_daily_akshare(stock_code, start_date, end_date)
                stock_data['financial'] = self.download_financial_akshare(stock_code)
            elif source == 'tushare':
                stock_data['daily'] = self.download_daily_tushare(stock_code, start_date, end_date)
                stock_data['financial'] = self.download_financial_tushare(stock_code)
            
            all_data[stock_code] = stock_data
            
            # 限速
            time.sleep(self.rate_limit)
        
        print("\n" + "="*60)
        print("所有数据下载完成")
        print("="*60)
        
        return all_data
    
    # ==================== 数据标准化 ====================
    
    def _standardize_daily_columns(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化日线数据列名"""
        # AKShare列名映射
        column_map = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }
        
        df = df.rename(columns=column_map)
        
        # 添加股票代码
        df['stock_code'] = stock_code
        
        # 转换日期格式
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def _standardize_minute_columns(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化分钟数据列名"""
        column_map = {
            '时间': 'datetime',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }
        
        df = df.rename(columns=column_map)
        df['stock_code'] = stock_code
        
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        return df
    
    def _standardize_financial_columns(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化财务数据列名"""
        df['stock_code'] = stock_code
        
        # 转换日期
        date_cols = [col for col in df.columns if '日期' in col or 'date' in col.lower()]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def _standardize_tushare_daily(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化Tushare日线数据"""
        column_map = {
            'trade_date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume',
            'amount': 'amount',
            'pct_chg': 'change_pct'
        }
        
        df = df.rename(columns=column_map)
        df['stock_code'] = stock_code
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def _standardize_tushare_financial(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化Tushare财务数据"""
        column_map = {
            'end_date': 'date',
            'total_revenue': 'revenue',
            'operate_profit': 'operating_profit',
            'n_income': 'net_profit',
            'total_assets': 'total_assets',
            'total_liabilities': 'total_liabilities',
            'total_hldr_eqy_exc_min_int': 'total_equity'
        }
        
        df = df.rename(columns=column_map)
        df['stock_code'] = stock_code
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    # ==================== 数据保存 ====================
    
    def _save_daily_data(self, df: pd.DataFrame, stock_code: str):
        """保存日线数据"""
        file_path = os.path.join(self.data_dir, 'daily', f"{stock_code}.parquet")
        df.to_parquet(file_path, index=False)
        print(f"  💾 已保存: {file_path}")
    
    def _save_minute_data(self, df: pd.DataFrame, stock_code: str, period: str):
        """保存分钟数据"""
        file_path = os.path.join(self.data_dir, 'minute', f"{stock_code}_{period}min.parquet")
        df.to_parquet(file_path, index=False)
        print(f"  💾 已保存: {file_path}")
    
    def _save_financial_data(self, df: pd.DataFrame, stock_code: str):
        """保存财务数据"""
        file_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.parquet")
        df.to_parquet(file_path, index=False)
        print(f"  💾 已保存: {file_path}")
    
    def _save_index_data(self, df: pd.DataFrame, index_code: str):
        """保存指数数据"""
        file_path = os.path.join(self.data_dir, 'index', f"{index_code}.parquet")
        df.to_parquet(file_path, index=False)
        print(f"  💾 已保存: {file_path}")
    
    # ==================== 数据更新 ====================
    
    def update_daily_data(self,
                         stock_codes: List[str],
                         source: str = 'akshare') -> Dict[str, pd.DataFrame]:
        """
        更新日线数据（增量更新）
        
        Args:
            stock_codes: 股票代码列表
            source: 数据源
            
        Returns:
            updated_data: 更新的数据
        """
        print("="*60)
        print("更新日线数据")
        print("="*60)
        
        updated_data = {}
        
        for stock_code in stock_codes:
            print(f"\n更新 {stock_code}...")
            
            # 检查现有数据
            file_path = os.path.join(self.data_dir, 'daily', f"{stock_code}.parquet")
            
            if os.path.exists(file_path):
                # 读取现有数据
                existing_df = pd.read_parquet(file_path)
                last_date = existing_df['date'].max()
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                
                print(f"  现有数据最新日期: {last_date.strftime('%Y-%m-%d')}")
                print(f"  更新起始日期: {start_date}")
            else:
                start_date = '2020-01-01'
                existing_df = pd.DataFrame()
                print(f"  未找到现有数据，全量下载")
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 下载新数据
            if source == 'akshare':
                new_df = self.download_daily_akshare(stock_code, start_date, end_date, save=False)
            elif source == 'tushare':
                new_df = self.download_daily_tushare(stock_code, start_date, end_date, save=False)
            else:
                continue
            
            if not new_df.empty:
                # 合并数据
                if not existing_df.empty:
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                    combined_df = combined_df.sort_values('date')
                else:
                    combined_df = new_df
                
                # 保存
                self._save_daily_data(combined_df, stock_code)
                updated_data[stock_code] = combined_df
                print(f"  ✅ 更新完成: {len(new_df)} 条新记录")
            else:
                print(f"  ⚠️ 无新数据")
            
            time.sleep(self.rate_limit)
        
        print("\n" + "="*60)
        print("数据更新完成")
        print("="*60)
        
        return updated_data

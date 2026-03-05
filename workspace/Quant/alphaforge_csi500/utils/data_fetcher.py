# 数据获取模块

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import baostock as bs
import akshare as ak
import tushare as ts

class IndexDataFetcher:
    def __init__(self, config):
        """初始化数据获取器"""
        self.config = config
        self.data_dir = config.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化数据源
        self.bs_available = False
        self.bs = None
        self.ts_available = False
        self.ts_pro = None
        self.ak_available = False
        
        # 初始化Baostock
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.bs_available = True
                self.bs = bs
                print("Baostock登录成功")
            else:
                print(f"Baostock登录失败: {lg.error_msg}")
        except Exception as e:
            print(f"Baostock初始化失败: {e}")
        
        # 初始化Tushare
        try:
            if config.DATA_SOURCE.get("tushare", {}).get("token"):
                self.ts_pro = ts.pro_api(config.DATA_SOURCE["tushare"]["token"])
                self.ts_available = True
                print("Tushare初始化成功")
        except Exception as e:
            print(f"Tushare初始化失败: {e}")
        
        # 初始化AkShare
        try:
            self.ak_available = True
            print("AkShare初始化成功")
        except Exception as e:
            print(f"AkShare初始化失败: {e}")
    
    def get_index_data(self, index_code, start_date, end_date):
        """获取指数行情数据"""
        file_path = os.path.join(self.data_dir, f"index_{index_code}_{start_date}_{end_date}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                print(f"从缓存读取指数数据: {index_code}")
                return df
            except Exception as e:
                print(f"读取指数数据失败: {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                print(f"尝试从Tushare获取指数数据: {index_code}")
                df = self.ts_pro.index_daily(
                    ts_code=index_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
                df.to_csv(file_path, index=False)
                print(f"从Tushare获取指数数据成功: {index_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从Tushare获取指数数据失败: {index_code}, {e}")
        
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                print(f"尝试从AkShare获取指数数据: {index_code}")
                symbol = index_code.split('.')[0]
                df = ak.index_zh_a_hist(symbol=symbol, period="daily", 
                                       start_date=start_date, end_date=end_date)
                df.to_csv(file_path, index=False)
                print(f"从AkShare获取指数数据成功: {index_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从AkShare获取指数数据失败: {index_code}, {e}")
        
        # 尝试从Baostock获取
        if self.bs_available:
            try:
                print(f"尝试从Baostock获取指数数据: {index_code}")
                symbol = index_code.split('.')[0]
                bs_code = f"sh.{symbol}" if symbol.startswith('0') or symbol.startswith('3') else f"sz.{symbol}"
                
                rs = self.bs.query_history_k_data_plus(
                    code=bs_code,
                    fields="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="3"
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    
                    # 转换数值列的数据类型
                    numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'adjustflag', 'turn', 'pctChg']
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df.to_csv(file_path, index=False)
                    print(f"从Baostock获取指数数据成功: {index_code}, {len(df)}条")
                    return df
            except Exception as e:
                print(f"从Baostock获取指数数据失败: {index_code}, {e}")
        
        print(f"无法获取指数数据: {index_code}")
        return pd.DataFrame()
    
    def get_index_components(self, index_code):
        """获取指数成分股"""
        file_path = os.path.join(self.data_dir, f"index_components_{index_code}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                print(f"从缓存读取指数成分股: {index_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"读取指数成分股失败: {e}")
        
        # 尝试从Baostock获取
        if self.bs_available:
            try:
                print(f"尝试从Baostock获取指数成分股: {index_code}")
                rs = self.bs.query_index_stock_list()
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    # 筛选指定指数
                    if 'index_code' in df.columns:
                        symbol = index_code.split('.')[0]
                        index_df = df[df['index_code'] == symbol]
                        if not index_df.empty:
                            index_df.to_csv(file_path, index=False)
                            print(f"从Baostock获取指数成分股成功: {index_code}, {len(index_df)}条")
                            return index_df
            except Exception as e:
                print(f"从Baostock获取指数成分股失败: {index_code}, {e}")
        
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                print(f"尝试从AkShare获取指数成分股: {index_code}")
                symbol = index_code.split('.')[0]
                df = ak.index_stock_cons(symbol=symbol)
                df.to_csv(file_path, index=False)
                print(f"从AkShare获取指数成分股成功: {index_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从AkShare获取指数成分股失败: {index_code}, {e}")
        
        print(f"无法获取指数成分股: {index_code}")
        return pd.DataFrame()
    
    def get_stock_quote(self, ts_code, start_date, end_date):
        """获取股票行情数据"""
        file_path = os.path.join(self.data_dir, f"stock_quote_{ts_code}_{start_date}_{end_date}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                return df
            except Exception as e:
                print(f"读取股票行情失败: {e}")
        
        # 转换股票代码格式
        ts_code_clean = ts_code.replace('.SZ', '').replace('.SH', '')
        if ts_code_clean.startswith('sh.'):
            symbol = ts_code_clean.split('.')[1]
            bs_code = f"sh.{symbol}"
        elif ts_code_clean.startswith('sz.'):
            symbol = ts_code_clean.split('.')[1]
            bs_code = f"sz.{symbol}"
        else:
            symbol = ts_code.split('.')[0]
            if symbol.startswith('6'):
                bs_code = f"sh.{symbol}"
            else:
                bs_code = f"sz.{symbol}"
        
        # 确保代码格式正确
        if len(bs_code.split('.')[1]) != 6:
            return pd.DataFrame()
        
        # 尝试从Baostock获取
        if self.bs_available:
            try:
                print(f"尝试从Baostock获取股票行情: {ts_code}")
                rs = self.bs.query_history_k_data_plus(
                    code=bs_code,
                    fields="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="3"
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    
                    # 转换数值列的数据类型
                    numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'adjustflag', 'turn', 'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df['ts_code'] = ts_code
                    df['trade_date'] = df['date']
                    df.to_csv(file_path, index=False)
                    print(f"从Baostock获取股票行情成功: {ts_code}, {len(df)}条")
                    return df
            except Exception as e:
                print(f"从Baostock获取股票行情失败: {ts_code}, {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                print(f"尝试从Tushare获取股票行情: {ts_code}")
                df = self.ts_pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
                df.to_csv(file_path, index=False)
                print(f"从Tushare获取股票行情成功: {ts_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从Tushare获取股票行情失败: {ts_code}, {e}")
        
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                print(f"尝试从AkShare获取股票行情: {ts_code}")
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                df['ts_code'] = ts_code
                df.to_csv(file_path, index=False)
                print(f"从AkShare获取股票行情成功: {ts_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从AkShare获取股票行情失败: {ts_code}, {e}")
        
        print(f"无法获取股票行情: {ts_code}")
        return pd.DataFrame()
    
    def get_stock_financial(self, ts_code, year, quarter):
        """获取股票财务数据"""
        file_path = os.path.join(self.data_dir, f"financial_{ts_code}_{year}Q{quarter}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                return df
            except Exception as e:
                print(f"读取财务数据失败: {e}")
        
        # 尝试从Baostock获取
        if self.bs_available:
            try:
                print(f"尝试从Baostock获取财务数据: {ts_code}")
                
                # 转换股票代码格式
                ts_code_clean = ts_code.replace('.SZ', '').replace('.SH', '')
                if ts_code_clean.startswith('sh.'):
                    symbol = ts_code_clean.split('.')[1]
                    bs_code = f"sh.{symbol}"
                elif ts_code_clean.startswith('sz.'):
                    symbol = ts_code_clean.split('.')[1]
                    bs_code = f"sz.{symbol}"
                else:
                    symbol = ts_code.split('.')[0]
                    if symbol.startswith('6'):
                        bs_code = f"sh.{symbol}"
                    else:
                        bs_code = f"sz.{symbol}"
                
                # 获取财务指标
                rs = self.bs.query_profit_data(
                    code=bs_code,
                    year=year,
                    quarter=quarter
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    df.to_csv(file_path, index=False)
                    print(f"从Baostock获取财务数据成功: {ts_code}")
                    return df
            except Exception as e:
                print(f"从Baostock获取财务数据失败: {ts_code}, {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                print(f"尝试从Tushare获取财务数据: {ts_code}")
                df = self.ts_pro.fina_indicator(
                    ts_code=ts_code,
                    year=year,
                    quarter=quarter
                )
                df.to_csv(file_path, index=False)
                print(f"从Tushare获取财务数据成功: {ts_code}")
                return df
            except Exception as e:
                print(f"从Tushare获取财务数据失败: {ts_code}, {e}")
        
        print(f"无法获取财务数据: {ts_code}")
        return pd.DataFrame()
    
    def get_data_source_status(self):
        """获取数据源状态"""
        status = {
            "tushare": "可用" if self.ts_available else "不可用",
            "akshare": "可用" if self.ak_available else "不可用",
            "baostock": "可用" if self.bs_available else "不可用"
        }
        return status
    
    def __del__(self):
        """析构函数，登出数据源"""
        if self.bs_available:
            try:
                bs.logout()
                print("Baostock登出成功")
            except:
                pass

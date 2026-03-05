# 数据获取模块 - 支持多数据源
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DataFetcher:
    def __init__(self, config):
        """初始化数据获取器"""
        self.config = config
        self.data_dir = config.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据源状态
        self.data_sources = {}
        
        # 尝试导入Tushare
        try:
            import tushare as ts
            self.ts_available = True
            if config.DATA_SOURCE["tushare"]["token"]:
                ts.set_token(config.DATA_SOURCE["tushare"]["token"])
                self.ts_pro = ts.pro_api()
                self.data_sources['tushare'] = True
            else:
                self.ts_pro = None
                self.data_sources['tushare'] = False
        except ImportError:
            self.ts_available = False
            self.ts_pro = None
            self.data_sources['tushare'] = False
        
        # 尝试导入AkShare
        try:
            import akshare as ak
            self.ak_available = True
            self.ak = ak
            self.data_sources['akshare'] = True
        except ImportError:
            self.ak_available = False
            self.ak = None
            self.data_sources['akshare'] = False
        
        # 尝试导入Baostock
        try:
            import baostock as bs
            self.bs_available = True
            self.bs = bs
            # 登录Baostock
            lg = bs.login()
            if lg.error_code != '0':
                print(f"Baostock登录失败: {lg.error_msg}")
                self.bs_available = False
                self.data_sources['baostock'] = False
            else:
                self.data_sources['baostock'] = True
                print("Baostock登录成功")
        except ImportError:
            self.bs_available = False
            self.bs = None
            self.data_sources['baostock'] = False
        
        # 尝试导入QuantDataCollector
        try:
            from quant_data_collector import QuantDataCollector
            self.qdc_available = True
            self.qdc = QuantDataCollector()
            self.data_sources['quant_data_collector'] = True
        except ImportError:
            self.qdc_available = False
            self.qdc = None
            self.data_sources['quant_data_collector'] = False
        
        print(f"可用数据源: {list(self.data_sources.keys())}")
    
    def get_stock_basic(self, market="all"):
        """获取股票基本信息"""
        file_path = os.path.join(self.data_dir, f"stock_basic_{market}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                print(f"从缓存读取股票基本信息: {len(df)}条")
                return df
            except Exception as e:
                print(f"读取股票基本信息失败: {e}")
        
        # 尝试从Baostock获取（免费，优先使用）
        if self.bs_available:
            try:
                print("尝试从Baostock获取股票基本信息...")
                rs = self.bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    # 转换列名
                    df = df.rename(columns={
                        'code': 'ts_code',
                        'code_name': 'name',
                        'ipoDate': 'list_date'
                    })
                    # 转换代码格式
                    df['ts_code'] = df['ts_code'].apply(lambda x: f"{x}.SH" if x.startswith('6') else f"{x}.SZ")
                    df.to_csv(file_path, index=False)
                    print(f"从Baostock获取股票基本信息成功: {len(df)}条")
                    return df
            except Exception as e:
                print(f"从Baostock获取股票基本信息失败: {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                print("尝试从Tushare获取股票基本信息...")
                df = self.ts_pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                df.to_csv(file_path, index=False)
                print(f"从Tushare获取股票基本信息成功: {len(df)}条")
                return df
            except Exception as e:
                print(f"从Tushare获取股票基本信息失败: {e}")
        
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                print("尝试从AkShare获取股票基本信息...")
                df = self.ak.stock_zh_a_spot_em()
                df.to_csv(file_path, index=False)
                print(f"从AkShare获取股票基本信息成功: {len(df)}条")
                return df
            except Exception as e:
                print(f"从AkShare获取股票基本信息失败: {e}")
        
        print("无法获取股票基本信息")
        return pd.DataFrame()
    
    def get_stock_quote(self, ts_code, start_date, end_date):
        """获取股票行情数据"""
        # 转换日期格式
        start_date_formatted = start_date.replace('-', '')
        end_date_formatted = end_date.replace('-', '')
        file_path = os.path.join(self.data_dir, f"quote_{ts_code}_{start_date_formatted}_{end_date_formatted}.csv")
        
        # 尝试从文件读取
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                if 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                print(f"从缓存读取股票行情: {ts_code}")
                return df
            except Exception as e:
                print(f"读取股票行情失败: {e}")
        
        # 转换股票代码格式
        # 处理ts_code格式，如sh.600519.SZ → sh.600519
        ts_code_clean = ts_code.replace('.SZ', '').replace('.SH', '')
        if ts_code_clean.startswith('sh.'):
            symbol = ts_code_clean.split('.')[1]
            bs_code = f"sh.{symbol}"
        elif ts_code_clean.startswith('sz.'):
            symbol = ts_code_clean.split('.')[1]
            bs_code = f"sz.{symbol}"
        else:
            # 处理纯代码格式
            symbol = ts_code.split('.')[0]
            if symbol.startswith('6'):
                bs_code = f"sh.{symbol}"
            else:
                bs_code = f"sz.{symbol}"
        # 确保代码格式正确
        if len(bs_code.split('.')[1]) != 6:
            return pd.DataFrame()
        
        # 尝试从Baostock获取（免费，优先使用）
        if self.bs_available:
            try:
                print(f"尝试从Baostock获取股票行情: {ts_code}")
                rs = self.bs.query_history_k_data_plus(
                    bs_code,
                    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="3"  # 1:后复权 2:前复权 3:不复权
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
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
                    start_date=start_date_formatted,
                    end_date=end_date_formatted
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
                df = self.ak.stock_zh_a_hist(
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
                symbol = ts_code.split('.')[0]
                if ts_code.endswith('.SH'):
                    bs_code = f"sh.{symbol}"
                elif ts_code.endswith('.SZ'):
                    bs_code = f"sz.{symbol}"
                else:
                    bs_code = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
                
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
        
        # 指数代码映射
        index_map = {
            "000300.SH": "000300",
            "000905.SH": "000905",
            "000852.SH": "000852",
            "000016.SH": "000016",
            "399001.SZ": "399001"
        }
        
        symbol = index_map.get(index_code, index_code.split('.')[0])
        
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
                        index_df = df[df['index_code'] == symbol]
                        if not index_df.empty:
                            index_df.to_csv(file_path, index=False)
                            print(f"从Baostock获取指数成分股成功: {index_code}, {len(index_df)}条")
                            return index_df
            except Exception as e:
                print(f"从Baostock获取指数成分股失败: {index_code}, {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                print(f"尝试从Tushare获取指数成分股: {index_code}")
                df = self.ts_pro.index_weight(
                    index_code=index_code,
                    trade_date=datetime.now().strftime("%Y%m%d")
                )
                df.to_csv(file_path, index=False)
                print(f"从Tushare获取指数成分股成功: {index_code}, {len(df)}条")
                return df
            except Exception as e:
                print(f"从Tushare获取指数成分股失败: {index_code}, {e}")
        
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                print(f"尝试从AkShare获取指数成分股: {index_code}")
                
                # 使用不同的接口
                if index_code == "000300.SH":
                    df = self.ak.index_stock_cons(symbol="000300")
                elif index_code == "000905.SH":
                    df = self.ak.index_stock_cons(symbol="000905")
                elif index_code == "000852.SH":
                    df = self.ak.index_stock_cons(symbol="000852")
                elif index_code == "000016.SH":
                    df = self.ak.index_stock_cons(symbol="000016")
                elif index_code == "399001.SZ":
                    df = self.ak.index_stock_cons(symbol="399001")
                else:
                    df = pd.DataFrame()
                
                if not df.empty:
                    df.to_csv(file_path, index=False)
                    print(f"从AkShare获取指数成分股成功: {index_code}, {len(df)}条")
                    return df
            except Exception as e:
                print(f"从AkShare获取指数成分股失败: {index_code}, {e}")
        
        print(f"无法获取指数成分股: {index_code}")
        return pd.DataFrame()
    
    def get_market_cap(self, ts_code):
        """获取股票市值"""
        # 尝试从Baostock获取
        if self.bs_available:
            try:
                symbol = ts_code.split('.')[0]
                if ts_code.endswith('.SH'):
                    bs_code = f"sh.{symbol}"
                elif ts_code.endswith('.SZ'):
                    bs_code = f"sz.{symbol}"
                else:
                    bs_code = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
                
                rs = self.bs.query_stock_basic(code=bs_code)
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    df['ts_code'] = ts_code
                    return df
            except Exception as e:
                print(f"从Baostock获取市值失败: {ts_code}, {e}")
        
        # 尝试从Tushare获取
        if self.ts_available and self.ts_pro:
            try:
                df = self.ts_pro.daily_basic(
                    ts_code=ts_code,
                    trade_date=datetime.now().strftime("%Y%m%d"),
                    fields='ts_code,total_mv,circ_mv'
                )
                return df
            except Exception as e:
                print(f"从Tushare获取市值失败: {ts_code}, {e}")
        
        return pd.DataFrame()
    
    def get_industry_pe(self):
        """获取行业市盈率"""
        # 尝试从AkShare获取
        if self.ak_available:
            try:
                df = self.ak.stock_zh_a_industry_pe_em()
                return df
            except Exception as e:
                print(f"从AkShare获取行业市盈率失败: {e}")
        
        return pd.DataFrame()
    
    def get_data_source_status(self):
        """获取数据源状态"""
        status = {}
        for source, available in self.data_sources.items():
            status[source] = "可用" if available else "不可用"
        return status
    
    def __del__(self):
        """析构函数，登出Baostock"""
        if self.bs_available:
            try:
                self.bs.logout()
                print("Baostock登出成功")
            except:
                pass

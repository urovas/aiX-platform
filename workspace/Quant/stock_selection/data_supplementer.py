import pandas as pd
import numpy as np
from pathlib import Path
import baostock as bs
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataSupplementer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.clean_dir = self.data_dir / "cleaned"
        self.supplement_dir = self.data_dir / "supplemented"
        self.supplement_dir.mkdir(exist_ok=True)
        
        bs.login()
        
    def __del__(self):
        bs.logout()
        
    def supplement_all(self):
        """补充所有数据"""
        print("="*80)
        print("数据补充")
        print("="*80)
        print()
        
        self.supplement_historical_data()
        self.supplement_fundamental_data()
        
        print()
        print("="*80)
        print("数据补充完成")
        print(f"补充后数据保存在: {self.supplement_dir}")
        print("="*80)
        
    def supplement_historical_data(self):
        """补充历史数据"""
        print("1. 补充历史数据（2021-2025年）")
        print("-"*80)
        
        stock_basic = self.clean_dir / "stock_basic_all.csv"
        
        if not stock_basic.exists():
            print("未找到股票基本信息文件")
            return
        
        df_stocks = pd.read_csv(stock_basic)
        
        stocks = df_stocks['ts_code'].tolist()
        
        print(f"待处理股票数: {len(stocks)}")
        
        start_date = "2021-01-01"
        end_date = "2025-12-31"
        
        print(f"时间范围: {start_date} 至 {end_date}")
        
        success_count = 0
        fail_count = 0
        
        for i, stock_code in enumerate(stocks, 1):
            try:
                stock_code_clean = stock_code.replace('.', '')
                
                rs = bs.query_history_k_data_plus(
                    stock_code_clean,
                    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM",
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
                    
                    numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df['ts_code'] = stock_code
                    
                    output_file = self.supplement_dir / f"quote_{stock_code}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.csv"
                    df.to_csv(output_file, index=False)
                    
                    success_count += 1
                    
                    if i % 100 == 0:
                        print(f"已处理: {i}/{len(stocks)}, 成功: {success_count}, 失败: {fail_count}")
                else:
                    fail_count += 1
                    
            except Exception as e:
                fail_count += 1
                pass
            
            time.sleep(0.1)
        
        print(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
        print()
        
    def supplement_fundamental_data(self):
        """补充基本面数据"""
        print("2. 补充基本面数据")
        print("-"*80)
        
        stock_basic = self.clean_dir / "stock_basic_all.csv"
        
        if not stock_basic.exists():
            print("未找到股票基本信息文件")
            return
        
        df_stocks = pd.read_csv(stock_basic)
        
        stocks = df_stocks['ts_code'].tolist()
        
        print(f"待处理股票数: {len(stocks)}")
        
        start_date = "2021-01-01"
        end_date = "2025-12-31"
        
        print(f"时间范围: {start_date} 至 {end_date}")
        
        success_count = 0
        fail_count = 0
        
        for i, stock_code in enumerate(stocks, 1):
            try:
                stock_code_clean = stock_code.replace('.', '')
                
                rs = bs.query_profit_data(
                    code=stock_code_clean,
                    year=2021,
                    quarter=4
                )
                
                profit_data = []
                while (rs.error_code == '0') & rs.next():
                    profit_data.append(rs.get_row_data())
                
                if profit_data:
                    df_profit = pd.DataFrame(profit_data, columns=rs.fields)
                    
                    output_file = self.supplement_dir / f"profit_{stock_code}.csv"
                    df_profit.to_csv(output_file, index=False)
                    
                    success_count += 1
                    
                    if i % 100 == 0:
                        print(f"已处理: {i}/{len(stocks)}, 成功: {success_count}, 失败: {fail_count}")
                else:
                    fail_count += 1
                    
            except Exception as e:
                fail_count += 1
                pass
            
            time.sleep(0.1)
        
        print(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
        print()

if __name__ == "__main__":
    data_dir = "/home/xcc/openclaw-platform/workspace/quant/stock_selection/data"
    supplementer = DataSupplementer(data_dir)
    supplementer.supplement_all()

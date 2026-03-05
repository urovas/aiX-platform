import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class DataCleaner:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.clean_dir = self.data_dir / "cleaned"
        self.clean_dir.mkdir(exist_ok=True)
        
    def clean_all(self):
        """清洗所有数据"""
        print("="*80)
        print("数据清洗")
        print("="*80)
        print()
        
        self.clean_quote_files()
        self.clean_stock_basic()
        
        print()
        print("="*80)
        print("数据清洗完成")
        print(f"清洗后数据保存在: {self.clean_dir}")
        print("="*80)
        
    def clean_quote_files(self):
        """清洗行情数据文件"""
        print("1. 清洗行情数据文件")
        print("-"*80)
        
        quote_files = list(self.data_dir.glob("quote_*.csv"))
        total_files = len(quote_files)
        
        print(f"待处理文件数: {total_files}")
        
        cleaned_count = 0
        total_records_before = 0
        total_records_after = 0
        
        for i, file in enumerate(quote_files, 1):
            try:
                df = pd.read_csv(file)
                total_records_before += len(df)
                
                df_cleaned = self.clean_single_file(df)
                total_records_after += len(df_cleaned)
                
                output_file = self.clean_dir / file.name
                df_cleaned.to_csv(output_file, index=False)
                
                cleaned_count += 1
                
                if i % 100 == 0:
                    print(f"已处理: {i}/{total_files}")
                    
            except Exception as e:
                print(f"处理文件 {file.name} 失败: {e}")
        
        print(f"清洗完成: {cleaned_count}/{total_files} 个文件")
        print(f"记录数变化: {total_records_before:,} -> {total_records_after:,} ({total_records_after/total_records_before*100:.2f}%)")
        print()
        
    def clean_single_file(self, df):
        """清洗单个文件"""
        df_cleaned = df.copy()
        
        df_cleaned = self.remove_duplicates(df_cleaned)
        df_cleaned = self.handle_missing_values(df_cleaned)
        df_cleaned = self.handle_outliers(df_cleaned)
        df_cleaned = self.validate_data(df_cleaned)
        
        return df_cleaned
        
    def remove_duplicates(self, df):
        """删除重复记录"""
        original_len = len(df)
        df_cleaned = df.drop_duplicates(subset=['date', 'code'], keep='first')
        
        removed = original_len - len(df_cleaned)
        if removed > 0:
            pass
            
        return df_cleaned
        
    def handle_missing_values(self, df):
        """处理缺失值"""
        df_cleaned = df.copy()
        
        numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'pctChg']
        
        for col in numeric_cols:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
        
        df_cleaned = df_cleaned.dropna(subset=['open', 'high', 'low', 'close'])
        
        for col in ['volume', 'amount', 'pctChg']:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
        
        valuation_cols = ['peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
        for col in valuation_cols:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].fillna(method='ffill').fillna(method='bfill')
        
        if 'turn' in df_cleaned.columns:
            df_cleaned['turn'] = df_cleaned['turn'].fillna(0)
        
        return df_cleaned
        
    def handle_outliers(self, df):
        """处理异常值"""
        df_cleaned = df.copy()
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pctChg']
        
        for col in numeric_cols:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
                
                Q1 = df_cleaned[col].quantile(0.25)
                Q3 = df_cleaned[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                df_cleaned[col] = df_cleaned[col].clip(lower_bound, upper_bound)
        
        df_cleaned = df_cleaned[
            (df_cleaned['open'] > 0) & 
            (df_cleaned['high'] > 0) & 
            (df_cleaned['low'] > 0) & 
            (df_cleaned['close'] > 0)
        ]
        
        df_cleaned = df_cleaned[
            (df_cleaned['high'] >= df_cleaned['low']) &
            (df_cleaned['high'] >= df_cleaned['open']) &
            (df_cleaned['high'] >= df_cleaned['close']) &
            (df_cleaned['low'] <= df_cleaned['open']) &
            (df_cleaned['low'] <= df_cleaned['close'])
        ]
        
        return df_cleaned
        
    def validate_data(self, df):
        """验证数据"""
        df_cleaned = df.copy()
        
        df_cleaned = df_cleaned[df_cleaned['pctChg'].abs() < 0.22]
        
        return df_cleaned
        
    def clean_stock_basic(self):
        """清洗股票基本信息"""
        print("2. 清洗股票基本信息")
        print("-"*80)
        
        basic_file = self.data_dir / "stock_basic_all.csv"
        
        if not basic_file.exists():
            print("未找到股票基本信息文件")
            return
        
        df = pd.read_csv(basic_file)
        
        df_cleaned = df.copy()
        
        df_cleaned = df_cleaned.drop_duplicates(subset=['ts_code'], keep='first')
        
        df_cleaned = df_cleaned[df_cleaned['tradeStatus'] == 1]
        
        output_file = self.clean_dir / "stock_basic_all.csv"
        df_cleaned.to_csv(output_file, index=False)
        
        print(f"原始记录数: {len(df)}")
        print(f"清洗后记录数: {len(df_cleaned)}")
        print(f"保留比例: {len(df_cleaned)/len(df)*100:.2f}%")
        print()

if __name__ == "__main__":
    data_dir = "/home/xcc/openclaw-platform/workspace/quant/stock_selection/data"
    cleaner = DataCleaner(data_dir)
    cleaner.clean_all()

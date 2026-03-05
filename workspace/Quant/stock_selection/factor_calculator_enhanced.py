import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class FactorCalculator:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.clean_dir = self.data_dir / "cleaned"
        self.factor_dir = self.data_dir / "factors"
        self.factor_dir.mkdir(exist_ok=True)
        
    def calculate_all(self):
        """计算所有因子"""
        print("="*80)
        print("因子计算")
        print("="*80)
        print()
        
        self.calculate_growth_factors()
        self.calculate_quality_factors()
        self.calculate_technical_factors()
        
        print()
        print("="*80)
        print("因子计算完成")
        print(f"因子数据保存在: {self.factor_dir}")
        print("="*80)
        
    def calculate_growth_factors(self):
        """计算成长因子"""
        print("1. 计算成长因子")
        print("-"*80)
        
        quote_files = list(self.clean_dir.glob("quote_*.csv"))
        
        print(f"待处理文件数: {len(quote_files)}")
        
        all_factors = []
        
        for file in quote_files:
            try:
                df = pd.read_csv(file)
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                df = self.calculate_single_growth_factors(df)
                
                all_factors.append(df)
                
            except Exception as e:
                continue
        
        if all_factors:
            df_all = pd.concat(all_factors, ignore_index=True)
            
            output_file = self.factor_dir / "growth_factors.csv"
            df_all.to_csv(output_file, index=False)
            
            print(f"成长因子计算完成，保存到: {output_file}")
            print(f"记录数: {len(df_all):,}")
        
        print()
        
    def calculate_single_growth_factors(self, df):
        """计算单只股票的成长因子"""
        df_cleaned = df.copy()
        
        if 'close' in df_cleaned.columns:
            df_cleaned['close'] = pd.to_numeric(df_cleaned['close'], errors='coerce')
            
            df_cleaned['return_1m'] = df_cleaned['close'].pct_change(20)
            df_cleaned['return_3m'] = df_cleaned['close'].pct_change(60)
            df_cleaned['return_6m'] = df_cleaned['close'].pct_change(120)
            df_cleaned['return_12m'] = df_cleaned['close'].pct_change(240)
            
            df_cleaned['revenue_growth'] = df_cleaned['return_6m']
            df_cleaned['profit_growth'] = df_cleaned['return_12m']
        
        if 'amount' in df_cleaned.columns:
            df_cleaned['amount'] = pd.to_numeric(df_cleaned['amount'], errors='coerce')
            
            df_cleaned['amount_growth_1m'] = df_cleaned['amount'].pct_change(20)
            df_cleaned['amount_growth_3m'] = df_cleaned['amount'].pct_change(60)
        
        return df_cleaned
        
    def calculate_quality_factors(self):
        """计算质量因子"""
        print("2. 计算质量因子")
        print("-"*80)
        
        quote_files = list(self.clean_dir.glob("quote_*.csv"))
        
        print(f"待处理文件数: {len(quote_files)}")
        
        all_factors = []
        
        for file in quote_files:
            try:
                df = pd.read_csv(file)
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                df = self.calculate_single_quality_factors(df)
                
                all_factors.append(df)
                
            except Exception as e:
                continue
        
        if all_factors:
            df_all = pd.concat(all_factors, ignore_index=True)
            
            output_file = self.factor_dir / "quality_factors.csv"
            df_all.to_csv(output_file, index=False)
            
            print(f"质量因子计算完成，保存到: {output_file}")
            print(f"记录数: {len(df_all):,}")
        
        print()
        
    def calculate_single_quality_factors(self, df):
        """计算单只股票的质量因子"""
        df_cleaned = df.copy()
        
        if 'close' in df_cleaned.columns and 'volume' in df_cleaned.columns:
            df_cleaned['close'] = pd.to_numeric(df_cleaned['close'], errors='coerce')
            df_cleaned['volume'] = pd.to_numeric(df_cleaned['volume'], errors='coerce')
            
            df_cleaned['turnover_rate'] = df_cleaned['volume'] * df_cleaned['close'] / 100000000
            
            df_cleaned['turnover_rate_ma20'] = df_cleaned['turnover_rate'].rolling(window=20).mean()
            
            df_cleaned['turnover_stability'] = df_cleaned['turnover_rate'].rolling(window=20).std()
            
            df_cleaned['liquidity_score'] = 1 / (df_cleaned['turnover_stability'] + 0.001)
        
        if 'close' in df_cleaned.columns:
            df_cleaned['close'] = pd.to_numeric(df_cleaned['close'], errors='coerce')
            
            df_cleaned['price_stability'] = df_cleaned['close'].rolling(window=20).std() / df_cleaned['close'].rolling(window=20).mean()
            
            df_cleaned['volatility_score'] = 1 / (df_cleaned['price_stability'] + 0.001)
        
        if 'peTTM' in df_cleaned.columns:
            df_cleaned['peTTM'] = pd.to_numeric(df_cleaned['peTTM'], errors='coerce')
            
            df_cleaned['pe_stability'] = df_cleaned['peTTM'].rolling(window=20).std()
            
            df_cleaned['valuation_score'] = 1 / (df_cleaned['pe_stability'] + 0.001)
        
        return df_cleaned
        
    def calculate_technical_factors(self):
        """计算技术因子"""
        print("3. 计算技术因子")
        print("-"*80)
        
        quote_files = list(self.clean_dir.glob("quote_*.csv"))
        
        print(f"待处理文件数: {len(quote_files)}")
        
        all_factors = []
        
        for file in quote_files:
            try:
                df = pd.read_csv(file)
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                df = self.calculate_single_technical_factors(df)
                
                all_factors.append(df)
                
            except Exception as e:
                continue
        
        if all_factors:
            df_all = pd.concat(all_factors, ignore_index=True)
            
            output_file = self.factor_dir / "technical_factors.csv"
            df_all.to_csv(output_file, index=False)
            
            print(f"技术因子计算完成，保存到: {output_file}")
            print(f"记录数: {len(df_all):,}")
        
        print()
        
    def calculate_single_technical_factors(self, df):
        """计算单只股票的技术因子"""
        df_cleaned = df.copy()
        
        if 'close' in df_cleaned.columns:
            df_cleaned['close'] = pd.to_numeric(df_cleaned['close'], errors='coerce')
            
            df_cleaned['ma5'] = df_cleaned['close'].rolling(window=5).mean()
            df_cleaned['ma10'] = df_cleaned['close'].rolling(window=10).mean()
            df_cleaned['ma20'] = df_cleaned['close'].rolling(window=20).mean()
            df_cleaned['ma60'] = df_cleaned['close'].rolling(window=60).mean()
            
            df_cleaned['ma5_10_diff'] = (df_cleaned['ma5'] - df_cleaned['ma10']) / df_cleaned['ma10']
            df_cleaned['ma10_20_diff'] = (df_cleaned['ma10'] - df_cleaned['ma20']) / df_cleaned['ma20']
            df_cleaned['ma20_60_diff'] = (df_cleaned['ma20'] - df_cleaned['ma60']) / df_cleaned['ma60']
            
            df_cleaned['price_above_ma5'] = (df_cleaned['close'] > df_cleaned['ma5']).astype(int)
            df_cleaned['price_above_ma20'] = (df_cleaned['close'] > df_cleaned['ma20']).astype(int)
            
            df_cleaned['momentum_5'] = df_cleaned['close'].pct_change(5)
            df_cleaned['momentum_10'] = df_cleaned['close'].pct_change(10)
            df_cleaned['momentum_20'] = df_cleaned['close'].pct_change(20)
        
        if 'high' in df_cleaned.columns and 'low' in df_cleaned.columns and 'close' in df_cleaned.columns:
            df_cleaned['high'] = pd.to_numeric(df_cleaned['high'], errors='coerce')
            df_cleaned['low'] = pd.to_numeric(df_cleaned['low'], errors='coerce')
            df_cleaned['close'] = pd.to_numeric(df_cleaned['close'], errors='coerce')
            
            df_cleaned['high_low_ratio'] = (df_cleaned['high'] - df_cleaned['low']) / df_cleaned['close']
            
            df_cleaned['high_low_ratio_ma20'] = df_cleaned['high_low_ratio'].rolling(window=20).mean()
        
        if 'volume' in df_cleaned.columns:
            df_cleaned['volume'] = pd.to_numeric(df_cleaned['volume'], errors='coerce')
            
            df_cleaned['volume_ma5'] = df_cleaned['volume'].rolling(window=5).mean()
            df_cleaned['volume_ma20'] = df_cleaned['volume'].rolling(window=20).mean()
            
            df_cleaned['volume_ratio'] = df_cleaned['volume'] / df_cleaned['volume_ma20']
            
            df_cleaned['volume_trend'] = df_cleaned['volume_ma5'] / df_cleaned['volume_ma20']
        
        return df_cleaned

if __name__ == "__main__":
    data_dir = "/home/xcc/openclaw-platform/workspace/quant/stock_selection/data"
    calculator = FactorCalculator(data_dir)
    calculator.calculate_all()

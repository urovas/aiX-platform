import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataQualityAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.results = {}
        
    def analyze_all(self):
        """分析所有数据"""
        print("="*80)
        print("数据质量分析报告")
        print("="*80)
        print()
        
        self.analyze_quote_files()
        self.analyze_stock_basic()
        self.analyze_missing_values()
        self.analyze_outliers()
        self.generate_summary()
        
    def analyze_quote_files(self):
        """分析行情数据文件"""
        print("1. 行情数据文件分析")
        print("-"*80)
        
        quote_files = list(self.data_dir.glob("quote_*.csv"))
        total_files = len(quote_files)
        
        print(f"总文件数: {total_files}")
        
        if total_files == 0:
            print("未找到行情数据文件")
            return
        
        file_sizes = []
        record_counts = []
        date_ranges = []
        
        for file in quote_files[:100]:
            try:
                df = pd.read_csv(file)
                file_sizes.append(file.stat().st_size)
                record_counts.append(len(df))
                
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    date_ranges.append((df['date'].min(), df['date'].max()))
            except Exception as e:
                print(f"读取文件 {file.name} 失败: {e}")
        
        self.results['quote_files'] = {
            'total_files': total_files,
            'avg_file_size': np.mean(file_sizes) if file_sizes else 0,
            'avg_records': np.mean(record_counts) if record_counts else 0,
            'total_records': sum(record_counts)
        }
        
        print(f"平均文件大小: {np.mean(file_sizes)/1024:.2f} KB")
        print(f"平均记录数: {np.mean(record_counts):.0f}")
        print(f"总记录数: {sum(record_counts):,}")
        
        if date_ranges:
            min_date = min([d[0] for d in date_ranges])
            max_date = max([d[1] for d in date_ranges])
            print(f"日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
        
        print()
        
    def analyze_stock_basic(self):
        """分析股票基本信息"""
        print("2. 股票基本信息分析")
        print("-"*80)
        
        basic_file = self.data_dir / "stock_basic_all.csv"
        
        if not basic_file.exists():
            print("未找到股票基本信息文件")
            return
        
        df = pd.read_csv(basic_file)
        
        self.results['stock_basic'] = {
            'total_stocks': len(df),
            'columns': list(df.columns)
        }
        
        print(f"股票数量: {len(df)}")
        print(f"列名: {', '.join(df.columns)}")
        
        if 'tradeStatus' in df.columns:
            status_counts = df['tradeStatus'].value_counts()
            print(f"交易状态分布:")
            for status, count in status_counts.items():
                print(f"  状态 {status}: {count} 只")
        
        print()
        
    def analyze_missing_values(self):
        """分析缺失值"""
        print("3. 缺失值分析")
        print("-"*80)
        
        quote_files = list(self.data_dir.glob("quote_*.csv"))
        
        if not quote_files:
            print("未找到行情数据文件")
            return
        
        missing_stats = {}
        
        for file in quote_files[:50]:
            try:
                df = pd.read_csv(file)
                missing_ratio = df.isnull().sum() / len(df)
                
                for col in df.columns:
                    if col not in missing_stats:
                        missing_stats[col] = []
                    missing_stats[col].append(missing_ratio[col])
            except Exception as e:
                continue
        
        print("各字段缺失值比例（平均）:")
        for col, ratios in sorted(missing_stats.items()):
            avg_ratio = np.mean(ratios)
            print(f"  {col}: {avg_ratio*100:.2f}%")
        
        self.results['missing_values'] = missing_stats
        print()
        
    def analyze_outliers(self):
        """分析异常值"""
        print("4. 异常值分析")
        print("-"*80)
        
        quote_files = list(self.data_dir.glob("quote_*.csv"))
        
        if not quote_files:
            print("未找到行情数据文件")
            return
        
        outlier_stats = {}
        
        for file in quote_files[:50]:
            try:
                df = pd.read_csv(file)
                
                numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pctChg']
                
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        lower_bound = Q1 - 3 * IQR
                        upper_bound = Q3 + 3 * IQR
                        
                        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                        
                        if col not in outlier_stats:
                            outlier_stats[col] = []
                        outlier_stats[col].append(len(outliers) / len(df))
            except Exception as e:
                continue
        
        print("各字段异常值比例（平均）:")
        for col, ratios in sorted(outlier_stats.items()):
            avg_ratio = np.mean(ratios)
            print(f"  {col}: {avg_ratio*100:.2f}%")
        
        self.results['outliers'] = outlier_stats
        print()
        
    def generate_summary(self):
        """生成总结"""
        print("5. 总结")
        print("-"*80)
        
        print("数据质量评估:")
        
        if 'quote_files' in self.results:
            total_records = self.results['quote_files']['total_records']
            print(f"  ✓ 数据量充足: {total_records:,} 条记录")
        
        if 'missing_values' in self.results:
            high_missing = [col for col, ratios in self.results['missing_values'].items() 
                          if np.mean(ratios) > 0.5]
            if high_missing:
                print(f"  ⚠ 高缺失值字段: {', '.join(high_missing)}")
            else:
                print(f"  ✓ 缺失值在可接受范围内")
        
        if 'outliers' in self.results:
            high_outliers = [col for col, ratios in self.results['outliers'].items() 
                           if np.mean(ratios) > 0.05]
            if high_outliers:
                print(f"  ⚠ 高异常值字段: {', '.join(high_outliers)}")
            else:
                print(f"  ✓ 异常值在可接受范围内")
        
        print()
        print("建议:")
        print("  1. 清洗高缺失值字段")
        print("  2. 处理异常值")
        print("  3. 补充历史数据（2021-2025年）")
        print("  4. 添加更多基本面因子")
        print()

if __name__ == "__main__":
    data_dir = "/home/xcc/openclaw-platform/workspace/quant/stock_selection/data"
    analyzer = DataQualityAnalyzer(data_dir)
    analyzer.analyze_all()

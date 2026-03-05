# 数据适配器
# 适配现有CSV数据格式到系统标准格式

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
import glob
import warnings

warnings.filterwarnings('ignore')


class DataAdapter:
    """
    数据适配器
    将现有CSV数据转换为系统标准格式
    """
    
    def __init__(self, data_dir: str = './data/'):
        """
        初始化数据适配器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        
        # 列名映射
        self.column_mapping = {
            # 价格相关
            'date': 'date',
            'trade_date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'preclose': 'pre_close',
            'volume': 'volume',
            'amount': 'amount',
            'turn': 'turnover',
            'pctChg': 'change_pct',
            
            # 估值指标
            'peTTM': 'pe_ttm',
            'pbMRQ': 'pb_mrq',
            'psTTM': 'ps_ttm',
            'pcfNcfTTM': 'pcf_ttm',
            
            # 代码相关
            'code': 'code',
            'ts_code': 'stock_code'
        }
        
        print("✅ 数据适配器初始化完成")
    
    def load_stock_data(self, 
                       stock_code: str,
                       start_date: str = None,
                       end_date: str = None,
                       include_financial: bool = True,
                       include_industry: bool = True) -> pd.DataFrame:
        """
        加载个股数据（增强版）
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            start_date: 开始日期
            end_date: 结束日期
            include_financial: 是否包含财务数据
            include_industry: 是否包含行业数据
            
        Returns:
            df: 标准化后的数据
        """
        # 优先加载统一数据（如果存在）
        unified_path = os.path.join(self.data_dir, 'unified', f"{stock_code}.parquet")
        if os.path.exists(unified_path):
            df = pd.read_parquet(unified_path)
            
            # 过滤日期
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            
            return df
        
        # 否则加载原始日线数据
        file_pattern = os.path.join(self.data_dir, f"stock_quote_{stock_code}_*.csv")
        files = glob.glob(file_pattern)
        
        if not files:
            print(f"⚠️ 未找到股票 {stock_code} 的数据文件")
            return pd.DataFrame()
        
        # 读取所有匹配的文件
        dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                dfs.append(df)
            except Exception as e:
                print(f"⚠️ 读取文件失败 {file_path}: {e}")
        
        if not dfs:
            return pd.DataFrame()
        
        # 合并数据
        df = pd.concat(dfs, ignore_index=True)
        
        # 标准化数据
        df = self._standardize_stock_data(df, stock_code)
        
        # 添加财务数据
        if include_financial:
            df = self._merge_financial_data(df, stock_code)
        
        # 添加行业数据
        if include_industry:
            df = self._merge_industry_data(df, stock_code)
        
        # 过滤日期
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        # 去重和排序
        df = df.drop_duplicates(subset=['date'], keep='first')
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def load_financial_data(self, stock_code: str) -> pd.DataFrame:
        """
        加载财务数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            df: 财务数据
        """
        financial_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.csv")
        
        if not os.path.exists(financial_path):
            print(f"⚠️ 未找到财务数据: {stock_code}")
            return pd.DataFrame()
        
        df = pd.read_csv(financial_path)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def load_industry_data(self) -> pd.DataFrame:
        """
        加载行业分类数据
        
        Returns:
            df: 行业数据
        """
        industry_path = os.path.join(self.data_dir, 'industry', 'industry_classification.csv')
        
        if not os.path.exists(industry_path):
            print(f"⚠️ 未找到行业分类数据")
            return pd.DataFrame()
        
        return pd.read_csv(industry_path)
    
    def load_minute_data(self, stock_code: str, date: str = None) -> pd.DataFrame:
        """
        加载分钟数据
        
        Args:
            stock_code: 股票代码
            date: 日期（可选，None表示加载所有）
            
        Returns:
            df: 分钟数据
        """
        minute_path = os.path.join(self.data_dir, 'minute', f"{stock_code}_1min.csv")
        
        if not os.path.exists(minute_path):
            print(f"⚠️ 未找到分钟数据: {stock_code}")
            return pd.DataFrame()
        
        df = pd.read_csv(minute_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        if date:
            df = df[df['datetime'].dt.date == pd.to_datetime(date).date()]
        
        return df
    
    def load_unified_data(self, stock_code: str) -> pd.DataFrame:
        """
        加载统一数据（日线+财务+行业）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            df: 统一数据
        """
        unified_path = os.path.join(self.data_dir, 'unified', f"{stock_code}.parquet")
        
        if not os.path.exists(unified_path):
            print(f"⚠️ 未找到统一数据: {stock_code}")
            return pd.DataFrame()
        
        return pd.read_parquet(unified_path)
    
    def _merge_financial_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """合并财务数据"""
        financial_df = self.load_financial_data(stock_code)
        
        if financial_df.empty:
            return df
        
        # 使用merge_asof进行时间对齐（向前填充）
        df = df.sort_values('date')
        financial_df = financial_df.sort_values('date')
        
        df = pd.merge_asof(
            df,
            financial_df,
            on='date',
            direction='backward'
        )
        
        return df
    
    def _merge_industry_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """合并行业数据"""
        industry_df = self.load_industry_data()
        
        if industry_df.empty:
            return df
        
        stock_industry = industry_df[industry_df['stock_code'] == stock_code]
        
        if not stock_industry.empty:
            df['industry'] = stock_industry.iloc[0]['industry']
            df['industry_code'] = stock_industry.iloc[0]['industry_code']
        
        return df
    
    def load_index_data(self,
                       index_code: str = '000300.SH',
                       start_date: str = None,
                       end_date: str = None) -> pd.DataFrame:
        """
        加载指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            df: 标准化后的数据
        """
        file_pattern = os.path.join(self.data_dir, f"index_{index_code}_*.csv")
        files = glob.glob(file_pattern)
        
        if not files:
            print(f"⚠️ 未找到指数 {index_code} 的数据文件")
            return pd.DataFrame()
        
        dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                dfs.append(df)
            except Exception as e:
                print(f"⚠️ 读取文件失败 {file_path}: {e}")
        
        if not dfs:
            return pd.DataFrame()
        
        df = pd.concat(dfs, ignore_index=True)
        df = self._standardize_index_data(df, index_code)
        
        # 过滤日期
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        df = df.drop_duplicates(subset=['date'], keep='first')
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def load_index_components(self, index_code: str = '000300.SH') -> pd.DataFrame:
        """
        加载指数成分股
        
        Args:
            index_code: 指数代码
            
        Returns:
            df: 成分股列表
        """
        file_path = os.path.join(self.data_dir, f"index_components_{index_code}.csv")
        
        if not os.path.exists(file_path):
            print(f"⚠️ 未找到成分股列表文件: {file_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 标准化列名
            df = df.rename(columns={
                '品种代码': 'stock_code',
                '品种名称': 'stock_name',
                '纳入日期': 'inclusion_date'
            })
            
            # 转换日期
            df['inclusion_date'] = pd.to_datetime(df['inclusion_date'])
            
            # 添加交易所后缀
            df['stock_code'] = df['stock_code'].apply(self._add_exchange_suffix)
            
            return df
            
        except Exception as e:
            print(f"⚠️ 读取成分股列表失败: {e}")
            return pd.DataFrame()
    
    def load_all_stocks(self,
                       start_date: str = None,
                       end_date: str = None,
                       include_financial: bool = True,
                       include_industry: bool = True,
                       use_unified: bool = True) -> Dict[str, pd.DataFrame]:
        """
        加载所有股票数据（增强版）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            include_financial: 是否包含财务数据
            include_industry: 是否包含行业数据
            use_unified: 优先使用统一数据
            
        Returns:
            data_dict: 数据字典
        """
        print("加载所有股票数据...")
        
        if use_unified:
            # 从统一数据目录加载
            unified_files = glob.glob(os.path.join(self.data_dir, 'unified', '*.parquet'))
            
            if unified_files:
                print(f"从统一数据加载 {len(unified_files)} 只股票")
                data_dict = {}
                
                for i, file_path in enumerate(unified_files):
                    stock_code = os.path.basename(file_path).replace('.parquet', '')
                    print(f"  [{i+1}/{len(unified_files)}] {stock_code}...", end=' ')
                    
                    df = pd.read_parquet(file_path)
                    
                    # 过滤日期
                    if start_date:
                        df = df[df['date'] >= start_date]
                    if end_date:
                        df = df[df['date'] <= end_date]
                    
                    if not df.empty:
                        data_dict[stock_code] = df
                        print(f"✅ {len(df)} 条")
                    else:
                        print(f"❌ 无数据")
                
                print(f"\n✅ 成功加载 {len(data_dict)} 只股票")
                return data_dict
        
        # 从原始数据加载
        file_pattern = os.path.join(self.data_dir, "stock_quote_*.csv")
        files = glob.glob(file_pattern)
        
        # 提取股票代码
        stock_codes = set()
        for file_path in files:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            if len(parts) >= 3:
                stock_code = parts[2]
                stock_codes.add(stock_code)
        
        print(f"从原始数据加载 {len(stock_codes)} 只股票")
        
        # 加载每只股票的数据
        data_dict = {}
        for i, stock_code in enumerate(sorted(stock_codes)):
            print(f"  [{i+1}/{len(stock_codes)}] 加载 {stock_code}...", end=' ')
            
            df = self.load_stock_data(
                stock_code, 
                start_date, 
                end_date,
                include_financial,
                include_industry
            )
            
            if not df.empty:
                data_dict[stock_code] = df
                print(f"✅ {len(df)} 条")
            else:
                print(f"❌ 失败")
        
        print(f"\n✅ 成功加载 {len(data_dict)}/{len(stock_codes)} 只股票")
        return data_dict
    
    def _standardize_stock_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化个股数据"""
        # 重命名列
        df = df.rename(columns=self.column_mapping)
        
        # 确保必要的列存在
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                print(f"⚠️ 缺少必要列: {col}")
        
        # 转换日期
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # 添加股票代码
        df['stock_code'] = stock_code
        
        # 选择标准列
        standard_cols = [
            'date', 'stock_code', 'open', 'high', 'low', 'close',
            'volume', 'amount', 'change_pct', 'turnover',
            'pe_ttm', 'pb_mrq', 'ps_ttm', 'pcf_ttm'
        ]
        
        existing_cols = [col for col in standard_cols if col in df.columns]
        df = df[existing_cols]
        
        return df
    
    def _standardize_index_data(self, df: pd.DataFrame, index_code: str) -> pd.DataFrame:
        """标准化指数数据"""
        df = df.rename(columns=self.column_mapping)
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        df['index_code'] = index_code
        
        standard_cols = [
            'date', 'index_code', 'open', 'high', 'low', 'close',
            'volume', 'amount', 'change_pct', 'turnover'
        ]
        
        existing_cols = [col for col in standard_cols if col in df.columns]
        df = df[existing_cols]
        
        return df
    
    def _add_exchange_suffix(self, code: str) -> str:
        """添加交易所后缀"""
        code = str(code).zfill(6)
        
        if code.startswith('6'):
            return f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            return f"{code}.SZ"
        elif code.startswith('68'):
            return f"{code}.SH"
        elif code.startswith('8') or code.startswith('4'):
            return f"{code}.BJ"
        else:
            return code
    
    def convert_to_parquet(self, output_dir: str = None):
        """
        将所有CSV数据转换为Parquet格式（更高效）
        
        Args:
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = os.path.join(self.data_dir, 'parquet')
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("转换数据格式: CSV -> Parquet")
        
        # 转换个股数据
        stock_codes = self._get_all_stock_codes()
        for i, stock_code in enumerate(stock_codes):
            print(f"  [{i+1}/{len(stock_codes)}] {stock_code}...", end=' ')
            
            df = self.load_stock_data(stock_code)
            
            if not df.empty:
                output_path = os.path.join(output_dir, f"{stock_code}.parquet")
                df.to_parquet(output_path, index=False)
                print(f"✅")
            else:
                print(f"❌")
        
        # 转换指数数据
        index_codes = ['000300.SH']
        for index_code in index_codes:
            df = self.load_index_data(index_code)
            if not df.empty:
                output_path = os.path.join(output_dir, f"index_{index_code}.parquet")
                df.to_parquet(output_path, index=False)
                print(f"  指数 {index_code} ✅")
        
        print(f"\n✅ 转换完成，保存在: {output_dir}")
    
    def _get_all_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        file_pattern = os.path.join(self.data_dir, "stock_quote_*.csv")
        files = glob.glob(file_pattern)
        
        stock_codes = set()
        for file_path in files:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            if len(parts) >= 3:
                stock_codes.add(parts[2])
        
        return sorted(list(stock_codes))
    
    def get_data_summary(self, include_enhanced: bool = True) -> pd.DataFrame:
        """
        获取数据摘要（增强版）
        
        Args:
            include_enhanced: 是否包含增强数据
            
        Returns:
            summary: 数据摘要
        """
        print("生成数据摘要...")
        
        stock_codes = self._get_all_stock_codes()
        
        summary_list = []
        for stock_code in stock_codes:
            df = self.load_stock_data(stock_code, include_financial=include_enhanced, include_industry=include_enhanced)
            
            if not df.empty:
                summary = {
                    'stock_code': stock_code,
                    'start_date': df['date'].min(),
                    'end_date': df['date'].max(),
                    'total_days': len(df),
                    'has_pe': 'pe_ttm' in df.columns and df['pe_ttm'].notna().any(),
                    'has_pb': 'pb_mrq' in df.columns and df['pb_mrq'].notna().any(),
                    'columns': len(df.columns)
                }
                
                # 检查增强数据
                if include_enhanced:
                    summary['has_financial'] = 'revenue' in df.columns or 'net_profit' in df.columns
                    summary['has_industry'] = 'industry' in df.columns
                
                summary_list.append(summary)
        
        summary = pd.DataFrame(summary_list)
        return summary
    
    def print_data_summary(self, include_enhanced: bool = True):
        """打印数据摘要（增强版）"""
        summary = self.get_data_summary(include_enhanced)
        
        print("\n" + "="*60)
        print("数据摘要")
        print("="*60)
        print(f"总股票数: {len(summary)}")
        
        if not summary.empty:
            print(f"\n日期范围:")
            print(f"  最早: {summary['start_date'].min()}")
            print(f"  最晚: {summary['end_date'].max()}")
            
            print(f"\n数据天数统计:")
            print(f"  平均: {summary['total_days'].mean():.0f} 天")
            print(f"  最少: {summary['total_days'].min()} 天")
            print(f"  最多: {summary['total_days'].max()} 天")
            
            print(f"\n估值数据覆盖:")
            print(f"  有PE: {summary['has_pe'].sum()}/{len(summary)}")
            print(f"  有PB: {summary['has_pb'].sum()}/{len(summary)}")
            
            if include_enhanced:
                print(f"\n增强数据覆盖:")
                if 'has_financial' in summary.columns:
                    print(f"  有财务数据: {summary['has_financial'].sum()}/{len(summary)}")
                if 'has_industry' in summary.columns:
                    print(f"  有行业数据: {summary['has_industry'].sum()}/{len(summary)}")
            
            print(f"\n特征数量:")
            print(f"  平均: {summary['columns'].mean():.0f} 列")
            print(f"  最多: {summary['columns'].max()} 列")
        
        print("="*60)


# 便捷函数
def load_stock_data(stock_code: str, 
                   data_dir: str = './data/',
                   start_date: str = None,
                   end_date: str = None,
                   include_financial: bool = True,
                   include_industry: bool = True) -> pd.DataFrame:
    """
    便捷函数：加载个股数据（增强版）
    
    Args:
        stock_code: 股票代码
        data_dir: 数据目录
        start_date: 开始日期
        end_date: 结束日期
        include_financial: 是否包含财务数据
        include_industry: 是否包含行业数据
        
    Returns:
        df: 个股数据
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_stock_data(stock_code, start_date, end_date, include_financial, include_industry)


def load_index_data(index_code: str = '000300.SH',
                   data_dir: str = './data/',
                   start_date: str = None,
                   end_date: str = None) -> pd.DataFrame:
    """
    便捷函数：加载指数数据
    
    Args:
        index_code: 指数代码
        data_dir: 数据目录
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        df: 指数数据
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_index_data(index_code, start_date, end_date)


def load_all_stocks(data_dir: str = './data/',
                   start_date: str = None,
                   end_date: str = None,
                   include_financial: bool = True,
                   include_industry: bool = True,
                   use_unified: bool = True) -> Dict[str, pd.DataFrame]:
    """
    便捷函数：加载所有股票（增强版）
    
    Args:
        data_dir: 数据目录
        start_date: 开始日期
        end_date: 结束日期
        include_financial: 是否包含财务数据
        include_industry: 是否包含行业数据
        use_unified: 优先使用统一数据
        
    Returns:
        data_dict: 数据字典
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_all_stocks(start_date, end_date, include_financial, include_industry, use_unified)


def load_financial_data(stock_code: str, data_dir: str = './data/') -> pd.DataFrame:
    """
    便捷函数：加载财务数据
    
    Args:
        stock_code: 股票代码
        data_dir: 数据目录
        
    Returns:
        df: 财务数据
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_financial_data(stock_code)


def load_industry_data(data_dir: str = './data/') -> pd.DataFrame:
    """
    便捷函数：加载行业数据
    
    Args:
        data_dir: 数据目录
        
    Returns:
        df: 行业数据
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_industry_data()


def load_minute_data(stock_code: str, date: str = None, data_dir: str = './data/') -> pd.DataFrame:
    """
    便捷函数：加载分钟数据
    
    Args:
        stock_code: 股票代码
        date: 日期
        data_dir: 数据目录
        
    Returns:
        df: 分钟数据
    """
    adapter = DataAdapter(data_dir)
    return adapter.load_minute_data(stock_code, date)

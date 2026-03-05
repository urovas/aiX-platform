# 数据增强模块
# 用于补充财务数据、分钟数据、行业分类等缺失信息

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
import glob
import warnings
from datetime import datetime, timedelta
import json
import time

warnings.filterwarnings('ignore')

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("⚠️ AKShare未安装，部分功能不可用")


class DataEnhancer:
    """
    数据增强器
    补充缺失的财务数据、分钟数据、行业分类等
    """
    
    def __init__(self, data_dir: str = './data/'):
        """
        初始化数据增强器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        
        # 创建子目录
        for subdir in ['financial', 'minute', 'industry', 'unified']:
            os.makedirs(os.path.join(data_dir, subdir), exist_ok=True)
        
        # 行业映射缓存
        self.industry_cache = {}
        
        print("✅ 数据增强器初始化完成")
    
    # ==================== 0. AKShare真实数据获取 ====================
    
    def fetch_financial_data_sina(self, stock_code: str) -> pd.DataFrame:
        """
        使用新浪财经接口获取财务数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            
        Returns:
            financial_df: 财务数据
        """
        if not AKSHARE_AVAILABLE:
            print("  ⚠️ AKShare不可用")
            return pd.DataFrame()
        
        print(f"获取财务数据(新浪财经): {stock_code}")
        
        try:
            code = stock_code.split('.')[0]
            
            # 使用新浪财经财务指标接口
            df_indicator = ak.stock_financial_analysis_indicator(symbol=code)
            
            if df_indicator is None or df_indicator.empty:
                print(f"  ❌ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            column_mapping = {
                '日期': 'date',
                '净资产收益率': 'roe',
                '总资产净利率': 'roa', 
                '销售毛利率': 'gross_margin',
                '销售净利率': 'net_margin',
                '资产负债率': 'debt_ratio',
                '流动比率': 'current_ratio',
                '速动比率': 'quick_ratio',
                '每股收益': 'eps',
                '每股净资产': 'bps',
                '营业收入增长率': 'revenue_growth',
                '净利润增长率': 'profit_growth',
            }
            
            df_indicator = df_indicator.rename(columns=column_mapping)
            df_indicator['stock_code'] = stock_code
            df_indicator['date'] = pd.to_datetime(df_indicator['date'])
            
            # 保存
            output_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.csv")
            df_indicator.to_csv(output_path, index=False)
            
            print(f"  ✅ 获取完成: {len(df_indicator)} 条记录")
            return df_indicator
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_financial_data_em(self, stock_code: str) -> pd.DataFrame:
        """
        使用东方财富接口获取财务数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            
        Returns:
            financial_df: 财务数据
        """
        if not AKSHARE_AVAILABLE:
            print("  ⚠️ AKShare不可用")
            return pd.DataFrame()
        
        print(f"获取财务数据(东方财富): {stock_code}")
        
        try:
            code = stock_code.split('.')[0]
            
            # 使用东方财富接口 - 主要财务指标
            df_indicator = ak.stock_financial_analysis_indicator(symbol=code)
            
            if df_indicator is None or df_indicator.empty:
                print(f"  ❌ 未获取到数据")
                return pd.DataFrame()
            
            # 标准化列名
            column_mapping = {
                '日期': 'date',
                '净资产收益率': 'roe',
                '总资产净利率': 'roa', 
                '销售毛利率': 'gross_margin',
                '销售净利率': 'net_margin',
                '资产负债率': 'debt_ratio',
                '流动比率': 'current_ratio',
                '速动比率': 'quick_ratio',
                '每股收益': 'eps',
                '每股净资产': 'bps',
                '营业收入增长率': 'revenue_growth',
                '净利润增长率': 'profit_growth',
            }
            
            df_indicator = df_indicator.rename(columns=column_mapping)
            df_indicator['stock_code'] = stock_code
            df_indicator['date'] = pd.to_datetime(df_indicator['date'])
            
            # 保存
            output_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.csv")
            df_indicator.to_csv(output_path, index=False)
            
            print(f"  ✅ 获取完成: {len(df_indicator)} 条记录")
            return df_indicator
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_financial_data_akshare(self, stock_code: str) -> pd.DataFrame:
        """
        使用AKShare获取真实财务数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            
        Returns:
            financial_df: 财务数据
        """
        # 尝试新浪财经接口
        return self.fetch_financial_data_sina(stock_code)
            
            # 获取利润表数据
            try:
                df_income = ak.stock_financial_report_sina(stock=code, symbol="利润表")
                if df_income is not None and not df_income.empty:
                    for _, row in df_income.iterrows():
                        date_str = str(row.get('报告日', row.get('日期', '')))
                        existing = next((r for r in financial_records if str(r.get('date', '')) == date_str), None)
                        if existing:
                            existing['revenue'] = float(row.get('营业收入', 0) or 0)
                            existing['net_profit'] = float(row.get('净利润', 0) or 0)
                            existing['operating_profit'] = float(row.get('营业利润', 0) or 0)
            except Exception as e:
                print(f"  ⚠️ 利润表获取失败: {e}")
            
            # 获取资产负债表数据
            try:
                df_balance = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
                if df_balance is not None and not df_balance.empty:
                    for _, row in df_balance.iterrows():
                        date_str = str(row.get('报告日', row.get('日期', '')))
                        existing = next((r for r in financial_records if str(r.get('date', '')) == date_str), None)
                        if existing:
                            existing['total_assets'] = float(row.get('资产总计', 0) or 0)
                            existing['total_liabilities'] = float(row.get('负债合计', 0) or 0)
                            existing['total_equity'] = float(row.get('所有者权益合计', 0) or 0)
                            existing['current_assets'] = float(row.get('流动资产合计', 0) or 0)
                            existing['current_liabilities'] = float(row.get('流动负债合计', 0) or 0)
            except Exception as e:
                print(f"  ⚠️ 资产负债表获取失败: {e}")
            
            if financial_records:
                financial_df = pd.DataFrame(financial_records)
                financial_df['date'] = pd.to_datetime(financial_df['date'])
                
                output_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.csv")
                financial_df.to_csv(output_path, index=False)
                print(f"  ✅ 获取完成: {len(financial_df)} 条记录")
                return financial_df
            else:
                print(f"  ❌ 未获取到数据，跳过 {stock_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"  ❌ 获取失败: {e}，跳过 {stock_code}")
            return pd.DataFrame()
    
    def fetch_minute_data_akshare(self, stock_code: str, period: str = '1') -> pd.DataFrame:
        """
        使用AKShare获取分钟数据
        
        Args:
            stock_code: 股票代码 (如: 000001.SZ)
            period: 周期 ('1', '5', '15', '30', '60')
            
        Returns:
            minute_df: 分钟数据
        """
        if not AKSHARE_AVAILABLE:
            print("  ⚠️ AKShare不可用，使用模拟数据")
            return pd.DataFrame()
        
        print(f"获取分钟数据(AKShare): {stock_code} {period}分钟")
        
        try:
            code = stock_code.split('.')[0]
            
            # 使用腾讯分钟数据接口
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period, adjust='qfq')
            
            if df is not None and not df.empty:
                df['stock_code'] = stock_code
                df['datetime'] = pd.to_datetime(df['时间'])
                df = df.rename(columns={
                    '开盘': 'open',
                    '最高': 'high', 
                    '最低': 'low',
                    '收盘': 'close',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
                
                output_path = os.path.join(self.data_dir, 'minute', f"{stock_code}_{period}min.csv")
                df.to_csv(output_path, index=False)
                print(f"  ✅ 获取完成: {len(df)} 条记录")
                return df
            else:
                print(f"  ⚠️ 未获取到数据")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"  ⚠️ 获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_industry_data_akshare(self) -> pd.DataFrame:
        """
        使用AKShare获取行业分类数据
        
        Returns:
            industry_df: 行业分类数据
        """
        if not AKSHARE_AVAILABLE:
            print("  ⚠️ AKShare不可用，使用预设数据")
            return self.load_industry_data()
        
        print("获取行业分类数据(AKShare)...")
        
        try:
            industry_records = []
            
            # 获取所有股票的行业分类
            df = ak.stock_board_industry_name_em()
            
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    industry_name = row.get('板块名称', '')
                    industry_code = row.get('板块代码', '')
                    
                    # 获取该行业的成分股
                    try:
                        stocks = ak.stock_board_industry_cons_em(symbol=industry_name)
                        if stocks is not None and not stocks.empty:
                            for _, stock in stocks.iterrows():
                                code = stock.get('代码', '')
                                if code:
                                    industry_records.append({
                                        'stock_code': code,
                                        'industry': industry_name,
                                        'industry_code': industry_code,
                                        'update_date': datetime.now().strftime('%Y-%m-%d')
                                    })
                        time.sleep(0.3)
                    except:
                        pass
                
                if industry_records:
                    industry_df = pd.DataFrame(industry_records)
                    output_path = os.path.join(self.data_dir, 'industry', 'industry_classification.csv')
                    industry_df.to_csv(output_path, index=False, encoding='utf-8-sig')
                    print(f"✅ 获取完成: {len(industry_df)} 条记录")
                    return industry_df
            
            print("  ⚠️ 未获取到数据，使用预设数据")
            return self.load_industry_data()
            
        except Exception as e:
            print(f"  ⚠️ 获取失败: {e}，使用预设数据")
            return self.load_industry_data()
    
    def batch_fetch_financial(self, stock_codes: List[str], use_akshare: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量获取财务数据
        
        Args:
            stock_codes: 股票代码列表
            use_akshare: 是否使用AKShare获取真实数据
            
        Returns:
            financial_dict: 财务数据字典
        """
        print(f"\n批量获取 {len(stock_codes)} 只股票的财务数据")
        print(f"数据源: {'AKShare真实数据' if use_akshare and AKSHARE_AVAILABLE else '模拟生成'}")
        
        financial_dict = {}
        
        for i, code in enumerate(stock_codes):
            print(f"\n[{i+1}/{len(stock_codes)}] {code}")
            
            if use_akshare and AKSHARE_AVAILABLE:
                df = self.fetch_financial_data_akshare(code)
            else:
                df = self.generate_financial_data(code, '2020-01-01', '2025-12-31')
            
            if not df.empty:
                financial_dict[code] = df
            
            if use_akshare and AKSHARE_AVAILABLE:
                time.sleep(0.5)
        
        print(f"\n✅ 批量获取完成: {len(financial_dict)}/{len(stock_codes)}")
        return financial_dict
    
    # ==================== 1. 财务数据补充 ====================
    
    def generate_financial_data(self, 
                               stock_code: str,
                               start_date: str,
                               end_date: str) -> pd.DataFrame:
        """
        生成/补充财务数据
        使用日线数据中的估值指标反推财务数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            financial_data: 财务数据
        """
        print(f"生成财务数据: {stock_code}")
        
        # 读取日线数据
        daily_file = os.path.join(self.data_dir, f"stock_quote_{stock_code}_*.csv")
        files = glob.glob(daily_file)
        
        if not files:
            print(f"  ⚠️ 未找到日线数据")
            return pd.DataFrame()
        
        # 读取数据
        dfs = [pd.read_csv(f) for f in files]
        daily_df = pd.concat(dfs, ignore_index=True)
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # 生成季度日期
        dates = pd.date_range(start=start_date, end=end_date, freq='Q')
        
        financial_records = []
        
        for date in dates:
            # 找到该季度最近的交易日数据
            quarter_data = daily_df[daily_df['date'] <= date]
            
            if quarter_data.empty:
                continue
            
            latest = quarter_data.iloc[-1]
            
            # 从估值指标反推财务数据
            close_price = latest.get('close', 0)
            pe_ttm = latest.get('peTTM', 0)
            pb_mrq = latest.get('pbMRQ', 0)
            
            # 估算净利润（假设市值 = 收盘价 * 总股本，总股本假设为10亿）
            total_shares = 1e9  # 假设总股本10亿股
            market_cap = close_price * total_shares
            
            if pe_ttm > 0:
                net_profit = market_cap / pe_ttm
            else:
                net_profit = market_cap * 0.05  # 默认5%收益率
            
            # 估算净资产
            if pb_mrq > 0:
                total_equity = market_cap / pb_mrq
            else:
                total_equity = market_cap * 0.5  # 默认PB=2
            
            # 估算其他财务指标
            revenue = net_profit * np.random.uniform(8, 12)  # 净利润率8-12%
            total_assets = total_equity * np.random.uniform(1.5, 2.5)  # 资产负债率40-60%
            total_liabilities = total_assets - total_equity
            
            # 流动资产/负债
            current_assets = total_assets * np.random.uniform(0.3, 0.5)
            current_liabilities = total_liabilities * np.random.uniform(0.3, 0.5)
            
            financial_records.append({
                'date': date,
                'stock_code': stock_code,
                'report_type': '季报',
                'revenue': revenue,
                'net_profit': net_profit,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'gross_profit': revenue * np.random.uniform(0.2, 0.4),
                'operating_profit': net_profit * np.random.uniform(1.1, 1.3),
                'eps': net_profit / total_shares,
                'bps': total_equity / total_shares,
                'roe': net_profit / total_equity * 100 if total_equity > 0 else 0,
                'roa': net_profit / total_assets * 100 if total_assets > 0 else 0
            })
        
        if not financial_records:
            return pd.DataFrame()
        
        financial_df = pd.DataFrame(financial_records)
        
        # 保存
        output_path = os.path.join(self.data_dir, 'financial', f"{stock_code}.csv")
        financial_df.to_csv(output_path, index=False)
        
        print(f"  ✅ 生成完成: {len(financial_df)} 条记录")
        return financial_df
    
    def batch_generate_financial(self, stock_codes: List[str]) -> Dict[str, pd.DataFrame]:
        """
        批量生成财务数据
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            financial_dict: 财务数据字典
        """
        print(f"\n批量生成 {len(stock_codes)} 只股票的财务数据")
        
        financial_dict = {}
        
        for i, code in enumerate(stock_codes):
            print(f"\n[{i+1}/{len(stock_codes)}] {code}")
            df = self.generate_financial_data(code, '2020-01-01', '2025-12-31')
            if not df.empty:
                financial_dict[code] = df
        
        print(f"\n✅ 批量生成完成: {len(financial_dict)}/{len(stock_codes)}")
        return financial_dict
    
    # ==================== 2. 分钟数据补充 ====================
    
    def generate_minute_data(self,
                            stock_code: str,
                            date: str,
                            num_minutes: int = 240) -> pd.DataFrame:
        """
        从日线数据生成模拟分钟数据
        
        Args:
            stock_code: 股票代码
            date: 日期
            num_minutes: 分钟数（默认240分钟，即4小时交易时间）
            
        Returns:
            minute_data: 分钟数据
        """
        # 读取日线数据
        daily_file = os.path.join(self.data_dir, f"stock_quote_{stock_code}_*.csv")
        files = glob.glob(daily_file)
        
        if not files:
            return pd.DataFrame()
        
        dfs = [pd.read_csv(f) for f in files]
        daily_df = pd.concat(dfs, ignore_index=True)
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # 找到指定日期的数据
        day_data = daily_df[daily_df['date'] == date]
        
        if day_data.empty:
            return pd.DataFrame()
        
        daily = day_data.iloc[0]
        
        # 生成分钟时间戳
        date_obj = pd.to_datetime(date)
        morning_times = pd.date_range(
            start=date_obj + pd.Timedelta(hours=9, minutes=30),
            end=date_obj + pd.Timedelta(hours=11, minutes=30),
            periods=int(num_minutes * 0.55)
        )
        afternoon_times = pd.date_range(
            start=date_obj + pd.Timedelta(hours=13, minutes=0),
            end=date_obj + pd.Timedelta(hours=15, minutes=0),
            periods=num_minutes - int(num_minutes * 0.55)
        )
        
        all_times = morning_times.append(afternoon_times)
        n = len(all_times)
        
        # 在OHLC之间生成价格序列
        open_price = daily['open']
        high_price = daily['high']
        low_price = daily['low']
        close_price = daily['close']
        total_volume = daily['volume']
        
        # 生成价格路径（布朗桥）
        prices = self._generate_price_path(open_price, high_price, low_price, close_price, n)
        
        # 生成成交量（随机分配）
        volumes = np.random.dirichlet(np.ones(n)) * total_volume
        
        # 构建分钟数据
        minute_df = pd.DataFrame({
            'datetime': all_times,
            'stock_code': stock_code,
            'price': prices,
            'volume': volumes.astype(int),
            'amount': prices * volumes
        })
        
        return minute_df
    
    def _generate_price_path(self, open_p: float, high: float, low: float, close: float, n: int) -> np.ndarray:
        """生成价格路径"""
        # 使用布朗桥在OHLC之间插值
        prices = np.zeros(n)
        prices[0] = open_p
        prices[-1] = close
        
        # 中间点随机游走
        for i in range(1, n-1):
            progress = i / (n-1)
            # 向收盘价靠拢的趋势
            trend = open_p + (close - open_p) * progress
            # 添加随机扰动
            noise = np.random.randn() * (high - low) * 0.1
            prices[i] = trend + noise
        
        # 确保不超过高低点
        prices = np.clip(prices, low, high)
        
        return prices
    
    def generate_minute_data_for_period(self,
                                       stock_code: str,
                                       start_date: str,
                                       end_date: str) -> pd.DataFrame:
        """
        为一段时间生成分钟数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            minute_data: 分钟数据
        """
        print(f"生成分钟数据: {stock_code} ({start_date} ~ {end_date})")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        all_minutes = []
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            minute_df = self.generate_minute_data(stock_code, date_str)
            if not minute_df.empty:
                all_minutes.append(minute_df)
        
        if not all_minutes:
            return pd.DataFrame()
        
        minute_df = pd.concat(all_minutes, ignore_index=True)
        
        # 保存
        output_path = os.path.join(self.data_dir, 'minute', f"{stock_code}_1min.csv")
        minute_df.to_csv(output_path, index=False)
        
        print(f"  ✅ 生成完成: {len(minute_df)} 条记录")
        return minute_df
    
    # ==================== 3. 行业分类补充 ====================
    
    def load_industry_data(self) -> pd.DataFrame:
        """
        加载行业分类数据
        
        Returns:
            industry_df: 行业数据
        """
        # 预定义的行业分类（基于常见股票）
        industry_map = {
            # 银行
            '000001.SZ': {'industry': '银行', 'industry_code': 'J66'},
            '600000.SH': {'industry': '银行', 'industry_code': 'J66'},
            '600036.SH': {'industry': '银行', 'industry_code': 'J66'},
            
            # 房地产
            '000002.SZ': {'industry': '房地产', 'industry_code': 'K70'},
            
            # 食品饮料
            '000858.SZ': {'industry': '食品饮料', 'industry_code': 'C15'},
            '600519.SH': {'industry': '食品饮料', 'industry_code': 'C15'},
            '600887.SH': {'industry': '食品饮料', 'industry_code': 'C15'},
            
            # 医药生物
            '000999.SZ': {'industry': '医药生物', 'industry_code': 'C27'},
            '002422.SZ': {'industry': '医药生物', 'industry_code': 'C27'},
            '600161.SH': {'industry': '医药生物', 'industry_code': 'C27'},
            
            # 电子
            '000725.SZ': {'industry': '电子', 'industry_code': 'C39'},
            '002415.SZ': {'industry': '电子', 'industry_code': 'C39'},
            '002384.SZ': {'industry': '电子', 'industry_code': 'C39'},
            '600522.SH': {'industry': '电子', 'industry_code': 'C39'},
            '603893.SH': {'industry': '电子', 'industry_code': 'C39'},
            
            # 汽车
            '002594.SZ': {'industry': '汽车', 'industry_code': 'C36'},
            '601127.SH': {'industry': '汽车', 'industry_code': 'C36'},
            
            # 电力设备
            '300750.SZ': {'industry': '电力设备', 'industry_code': 'C38'},
            '600027.SH': {'industry': '电力设备', 'industry_code': 'C38'},
            '600930.SH': {'industry': '电力设备', 'industry_code': 'C38'},
            
            # 通信
            '000063.SZ': {'industry': '通信', 'industry_code': 'I63'},
            
            # 家电
            '000333.SZ': {'industry': '家电', 'industry_code': 'C38'},
            '000651.SZ': {'industry': '家电', 'industry_code': 'C38'},
            
            # 传媒
            '300059.SZ': {'industry': '传媒', 'industry_code': 'R86'},
            '300251.SZ': {'industry': '传媒', 'industry_code': 'R86'},
            
            # 计算机
            '300803.SZ': {'industry': '计算机', 'industry_code': 'I65'},
            '688047.SH': {'industry': '计算机', 'industry_code': 'I65'},
            
            # 机械设备
            '600066.SH': {'industry': '机械设备', 'industry_code': 'C35'},
            '601298.SH': {'industry': '机械设备', 'industry_code': 'C35'},
            
            # 化工
            '600160.SH': {'industry': '化工', 'industry_code': 'C26'},
            '600489.SH': {'industry': '化工', 'industry_code': 'C26'},
            
            # 有色金属
            '000630.SZ': {'industry': '有色金属', 'industry_code': 'C32'},
            '000807.SZ': {'industry': '有色金属', 'industry_code': 'C32'},
            '000975.SZ': {'industry': '有色金属', 'industry_code': 'C32'},
            
            # 交通运输
            '001391.SZ': {'industry': '交通运输', 'industry_code': 'G53'},
            '600026.SH': {'industry': '交通运输', 'industry_code': 'G53'},
            '600377.SH': {'industry': '交通运输', 'industry_code': 'G53'},
            '601018.SH': {'industry': '交通运输', 'industry_code': 'G53'},
            
            # 建筑装饰
            '002028.SZ': {'industry': '建筑装饰', 'industry_code': 'E50'},
            
            # 商贸零售
            '600415.SH': {'industry': '商贸零售', 'industry_code': 'F52'},
            
            # 国防军工
            '302132.SZ': {'industry': '国防军工', 'industry_code': 'C37'},
            '600482.SH': {'industry': '国防军工', 'industry_code': 'C37'},
            
            # 非银金融
            '300059.SZ': {'industry': '非银金融', 'industry_code': 'J67'},
            '601077.SH': {'industry': '非银金融', 'industry_code': 'J67'},
            '601825.SH': {'industry': '非银金融', 'industry_code': 'J67'},
            
            # 公用事业
            '002600.SZ': {'industry': '公用事业', 'industry_code': 'D44'},
            
            # 轻工制造
            '002625.SZ': {'industry': '轻工制造', 'industry_code': 'C22'},
            
            # 社会服务
            '601456.SH': {'industry': '社会服务', 'industry_code': 'O80'},
            
            # 纺织服饰
            '300866.SZ': {'industry': '纺织服饰', 'industry_code': 'C18'},
            
            # 美容护理
            '300896.SZ': {'industry': '美容护理', 'industry_code': 'C26'},
            
            # 环保
            '688169.SH': {'industry': '环保', 'industry_code': 'N77'},
            
            # 建筑材料
            '601136.SH': {'industry': '建筑材料', 'industry_code': 'C30'},
            
            # 煤炭
            '601018.SH': {'industry': '煤炭', 'industry_code': 'B06'},
            
            # 石油石化
            '601018.SH': {'industry': '石油石化', 'industry_code': 'B07'},
            
            # 钢铁
            '601018.SH': {'industry': '钢铁', 'industry_code': 'C31'},
            
            # 基础化工
            '688009.SH': {'industry': '基础化工', 'industry_code': 'C26'},
            
            # 医药商业
            '688082.SH': {'industry': '医药商业', 'industry_code': 'F51'},
            
            # 半导体
            '688472.SH': {'industry': '半导体', 'industry_code': 'C39'},
            '688506.SH': {'industry': '半导体', 'industry_code': 'C39'},
            
            # 消费电子
            '688169.SH': {'industry': '消费电子', 'industry_code': 'C39'},
            
            # 通信设备
            '688169.SH': {'industry': '通信设备', 'industry_code': 'C39'},
            
            # 软件开发
            '301236.SZ': {'industry': '软件开发', 'industry_code': 'I65'},
            
            # IT服务
            '301236.SZ': {'industry': 'IT服务', 'industry_code': 'I65'},
            
            # 光伏设备
            '300394.SZ': {'industry': '光伏设备', 'industry_code': 'C38'},
            
            # 电池
            '300418.SZ': {'industry': '电池', 'industry_code': 'C38'},
            
            # 电网设备
            '300442.SZ': {'industry': '电网设备', 'industry_code': 'C38'},
            
            # 风电设备
            '300476.SZ': {'industry': '风电设备', 'industry_code': 'C38'},
            
            # 电机
            '300502.SZ': {'industry': '电机', 'industry_code': 'C38'},
            
            # 其他设备
            '300832.SZ': {'industry': '专用设备', 'industry_code': 'C35'},
            '603296.SH': {'industry': '专用设备', 'industry_code': 'C35'},
        }
        
        # 获取所有股票代码
        stock_files = glob.glob(os.path.join(self.data_dir, "stock_quote_*.csv"))
        stock_codes = []
        for f in stock_files:
            basename = os.path.basename(f)
            parts = basename.split('_')
            if len(parts) >= 3:
                stock_codes.append(parts[2])
        
        stock_codes = list(set(stock_codes))
        
        # 构建行业数据
        industry_records = []
        for code in stock_codes:
            if code in industry_map:
                info = industry_map[code]
            else:
                # 默认分类
                info = {'industry': '其他', 'industry_code': 'Z99'}
            
            industry_records.append({
                'stock_code': code,
                'industry': info['industry'],
                'industry_code': info['industry_code'],
                'update_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        industry_df = pd.DataFrame(industry_records)
        
        # 保存
        output_path = os.path.join(self.data_dir, 'industry', 'industry_classification.csv')
        industry_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ 行业分类数据生成完成: {len(industry_df)} 只股票")
        return industry_df
    
    def get_industry_for_stock(self, stock_code: str) -> Dict:
        """
        获取股票的行业信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            industry_info: 行业信息
        """
        # 加载行业数据
        industry_file = os.path.join(self.data_dir, 'industry', 'industry_classification.csv')
        
        if not os.path.exists(industry_file):
            self.load_industry_data()
        
        industry_df = pd.read_csv(industry_file)
        
        stock_industry = industry_df[industry_df['stock_code'] == stock_code]
        
        if stock_industry.empty:
            return {'industry': '其他', 'industry_code': 'Z99'}
        
        return {
            'industry': stock_industry.iloc[0]['industry'],
            'industry_code': stock_industry.iloc[0]['industry_code']
        }
    
    # ==================== 4. 数据统一管理 ====================
    
    def create_unified_dataset(self, stock_codes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        创建统一的数据集
        将日线、财务、行业数据合并
        
        Args:
            stock_codes: 股票代码列表，None表示所有股票
            
        Returns:
            unified_data: 统一数据字典
        """
        print("="*60)
        print("创建统一数据集")
        print("="*60)
        
        if stock_codes is None:
            # 获取所有股票代码
            stock_files = glob.glob(os.path.join(self.data_dir, "stock_quote_*.csv"))
            stock_codes = []
            for f in stock_files:
                basename = os.path.basename(f)
                parts = basename.split('_')
                if len(parts) >= 3:
                    stock_codes.append(parts[2])
            stock_codes = list(set(stock_codes))
        
        print(f"处理 {len(stock_codes)} 只股票...")
        
        # 加载行业数据
        industry_df = self.load_industry_data()
        
        unified_data = {}
        
        for i, code in enumerate(stock_codes):
            print(f"\n[{i+1}/{len(stock_codes)}] {code}")
            
            # 1. 加载日线数据
            daily_file = os.path.join(self.data_dir, f"stock_quote_{code}_*.csv")
            daily_files = glob.glob(daily_file)
            
            if not daily_files:
                print(f"  ⚠️ 未找到日线数据")
                continue
            
            dfs = [pd.read_csv(f) for f in daily_files]
            daily_df = pd.concat(dfs, ignore_index=True)
            daily_df['date'] = pd.to_datetime(daily_df['date'])
            daily_df = daily_df.sort_values('date').reset_index(drop=True)
            
            # 2. 加载财务数据
            financial_file = os.path.join(self.data_dir, 'financial', f"{code}.csv")
            if os.path.exists(financial_file):
                financial_df = pd.read_csv(financial_file)
                financial_df['date'] = pd.to_datetime(financial_df['date'])
                
                # 合并财务数据（向前填充）
                daily_df = pd.merge_asof(
                    daily_df.sort_values('date'),
                    financial_df.sort_values('date'),
                    on='date',
                    direction='backward'
                )
            
            # 3. 添加行业信息
            industry_info = self.get_industry_for_stock(code)
            daily_df['industry'] = industry_info['industry']
            daily_df['industry_code'] = industry_info['industry_code']
            
            # 4. 标准化列名
            daily_df = self._standardize_columns(daily_df)
            
            # 保存统一数据
            output_path = os.path.join(self.data_dir, 'unified', f"{code}.parquet")
            daily_df.to_parquet(output_path, index=False)
            
            unified_data[code] = daily_df
            print(f"  ✅ 完成: {len(daily_df)} 条记录, {len(daily_df.columns)} 列")
        
        print("\n" + "="*60)
        print(f"统一数据集创建完成: {len(unified_data)} 只股票")
        print("="*60)
        
        return unified_data
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 列名映射
        column_map = {
            'date': 'date',
            'code': 'code',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'preclose': 'pre_close',
            'volume': 'volume',
            'amount': 'amount',
            'turn': 'turnover',
            'pctChg': 'change_pct',
            'peTTM': 'pe_ttm',
            'pbMRQ': 'pb_mrq',
            'psTTM': 'ps_ttm',
            'pcfNcfTTM': 'pcf_ttm',
            'tradestatus': 'trade_status',
            'adjustflag': 'adjust_flag'
        }
        
        # 重命名存在的列
        rename_map = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=rename_map)
        
        return df
    
    def get_data_inventory(self) -> pd.DataFrame:
        """
        获取数据清单
        
        Returns:
            inventory: 数据清单
        """
        print("生成数据清单...")
        
        inventory = []
        
        # 1. 日线数据
        daily_files = glob.glob(os.path.join(self.data_dir, "stock_quote_*.csv"))
        for f in daily_files:
            basename = os.path.basename(f)
            size = os.path.getsize(f) / 1024  # KB
            inventory.append({
                'file': basename,
                'type': '日线',
                'size_kb': size,
                'path': f
            })
        
        # 2. 财务数据
        financial_files = glob.glob(os.path.join(self.data_dir, "financial", "*.csv"))
        for f in financial_files:
            basename = os.path.basename(f)
            size = os.path.getsize(f) / 1024
            inventory.append({
                'file': basename,
                'type': '财务',
                'size_kb': size,
                'path': f
            })
        
        # 3. 分钟数据
        minute_files = glob.glob(os.path.join(self.data_dir, "minute", "*.csv"))
        for f in minute_files:
            basename = os.path.basename(f)
            size = os.path.getsize(f) / 1024
            inventory.append({
                'file': basename,
                'type': '分钟',
                'size_kb': size,
                'path': f
            })
        
        # 4. 行业数据
        industry_files = glob.glob(os.path.join(self.data_dir, "industry", "*.csv"))
        for f in industry_files:
            basename = os.path.basename(f)
            size = os.path.getsize(f) / 1024
            inventory.append({
                'file': basename,
                'type': '行业',
                'size_kb': size,
                'path': f
            })
        
        # 5. 统一数据
        unified_files = glob.glob(os.path.join(self.data_dir, "unified", "*.parquet"))
        for f in unified_files:
            basename = os.path.basename(f)
            size = os.path.getsize(f) / 1024
            inventory.append({
                'file': basename,
                'type': '统一',
                'size_kb': size,
                'path': f
            })
        
        inventory_df = pd.DataFrame(inventory)
        
        # 统计
        print("\n数据清单统计:")
        print(f"  日线数据: {len([x for x in inventory if x['type'] == '日线'])} 个文件")
        print(f"  财务数据: {len([x for x in inventory if x['type'] == '财务'])} 个文件")
        print(f"  分钟数据: {len([x for x in inventory if x['type'] == '分钟'])} 个文件")
        print(f"  行业数据: {len([x for x in inventory if x['type'] == '行业'])} 个文件")
        print(f"  统一数据: {len([x for x in inventory if x['type'] == '统一'])} 个文件")
        
        return inventory_df
    
    def enhance_all_data(self):
        """
        增强所有数据
        一键补充所有缺失数据
        """
        print("="*60)
        print("开始数据增强")
        print("="*60)
        
        # 1. 获取所有股票代码
        stock_files = glob.glob(os.path.join(self.data_dir, "stock_quote_*.csv"))
        stock_codes = []
        for f in stock_files:
            basename = os.path.basename(f)
            parts = basename.split('_')
            if len(parts) >= 3:
                stock_codes.append(parts[2])
        stock_codes = list(set(stock_codes))
        
        print(f"\n发现 {len(stock_codes)} 只股票")
        
        # 2. 生成财务数据
        print("\n" + "-"*60)
        print("步骤1: 生成财务数据")
        print("-"*60)
        self.batch_generate_financial(stock_codes)
        
        # 3. 生成行业分类
        print("\n" + "-"*60)
        print("步骤2: 生成行业分类")
        print("-"*60)
        self.load_industry_data()
        
        # 4. 创建统一数据集
        print("\n" + "-"*60)
        print("步骤3: 创建统一数据集")
        print("-"*60)
        self.create_unified_dataset(stock_codes)
        
        # 5. 生成数据清单
        print("\n" + "-"*60)
        print("步骤4: 生成数据清单")
        print("-"*60)
        inventory = self.get_data_inventory()
        
        print("\n" + "="*60)
        print("数据增强完成")
        print("="*60)
        
        return inventory

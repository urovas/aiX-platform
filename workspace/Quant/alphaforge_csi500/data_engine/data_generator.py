# 示例数据生成器

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
from datetime import datetime, timedelta
import os

warnings.filterwarnings('ignore')


class DataGenerator:
    """
    示例数据生成器
    用于生成模拟数据供测试和演示使用
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据生成器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 随机种子
        self.random_seed = self.config.get('random_seed', 42)
        np.random.seed(self.random_seed)
        
        # 默认参数
        self.default_stock_codes = [
            '000001.SZ', '000002.SZ', '000063.SZ', '000333.SZ', '000651.SZ',
            '000725.SZ', '000858.SZ', '002415.SZ', '002594.SZ', '300059.SZ',
            '300750.SZ', '600000.SH', '600036.SH', '600519.SH', '600887.SH'
        ]
        
        # 行业映射
        self.industry_map = {
            '000001.SZ': '银行',
            '000002.SZ': '房地产',
            '000063.SZ': '通信',
            '000333.SZ': '家电',
            '000651.SZ': '家电',
            '000725.SZ': '电子',
            '000858.SZ': '食品饮料',
            '002415.SZ': '电子',
            '002594.SZ': '汽车',
            '300059.SZ': '传媒',
            '300750.SZ': '电力设备',
            '600000.SH': '银行',
            '600036.SH': '银行',
            '600519.SH': '食品饮料',
            '600887.SH': '食品饮料'
        }
        
        print("✅ 数据生成器初始化完成")
    
    def generate_tick_data(self,
                          stock_code: str,
                          start_date: str,
                          end_date: str,
                          ticks_per_day: int = 1000) -> pd.DataFrame:
        """
        生成逐笔交易数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            ticks_per_day: 每天的tick数量
            
        Returns:
            tick_data: 逐笔交易数据
        """
        print(f"生成逐笔交易数据: {stock_code} ({start_date} ~ {end_date})")
        
        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
        
        all_ticks = []
        
        for date in dates:
            # 生成当天的tick数据
            ticks = self._generate_one_day_ticks(stock_code, date, ticks_per_day)
            all_ticks.append(ticks)
        
        # 合并所有tick数据
        tick_data = pd.concat(all_ticks, ignore_index=True)
        
        print(f"  ✅ 生成完成: {len(tick_data)} 条记录")
        return tick_data
    
    def _generate_one_day_ticks(self,
                                stock_code: str,
                                date: pd.Timestamp,
                                ticks_per_day: int) -> pd.DataFrame:
        """生成一天的tick数据"""
        # 交易时间：9:30-11:30, 13:00-15:00
        morning_start = date + pd.Timedelta(hours=9, minutes=30)
        morning_end = date + pd.Timedelta(hours=11, minutes=30)
        afternoon_start = date + pd.Timedelta(hours=13, minutes=0)
        afternoon_end = date + pd.Timedelta(hours=15, minutes=0)
        
        # 生成时间戳
        morning_ticks = int(ticks_per_day * 0.55)
        afternoon_ticks = ticks_per_day - morning_ticks
        
        morning_times = pd.date_range(start=morning_start, end=morning_end, periods=morning_ticks)
        afternoon_times = pd.date_range(start=afternoon_start, end=afternoon_end, periods=afternoon_ticks)
        
        all_times = morning_times.append(afternoon_times)
        
        # 生成价格数据（随机游走）
        base_price = np.random.uniform(10, 100)
        price_changes = np.random.randn(len(all_times)) * 0.001
        prices = base_price * (1 + np.cumsum(price_changes))
        prices = np.maximum(prices, 0.1)  # 确保价格为正
        
        # 生成成交量
        volumes = np.random.randint(100, 10000, len(all_times))
        
        # 生成买卖方向
        directions = np.random.choice([1, -1, 0], len(all_times), p=[0.4, 0.4, 0.2])
        
        # 生成订单簿数据
        bid_prices = prices - np.random.uniform(0.01, 0.05, len(all_times))
        ask_prices = prices + np.random.uniform(0.01, 0.05, len(all_times))
        bid_volumes = np.random.randint(100, 5000, len(all_times))
        ask_volumes = np.random.randint(100, 5000, len(all_times))
        
        # 构建DataFrame
        tick_data = pd.DataFrame({
            'datetime': all_times,
            'stock_code': stock_code,
            'price': prices,
            'volume': volumes,
            'amount': prices * volumes,
            'direction': directions,
            'bid_price': bid_prices,
            'ask_price': ask_prices,
            'bid_volume': bid_volumes,
            'ask_volume': ask_volumes
        })
        
        return tick_data
    
    def generate_minute_data(self,
                            stock_code: str,
                            start_date: str,
                            end_date: str) -> pd.DataFrame:
        """
        生成分钟级数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            minute_data: 分钟级数据
        """
        print(f"生成分钟级数据: {stock_code} ({start_date} ~ {end_date})")
        
        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        all_minutes = []
        
        for date in dates:
            minutes = self._generate_one_day_minutes(stock_code, date)
            all_minutes.append(minutes)
        
        minute_data = pd.concat(all_minutes, ignore_index=True)
        
        print(f"  ✅ 生成完成: {len(minute_data)} 条记录")
        return minute_data
    
    def _generate_one_day_minutes(self,
                                  stock_code: str,
                                  date: pd.Timestamp) -> pd.DataFrame:
        """生成一天的分钟数据"""
        # 交易时间
        morning_times = pd.date_range(
            start=date + pd.Timedelta(hours=9, minutes=30),
            end=date + pd.Timedelta(hours=11, minutes=30),
            freq='1min'
        )
        afternoon_times = pd.date_range(
            start=date + pd.Timedelta(hours=13, minutes=0),
            end=date + pd.Timedelta(hours=15, minutes=0),
            freq='1min'
        )
        
        all_times = morning_times.append(afternoon_times)
        n = len(all_times)
        
        # 生成OHLCV数据
        base_price = np.random.uniform(10, 100)
        
        # 开盘价
        opens = np.zeros(n)
        opens[0] = base_price
        
        # 收盘价（随机游走）
        returns = np.random.randn(n) * 0.005
        closes = base_price * np.exp(np.cumsum(returns))
        
        # 开盘价基于前一根K线收盘价
        for i in range(1, n):
            opens[i] = closes[i-1] * (1 + np.random.uniform(-0.002, 0.002))
        
        # 最高价和最低价
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.randn(n)) * 0.003)
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.randn(n)) * 0.003)
        
        # 成交量
        volumes = np.random.randint(10000, 100000, n)
        amounts = closes * volumes
        
        # 构建DataFrame
        minute_data = pd.DataFrame({
            'datetime': all_times,
            'stock_code': stock_code,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'amount': amounts,
            'turnover': volumes / 1e8  # 换手率（假设）
        })
        
        return minute_data
    
    def generate_daily_data(self,
                           stock_code: str,
                           start_date: str,
                           end_date: str) -> pd.DataFrame:
        """
        生成日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            daily_data: 日线数据
        """
        print(f"生成日线数据: {stock_code} ({start_date} ~ {end_date})")
        
        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        
        # 生成价格数据
        base_price = np.random.uniform(10, 100)
        
        # 收盘价（几何布朗运动）
        returns = np.random.randn(n) * 0.02
        closes = base_price * np.exp(np.cumsum(returns))
        
        # 开盘价
        opens = np.roll(closes, 1)
        opens[0] = base_price
        opens = opens * (1 + np.random.uniform(-0.01, 0.01, n))
        
        # 最高价和最低价
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.randn(n)) * 0.02)
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.randn(n)) * 0.02)
        
        # 成交量
        base_volume = np.random.uniform(1e6, 1e8)
        volumes = base_volume * (1 + np.random.randn(n) * 0.3)
        volumes = np.maximum(volumes, 1000)
        
        # 成交额
        amounts = closes * volumes
        
        # 换手率
        total_shares = np.random.uniform(1e8, 1e10)
        turnovers = volumes / total_shares * 100
        
        # 构建DataFrame
        daily_data = pd.DataFrame({
            'date': dates,
            'stock_code': stock_code,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'amount': amounts,
            'turnover': turnovers,
            'industry': self.industry_map.get(stock_code, '其他')
        })
        
        print(f"  ✅ 生成完成: {len(daily_data)} 条记录")
        return daily_data
    
    def generate_financial_data(self,
                               stock_code: str,
                               start_date: str,
                               end_date: str) -> pd.DataFrame:
        """
        生成财务数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            financial_data: 财务数据
        """
        print(f"生成财务数据: {stock_code} ({start_date} ~ {end_date})")
        
        # 生成季度报告日期
        dates = pd.date_range(start=start_date, end=end_date, freq='BQS')  # 季初工作日
        n = len(dates)
        
        if n == 0:
            return pd.DataFrame()
        
        # 基础财务指标
        base_revenue = np.random.uniform(1e9, 1e11)
        base_assets = np.random.uniform(1e10, 1e12)
        
        # 营业收入（季度增长）
        revenue_growth = np.random.uniform(0.9, 1.1, n)
        revenues = base_revenue * np.cumprod(revenue_growth)
        
        # 营业成本
        cost_ratio = np.random.uniform(0.6, 0.9, n)
        costs = revenues * cost_ratio
        
        # 毛利润
        gross_profits = revenues - costs
        
        # 营业利润
        operating_ratio = np.random.uniform(0.05, 0.2, n)
        operating_profits = revenues * operating_ratio
        
        # 净利润
        net_ratio = np.random.uniform(0.03, 0.15, n)
        net_profits = revenues * net_ratio
        
        # 总资产
        asset_growth = np.random.uniform(0.95, 1.05, n)
        total_assets = base_assets * np.cumprod(asset_growth)
        
        # 总负债
        debt_ratio = np.random.uniform(0.3, 0.7, n)
        total_liabilities = total_assets * debt_ratio
        
        # 股东权益
        total_equity = total_assets - total_liabilities
        
        # 流动资产和流动负债
        current_ratio = np.random.uniform(1.0, 2.0, n)
        current_assets = total_equity * current_ratio * np.random.uniform(0.3, 0.5, n)
        current_liabilities = current_assets / current_ratio
        
        # 存货
        inventory = revenues * np.random.uniform(0.05, 0.15, n)
        
        # 经营活动现金流
        cash_flow_ratio = np.random.uniform(0.1, 0.3, n)
        operating_cash_flows = net_profits * cash_flow_ratio
        
        # 构建DataFrame
        financial_data = pd.DataFrame({
            'date': dates,
            'stock_code': stock_code,
            'report_type': '季报',
            'revenue': revenues,
            'cost': costs,
            'gross_profit': gross_profits,
            'operating_profit': operating_profits,
            'net_profit': net_profits,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'inventory': inventory,
            'operating_cash_flow': operating_cash_flows,
            'industry': self.industry_map.get(stock_code, '其他')
        })
        
        print(f"  ✅ 生成完成: {len(financial_data)} 条记录")
        return financial_data
    
    def generate_order_book_data(self,
                                stock_code: str,
                                start_date: str,
                                end_date: str,
                                snapshots_per_day: int = 100) -> pd.DataFrame:
        """
        生成订单簿数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            snapshots_per_day: 每天的快照数量
            
        Returns:
            order_book_data: 订单簿数据
        """
        print(f"生成订单簿数据: {stock_code} ({start_date} ~ {end_date})")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        all_snapshots = []
        
        for date in dates:
            snapshots = self._generate_one_day_order_book(stock_code, date, snapshots_per_day)
            all_snapshots.append(snapshots)
        
        order_book_data = pd.concat(all_snapshots, ignore_index=True)
        
        print(f"  ✅ 生成完成: {len(order_book_data)} 条记录")
        return order_book_data
    
    def _generate_one_day_order_book(self,
                                     stock_code: str,
                                     date: pd.Timestamp,
                                     snapshots_per_day: int) -> pd.DataFrame:
        """生成一天的订单簿数据"""
        # 生成时间戳
        morning_times = pd.date_range(
            start=date + pd.Timedelta(hours=9, minutes=30),
            end=date + pd.Timedelta(hours=11, minutes=30),
            periods=int(snapshots_per_day * 0.55)
        )
        afternoon_times = pd.date_range(
            start=date + pd.Timedelta(hours=13, minutes=0),
            end=date + pd.Timedelta(hours=15, minutes=0),
            periods=snapshots_per_day - int(snapshots_per_day * 0.55)
        )
        
        all_times = morning_times.append(afternoon_times)
        n = len(all_times)
        
        # 生成中间价
        mid_price = np.random.uniform(10, 100)
        price_changes = np.random.randn(n) * 0.002
        mid_prices = mid_price * (1 + np.cumsum(price_changes))
        
        # 生成10档买卖盘
        levels = 10
        data = {
            'datetime': all_times,
            'stock_code': stock_code,
            'mid_price': mid_prices
        }
        
        for level in range(1, levels + 1):
            # 买盘
            data[f'bid_price_{level}'] = mid_prices - level * 0.01
            data[f'bid_volume_{level}'] = np.random.randint(100, 10000, n)
            
            # 卖盘
            data[f'ask_price_{level}'] = mid_prices + level * 0.01
            data[f'ask_volume_{level}'] = np.random.randint(100, 10000, n)
        
        return pd.DataFrame(data)
    
    def generate_market_data(self,
                            start_date: str,
                            end_date: str) -> pd.DataFrame:
        """
        生成市场整体数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            market_data: 市场数据
        """
        print(f"生成市场数据: ({start_date} ~ {end_date})")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        
        # 上证指数
        base_index = 3000
        index_returns = np.random.randn(n) * 0.01
        sh_index = base_index * np.exp(np.cumsum(index_returns))
        
        # 深证成指
        sz_index = sh_index * np.random.uniform(1.0, 1.2) * (1 + np.random.randn(n) * 0.005)
        
        # 创业板指
        cyb_index = sh_index * np.random.uniform(0.3, 0.5) * (1 + np.random.randn(n) * 0.015)
        
        # 市场成交量
        market_volume = np.random.uniform(5e11, 1e12, n) * (1 + np.random.randn(n) * 0.2)
        
        # 市场成交额
        market_amount = market_volume * np.random.uniform(10, 20, n)
        
        # 涨跌家数
        up_count = np.random.randint(1000, 3000, n)
        down_count = np.random.randint(1000, 3000, n)
        flat_count = 5000 - up_count - down_count
        
        # 构建DataFrame
        market_data = pd.DataFrame({
            'date': dates,
            'sh_index': sh_index,
            'sz_index': sz_index,
            'cyb_index': cyb_index,
            'market_volume': market_volume,
            'market_amount': market_amount,
            'up_count': up_count,
            'down_count': down_count,
            'flat_count': flat_count,
            'advance_decline_ratio': up_count / (down_count + 1)
        })
        
        print(f"  ✅ 生成完成: {len(market_data)} 条记录")
        return market_data
    
    def generate_industry_data(self,
                              start_date: str,
                              end_date: str) -> pd.DataFrame:
        """
        生成行业数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            industry_data: 行业数据
        """
        print(f"生成行业数据: ({start_date} ~ {end_date})")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # 行业列表
        industries = [
            '银行', '房地产', '通信', '家电', '电子',
            '食品饮料', '汽车', '传媒', '电力设备', '医药生物',
            '计算机', '机械设备', '化工', '有色金属', '建筑材料'
        ]
        
        all_data = []
        
        for industry in industries:
            n = len(dates)
            
            # 行业指数
            base_index = np.random.uniform(1000, 5000)
            index_returns = np.random.randn(n) * 0.015
            industry_index = base_index * np.exp(np.cumsum(index_returns))
            
            # 行业涨跌幅
            industry_return = np.concatenate([[0], np.diff(industry_index) / industry_index[:-1]])
            
            # 行业成交额
            industry_amount = np.random.uniform(1e10, 1e11, n) * (1 + np.random.randn(n) * 0.3)
            
            # 行业市盈率
            pe_ratio = np.random.uniform(10, 50, n) + np.random.randn(n) * 5
            
            # 行业市净率
            pb_ratio = np.random.uniform(1, 5, n) + np.random.randn(n) * 0.5
            
            df = pd.DataFrame({
                'date': dates,
                'industry': industry,
                'industry_index': industry_index,
                'industry_return': industry_return,
                'industry_amount': industry_amount,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio
            })
            
            all_data.append(df)
        
        industry_data = pd.concat(all_data, ignore_index=True)
        
        print(f"  ✅ 生成完成: {len(industry_data)} 条记录")
        return industry_data
    
    def generate_all_data(self,
                         stock_codes: List[str] = None,
                         start_date: str = '2023-01-01',
                         end_date: str = '2023-12-31') -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        生成所有类型的模拟数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            all_data: 所有数据字典
        """
        print("="*60)
        print("生成所有模拟数据")
        print("="*60)
        
        if stock_codes is None:
            stock_codes = self.default_stock_codes[:5]  # 默认生成5只股票
        
        all_data = {}
        
        for stock_code in stock_codes:
            print(f"\n生成 {stock_code} 数据...")
            
            all_data[stock_code] = {
                'tick': self.generate_tick_data(stock_code, start_date, end_date, ticks_per_day=500),
                'minute': self.generate_minute_data(stock_code, start_date, end_date),
                'daily': self.generate_daily_data(stock_code, start_date, end_date),
                'financial': self.generate_financial_data(stock_code, start_date, end_date),
                'order_book': self.generate_order_book_data(stock_code, start_date, end_date, snapshots_per_day=50)
            }
        
        # 生成市场数据
        all_data['market'] = {
            'market': self.generate_market_data(start_date, end_date),
            'industry': self.generate_industry_data(start_date, end_date)
        }
        
        print("\n" + "="*60)
        print("所有数据生成完成")
        print("="*60)
        
        return all_data
    
    def save_all_data(self,
                     all_data: Dict,
                     output_dir: str = './data/'):
        """
        保存所有数据到文件
        
        Args:
            all_data: 数据字典
            output_dir: 输出目录
        """
        print(f"\n保存数据到: {output_dir}")
        
        for stock_code, data_dict in all_data.items():
            if stock_code == 'market':
                continue
            
            for data_type, data in data_dict.items():
                # 创建目录
                type_dir = os.path.join(output_dir, data_type)
                os.makedirs(type_dir, exist_ok=True)
                
                # 保存文件
                file_path = os.path.join(type_dir, f"{stock_code}.parquet")
                data.to_parquet(file_path, index=False)
                print(f"  ✅ 保存: {file_path}")
        
        # 保存市场数据
        if 'market' in all_data:
            market_dir = os.path.join(output_dir, 'market')
            os.makedirs(market_dir, exist_ok=True)
            
            for data_type, data in all_data['market'].items():
                file_path = os.path.join(market_dir, f"{data_type}.parquet")
                data.to_parquet(file_path, index=False)
                print(f"  ✅ 保存: {file_path}")
        
        print("\n✅ 所有数据保存完成")
    
    def generate_training_data(self,
                              stock_codes: List[str] = None,
                              start_date: str = '2023-01-01',
                              end_date: str = '2023-12-31') -> Dict:
        """
        生成用于模型训练的数据集
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            training_data: 训练数据集
        """
        print("生成训练数据集...")
        
        if stock_codes is None:
            stock_codes = self.default_stock_codes[:3]
        
        training_data = {
            'tick_data': {},
            'minute_data': {},
            'daily_data': {},
            'financial_data': {},
            'price_data': {},
            'market_data': None,
            'industry_data': None
        }
        
        for stock_code in stock_codes:
            # 生成分钟数据
            minute_data = self.generate_minute_data(stock_code, start_date, end_date)
            training_data['minute_data'][stock_code] = minute_data
            
            # 生成日线数据
            daily_data = self.generate_daily_data(stock_code, start_date, end_date)
            training_data['daily_data'][stock_code] = daily_data
            
            # 生成财务数据
            financial_data = self.generate_financial_data(stock_code, start_date, end_date)
            training_data['financial_data'][stock_code] = financial_data
            
            # 价格数据（简化版日线）
            price_data = daily_data[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            training_data['price_data'][stock_code] = price_data
            
            # 生成tick数据（较少）
            tick_data = self.generate_tick_data(stock_code, start_date, end_date, ticks_per_day=100)
            training_data['tick_data'][stock_code] = tick_data
        
        # 市场数据
        training_data['market_data'] = self.generate_market_data(start_date, end_date)
        
        # 行业数据
        training_data['industry_data'] = self.generate_industry_data(start_date, end_date)
        
        print("✅ 训练数据集生成完成")
        return training_data
    
    def get_data_summary(self, data: Dict) -> pd.DataFrame:
        """
        获取数据摘要
        
        Args:
            data: 数据字典
            
        Returns:
            summary: 数据摘要
        """
        summary_list = []
        
        for stock_code, data_dict in data.items():
            if stock_code == 'market':
                continue
            
            for data_type, df in data_dict.items():
                summary_list.append({
                    'stock_code': stock_code,
                    'data_type': data_type,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
                    'start_date': df.iloc[0, 0] if len(df) > 0 else None,
                    'end_date': df.iloc[-1, 0] if len(df) > 0 else None
                })
        
        summary = pd.DataFrame(summary_list)
        return summary

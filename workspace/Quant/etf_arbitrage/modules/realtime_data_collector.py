#!/usr/bin/env python3
"""
实时数据采集模块（修复版）
负责获取ETF实时行情、IOPV和成分股数据

修改说明：
1. 修复东方财富IOPV接口URL被截断的问题
2. 修复成分股获取逻辑（使用正确接口）
3. 添加数据验证和重试机制
4. 优化错误处理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import requests
from typing import Dict, List, Optional, Tuple
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class RealtimeDataCollector:
    """
    实时数据采集类
    """
    
    def __init__(self, config):
        """
        初始化实时数据采集器
        
        Args:
            config: 配置对象（在外部定义）
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.etf_quote_cache = {}
        self.iopv_cache = {}
        self.constituent_cache = {}
        
        self.last_update_time = None
        self.cache_duration = 5  # 缓存有效期（秒）

    def check_data_freshness(self, quarter_str: str) -> Tuple[bool, str]:
        """
        检查数据新鲜度
        
        Args:
            quarter_str: 季度字符串（如"2025年1季度股票投资明细"）
            
        Returns:
            Tuple[bool, str]: (是否过期, 警告信息)
        """
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # 解析季度字符串
            if '年' in quarter_str and '季度' in quarter_str:
                parts = quarter_str.split('年')
                data_year = int(parts[0])
                
                # 计算数据过期时间
                if current_year - data_year > 1:
                    return True, f"数据过期超过1年！数据年份: {data_year}, 当前年份: {current_year}"
                elif current_year - data_year == 1:
                    return True, f"数据过期约1年！数据年份: {data_year}, 当前年份: {current_year}"
                elif current_year - data_year == 0:
                    return False, "数据新鲜"
                else:
                    return True, f"数据来自未来！数据年份: {data_year}, 当前年份: {current_year}"
            else:
                return True, f"无法解析季度数据: {quarter_str}"
                
        except Exception as e:
            return True, f"数据新鲜度检查失败: {e}"

    def requests_with_retry(self, url: str, max_retries: int = 3, delay: int = 1) -> Optional[requests.Response]:
        """
        带重试机制的HTTP请求
        
        Args:
            url: 请求URL
            max_retries: 最大重试次数
            delay: 重试间隔（秒）
            
        Returns:
            Response对象或None
        """
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return response
                self.logger.warning(f"请求返回状态码: {response.status_code}")
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时(第{i+1}次): {url}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"连接错误(第{i+1}次): {url}")
            except Exception as e:
                self.logger.warning(f"请求异常(第{i+1}次): {e}")
            
            if i < max_retries - 1:
                time.sleep(delay)
        
        return None

    def validate_quote_data(self, quote: Dict) -> bool:
        """
        验证行情数据的有效性
        
        Args:
            quote: 行情数据字典
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['price', 'open', 'high', 'low', 'volume', 'amount']
        
        for field in required_fields:
            if field not in quote:
                self.logger.warning(f"缺少必要字段: {field}")
                return False
        
        # 检查价格是否合理（>0且<100）
        if quote['price'] <= 0 or quote['price'] > 100:
            self.logger.warning(f"价格异常: {quote['price']}")
            return False
        
        # 检查高低价逻辑
        if quote['high'] < quote['low']:
            self.logger.warning(f"高价{quote['high']}低于低价{quote['low']}")
            return False
        
        # 检查量能数据
        if quote['volume'] < 0 or quote['amount'] < 0:
            self.logger.warning(f"量能数据异常: 成交量{quote['volume']}, 成交额{quote['amount']}")
            return False
        
        return True

    def get_etf_quote_akshare(self, etf_code: str) -> Optional[Dict]:
        """
        使用AkShare获取ETF实时行情
        
        Args:
            etf_code: ETF代码
            
        Returns:
            Dict: ETF行情数据
        """
        try:
            import akshare as ak
            
            self.logger.info(f"使用AkShare获取ETF行情: {etf_code}")
            
            # 获取全市场ETF实时行情
            df = ak.fund_etf_spot_em()
            
            # 确保代码列是字符串类型
            df['代码'] = df['代码'].astype(str)
            
            # 精确匹配
            etf_data = df[df['代码'] == etf_code]
            
            if len(etf_data) == 0:
                self.logger.warning(f"未找到ETF数据: {etf_code}")
                return None
            
            row = etf_data.iloc[0]
            
            quote = {
                'code': etf_code,
                'name': row['名称'],
                'price': float(row['最新价']),
                'open': float(row['开盘价']),
                'high': float(row['最高价']),
                'low': float(row['最低价']),
                'volume': float(row['成交量']),
                'amount': float(row['成交额']),
                'timestamp': datetime.now()
            }
            
            # 验证数据有效性
            if not self.validate_quote_data(quote):
                self.logger.warning(f"行情数据验证失败: {etf_code}")
                return None
            
            self.logger.info(f"获取ETF行情成功: {etf_code}, 价格={quote['price']:.4f}")
            return quote
            
        except ImportError:
            self.logger.error("AkShare未安装,请运行: pip install akshare")
            return None
        except Exception as e:
            self.logger.error(f"获取ETF行情失败: {e}")
            return None

    def get_etf_quote_sina(self, etf_code: str) -> Optional[Dict]:
        """
        使用新浪财经API获取ETF实时行情
        
        Args:
            etf_code: ETF代码
            
        Returns:
            Dict: ETF行情数据
        """
        try:
            # 判断市场（上海ETF以5开头）
            market = "sh" if etf_code.startswith('5') or etf_code.startswith('51') else "sz"
            url = f"http://hq.sinajs.cn/list={market}{etf_code}"
            
            response = self.requests_with_retry(url)
            if not response:
                return None
            
            response.encoding = 'gbk'
            data_str = response.text
            
            # 解析新浪数据格式
            if '=' not in data_str or '"' not in data_str:
                self.logger.error(f"新浪数据格式错误: {data_str[:100]}")
                return None
            
            content = data_str.split('=')[1].strip().strip(';').strip('"')
            fields = content.split(',')
            
            if len(fields) < 32:
                self.logger.error(f"新浪API数据字段不足: {len(fields)}个")
                return None
            
            # 新浪数据字段说明
            # 0:股票名称,1:今开,2:昨收,3:当前,4:最高,5:最低,8:成交量,9:成交额
            quote = {
                'code': etf_code,
                'name': fields[0],
                'open': float(fields[1]) if fields[1] else 0,
                'pre_close': float(fields[2]) if fields[2] else 0,
                'price': float(fields[3]) if fields[3] else 0,
                'high': float(fields[4]) if fields[4] else 0,
                'low': float(fields[5]) if fields[5] else 0,
                'volume': float(fields[8]) if fields[8] else 0,
                'amount': float(fields[9]) if fields[9] else 0,
                'timestamp': datetime.now()
            }
            
            if not self.validate_quote_data(quote):
                return None
            
            self.logger.info(f"获取ETF行情成功: {etf_code}, 价格={quote['price']:.4f}")
            return quote
            
        except Exception as e:
            self.logger.error(f"获取ETF行情失败: {e}")
            return None

    def get_iopv_tencent(self, etf_code: str) -> Optional[float]:
        """
        使用腾讯财经API获取IOPV（已废弃，使用AkShare替代）
        
        Args:
            etf_code: ETF代码
            
        Returns:
            float: IOPV值
        """
        self.logger.warning("腾讯API IOPV获取已废弃，请使用AkShare接口")
        return None

    def get_iopv_eastmoney(self, etf_code: str) -> Optional[float]:
        """
        使用AkShare获取IOPV（实时参考净值）
        
        Args:
            etf_code: ETF代码
            
        Returns:
            float: IOPV值
        """
        try:
            import akshare as ak
            
            self.logger.info(f"使用AkShare获取IOPV: {etf_code}")
            
            # 获取全市场ETF实时行情
            df = ak.fund_etf_spot_em()
            
            # 确保代码列是字符串类型
            df['代码'] = df['代码'].astype(str)
            
            # 精确匹配
            etf_data = df[df['代码'] == etf_code]
            
            if len(etf_data) == 0:
                self.logger.warning(f"未找到ETF数据: {etf_code}")
                return None
            
            row = etf_data.iloc[0]
            
            # 获取IOPV实时估值
            iopv = row.get('IOPV实时估值')
            
            if iopv is not None and iopv > 0:
                iopv_float = float(iopv)
                self.logger.info(f"获取IOPV成功: {etf_code}, IOPV={iopv_float:.4f}")
                return iopv_float
            else:
                self.logger.warning(f"IOPV数据无效: {etf_code}, IOPV={iopv}")
                return None
            
        except Exception as e:
            self.logger.error(f"AkShare IOPV获取失败: {e}")
            return None

    def get_constituent_stocks_akshare(self, etf_code: str) -> Optional[List[Dict]]:
        """
        使用AkShare获取ETF成分股（修复版）
        
        Args:
            etf_code: ETF代码
            
        Returns:
            List[Dict]: 成分股列表
        """
        try:
            import akshare as ak
            
            self.logger.info(f"使用AkShare获取ETF成分股: {etf_code}")
            
            constituents = []
            
            # 方法1: 通过ETF持仓明细接口
            try:
                # 获取最新持仓
                current_year = str(datetime.now().year)
                # 尝试获取当前年份数据
                try:
                    df = ak.fund_portfolio_hold_em(symbol=etf_code, date=current_year)
                    self.logger.info(f"尝试获取 {current_year} 年数据: {len(df)} 行")
                    
                    # 如果当前年份数据为空，尝试上一年
                    if df is None or df.empty:
                        last_year = str(int(current_year) - 1)
                        self.logger.info(f"当前年份数据为空，尝试获取 {last_year} 年数据")
                        df = ak.fund_portfolio_hold_em(symbol=etf_code, date=last_year)
                except Exception as e:
                    # 如果指定年份失败，使用默认参数
                    self.logger.warning(f"指定年份获取失败: {e}")
                    df = ak.fund_portfolio_hold_em(symbol=etf_code)
                
                if df is not None and not df.empty:
                    # 获取最新季度
                    latest_quarter = df['季度'].iloc[0]
                    
                    # 检查数据新鲜度
                    is_expired, warning_msg = self.check_data_freshness(latest_quarter)
                    if is_expired:
                        self.logger.warning(f"⚠️ {warning_msg}")
                        self.logger.warning(f"⚠️ 成分股数据可能不准确，请谨慎使用！")
                    else:
                        self.logger.info(f"获取最新季度持仓: {latest_quarter}")
                    
                    # 只取最新季度的数据
                    latest_df = df[df['季度'] == latest_quarter]
                    self.logger.info(f"最新季度数据行数: {len(latest_df)}")
                    
                    # 使用集合去重
                    seen_codes = set()
                    
                    for _, row in latest_df.iterrows():
                        code = row.get('股票代码')
                        name = row.get('股票名称')
                        weight = float(row.get('占净值比例', 0))
                        
                        if code and weight > 0:
                            # 标准化股票代码（补齐6位）
                            code_str = str(code)
                            if len(code_str) < 6 and code_str.isdigit():
                                code_str = code_str.zfill(6)
                            
                            # 去重
                            if code_str not in seen_codes:
                                seen_codes.add(code_str)
                                constituents.append({
                                    'code': code_str,
                                    'name': str(name) if name else '',
                                    'weight': weight,
                                    'timestamp': datetime.now(),
                                    'data_quarter': latest_quarter,
                                    'is_expired': is_expired
                                })
                    
                    self.logger.info(f"方法1成功: 获取{len(constituents)}只成分股")
                    return constituents
            except Exception as e:
                self.logger.warning(f"方法1失败: {e}")
            
            # 方法2: 针对主流ETF的特殊处理
            etf_composition_map = {
                '510050': '510050',  # 上证50
                '510300': '510300',  # 沪深300
                '510500': '510500',  # 中证500
                '159915': '159915',  # 创业板
            }
            
            if etf_code in etf_composition_map:
                try:
                    df = ak.fund_etf_holdings_em(symbol=etf_composition_map[etf_code])
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            code = row.get('股票代码')
                            name = row.get('股票名称')
                            weight = float(row.get('占净值比例', 0))
                            
                            if code and weight > 0:
                                constituents.append({
                                    'code': str(code).zfill(6),
                                    'name': str(name) if name else '',
                                    'weight': weight,
                                    'timestamp': datetime.now()
                                })
                        
                        self.logger.info(f"方法2成功: 获取{len(constituents)}只成分股")
                        return constituents
                except Exception as e:
                    self.logger.warning(f"方法2失败: {e}")
            
            self.logger.warning(f"未找到ETF成分股: {etf_code}")
            return None
            
        except ImportError:
            self.logger.error("AkShare未安装，请运行: pip install akshare")
            return None
        except Exception as e:
            self.logger.error(f"获取ETF成分股失败: {e}")
            return None

    def get_constituent_stocks_cache(self, etf_code: str) -> Optional[List[Dict]]:
        """
        从本地缓存获取成分股数据
        
        Args:
            etf_code: ETF代码
            
        Returns:
            List[Dict]: 成分股列表
        """
        cache_dir = os.path.join(self.config.DATA_DIR, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"constituents_{etf_code}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查缓存是否过期（默认7天）
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                if (datetime.now() - cache_time).days < 7:
                    self.logger.info(f"使用缓存成分股: {etf_code}, {len(data['constituents'])}只")
                    return data['constituents']
            except Exception as e:
                self.logger.warning(f"读取缓存失败: {e}")
        
        return None
    
    def get_stock_quote_sina(self, stock_code: str) -> Optional[float]:
        """
        使用新浪财经API获取股票实时价格
        
        Args:
            stock_code: 股票代码
            
        Returns:
            float: 股票实时价格
        """
        try:
            # 判断市场（上海股票以6开头）
            market = "sh" if stock_code.startswith('6') else "sz"
            url = f"http://hq.sinajs.cn/list={market}{stock_code}"
            
            response = self.requests_with_retry(url)
            if not response:
                return None
            
            response.encoding = 'gbk'
            data_str = response.text
            
            if '=' not in data_str or '"' not in data_str:
                return None
            
            content = data_str.split('=')[1].strip().strip(';').strip('"')
            fields = content.split(',')
            
            if len(fields) < 4:
                return None
            
            price = float(fields[3]) if fields[3] else 0
            
            if price > 0:
                return price
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"获取股票价格失败: {stock_code}, {e}")
            return None
    
    def get_stock_quotes_batch(self, stock_codes: List[str]) -> Dict[str, float]:
        """
        批量获取股票实时价格
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            Dict[str, float]: 股票代码到价格的映射
        """
        try:
            import concurrent.futures
            
            stock_quotes = {}
            
            # 使用线程池并发获取股票价格
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # 提交所有任务
                future_to_code = {
                    executor.submit(self.get_stock_quote_sina, code): code 
                    for code in stock_codes
                }
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_code):
                    code = future_to_code[future]
                    try:
                        price = future.result()
                        if price is not None:
                            stock_quotes[code] = price
                    except Exception as e:
                        self.logger.error(f"获取股票价格异常: {code}, {e}")
            
            self.logger.info(f"批量获取股票价格完成: {len(stock_quotes)}/{len(stock_codes)}只")
            return stock_quotes
            
        except ImportError:
            # 如果没有线程池支持，使用顺序执行
            stock_quotes = {}
            
            for code in stock_codes:
                price = self.get_stock_quote_sina(code)
                if price is not None:
                    stock_quotes[code] = price
            
            self.logger.info(f"批量获取股票价格完成: {len(stock_quotes)}/{len(stock_codes)}只")
            return stock_quotes
    
    def calculate_t0_arbitrage_opportunity(self, etf_code: str, 
                                          etf_price: float, 
                                          constituents: List[Dict], 
                                          stock_quotes: Dict[str, float]) -> Optional[Dict]:
        """
        计算T+0折套利机会
        
        Args:
            etf_code: ETF代码
            etf_price: ETF价格
            constituents: 成分股列表
            stock_quotes: 成分股价格映射
            
        Returns:
            Dict: T+0折套利机会数据
        """
        try:
            # 验证输入参数
            if not constituents:
                self.logger.warning(f"成分股列表为空: {etf_code}")
                return None
            
            if not stock_quotes:
                self.logger.warning(f"股票价格数据为空: {etf_code}")
                return None
            
            if etf_price <= 0:
                self.logger.warning(f"ETF价格异常: {etf_code}, {etf_price}")
                return None
            
            # 计算成分股组合价格
            total_value = 0.0
            total_weight = 0.0
            matched_count = 0
            
            for stock in constituents:
                code = stock['code']
                weight = stock.get('weight', 0)
                
                if code in stock_quotes and weight > 0:
                    total_value += stock_quotes[code] * weight
                    total_weight += weight
                    matched_count += 1
            
            if total_weight <= 0:
                self.logger.warning(f"有效成分股权重为0: {etf_code}")
                return None
            
            # 计算理论净值
            theoretical_nav = total_value / total_weight
            
            # 验证理论净值
            if theoretical_nav <= 0:
                self.logger.warning(f"理论净值异常: {etf_code}, {theoretical_nav}")
                return None
            
            # 计算折价率
            discount_rate = (theoretical_nav - etf_price) / theoretical_nav * 100
            
            # 计算套利收益（考虑交易成本）
            trading_fee = 0.0003  # 交易费率
            stamp_duty = 0.001  # 印花税
            
            # 买入ETF的成本
            buy_cost = etf_price * (1 + trading_fee)
            # 卖出成分股的收入（扣除成本）
            sell_revenue = theoretical_nav * (1 - trading_fee - stamp_duty)
            
            # 计算套利收益
            arbitrage_profit = sell_revenue - buy_cost
            profit_rate = arbitrage_profit / buy_cost * 100 if buy_cost > 0 else 0
            
            # 计算股票覆盖度
            stock_coverage = (matched_count / len(constituents)) * 100
            
            opportunity = {
                'etf_code': etf_code,
                'etf_price': etf_price,
                'theoretical_nav': theoretical_nav,
                'discount_rate': discount_rate,
                'buy_cost': buy_cost,
                'sell_revenue': sell_revenue,
                'arbitrage_profit': arbitrage_profit,
                'profit_rate': profit_rate,
                'stock_coverage': stock_coverage,
                'matched_stocks': matched_count,
                'total_stocks': len(constituents),
                'timestamp': datetime.now()
            }
            
            # 根据收益率级别记录日志
            if abs(profit_rate) > 1:
                self.logger.info(f"T+0折套利分析: 折价率={discount_rate:.4f}%, 收益率={profit_rate:.4f}% (高收益)")
            elif abs(profit_rate) > 0.5:
                self.logger.info(f"T+0折套利分析: 折价率={discount_rate:.4f}%, 收益率={profit_rate:.4f}% (中等收益)")
            else:
                self.logger.debug(f"T+0折套利分析: 折价率={discount_rate:.4f}%, 收益率={profit_rate:.4f}% (低收益)")
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"计算T+0折套利机会失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def save_constituents_cache(self, etf_code: str, constituents: List[Dict]):
        """
        保存成分股数据到缓存
        
        Args:
            etf_code: ETF代码
            constituents: 成分股列表
        """
        cache_dir = os.path.join(self.config.DATA_DIR, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"constituents_{etf_code}.json")
        
        try:
            # 检查是否有过期数据
            is_expired = any(stock.get('is_expired', False) for stock in constituents)
            data_quarter = constituents[0].get('data_quarter', 'Unknown') if constituents else 'Unknown'
            
            # 序列化datetime对象
            for stock in constituents:
                if isinstance(stock.get('timestamp'), datetime):
                    stock['timestamp'] = stock['timestamp'].isoformat()
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'constituents': constituents,
                'count': len(constituents),
                'data_quarter': data_quarter,
                'is_expired': is_expired
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            warning_msg = "⚠️ 数据已过期！" if is_expired else ""
            self.logger.info(f"成分股缓存已保存: {cache_file} {warning_msg}")
        except Exception as e:
            self.logger.warning(f"保存缓存失败: {e}")

    def calculate_real_nav(self, constituents: List[Dict], 
                         stock_quotes: Dict[str, float]) -> Optional[float]:
        """
        根据成分股价格计算实时净值
        
        Args:
            constituents: 成分股列表
            stock_quotes: 成分股实时行情 {code: price}
            
        Returns:
            float: 实时净值
        """
        try:
            total_value = 0.0
            total_weight = 0.0
            
            for stock in constituents:
                code = stock['code']
                weight = stock['weight']
                
                # 尝试不同格式的股票代码匹配
                matched_price = None
                for quote_code, price in stock_quotes.items():
                    if code in quote_code or quote_code in code:
                        matched_price = price
                        break
                
                if matched_price is not None:
                    total_value += matched_price * weight
                    total_weight += weight
            
            if total_weight > 0:
                nav = total_value / total_weight
                self.logger.info(f"计算实时净值成功: {nav:.4f}")
                return nav
            else:
                self.logger.warning("无法计算净值：缺少成分股价格数据")
                return None
                
        except Exception as e:
            self.logger.error(f"计算实时净值失败: {e}")
            return None

    def get_all_data(self, etf_code: str, 
                   use_akshare: bool = True,
                   use_cache: bool = True,
                   include_t0_opportunity: bool = False) -> Optional[Dict]:
        """
        获取所有实时数据
        
        Args:
            etf_code: ETF代码
            use_akshare: 是否使用AkShare
            use_cache: 是否使用缓存
            include_t0_opportunity: 是否包含T+0折套利机会
            
        Returns:
            Dict: 所有数据
        """
        self.logger.info(f"开始获取所有实时数据: {etf_code}")
        
        # 检查缓存
        if use_cache:
            cached = self.get_cached_data(etf_code)
            if cached and not include_t0_opportunity:
                return cached
        
        # 获取ETF行情
        if use_akshare:
            etf_quote = self.get_etf_quote_akshare(etf_code)
        else:
            etf_quote = self.get_etf_quote_sina(etf_code)
        
        if etf_quote is None:
            self.logger.error("获取ETF行情失败")
            return None
        
        # 获取IOPV（使用AkShare接口）
        iopv = None
        if use_akshare:
            iopv = self.get_iopv_eastmoney(etf_code)
        
        if iopv is None:
            self.logger.warning("IOPV获取失败，溢价率计算将受影响")
        
        # 获取成分股（先从缓存读，没有则实时获取）
        constituents = None
        if use_cache:
            constituents = self.get_constituent_stocks_cache(etf_code)
        
        if constituents is None and use_akshare:
            constituents = self.get_constituent_stocks_akshare(etf_code)
            if constituents and use_cache:
                self.save_constituents_cache(etf_code, constituents)
        
        data = {
            'etf_quote': etf_quote,
            'iopv': iopv,
            'constituents': constituents,
            'timestamp': datetime.now()
        }
        
        # 计算溢价率
        if iopv is not None and iopv > 0:
            premium_rate = (etf_quote['price'] - iopv) / iopv * 100
            data['premium_rate'] = round(premium_rate, 4)
            self.logger.info(f"溢价率: {data['premium_rate']:.4f}%")
        
        # 计算T+0折套利机会
        if include_t0_opportunity and constituents:
            # 提取成分股代码
            stock_codes = [stock['code'] for stock in constituents]
            
            # 批量获取成分股价格
            stock_quotes = self.get_stock_quotes_batch(stock_codes)
            
            if stock_quotes:
                # 计算T+0折套利机会
                t0_opportunity = self.calculate_t0_arbitrage_opportunity(
                    etf_code,
                    etf_quote['price'],
                    constituents,
                    stock_quotes
                )
                
                if t0_opportunity:
                    data['t0_opportunity'] = t0_opportunity
                    self.logger.info(f"T+0折套利机会: 收益率={t0_opportunity['profit_rate']:.4f}%")
        
        # 更新缓存
        self.update_cache(etf_code, data)
        self.last_update_time = datetime.now()
        
        self.logger.info("获取所有实时数据完成")
        return data

    def update_cache(self, etf_code: str, data: Dict):
        """
        更新缓存
        
        Args:
            etf_code: ETF代码
            data: 数据
        """
        self.etf_quote_cache[etf_code] = data.get('etf_quote')
        self.iopv_cache[etf_code] = data.get('iopv')
        self.constituent_cache[etf_code] = data.get('constituents')
        self.logger.info(f"缓存已更新: {etf_code}")

    def get_cached_data(self, etf_code: str) -> Optional[Dict]:
        """
        获取缓存数据
        
        Args:
            etf_code: ETF代码
            
        Returns:
            Dict: 缓存数据
        """
        if self.last_update_time is None:
            return None
        
        elapsed = (datetime.now() - self.last_update_time).total_seconds()
        
        if elapsed > self.cache_duration:
            self.logger.info(f"缓存已过期: {elapsed:.1f}秒")
            return None
        
        if etf_code not in self.etf_quote_cache:
            return None
        
        data = {
            'etf_quote': self.etf_quote_cache.get(etf_code),
            'iopv': self.iopv_cache.get(etf_code),
            'constituents': self.constituent_cache.get(etf_code),
            'timestamp': self.last_update_time
        }
        
        # 重新计算溢价率
        if data['iopv'] and data['iopv'] > 0 and data['etf_quote']:
            premium_rate = (data['etf_quote']['price'] - data['iopv']) / data['iopv'] * 100
            data['premium_rate'] = round(premium_rate, 4)
        
        self.logger.info(f"返回缓存数据: {etf_code}")
        return data

    def save_realtime_data(self, data: Dict, filename: str = None):
        """
        保存实时数据
        
        Args:
            data: 实时数据
            filename: 保存文件名
        """
        if filename is None:
            filename = os.path.join(
                self.config.RESULTS_DIR,
                f'{self.config.ETF_CODE}_realtime.csv'
            )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            record = {
                'timestamp': data['timestamp'],
                'etf_code': data['etf_quote']['code'],
                'etf_name': data['etf_quote']['name'],
                'etf_price': data['etf_quote']['price'],
                'iopv': data.get('iopv', 0),
                'premium_rate': data.get('premium_rate', 0),
                'volume': data['etf_quote']['volume'],
                'amount': data['etf_quote']['amount']
            }
            
            df = pd.DataFrame([record])
            
            if os.path.exists(filename):
                existing_df = pd.read_csv(filename)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(filename, index=False)
            self.logger.info(f"实时数据已保存: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存实时数据失败: {e}")


# 仅用于测试的代码，实际使用时由外部传入配置
if __name__ == '__main__':
    import sys
    
    # 测试配置（实际使用时会从外部导入）
    class TestConfig:
        ETF_CODE = '510500'
        RESULTS_DIR = './test_results'
    
    config = TestConfig()
    
    # 创建采集器
    collector = RealtimeDataCollector(config)
    
    # 测试函数
    def test_single_etf(etf_code):
        print(f"\n{'='*60}")
        print(f"测试ETF: {etf_code}")
        print('='*60)
        
        # 测试1: 获取实时行情
        print("\n1. 测试实时行情:")
        quote = collector.get_etf_quote_akshare(etf_code)
        if quote:
            print(f"   ✅ 成功: {quote['name']} 价格={quote['price']:.4f}")
        else:
            print("   ❌ 失败")
        
        # 测试2: 获取IOPV
        print("\n2. 测试IOPV获取:")
        iopv_em = collector.get_iopv_eastmoney(etf_code)
        if iopv_em:
            print(f"   ✅ 东方财富: {iopv_em:.4f}")
        else:
            print("   ❌ 东方财富失败")
        
        iopv_tx = collector.get_iopv_tencent(etf_code)
        if iopv_tx:
            print(f"   ✅ 腾讯: {iopv_tx:.4f}")
        else:
            print("   ❌ 腾讯失败")
        
        # 测试3: 获取成分股
        print("\n3. 测试成分股获取:")
        constituents = collector.get_constituent_stocks_akshare(etf_code)
        if constituents:
            print(f"   ✅ 成功: {len(constituents)}只成分股")
            print("   前5只:")
            for i, s in enumerate(constituents[:5]):
                print(f"     {i+1}. {s['code']} {s['name']} {s['weight']:.2f}%")
        else:
            print("   ❌ 失败")
        
        # 测试4: 获取所有数据
        print("\n4. 测试完整数据获取:")
        data = collector.get_all_data(etf_code)
        if data:
            print(f"   ✅ 成功")
            print(f"     价格: {data['etf_quote']['price']:.4f}")
            print(f"     IOPV: {data.get('iopv', 'N/A')}")
            print(f"     溢价率: {data.get('premium_rate', 'N/A')}%")
            if data.get('constituents'):
                print(f"     成分股: {len(data['constituents'])}只")
        else:
            print("   ❌ 失败")
    
    # 测试多个ETF
    test_etfs = ['510050', '510300', '510500', '159915']
    
    for etf in test_etfs:
        test_single_etf(etf)
        time.sleep(2)  #
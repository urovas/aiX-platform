#!/usr/bin/env python3
"""
订单执行模块
负责执行ETF套利交易订单
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Optional
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class OrderExecutor:
    """
    订单执行类
    """

    def __init__(self, config):
        """
        初始化订单执行器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.orders = []
        self.positions = {}

    def create_order(self, symbol: str, operation: str, 
                   quantity: float, price: float = None) -> Dict:
        """
        创建订单
        
        Args:
            symbol: 交易标的
            operation: 操作类型 ('buy' 或 'sell')
            quantity: 交易数量
            price: 交易价格（None为市价单）
            
        Returns:
            Dict: 订单信息
        """
        order = {
            'order_id': self.generate_order_id(),
            'symbol': symbol,
            'operation': operation,
            'quantity': quantity,
            'price': price,
            'status': 'pending',
            'create_time': datetime.now(),
            'update_time': datetime.now()
        }
        
        self.logger.info(f"创建订单: {order['order_id']}, {operation} {quantity} {symbol}")
        return order

    def generate_order_id(self) -> str:
        """
        生成订单ID
        
        Returns:
            str: 订单ID
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_num = np.random.randint(1000, 9999)
        return f"ORD{timestamp}{random_num}"

    def execute_order(self, order: Dict, 
                    execution_price: float = None) -> Dict:
        """
        执行订单
        
        Args:
            order: 订单信息
            execution_price: 执行价格（None为市价）
            
        Returns:
            Dict: 执行结果
        """
        self.logger.info(f"执行订单: {order['order_id']}")
        
        order['status'] = 'executing'
        order['update_time'] = datetime.now()
        
        if execution_price is None:
            execution_price = self.get_market_price(order['symbol'])
        
        order['execution_price'] = execution_price
        order['execution_time'] = datetime.now()
        order['status'] = 'filled'
        
        order['commission'] = self.calculate_commission(
            execution_price, 
            order['quantity']
        )
        
        if order['operation'] == 'sell':
            order['stamp_duty'] = self.calculate_stamp_duty(
                execution_price,
                order['quantity']
            )
        else:
            order['stamp_duty'] = 0
        
        order['total_cost'] = order['commission'] + order['stamp_duty']
        
        self.orders.append(order)
        self.update_position(order)
        
        self.logger.info(f"订单执行成功: {order['order_id']}, "
                      f"价格={execution_price:.4f}, "
                      f"成本={order['total_cost']:.2f}")
        
        return order

    def get_market_price(self, symbol: str) -> float:
        """
        获取市场价格（模拟）
        
        Args:
            symbol: 交易标的
            
        Returns:
            float: 市场价格
        """
        return np.random.uniform(4.5, 5.5)

    def calculate_commission(self, price: float, quantity: float) -> float:
        """
        计算佣金
        
        Args:
            price: 价格
            quantity: 数量
            
        Returns:
            float: 佣金
        """
        amount = price * quantity
        commission = amount * self.config.TRADING_FEE_RATE
        
        commission = max(commission, 5)
        
        return commission

    def calculate_stamp_duty(self, price: float, quantity: float) -> float:
        """
        计算印花税
        
        Args:
            price: 价格
            quantity: 数量
            
        Returns:
            float: 印花税
        """
        amount = price * quantity
        stamp_duty = amount * self.config.STAMP_DUTY_RATE
        
        return stamp_duty

    def update_position(self, order: Dict):
        """
        更新持仓
        
        Args:
            order: 订单信息
        """
        symbol = order['symbol']
        
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0
            }
        
        if order['operation'] == 'buy':
            old_quantity = self.positions[symbol]['quantity']
            old_cost = self.positions[symbol]['total_cost']
            
            new_quantity = old_quantity + order['quantity']
            new_cost = old_cost + order['quantity'] * order['execution_price'] + order['total_cost']
            
            self.positions[symbol]['quantity'] = new_quantity
            self.positions[symbol]['avg_price'] = new_cost / new_quantity
            self.positions[symbol]['total_cost'] = new_cost
        
        elif order['operation'] == 'sell':
            old_quantity = self.positions[symbol]['quantity']
            
            self.positions[symbol]['quantity'] = old_quantity - order['quantity']
            
            if self.positions[symbol]['quantity'] <= 0:
                self.positions[symbol]['quantity'] = 0
                self.positions[symbol]['avg_price'] = 0
                self.positions[symbol]['total_cost'] = 0

    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 是否成功
        """
        for order in self.orders:
            if order['order_id'] == order_id and order['status'] == 'pending':
                order['status'] = 'cancelled'
                order['update_time'] = datetime.now()
                
                self.logger.info(f"订单已撤销: {order_id}")
                return True
        
        self.logger.warning(f"订单不存在或无法撤销: {order_id}")
        return False

    def query_order(self, order_id: str) -> Optional[Dict]:
        """
        查询订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            Dict: 订单信息
        """
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        
        return None

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        获取持仓
        
        Args:
            symbol: 交易标的
            
        Returns:
            Dict: 持仓信息
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict:
        """
        获取所有持仓
        
        Returns:
            Dict: 所有持仓
        """
        return self.positions

    def execute_premium_arbitrage(self, etf_code: str, 
                                etf_price: float, 
                                nav: float) -> Dict:
        """
        执行溢价套利
        
        Args:
            etf_code: ETF代码
            etf_price: ETF价格
            nav: 基金净值
            
        Returns:
            Dict: 执行结果
        """
        self.logger.info(f"执行溢价套利: {etf_code}, 价格={etf_price:.4f}, 净值={nav:.4f}")
        
        quantity = self.calculate_position_size(nav)
        
        buy_order = self.create_order(etf_code, 'buy', quantity, nav)
        buy_result = self.execute_order(buy_order, nav)
        
        sell_order = self.create_order(etf_code, 'sell', quantity, etf_price)
        sell_result = self.execute_order(sell_order, etf_price)
        
        total_cost = buy_result['total_cost'] + sell_result['total_cost']
        total_revenue = quantity * etf_price
        profit = total_revenue - quantity * nav - total_cost
        
        result = {
            'operation': 'premium_arbitrage',
            'etf_code': etf_code,
            'buy_price': nav,
            'sell_price': etf_price,
            'quantity': quantity,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'profit': profit,
            'profit_rate': profit / (quantity * nav),
            'execution_time': datetime.now()
        }
        
        self.logger.info(f"溢价套利完成，收益: {profit:.2f}, 收益率: {result['profit_rate']:.4f}")
        
        return result

    def execute_discount_arbitrage(self, etf_code: str, 
                                 etf_price: float, 
                                 nav: float) -> Dict:
        """
        执行折价套利
        
        Args:
            etf_code: ETF代码
            etf_price: ETF价格
            nav: 基金净值
            
        Returns:
            Dict: 执行结果
        """
        self.logger.info(f"执行折价套利: {etf_code}, 价格={etf_price:.4f}, 净值={nav:.4f}")
        
        quantity = self.calculate_position_size(etf_price)
        
        buy_order = self.create_order(etf_code, 'buy', quantity, etf_price)
        buy_result = self.execute_order(buy_order, etf_price)
        
        sell_order = self.create_order(etf_code, 'sell', quantity, nav)
        sell_result = self.execute_order(sell_order, nav)
        
        total_cost = buy_result['total_cost'] + sell_result['total_cost']
        total_revenue = quantity * nav
        profit = total_revenue - quantity * etf_price - total_cost
        
        result = {
            'operation': 'discount_arbitrage',
            'etf_code': etf_code,
            'buy_price': etf_price,
            'sell_price': nav,
            'quantity': quantity,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'profit': profit,
            'profit_rate': profit / (quantity * etf_price),
            'execution_time': datetime.now()
        }
        
        self.logger.info(f"折价套利完成，收益: {profit:.2f}, 收益率: {result['profit_rate']:.4f}")
        
        return result

    def calculate_position_size(self, price: float) -> float:
        """
        计算持仓规模
        
        Args:
            price: 价格
            
        Returns:
            float: 持仓数量
        """
        max_by_capital = self.config.MAX_POSITION / price
        max_by_single_trade = self.config.MAX_SINGLE_TRADE / price
        
        position_size = min(max_by_capital, max_by_single_trade)
        
        return position_size
    
    def execute_t0_arbitrage(self, etf_code: str, 
                           etf_price: float, 
                           constituents: List[Dict], 
                           stock_quotes: Dict[str, float]) -> Dict:
        """
        执行T+0折套利
        
        Args:
            etf_code: ETF代码
            etf_price: ETF价格
            constituents: 成分股列表
            stock_quotes: 成分股价格映射
            
        Returns:
            Dict: 执行结果
        """
        self.logger.info(f"执行T+0折套利: {etf_code}, 价格={etf_price:.4f}")
        
        # 计算ETF买入数量
        etf_quantity = self.calculate_position_size(etf_price)
        
        # 执行ETF买入订单
        etf_buy_order = self.create_order(etf_code, 'buy', etf_quantity, etf_price)
        etf_buy_result = self.execute_order(etf_buy_order, etf_price)
        
        # 执行成分股卖出订单
        stock_sell_orders = []
        total_stock_revenue = 0.0
        total_stock_cost = 0.0
        
        for stock in constituents:
            stock_code = stock['code']
            weight = stock['weight']
            
            if stock_code in stock_quotes:
                stock_price = stock_quotes[stock_code]
                # 根据权重计算卖出数量
                stock_quantity = etf_quantity * (weight / 100)  # 权重转换为比例
                
                if stock_quantity > 0:
                    stock_sell_order = self.create_order(stock_code, 'sell', stock_quantity, stock_price)
                    stock_sell_result = self.execute_order(stock_sell_order, stock_price)
                    
                    stock_sell_orders.append(stock_sell_result)
                    total_stock_revenue += stock_quantity * stock_price
                    total_stock_cost += stock_sell_result['total_cost']
        
        # 计算总成本和总收益
        total_cost = etf_buy_result['total_cost'] + total_stock_cost
        total_revenue = total_stock_revenue
        profit = total_revenue - etf_quantity * etf_price - total_cost
        
        result = {
            'operation': 't0_arbitrage',
            'etf_code': etf_code,
            'etf_buy_price': etf_price,
            'etf_quantity': etf_quantity,
            'stock_sell_count': len(stock_sell_orders),
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'profit': profit,
            'profit_rate': profit / (etf_quantity * etf_price),
            'execution_time': datetime.now(),
            'etf_order': etf_buy_result,
            'stock_orders': stock_sell_orders
        }
        
        self.logger.info(f"T+0折套利完成，收益: {profit:.2f}, 收益率: {result['profit_rate']:.4f}")
        
        return result

    def get_execution_summary(self) -> Dict:
        """
        获取执行摘要
        
        Returns:
            Dict: 执行摘要
        """
        total_orders = len(self.orders)
        filled_orders = len([o for o in self.orders if o['status'] == 'filled'])
        cancelled_orders = len([o for o in self.orders if o['status'] == 'cancelled'])
        
        total_cost = sum(o['total_cost'] for o in self.orders)
        
        summary = {
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'fill_rate': filled_orders / total_orders if total_orders > 0 else 0,
            'total_cost': total_cost,
            'current_positions': len(self.positions)
        }
        
        return summary


if __name__ == '__main__':
    import sys
    sys.path.append('..')
    from config import config
    
    executor = OrderExecutor(config)
    
    order = executor.create_order('510500', 'buy', 1000, 5.0)
    result = executor.execute_order(order, 5.0)
    
    print("\n订单执行结果:")
    print(f"订单ID: {result['order_id']}")
    print(f"执行价格: {result['execution_price']:.4f}")
    print(f"佣金: {result['commission']:.2f}")
    print(f"印花税: {result['stamp_duty']:.2f}")
    print(f"总成本: {result['total_cost']:.2f}")
    
    summary = executor.get_execution_summary()
    print("\n执行摘要:")
    print(f"总订单数: {summary['total_orders']}")
    print(f"成交订单数: {summary['filled_orders']}")
    print(f"成交率: {summary['fill_rate']:.4f}")
    print(f"总成本: {summary['total_cost']:.2f}")

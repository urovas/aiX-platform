#!/usr/bin/env python3
"""
ETF套利系统配置文件
"""

import os

class Config:
    """
    ETF套利系统配置类
    """

    ETF_CODE = '513100'
    ETF_NAME = '纳指ETF'

    # 监控的ETF列表(只保留中证500ETF)
    MONITORED_ETFS = [
        {'code': '510500', 'name': '中证500ETF', 'type': 'index'},
    ]

    DATA_DIR = '/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage/data'
    LOGS_DIR = '/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage/logs'
    RESULTS_DIR = '/home/xcc/openclaw-platform/workspace/quant/etf_arbitrage/results'

    PREMIUM_THRESHOLD = 0.005
    DISCOUNT_THRESHOLD = 0.005

    MIN_PROFIT_THRESHOLD = 0.003  # 0.3%，当收益率达到0.3%时即可交易

    TRADING_FEE_RATE = 0.001  # 0.1%
    STAMP_DUTY_RATE = 0.0  # T+0交易无印花税

    MAX_POSITION = 1000000
    MAX_SINGLE_TRADE = 100000

    MAX_SUSPENDED_STOCKS = 3

    MONITOR_INTERVAL = 1

    LOG_LEVEL = 'INFO'

    BACKTEST_START_DATE = '2020-01-01'
    BACKTEST_END_DATE = '2025-12-31'

    INITIAL_CAPITAL = 1000000

    RISK_FREE_RATE = 0.03

config = Config()

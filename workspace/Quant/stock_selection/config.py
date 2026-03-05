# 量化选股模型配置文件

class Config:
    # 基础配置
    PROJECT_NAME = "Quantitative Stock Selection Model"
    VERSION = "1.0.0"
    
    # 数据配置
    DATA_DIR = "/home/xcc/openclaw-platform/workspace/quant/stock_selection/data"
    
    # 股票池配置
    STOCK_UNIVERSE = {
        "CSI300": "沪深300",
        "CSI500": "中证500",
        "CSI1000": "中证1000",
        "SH50": "上证50",
        "SZ50": "深证50"
    }
    
    # 因子配置
    FACTORS = {
        # 价值因子
        "value": [
            "pb",  # 市净率
            "pe_ttm",  # 滚动市盈率
            "ps_ttm",  # 滚动市销率
            "pcf_ttm",  # 滚动市现率
            "ev_ebitda"  # 企业价值/息税折旧摊销前利润
        ],
        
        # 成长因子
        "growth": [
            "revenue_growth_rate",  # 营收增长率
            "net_profit_growth_rate",  # 净利润增长率
            "eps_growth_rate",  # 每股收益增长率
            "roe_growth_rate",  # 净资产收益率增长率
            "operating_profit_growth_rate"  # 营业利润增长率
        ],
        
        # 质量因子
        "quality": [
            "roe",  # 净资产收益率
            "roa",  # 总资产收益率
            "net_profit_margin",  # 净利润率
            "operating_profit_margin",  # 营业利润率
            "asset_turnover",  # 总资产周转率
            "debt_to_asset_ratio",  # 资产负债率
            "current_ratio"  # 流动比率
        ],
        
        # 动量因子
        "momentum": [
            "return_1m",  # 1个月收益率
            "return_3m",  # 3个月收益率
            "return_6m",  # 6个月收益率
            "return_12m",  # 12个月收益率
            "volatility_1m",  # 1个月波动率
            "volatility_3m"  # 3个月波动率
        ],
        
        # 技术因子
        "technical": [
            "macd",  # MACD指标
            "kdj_k",  # KDJ指标K值
            "kdj_d",  # KDJ指标D值
            "rsi",  # RSI指标
            "ma_5_20_diff",  # 5日均线与20日均线差值
            "volume_change_rate"  # 成交量变化率
        ]
    }
    
    # 模型配置
    MODEL_CONFIG = {
        # 因子权重
        "factor_weights": {
            "value": 0.25,
            "growth": 0.25,
            "quality": 0.25,
            "momentum": 0.15,
            "technical": 0.10
        },
        
        # 模型参数
        "model_params": {
            "lookback_period": 12,  # 回溯期（月）
            "holding_period": 3,  # 持有期（月）
            "rebalance_frequency": "monthly",  # 再平衡频率
            "top_n": 50,  # 选股数量
            "min_market_cap": 10,  # 最小市值（亿）
            "max_pe": 50,  # 最大市盈率
            "max_pb": 5,  # 最大市净率
            "exclude_st": True,  # 排除ST股票
            "exclude_suspended": True  # 排除停牌股票
        },
        
        # 回测配置
        "backtest_params": {
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 1000000,  # 初始资金
            "transaction_fee": 0.0003,  # 交易费率
            "slippage": 0.0005  # 滑点
        }
    }
    
    # 数据源配置
    DATA_SOURCE = {
        "tushare": {
            "token": "8d493c0fbdfc7a1a3e75ff198eba7dae63e25099ffcdf99cd5843a8f",  # Tushare token
            "timeout": 30,
            "retry_count": 3
        },
        "akshare": {
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    # 日志配置
    LOG_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_dir": "/home/xcc/openclaw-platform/workspace/quant/stock_selection/logs"
    }

# 导出配置实例
config = Config()

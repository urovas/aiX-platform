# 量化指数增强（Quantitative Index Enhancement）配置文件

class Config:
    # 项目信息
    PROJECT_NAME = "Quantitative Index Enhancement"
    VERSION = "2.0.0"
    
    # 数据目录
    DATA_DIR = "/home/xcc/openclaw-platform/workspace/quant/index_enhancement/data"
    RESULT_DIR = "/home/xcc/openclaw-platform/workspace/quant/index_enhancement/results"
    LOG_DIR = "/home/xcc/openclaw-platform/workspace/quant/index_enhancement/logs"
    
    # 指数配置
    INDEX_CONFIG = {
        "CSI300": {
            "code": "000300.SH",
            "name": "沪深300",
            "description": "沪深300指数增强"
        },
        "CSI500": {
            "code": "000905.SH",
            "name": "中证500",
            "description": "中证500指数增强"
        },
        "CSI1000": {
            "code": "000852.SH",
            "name": "中证1000",
            "description": "中证1000指数增强"
        }
    }
    
    # 数据源配置
    DATA_SOURCE = {
        "tushare": {
            "token": "8d493c0fbdfc7a1a3e75ff198eba7dae63e25099ffcdf99cd5843a8f",
            "timeout": 30,
            "retry_count": 3
        },
        "akshare": {
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    # 因子配置
    # 传统因子（基本面、量价、估值）
    TRADITIONAL_FACTORS = {
        # 基本面因子（捕捉企业盈利，即EPS）
        "fundamental": [
            "eps_growth",  # EPS增长率
            "roe",  # 净资产收益率
            "roa",  # 总资产收益率
            "revenue_growth",  # 营收增长率
            "profit_growth",  # 利润增长率
            "debt_ratio",  # 资产负债率
            "current_ratio",  # 流动比率
        ],
        
        # 量价因子（捕捉市场情绪）
        "price_volume": [
            "momentum_5d",  # 5日动量
            "momentum_20d",  # 20日动量
            "momentum_60d",  # 60日动量
            "volatility_5d",  # 5日波动率
            "volatility_20d",  # 20日波动率
            "volume_ratio",  # 成交量比率
            "turnover_rate",  # 换手率
        ],
        
        # 估值因子（捕捉市场情绪，即PE）
        "valuation": [
            "pe_ttm",  # 滚动市盈率
            "pb",  # 市净率
            "ps_ttm",  # 滚动市销率
            "pcf_ttm",  # 滚动市现率
            "pe_g",  # PEG比率
        ]
    }
    
    # AI驱动因子（端到端神经网络）
    AI_FACTORS = {
        "nn_features": [
            "nn_raw_1",  # 神经网络原始特征1
            "nn_raw_2",  # 神经网络原始特征2
            "nn_raw_3",  # 神经网络原始特征3
            # ... 更多原始特征
        ],
        "nn_output": [
            "nn_prediction",  # 神经网络预测值
            "nn_confidence",  # 神经网络预测置信度
        ]
    }
    
    # 模型配置
    MODEL_CONFIG = {
        # 双均衡框架
        "dual_balance": {
            # 方法论均衡：传统多因子模型与AI全流程模型各占50%权重
            "methodology_balance": {
                "traditional_weight": 0.5,
                "ai_weight": 0.5
            },
            
            # 因子来源均衡：收益预测的一半来源于基本面因子，另一半来源于量价、估值因子
            "factor_source_balance": {
                "fundamental_weight": 0.5,
                "price_volume_valuation_weight": 0.5
            }
        },
        
        # 模型融合：GBDT + NN
        "model_fusion": {
            "gbdt_weight": 0.5,
            "nn_weight": 0.5
        },
        
        # 传统因子模型参数
        "traditional_model": {
            "lookback_period": 20,  # 回溯期（交易日）
            "holding_period": 20,  # 持有期（交易日）
            "rebalance_frequency": "monthly",  # 再平衡频率
        },
        
        # AI模型参数
        "ai_model": {
            "nn_layers": [128, 64, 32],  # 神经网络层数和神经元数
            "activation": "relu",  # 激活函数
            "dropout": 0.2,  # Dropout率
            "learning_rate": 0.001,  # 学习率
            "epochs": 100,  # 训练轮数
            "batch_size": 32,  # 批次大小
        },
        
        # GBDT模型参数
        "gbdt_model": {
            "n_estimators": 50,  # 树的数量（减少以减少过拟合）
            "max_depth": 3,  # 树的最大深度（减少以减少过拟合）
            "learning_rate": 0.1,  # 学习率
            "subsample": 0.8,  # 子采样率
            "min_samples_split": 5,  # 最小分裂样本数
            "min_samples_leaf": 2,  # 最小叶节点样本数
        },
        
        # 权重分配器配置（统一配置）
        "weight_allocator": {
            # 权重分配方法: 'baseline', 'ppo', 'hybrid'
            # - baseline: 基于规则的动态权重分配
            # - ppo: 基于PPO强化学习的权重分配
            # - hybrid: 混合模式（优先使用PPO，如果不可用则使用baseline）
            "weight_method": "baseline",
            
            # 是否启用PPO（默认禁用，训练后可启用）
            "enable_ppo": False,
            "ppo_model_path": "./models/saved/ppo_weight_allocator.pth",
            
            # 基线方法配置
            "base_weights": {
                "high_frequency": 0.5,
                "fundamental": 0.5,
            },
            "adjustment_factors": {
                "market_regime": 0.3,
                "signal_quality": 0.25,
                "volatility": 0.2,
                "liquidity": 0.15,
                "time_decay": 0.1,
            },
            "market_regimes": {
                "bull": {"hf_weight": 0.6, "fd_weight": 0.4},
                "bear": {"hf_weight": 0.4, "fd_weight": 0.6},
                "sideways": {"hf_weight": 0.5, "fd_weight": 0.5},
                "crisis": {"hf_weight": 0.7, "fd_weight": 0.3},
            },
            "smoothing_factor": 0.7,
            
            # PPO方法配置
            "ppo_lr": 3e-4,  # 学习率
            "ppo_gamma": 0.99,  # 折扣因子
            "ppo_gae_lambda": 0.95,  # GAE参数
            "ppo_clip_epsilon": 0.2,  # PPO裁剪参数
            "ppo_entropy_coef": 0.01,  # 熵系数
            "ppo_value_coef": 0.5,  # 价值函数系数
            "ppo_max_grad_norm": 0.5,  # 梯度裁剪
            "ppo_epochs": 10,  # PPO更新轮数
            "ppo_batch_size": 64,  # 批次大小
            "ppo_buffer_size": 2048,  # 经验缓冲区大小
            "ppo_state_dim": 20,  # 状态空间维度
            "ppo_num_episodes": 1000,  # 训练轮数
            "ppo_save_interval": 100,  # 保存间隔
            "ppo_eval_interval": 50,  # 评估间隔
        }
    }
    
    # 组合优化配置
    PORTFOLIO_OPTIMIZATION = {
        # 跟踪误差控制
        "tracking_error": {
            "max_tracking_error": 0.03,  # 最大跟踪误差3%
            "max_sector_deviation": 0.1,  # 最大行业偏离度10%
            "max_stock_weight": 0.05,  # 单只股票最大权重5%
            "min_stock_weight": 0.001,  # 单只股票最小权重0.1%
        },
        
        # 风险控制
        "risk_control": {
            "max_turnover": 0.5,  # 最大换手率50%
            "max_drawdown": 0.15,  # 最大回撤15%
            "volatility_target": 0.2,  # 目标波动率20%
        }
    }
    
    # 回测配置
    BACKTEST_CONFIG = {
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "initial_capital": 100000000,  # 初始资金1亿
        "transaction_cost": 0.0003,  # 交易成本0.03%
        "slippage": 0.0005,  # 滑点0.05%
    }
    
    # 评估指标
    EVALUATION_METRICS = {
        "return_metrics": [
            "total_return",  # 总收益率
            "annual_return",  # 年化收益率
            "excess_return",  # 超额收益
            "annual_excess_return",  # 年化超额收益
        ],
        "risk_metrics": [
            "volatility",  # 波动率
            "max_drawdown",  # 最大回撤
            "tracking_error",  # 跟踪误差
            "information_ratio",  # 信息比率
            "sharpe_ratio",  # 夏普比率
        ]
    }

# 导出配置实例
config = Config()

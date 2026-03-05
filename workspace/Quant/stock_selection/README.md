# 量化选股模型

## 项目简介

这是一个基于多因子模型的量化选股系统，能够：
- 基于价值、成长、质量、动量、技术等多维度因子进行股票选择
- 分析选股结果的行业分布和市值分布
- 构建投资组合并计算权重
- 回测选股策略的历史表现

## 目录结构

```
stock_selection/
├── config.py          # 配置文件
├── main.py            # 主脚本
├── data/              # 数据目录
├── models/            # 模型目录
│   └── selection_model.py  # 选股模型
├── strategies/        # 策略目录
│   └── execution_strategy.py  # 执行策略
└── utils/             # 工具目录
    ├── data_fetcher.py       # 数据获取
    └── factor_calculator.py  # 因子计算
```

## 系统要求

- Python 3.7+
- 依赖库：
  - pandas
  - numpy
  - scikit-learn
  - tushare (可选，用于获取更多数据)
  - akshare (可选，用于获取更多数据)

## 安装依赖

```bash
pip install pandas numpy scikit-learn tushare akshare
```

## 配置说明

1. **修改配置文件** (`config.py`):
   - 设置 Tushare token (可选)
   - 调整因子权重
   - 配置回测参数

2. **数据目录**:
   - 系统会自动在 `data/` 目录下创建和管理数据文件
   - 首次运行会下载必要的股票数据

## 使用方法

### 运行主脚本

```bash
cd /home/xcc/openclaw-platform/workspace/quant/stock_selection
python main.py
```

### 操作菜单

1. **运行量化选股策略**
   - 选择股票池 (沪深300、中证500等)
   - 设置选股数量
   - 选择模型类型 (线性回归、随机森林)
   - 选择加权方法 (等权、市值加权、收益率加权)

2. **训练选股模型**
   - 系统会自动准备训练数据并训练模型
   - 训练完成后会显示模型评估结果

3. **回测策略**
   - 系统会回测过去一年的策略表现
   - 显示月度收益率和累计收益

4. **查看选股结果**
   - 显示最近的选股结果文件
   - 查看详细的选股列表

## 因子说明

### 价值因子
- pb: 市净率
- pe_ttm: 滚动市盈率
- ps_ttm: 滚动市销率
- pcf_ttm: 滚动市现率

### 成长因子
- revenue_growth_rate: 营收增长率
- net_profit_growth_rate: 净利润增长率
- eps_growth_rate: 每股收益增长率

### 质量因子
- roe: 净资产收益率
- roa: 总资产收益率
- net_profit_margin: 净利润率
- debt_to_asset_ratio: 资产负债率

### 动量因子
- return_1m: 1个月收益率
- return_3m: 3个月收益率
- return_6m: 6个月收益率
- return_12m: 12个月收益率
- volatility_1m: 1个月波动率
- volatility_3m: 3个月波动率

### 技术因子
- macd: MACD指标
- kdj_k: KDJ指标K值
- kdj_d: KDJ指标D值
- rsi: RSI指标
- ma_5_20_diff: 5日均线与20日均线差值
- volume_change_rate: 成交量变化率

## 输出结果

系统会在 `data/results/` 目录下生成以下文件：

- `stock_selection_{universe}_{timestamp}.csv`: 选股结果
- `industry_distribution_{timestamp}.csv`: 行业分布
- `market_cap_distribution_{timestamp}.csv`: 市值分布
- `portfolio_{timestamp}.csv`: 投资组合

## 示例输出

### 选股结果

| rank | name     | ts_code    | industry | predicted_return |
|------|----------|------------|----------|------------------|
| 1    | 贵州茅台 | 600519.SH  | 白酒     | 0.085            |
| 2    | 宁德时代 | 300750.SZ  | 新能源   | 0.072            |
| 3    | 腾讯控股 | 0700.HK    | 互联网   | 0.065            |

### 行业分布

| industry | count | percentage |
|----------|-------|------------|
| 新能源   | 15    | 30.0%      |
| 科技     | 10    | 20.0%      |
| 医药     | 8     | 16.0%      |

## 注意事项

1. **数据质量**:
   - 首次运行时数据下载可能需要较长时间
   - 部分数据可能存在缺失，系统会自动处理

2. **模型性能**:
   - 模型预测结果仅供参考，不构成投资建议
   - 建议结合基本面分析和市场环境进行投资决策

3. **风险管理**:
   - 投资有风险，入市需谨慎
   - 建议设置合理的止损策略

4. **系统维护**:
   - 定期更新数据以确保模型准确性
   - 根据市场变化调整因子权重

## 版本历史

- v1.0.0 (2026-02-25): 初始版本，支持多因子选股和回测

## 联系信息

如有问题或建议，请联系系统管理员。



🎯 第三版训练脚本特性 trainer_expert.py
高级特征工程：20个特征，智能特征选择
多样化模型：线性模型、树模型、Boosting模型
模型集成：综合多个模型的预测
时间序列划分：避免数据泄露
特征标准化：提高模型稳定性
最佳模型：ElasticNet（测试集R²=0.5553）
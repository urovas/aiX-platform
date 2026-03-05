#!/usr/bin/env python3
# csi500_backtest_min.py
# 中证500因子回测（最小可行版）—— 仅依赖 pandas/numpy
import pandas as pd
import numpy as np

np.random.seed(42)
months = 24
n_stocks = 10
stocks = [f"STK{i:03d}" for i in range(1, n_stocks+1)]

# 模拟因子：动量（均值 0.05，标准差 0.03）
factor_data = pd.DataFrame(
    np.random.normal(0.05, 0.03, size=(months, n_stocks)),
    index=pd.date_range("2024-02-01", periods=months, freq="MS"),
    columns=stocks
)

# 模拟收益：与因子正相关 + 噪声
returns = factor_data * 0.8 + np.random.normal(0, 0.02, size=factor_data.shape)
returns = returns.clip(lower=-0.3, upper=0.3)  # 限制极端值

# 回测：每月按因子分组，做多Top2，做空Bottom2
equity_curve = [1.0]
long_short_returns = []

for i, date in enumerate(factor_data.index[:-1]):  # 最后一个月无未来收益
    factors = factor_data.loc[date]
    rets_next = returns.loc[factor_data.index[i+1]]
    
    # 分组
    ranked = factors.sort_values(ascending=False)
    long_ids = ranked.head(2).index
    short_ids = ranked.tail(2).index
    
    long_ret = rets_next[long_ids].mean()
    short_ret = -rets_next[short_ids].mean()  # 做空收益取反
    portfolio_ret = (long_ret + short_ret) / 2  # 等权
    
    long_short_returns.append(portfolio_ret)
    equity_curve.append(equity_curve[-1] * (1 + portfolio_ret))

# 统计
eq_series = pd.Series(equity_curve, index=factor_data.index.insert(0, factor_data.index[0] - pd.DateOffset(months=1)))
annual_return = (eq_series.iloc[-1] ** (12/len(long_short_returns)) - 1) * 100
max_drawdown = (eq_series / eq_series.cummax() - 1).min() * 100
win_rate = np.mean(np.array(long_short_returns) > 0) * 100

print("📈 中证500因子回测结果（24个月模拟）")
print(f"年化收益: {annual_return:.2f}%")
print(f"最大回撤: {max_drawdown:.2f}%")
print(f"胜率: {win_rate:.1f}%")
print(f"夏普比率: {np.mean(long_short_returns)/np.std(long_short_returns)*np.sqrt(12):.2f}")

# 保存
output_dir = "./reports/csi500_backtest_20260222"
import os
os.makedirs(output_dir, exist_ok=True)
with open(f"{output_dir}/result.txt", "w") as f:
    f.write(f"年化收益: {annual_return:.2f}%\n")
    f.write(f"最大回撤: {max_drawdown:.2f}%\n")
    f.write(f"胜率: {win_rate:.1f}%\n")
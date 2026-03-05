import akshare as ak
import pandas as pd

# 方案A：尝试获取ETF列表（验证akshare是否正常）
print("尝试获取ETF列表...")
etf_list = ak.fund_etf_category_sina(symbol="ETF基金")
print(f"成功获取ETF列表，共{len(etf_list)}只")
print(etf_list.head())

# 方案B：获取510500日线（备选接口）
try:
    df = ak.fund_etf_hist_sina(symbol="sh510500")
    df.to_csv("510500_daily.csv")
    print(f"日线数据已保存，共{len(df)}条")
    print(df.head())
except Exception as e:
    print(f"方案B失败: {e}")
    
    # 方案C：用股票接口代替（ETF本质也是股票）
    print("尝试用股票接口获取...")
    df = ak.stock_zh_a_hist(symbol="510500", 
                            period="daily", 
                            start_date="20200101",
                            adjust="qfq")
    df.to_csv("510500_daily.csv")
    print(f"股票接口数据已保存，共{len(df)}条")
    print(df.head())
    
import akshare as ak
import pandas as pd

print("akshare版本:", ak.__version__)
print("可用函数示例:", dir(ak)[:20])  # 打印前20个函数名看看

# 尝试获取ETF日线
try:
    df = ak.fund_etf_hist_sina(symbol="sh510500")
    print("fund_etf_hist_sina 成功")
except Exception as e:
    print("fund_etf_hist_sina 失败:", e)
    try:
        df = ak.stock_zh_a_hist(symbol="510500", period="daily", start_date="20200101")
        print("stock_zh_a_hist 成功")
    except Exception as e:
        print("stock_zh_a_hist 失败:", e)
        df = None

if df is not None:
    df.to_csv("510500_daily.csv")
    print(f"数据已保存，共{len(df)}条")
    print(df.head())
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

try:
    # ========= 0. 确保工作目录在仓库根目录 =========
    os.chdir(os.getcwd())

    # ========= 1. streak 文件 =========
    STREAK_FILE = "top500_streak.csv"
    if os.path.exists(STREAK_FILE):
        streak_df = pd.read_csv(STREAK_FILE)
        streak_dict = dict(zip(streak_df["Symbol"], streak_df["Streak"]))
    else:
        streak_dict = {}

    # ========= 2. 测试股票列表 =========
    symbols = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"]  # 小规模测试

    print(f"股票总数量: {len(symbols)}")

    # ========= 3. 拉行情 =========
    data = yf.download(symbols, period="3d", interval="1d", group_by="ticker", threads=True, progress=False)

    rows = []
    for sym in symbols:
        try:
            df = data[sym].dropna()
            if len(df) < 2:
                continue
            y, p = df.iloc[-1], df.iloc[-2]
            turnover = y["Close"] * y["Volume"]
            direction = 1 if y["Close"] > p["Close"] else -1
            net_flow = turnover * direction

            rows.append({
                "Symbol": sym,
                "Close": round(y["Close"], 2),
                "Volume": int(y["Volume"]),
                "Turnover": round(turnover, 2),
                "NetMoneyFlow": round(net_flow, 2)
            })
        except Exception as e:
            print(f"跳过 {sym}，原因：{e}")
            continue

    df = pd.DataFrame(rows)
    print(f"抓取数据行数: {len(df)}")
    print("前5条数据示例:")
    print(df.head())

    # ========= 4. Top 5 =========
    top500 = df.sort_values("Turnover", ascending=False).head(5)
    today_symbols = set(top500["Symbol"])
    print(f"Top5 记录数: {len(top500)}")

    # ========= 5. 更新 streak =========
    new_streak = {}
    for sym in today_symbols:
        if sym in streak_dict:
            new_streak[sym] = streak_dict[sym] + 1
        else:
            new_streak[sym] = 1

    pd.DataFrame([{"Symbol": k, "Streak": v} for k, v in new_streak.items()]).to_csv(STREAK_FILE, index=False)

    # ========= 6. 合并 streak =========
    top500["Top500_Streak"] = top500["Symbol"].map(new_streak)

    # ========= 7. 导出 Excel =========
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(os.getcwd(), f"US_Top500_NetInflow_Test_{date_str}.xlsx")
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    top500.to_excel(writer, sheet_name='Top5', index=False)
    top500[top500["Top500_Streak"] >= 2].to_excel(writer, sheet_name='重点关注', index=False)
    writer.save()

    print("完成：", filename)

except Exception as e:
    print("全局捕获错误：", e)
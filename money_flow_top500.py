import yfinance as yf
import pandas as pd
from datetime import datetime
import os

try:
    # ========= 1. 读取历史 streak 数据 =========
    STREAK_FILE = "top500_streak.csv"

    if os.path.exists(STREAK_FILE):
        streak_df = pd.read_csv(STREAK_FILE)
        streak_dict = dict(zip(streak_df["Symbol"], streak_df["Streak"]))
    else:
        streak_dict = {}

    # ========= 2. 获取美股代码 =========
    nasdaq = pd.read_csv(
        "https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
        sep="|"
    )
    nyse = pd.read_csv(
        "https://ftp.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
        sep="|"
    )

    symbols = list(set(
        nasdaq["Symbol"].dropna().tolist() +
        nyse["ACT Symbol"].dropna().tolist()
    ))

    # ========= 3. 拉行情 =========
    data = yf.download(
        symbols,
        period="3d",
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False
    )

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

    # ========= 4. Top 500 =========
    top500 = df.sort_values("Turnover", ascending=False).head(500)

    today_symbols = set(top500["Symbol"])

    # ========= 5. 更新 streak =========
    new_streak = {}
    for sym in today_symbols:
        if sym in streak_dict:
            new_streak[sym] = streak_dict[sym] + 1
        else:
            new_streak[sym] = 1

    streak_out = pd.DataFrame(
        [{"Symbol": k, "Streak": v} for k, v in new_streak.items()]
    )
    streak_out.to_csv(STREAK_FILE, index=False)

    # ========= 6. 合并 streak 到结果 =========
    top500["Top500_Streak"] = top500["Symbol"].map(new_streak)

    # 只保留净流入
    top500 = top500[top500["NetMoneyFlow"] > 0]

    top500 = top500.sort_values("NetMoneyFlow", ascending=False)

    # ========= 7. 导出 Excel =========
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"US_Top500_NetInflow_{date_str}.xlsx"
    top500.to_excel(filename, index=False)

    print("完成：", filename)

except Exception as e:
    print("全局捕获错误：", e)
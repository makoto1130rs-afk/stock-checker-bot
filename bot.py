import os
import requests
import pandas as pd
import yfinance as yf

# 監視・スクリーニング対象の銘柄リスト（東証銘柄コード + .T）
TARGET_STOCKS = [
    "7011.T", # 三菱重工業
    "4587.T", # ペプチドリーム
    "4100.T", # ステラケミファ
    "7701.T", # 島津製作所
    "8306.T", # 三菱UFJ FG
    "7013.T", # IHI
]

# GitHubのSecretからWebhook URLを取得
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def check_stocks():
    matched_stocks = []

    for code in TARGET_STOCKS:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info

            name = info.get("shortName", code)
            per = info.get("trailingPE")
            pbr = info.get("priceToBook")
            roe = info.get("returnOnEquity")
            if roe:
                roe = roe * 100

            # スクリーニング条件（PER < 15, PBR < 1.0, ROE >= 10.0）
            if per and pbr and roe:
                if per < 15.0 and pbr < 1.0 and roe >= 10.0:
                    matched_stocks.append({
                        "code": code,
                        "name": name,
                        "per": round(per, 2),
                        "pbr": round(pbr, 2),
                        "roe": round(roe, 2)
                    })
        except Exception as e:
            print(f"Error fetching {code}: {e}")

    return matched_stocks

def send_notification(stocks):
    # 【条件に一致する銘柄が0件の場合の通知処理】
    if not stocks:
        message = "【🤖 株価・財務スクリーニング BOT】\n本日のスクリーニング結果：条件を満たす銘柄はありませんでした。"
        payload = {"content": message}
        requests.post(WEBHOOK_URL, json=payload)
        print("該当なしの通知を送信しました。")
        return

    # 【条件に一致する銘柄がある場合の通知処理】
    message = "【🤖 株価・財務スクリーニング BOT】\n条件を満たす注目銘柄が見つかりました！\n\n"
    for s in stocks:
        message += f"■ {s['name']} ({s['code']})\n"
        message += f"  ・PER: {s['per']}倍 / PBR: {s['pbr']}倍 / ROE: {s['roe']}%\n\n"

    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)
    print("条件一致の通知を送信しました。")

if __name__ == "__main__":
    results = check_stocks()
    send_notification(results)

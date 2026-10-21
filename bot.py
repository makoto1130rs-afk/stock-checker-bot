import os
import discord
from discord import app_commands
import yfinance as yf

# 監視対象銘柄リスト
TARGET_STOCKS = [
    "7011.T", # 三菱重工業
    "4587.T", # ペプチドリーム
    "4100.T", # ステラケミファ
    "7701.T", # 島津製作所
    "8306.T", # 三菱UFJ FG
    "7013.T", # IHI
]

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class StockBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # スラッシュコマンドをDiscordサーバーに同期
        await self.tree.sync()

client = StockBot()

@client.tree.command(name="screen", description="条件を指定して株価スクリーニングを実行します")
@app_commands.describe(
    per="PERの上限（例: 20.0）",
    pbr="PBRの上限（例: 1.5）",
    roe="ROEの下限%（例: 8.0）"
)
async def screen(
    interaction: discord.Interaction, 
    per: float = 15.0, 
    pbr: float = 1.0, 
    roe: float = 10.0
):
    # 処理に数秒かかるため、応答を保留状態にする
    await interaction.response.defer()

    matched_stocks = []

    for code in TARGET_STOCKS:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info

            name = info.get("shortName", code)
            curr_per = info.get("trailingPE")
            curr_pbr = info.get("priceToBook")
            curr_roe = info.get("returnOnEquity")
            if curr_roe:
                curr_roe = curr_roe * 100

            if curr_per and curr_pbr and curr_roe:
                if curr_per < per and curr_pbr < pbr and curr_roe >= roe:
                    matched_stocks.append({
                        "code": code,
                        "name": name,
                        "per": round(curr_per, 2),
                        "pbr": round(curr_pbr, 2),
                        "roe": round(curr_roe, 2)
                    })
        except Exception as e:
            print(f"Error fetching {code}: {e}")

    # 結果メッセージ作成
    header = f"【🤖 株価スクリーニング結果】\n設定条件: PER < {per}倍 / PBR < {pbr}倍 / ROE ≥ {roe}%\n"
    
    if not matched_stocks:
        await interaction.followup.send(f"{header}\n条件に一致する銘柄はありませんでした。")
        return

    message = header + "\n"
    for s in matched_stocks:
        message += f"■ {s['name']} ({s['code']})\n"
        message += f"  ・PER: {s['per']}倍 / PBR: {s['pbr']}倍 / ROE: {s['roe']}%\n\n"

    await interaction.followup.send(message)

if __name__ == "__main__":
    client.run(TOKEN)

import asyncio
from data_collector import fetch_historical_data_for_training
from analysemotor import analyze_market_conditions
from telegram_handler import send_telegram_message

async def test_single_coin():
    coin = "BTC"
    print(f"🔍 Tester signal for {coin}...")

    df = await fetch_historical_data_for_training(coin)
    if df is None or df.empty:
        print("🚫 Ingen historiske data hentet.")
        return

    analysis = analyze_market_conditions(df)
    if analysis.get("confidence") is None:
        print("🚫 Analyse feilet.")
        return

    entry_price = df["close"].iloc[-1]
    message = (
        f"✅ *TESTSIGNAL OK*\n"
        f"Coin: {coin}\n"
        f"Entry: ${entry_price:,.2f}\n"
        f"Confidence: {analysis['confidence']}\n"
        f"Bias: {analysis.get('bias', 'N/A')}\n"
        f"Volume: {analysis.get('volume', 0):,.0f}\n"
    )
    await send_telegram_message(message)
    print("📬 Testmelding sendt til Telegram.")

if __name__ == "__main__":
    asyncio.run(test_single_coin())

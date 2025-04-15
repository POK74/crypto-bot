# Analysemotor for Telegram Krypto-bot

Denne modulen analyserer trender, sentiment, og hendelser for 5 kryptovalutaer (BTC, ETH, BNB, SOL, ADA) én gang annenhver dag og sender varsler til Telegram om potensielle bullish bevegelser.

## Bruk

I `main.py`:

```python
import asyncio
from data_collector import get_top_100_coins
import analysemotor

async def main_loop():
    while True:
        # Kjør annenhver dag (f.eks. mandag, onsdag, fredag)
        top_100 = await get_top_100_coins()
        await analysemotor.run_analysis(top_100)
        await asyncio.sleep(48 * 60 * 60)  # 48 timer

if __name__ == "__main__":
    asyncio.run(main_loop())

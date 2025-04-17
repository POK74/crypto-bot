import asyncio
import logging
from analyse_motor import analyser_alle_coins
from telegram_handler import notify_signal
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    start_tid = datetime.now()
    logger.info(f"\n🟢 Starter analyseklokke: {start_tid.strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        signal_summary = await analyser_alle_coins()

        # Kun send signal hvis det er et faktisk kjøpssignal
        await notify_signal(signal_summary)

    except Exception as e:
        logger.exception(f"❌ Uventet feil i hovedprosessen: {e}")

    slutt_tid = datetime.now()
    tid_brukt = (slutt_tid - start_tid).total_seconds()
    logger.info(f"🕒 Analyse fullført på {tid_brukt:.2f} sekunder.")

if __name__ == "__main__":
    asyncio.run(main())

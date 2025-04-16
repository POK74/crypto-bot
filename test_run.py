import asyncio
from dotenv import load_dotenv
from analyse_motor import run_signal_scan

# Laster inn miljøvariabler fra .env-filen
load_dotenv()

async def main():
    await run_signal_scan()

if __name__ == "__main__":
    asyncio.run(main())

# formatter.py

from typing import Dict

def formater_telegram_melding(ticker: str, analyse: Dict, strategi: Dict) -> str:
    melding = f"""
🔎 Analysis for {ticker}

• 📈 Trend: {analyse['trend']}
• ⚡️ Momentum: {analyse['momentum']}
• 📊 Volume: {analyse['volume_comment']}
• 🛡️ Risk/Reward: Moderate Volatility

✅ Short-term Outlook: {analyse['short_score']}%
✅ Mid-term Outlook: {analyse['mid_score']}%

📌 Suggested Strategy:
• Entry: {strategi['entry']}
• Stop Loss: {strategi['stop_loss']}
• Target 1: {strategi['target1']}
"""

    if strategi['target2']:
        melding += f"• Target 2: {strategi['target2']}\n"

    melding += f"\n📝 Note:\n{strategi['note']}\n"

    return melding.strip()

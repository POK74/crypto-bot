import logging
from datetime import datetime
from statistics import mean

logger = logging.getLogger(__name__)

def analyze_signals_realtime(price_info: dict, symbol: str):
    """
    Ekstrem enkel analyse: Ser på endringer over tid (fra cache).
    Score beregnes basert på prosentvis vekst siste minutter.
    """
    history = price_info.get("cached", [])
    current_price = price_info.get("price")
    now = datetime.utcnow()

    if not history or len(history) < 3:
        logger.warning(f"Not enough price history for {symbol}")
        return 0, "📉 For lite data for sanntidsanalyse"

    try:
        # Tar de siste 3 prisene og regner ut snitt
        values = [entry["price"] for entry in history[-3:]]
        avg_price = mean(values)
        change_pct = ((current_price - avg_price) / avg_price) * 100

        score = min(max(int(change_pct * 5), 0), 100)

        message = (
            f"💰 Nå: ${current_price:.4f}\n"
            f"📊 Snitt (siste 3): ${avg_price:.4f}\n"
            f"📈 Endring: {change_pct:.2f}%"
        )
        return score, message

    except Exception as e:
        logger.error(f"❌ Error i analyze_signals_realtime({symbol}): {e}")
        return 0, "⚠️ Analysefeil"

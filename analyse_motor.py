
import ta
import yfinance as yf

def hent_indikatorer(ticker):
    data = yf.download(ticker, interval="15m", period="2d")
    if data.empty:
        return None

    df = data.copy()
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"].squeeze()).rsi()
    df["EMA9"] = ta.trend.EMAIndicator(df["Close"], window=9).ema_indicator()
    df["MACD"] = ta.trend.MACD(df["Close"]).macd_diff()
    df["ATR"] = ta.volatility.AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"]).average_true_range()

    siste = df.iloc[-1]
    return {
        "RSI": round(siste["RSI"], 2),
        "EMA9": round(siste["EMA9"], 6),
        "MACD": round(siste["MACD"], 6),
        "ATR": round(siste["ATR"], 6)
    }

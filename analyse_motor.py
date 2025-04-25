
import yfinance as yf
import ta
import pandas as pd

def hent_indikatorer(ticker):
    try:
        df15 = yf.download(ticker, interval="15m", period="2d")
        df1h = yf.download(ticker, interval="60m", period="7d")

        if df15.empty or df1h.empty:
            return None

        # 15m indikatorer
        df15["EMA9"] = ta.trend.EMAIndicator(df15["Close"], window=9).ema_indicator()
        df15["EMA21"] = ta.trend.EMAIndicator(df15["Close"], window=21).ema_indicator()
        df15["EMA50"] = ta.trend.EMAIndicator(df15["Close"], window=50).ema_indicator()
        df15["EMA200"] = ta.trend.EMAIndicator(df15["Close"], window=200).ema_indicator()
        df15["MACD"] = ta.trend.MACD(df15["Close"]).macd_diff()
        df15["ATR"] = ta.volatility.AverageTrueRange(df15["High"], df15["Low"], df15["Close"]).average_true_range()
        df15["STOCHRSI"] = ta.momentum.StochRSIIndicator(df15["Close"]).stochrsi()
        df15["ADX"] = ta.trend.ADXIndicator(df15["High"], df15["Low"], df15["Close"]).adx()
        df15["RSI"] = ta.momentum.RSIIndicator(df15["Close"]).rsi()
        bb15 = ta.volatility.BollingerBands(df15["Close"])
        df15["BB_upper"] = bb15.bollinger_hband()
        df15["BB_lower"] = bb15.bollinger_lband()
        df15["Volume_SMA"] = df15["Volume"].rolling(window=20).mean()

        # 1H indikatorer
        df1h["EMA9"] = ta.trend.EMAIndicator(df1h["Close"], window=9).ema_indicator()
        df1h["EMA21"] = ta.trend.EMAIndicator(df1h["Close"], window=21).ema_indicator()
        df1h["EMA50"] = ta.trend.EMAIndicator(df1h["Close"], window=50).ema_indicator()
        df1h["EMA200"] = ta.trend.EMAIndicator(df1h["Close"], window=200).ema_indicator()
        df1h["MACD"] = ta.trend.MACD(df1h["Close"]).macd_diff()
        df1h["ATR"] = ta.volatility.AverageTrueRange(df1h["High"], df1h["Low"], df1h["Close"]).average_true_range()
        df1h["STOCHRSI"] = ta.momentum.StochRSIIndicator(df1h["Close"]).stochrsi()
        df1h["ADX"] = ta.trend.ADXIndicator(df1h["High"], df1h["Low"], df1h["Close"]).adx()
        df1h["RSI"] = ta.momentum.RSIIndicator(df1h["Close"]).rsi()
        bb1h = ta.volatility.BollingerBands(df1h["Close"])
        df1h["BB_upper"] = bb1h.bollinger_hband()
        df1h["BB_lower"] = bb1h.bollinger_lband()
        df1h["Volume_SMA"] = df1h["Volume"].rolling(window=20).mean()

        latest_15m = df15.iloc[-1]
        latest_1h = df1h.iloc[-1]

        return {
            "indikatorer_15m": {
                "RSI": round(latest_15m["RSI"], 2),
                "STOCHRSI": round(latest_15m["STOCHRSI"], 2),
                "EMA9": round(latest_15m["EMA9"], 6),
                "EMA21": round(latest_15m["EMA21"], 6),
                "EMA50": round(latest_15m["EMA50"], 6),
                "EMA200": round(latest_15m["EMA200"], 6),
                "MACD": round(latest_15m["MACD"], 6),
                "ATR": round(latest_15m["ATR"], 6),
                "ADX": round(latest_15m["ADX"], 2),
                "BB_upper": round(latest_15m["BB_upper"], 6),
                "BB_lower": round(latest_15m["BB_lower"], 6),
                "Volume": round(latest_15m["Volume"], 0),
                "Volume_SMA": round(latest_15m["Volume_SMA"], 0)
            },
            "indikatorer_1h": {
                "RSI": round(latest_1h["RSI"], 2),
                "STOCHRSI": round(latest_1h["STOCHRSI"], 2),
                "EMA9": round(latest_1h["EMA9"], 6),
                "EMA21": round(latest_1h["EMA21"], 6),
                "EMA50": round(latest_1h["EMA50"], 6),
                "EMA200": round(latest_1h["EMA200"], 6),
                "MACD": round(latest_1h["MACD"], 6),
                "ATR": round(latest_1h["ATR"], 6),
                "ADX": round(latest_1h["ADX"], 2),
                "BB_upper": round(latest_1h["BB_upper"], 6),
                "BB_lower": round(latest_1h["BB_lower"], 6),
                "Volume": round(latest_1h["Volume"], 0),
                "Volume_SMA": round(latest_1h["Volume_SMA"], 0)
            }
        }

    except Exception as e:
        print(f"[Feil i indikatorberegning] {e}")
        return None

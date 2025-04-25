
import yfinance as yf
import ta
import pandas as pd

def hent_indikatorer(ticker):
    try:
        df15 = yf.download(ticker, interval="15m", period="2d")
        df1h = yf.download(ticker, interval="60m", period="7d")

        if df15.empty or df1h.empty:
            return None

        close15 = df15["Close"].squeeze()
        high15 = df15["High"].squeeze()
        low15 = df15["Low"].squeeze()
        volume15 = df15["Volume"].squeeze()

        df15["EMA9"] = ta.trend.EMAIndicator(close15, window=9).ema_indicator()
        df15["EMA21"] = ta.trend.EMAIndicator(close15, window=21).ema_indicator()
        df15["EMA50"] = ta.trend.EMAIndicator(close15, window=50).ema_indicator()
        df15["EMA200"] = ta.trend.EMAIndicator(close15, window=200).ema_indicator()
        df15["MACD"] = ta.trend.MACD(close15).macd_diff()
        df15["ATR"] = ta.volatility.AverageTrueRange(high15, low15, close15).average_true_range()
        df15["STOCHRSI"] = ta.momentum.StochRSIIndicator(close15).stochrsi()
        df15["ADX"] = ta.trend.ADXIndicator(high15, low15, close15).adx()
        df15["RSI"] = ta.momentum.RSIIndicator(close15).rsi()

        bb = ta.volatility.BollingerBands(close15)
        df15["BB_upper"] = bb.bollinger_hband()
        df15["BB_lower"] = bb.bollinger_lband()

        df15["Volume_SMA"] = volume15.rolling(window=20).mean()

        close1h = df1h["Close"].squeeze()
        high1h = df1h["High"].squeeze()
        low1h = df1h["Low"].squeeze()

        df1h["EMA50"] = ta.trend.EMAIndicator(close1h, window=50).ema_indicator()
        df1h["EMA200"] = ta.trend.EMAIndicator(close1h, window=200).ema_indicator()
        df1h["RSI"] = ta.momentum.RSIIndicator(close1h).rsi()

        siste_15m = df15.iloc[-1]
        siste_1h = df1h.iloc[-1]

        return {
            "RSI_15m": round(siste_15m["RSI"], 2),
            "STOCHRSI_15m": round(siste_15m["STOCHRSI"], 2),
            "EMA9": round(siste_15m["EMA9"], 6),
            "EMA21": round(siste_15m["EMA21"], 6),
            "EMA50": round(siste_15m["EMA50"], 6),
            "EMA200": round(siste_15m["EMA200"], 6),
            "MACD": round(siste_15m["MACD"], 6),
            "ATR": round(siste_15m["ATR"], 6),
            "ADX": round(siste_15m["ADX"], 2),
            "BB_upper": round(siste_15m["BB_upper"], 6),
            "BB_lower": round(siste_15m["BB_lower"], 6),
            "Volume": round(siste_15m["Volume"], 0),
            "Volume_SMA": round(siste_15m["Volume_SMA"], 0),
            "RSI_1h": round(siste_1h["RSI"], 2),
            "EMA50_1h": round(siste_1h["EMA50"], 6),
            "EMA200_1h": round(siste_1h["EMA200"], 6)
        }

    except Exception as e:
        print(f"[Feil i indikatorberegning] {e}")
        return None

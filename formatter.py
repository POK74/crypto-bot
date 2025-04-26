def tolk_trend(ema9, ema21, ema50, ema200):
    if ema9 > ema21 > ema50 > ema200:
        return "Strong Uptrend"
    elif ema9 < ema21 < ema50 < ema200:
        return "Strong Downtrend"
    else:
        return "Sideways / Unclear"

def vurder_momentum(rsi, macd):
    if rsi > 70 and macd > 0:
        return "Overbought but bullish"
    elif rsi < 30 and macd < 0:
        return "Oversold and bearish"
    elif macd > 0:
        return "Moderately bullish momentum"
    elif macd < 0:
        return "Moderately bearish momentum"
    else:
        return "Neutral"

def vurder_volume(volume, volume_sma):
    if volume > volume_sma:
        return "High volume (potential interest)"
    elif volume < volume_sma * 0.5:
        return "Low volume"
    else:
        return "Normal volume"

def vurder_risk_reward(atr, bb_upper, bb_lower):
    spread = bb_upper - bb_lower
    if atr > 0.6 * spread:
        return "High volatility – high risk"
    elif atr < 0.3 * spread:
        return "Low volatility – low risk"
    else:
        return "Moderate risk"

def konklusjon_short_mid(rsi, stochrsi, adx):
    short = 65
    mid = 70
    if adx > 25 and rsi > 50 and stochrsi > 0.5:
        short = 80
        mid = 85
    elif adx > 20 and rsi > 45:
        short = 70
        mid = 75
    return short, mid

def anbefalt_strategi(breakout_sjanse):
    if breakout_sjanse >= 75:
        return "Consider buying on EMA9 cross and BB-lower support"
    elif breakout_sjanse >= 60:
        return "Wait for break above EMA21 and volume confirmation"
    else:
        return "Not a buy now"

def generer_strategi_entry_sl_target(ind, df):
    def f(val): return f"{val:.4f}" if isinstance(val, float) else "-"

    ema9 = f(ind["EMA9"])
    ema21 = f(ind["EMA21"])
    bb_lower = ind["BB_lower"]
    bb_upper = f(ind["BB_upper"])
    ema200 = f(ind["EMA200"])

    swing_low = df["Low"].tail(5).min()
    sl_val = min(swing_low, bb_lower)
    sl = f(sl_val)

    return f"""\u2022 Entry: {ema9} (EMA9) or {ema21} (EMA21)
• SL: {sl} (last swing-low / BB-lower)
• Target: {bb_upper} (BB-upper) or {ema200} (EMA200)"""

def utvidet_formatter_output(ticker, ind15, ind1h, df15, trend, momentum, volume, risk, short, mid, strategi):
    def v(val): return f"{val:.2f}" if isinstance(val, float) else str(val)
    strategi_tekst = generer_strategi_entry_sl_target(ind15, df15)

    vurdering_rsi = "High" if ind15["RSI"] > 70 else "Low" if ind15["RSI"] < 30 else "Normal"
    vurdering_macd = "Bullish" if ind15["MACD"] > 0 else "Bearish"
    vurdering_adx = "Strong trend" if ind15["ADX"] > 25 else "Weak trend"

    return f"""
📊 <b>Technical analysis for {ticker}</b>

📍 <b>Factor</b>        | <b>15m Chart</b>       | <b>1h Chart</b>        | <b>Evaluation</b>
------------------------|------------------------|------------------------|------------------------
1. Price level (EMA9)      | {v(ind15["EMA9"])}     | {v(ind1h["EMA9"])}     | -
2. EMA structure         | {v(ind15["EMA9"])} / {v(ind15["EMA21"])} / {v(ind15["EMA50"])} / {v(ind15["EMA200"])} | {v(ind1h["EMA9"])} / {v(ind1h["EMA21"])} / {v(ind1h["EMA50"])} / {v(ind1h["EMA200"])} | {trend}
3. Bollinger Bands      | {v(ind15["BB_lower"])} - {v(ind15["BB_upper"])} | {v(ind1h["BB_lower"])} - {v(ind1h["BB_upper"])} | -
4. RSI (14)             | {v(ind15["RSI"])}       | {v(ind1h["RSI"])}       | {vurdering_rsi}
5. Stochastic RSI       | {v(ind15["STOCHRSI"])}  | {v(ind1h["STOCHRSI"])}  | -
6. MACD                 | {v(ind15["MACD"])}      | {v(ind1h["MACD"])}      | {vurdering_macd}
7. ADX                  | {v(ind15["ADX"])}       | {v(ind1h["ADX"])}       | {vurdering_adx}
9. ATR (Volatility)    | {v(ind15["ATR"])}       | {v(ind1h["ATR"])}       | {risk}
10. Volume / SMA         | {v(ind15["Volume"])} / {v(ind15["Volume_SMA"])} | {v(ind1h["Volume"])} / {v(ind1h["Volume_SMA"])} | {volume}

✅ <b>Summary analysis</b>
• <b>Trend direction:</b> {trend}
• <b>Momentum:</b> {momentum}
• <b>Volume:</b> {volume}
• <b>Risk/Reward:</b> {risk}

📈 <b>Conclusion</b>:
• 🔸 <b>Short-term:</b> {short}%
• 🔹 <b>Mid-term:</b> {mid}%

📌 <b>Recommended strategy</b>:
{strategi_tekst}
• Comment: {strategi}
"""

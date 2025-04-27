def tolk_trend(ema9, ema21, ema50, ema200):
    if ema9 > ema21 > ema50 > ema200:
        return "Sterk opptrend"
    elif ema9 < ema21 < ema50 < ema200:
        return "Sterk nedtrend"
    elif ema9 > ema21 and ema21 > ema50:
        return "Mild opptrend"
    elif ema9 < ema21 and ema21 < ema50:
        return "Mild nedtrend"
    else:
        return "Sideveis / Uavklart"

def vurder_momentum(rsi, macd):
    if rsi > 70 and macd > 0:
        return "Sterkt positivt momentum"
    elif rsi < 30 and macd < 0:
        return "Sterkt negativt momentum"
    elif macd > 0:
        return "Moderat positivt momentum"
    elif macd < 0:
        return "Moderat negativt momentum"
    else:
        return "Nøytralt"

def vurder_volume(volume, volume_sma):
    if volume > volume_sma:
        return "Høyt volum (potensiell interesse)"
    elif volume < volume_sma * 0.5:
        return "Lavt volum"
    else:
        return "Normalt volum"

def vurder_risk_reward(atr, bb_upper, bb_lower):
    spread = bb_upper - bb_lower
    if spread == 0:
        return "Utilstrekkelig data"
    forhold = atr / spread
    if forhold > 0.6:
        return "Høy volatilitet – høy risiko"
    elif forhold < 0.3:
        return "Lav volatilitet – lav risiko"
    else:
        return "Moderat risiko"

def anbefalt_strategi(short_term_score):
    if short_term_score >= 80:
        return "Sterkt kjøpssignal. Vurder inngang nå med bekreftelse på volum."
    elif short_term_score >= 70:
        return "Avvent bekreftelse på brudd over EMA9 og stigende volum før kjøp."
    else:
        return "Ikke anbefalt kjøp nå. Vent på bedre signal."

def konklusjon_short_mid(rsi, stochrsi, adx):
    base = 60
    bonus = 0
    if adx > 25:
        bonus += 10
    if rsi > 55:
        bonus += 10
    if stochrsi > 0.6:
        bonus += 5
    short = base + bonus
    mid = short + 5
    short = min(short, 90)
    mid = min(mid, 95)
    return short, mid

def generer_strategi_entry_sl_target(ind, df):
    def f(val):
        return f"{val:.4f}" if isinstance(val, float) else "-"

    ema9 = f(ind["EMA9"])
    ema21 = f(ind["EMA21"])
    bb_lower = ind["BB_lower"]
    bb_upper = f(ind["BB_upper"])
    ema200 = f(ind["EMA200"])

    swing_low = df["Low"].tail(5).min()
    sl_val = min(swing_low, bb_lower)
    sl = f(sl_val)

    target_val = ind["BB_upper"]
    if not target_val or target_val == 0:
        target_val = ind["EMA200"]

    target = f(target_val)

    return f"""• Entry (kjøp): {ema9} (EMA9) eller {ema21} (EMA21)
• Stop Loss: {sl} (laveste sving eller BB-lower)
• Target: {target} (BB-upper eller EMA200)"""

def utvidet_formatter_output(ticker, ind15, ind1h, df15, trend, momentum, volume, risk, short, mid, strategi):
    def v(val):
        return f"{val:.2f}" if isinstance(val, float) else str(val)
    strategi_tekst = generer_strategi_entry_sl_target(ind15, df15)

    vurdering_rsi = "Høy" if ind15["RSI"] > 70 else "Lav" if ind15["RSI"] < 30 else "Normal"
    vurdering_macd = "Bullish" if ind15["MACD"] > 0 else "Bearish"
    vurdering_adx = "Sterk trend" if ind15["ADX"] > 25 else "Svak trend"

    return f"""
📊 <b>Teknisk analyse for {ticker}</b>

📍 <b>Faktor</b>        | <b>15m Chart</b>       | <b>1h Chart</b>        | <b>Vurdering</b>
------------------------|------------------------|------------------------|------------------------
1. Prisnivå (EMA9)      | {v(ind15["EMA9"])}     | {v(ind1h["EMA9"])}     | -
2. EMA-struktur         | {v(ind15["EMA9"])} / {v(ind15["EMA21"])} / {v(ind15["EMA50"])} / {v(ind15["EMA200"])} | {v(ind1h["EMA9"])} / {v(ind1h["EMA21"])} / {v(ind1h["EMA50"])} / {v(ind1h["EMA200"])} | {trend}
3. Bollinger Bands      | {v(ind15["BB_lower"])} - {v(ind15["BB_upper"])} | {v(ind1h["BB_lower"])} - {v(ind1h["BB_upper"])} | -
4. RSI (14)             | {v(ind15["RSI"])}       | {v(ind1h["RSI"])}       | {vurdering_rsi}
5. Stochastic RSI       | {v(ind15["STOCHRSI"])}  | {v(ind1h["STOCHRSI"])}  | -
6. MACD                 | {v(ind15["MACD"])}      | {v(ind1h["MACD"])}      | {vurdering_macd}
7. ADX                  | {v(ind15["ADX"])}       | {v(ind1h["ADX"])}       | {vurdering_adx}
9. ATR (Volatilitet)    | {v(ind15["ATR"])}       | {v(ind1h["ATR"])}       | {risk}
10. Volum / SMA         | {v(ind15["Volume"])} / {v(ind15["Volume_SMA"])} | {v(ind1h["Volume"])} / {v(ind1h["Volume_SMA"])} | {volume}

✅ <b>Oppsummert analyse</b>
• <b>Trendretning:</b> {trend}
• <b>Momentum:</b> {momentum}
• <b>Volum:</b> {volume}
• <b>Risk/Reward:</b> {risk}

📈 <b>Konklusjon</b>:
• 🔵 <b>Short-term:</b> {short}%
• 🟢 <b>Mid-term:</b> {mid}%

📌 <b>Anbefalt strategi</b>:
{strategi_tekst}
• Kommentar: {strategi}
"""

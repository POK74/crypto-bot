
def tolk_trend(ema9, ema21, ema50, ema200):
    if ema9 > ema21 > ema50 > ema200:
        return "Sterk opptrend"
    elif ema9 < ema21 < ema50 < ema200:
        return "Sterk nedtrend"
    else:
        return "Sideveis / Uavklart"

def vurder_momentum(rsi, macd):
    if rsi > 70 and macd > 0:
        return "Overkjøpt men bullish"
    elif rsi < 30 and macd < 0:
        return "Oversolgt og bearish"
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
    if atr > 0.6 * spread:
        return "Høy volatilitet – høy risiko"
    elif atr < 0.3 * spread:
        return "Lav volatilitet – lav risiko"
    else:
        return "Moderat risiko"

def anbefalt_strategi(breakout_sjanse):
    if breakout_sjanse >= 75:
        return "Vurder kjøp ved EMA9-kryss og støtte på BB-lower"
    elif breakout_sjanse >= 60:
        return "Avvent brudd over EMA21 og bekreftelse på volum"
    else:
        return "Ikke kjøp nå"

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

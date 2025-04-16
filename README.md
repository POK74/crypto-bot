# 📘 README.md – MenBreakthrough AI-Trader (v2.0)

Dette er den komplette dokumentasjonen for den nyeste versjonen av MenBreakthrough AI-Trader – en kraftfull, asynkron tradingbot bygget for å finne sterke kjøpssignaler basert på AI-drevet analyse, sentiment, volum og whale-aktivitet. Fullt integrert med Telegram og klar for Render.

---

## 🚀 Funksjoner i v2.0

- **AI-basert signalmotor**: Beregner score ut fra 24t-, 6t-, og 1t-trender + volatilitet
- **Boosters**:
  - 🔹 Whale-aktivitet (on-chain sporing)
  - 🔹 Volumanalyse (CoinGecko/Binance)
  - 🔹 Sentiment (Reddit, X/Twitter, Google)
- **Telegram-integrasjon**: Sender signaler som Markdown-meldinger med score og vurdering
- **Render-støtte**: Klar for cron-jobb og asynkron kjøring i bakgrunnen
- **Skalerbar filstruktur**: Alle moduler (analyse, scraping, tracking, sending) er separert
- **Miljøvariabel-styrt**: Ingen nøkler hardkodet, lett å tilpasse
- **Logg og feilhåndtering**: Robust logging for drift og utvikling

---

## 📁 Prosjektstruktur

```
crypto-bot/
├── main.py                  # Hovedmotor for analyse og Telegram-varsling
├── test_run.py             # Manuell test av signalmotor
├── analyse_motor.py        # Beregner basisscore basert på pris og volatilitet
├── signal_scoring.py       # Kombinerer boosters + basisscore
├── data_collector.py       # Henter top coins + historiske priser
├── volume_analyzer.py      # Henter og booster score ut fra faktisk volum
├── sentiment_scraper.py    # Scraper Reddit/X/Google og beregner sentiment
├── whale_tracker.py        # Sjekker whale-aktivitet og booster score
├── telegram_handler.py     # Sender signaler til Telegram med logging
├── requirements.txt        # Nødvendige Python-avhengigheter
├── .env.template           # Mal for miljøvariabler
├── README.md               # Dokumentasjonen (denne filen)
```

---

## ⚙️ Miljøvariabler (.env)

Opprett en `.env`-fil med følgende:

```
TELEGRAM_BOT_TOKEN=din_token
TELEGRAM_CHAT_ID=din_chat_id
```

Tillegg ved bruk av boosters:
```
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=...
```

---

## 🧪 Lokal testing

```bash
pip install -r requirements.txt
python test_run.py
```

Signalene sendes til Telegram om score > 70.

---

## 📈 Hvordan fungerer analyse- og boostermotoren?

1. Henter topp 20 coins via CoinGecko
2. For hvert coin:
   - Henter 48 timer med prisdata (1t-intervall)
   - Beregner basisscore: 24t, 6t, 1t + volatilitet
   - Kombinerer med:
     - Whale-boost
     - Volum-boost
     - Sentiment-score
3. Sluttresultat = samlet AI-score 0–100
4. Meldinger over score 70 sendes til Telegram

Eksempel på melding:

```
🚀 *KJØPSSIGNAL* - SOL/USDT
⭐ Score: *85*
24h: +6.7%, 6h: +2.1%, 1h: +0.7%
📈 Normal volatility
🔹 Boost: Whale + Volum + Sentiment
```

---

## 🌐 Render-deploy (cron-job)

- Legg prosjektet på GitHub og koble til Render
- Deploy som **Background Worker**
- Sett opp `.env`-variabler i Render-dashboard
- Cron: `python main.py` hver 60. minutt (eller annet)

---

## ✅ Fremtidige forbedringer (planlagt)

- Integrere CoinMarketCal-eventer
- Sanntids winrate-tracking
- Web-dashboard / Notion-dashboard
- Telegram UI (knapper, interaktiv spørring)
- Backtest-modul for historiske signaler

---

## 🧠 Om MenBreakthrough AI-Trader

Bygget som en del av det langsiktige prosjektet MenBreakthrough for å gi nybegynnere og viderekomne et AI-verktøy som gir tidlige og smarte kjøpsbeslutninger i kryptomarkedet.

> "Din neste breakthrough starter med et signal."

**Lisens:** MIT


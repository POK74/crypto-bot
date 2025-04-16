# 📘 README.md - MenBreakthrough Crypto Trading Bot

Denne README-filen dokumenterer hele boten din fra start til slutt, med alle funksjoner vi har implementert og konfigurert.

---

## 🚀 Funksjoner

- **AI-drevet kjøpssignal:** Analysere topp coins fra CoinGecko og sende signaler med score
- **Volatilitetsanalyse:** Justering av score basert på volatilitet (volatility boost)
- **Telegram-integrasjon:** Sender kjøpssignaler rett til Telegram
- **Automatisert scanning:** Klar for cron-jobb i Render (hver time eller etter behov)
- **Asynkron og rask:** Bruker `aiohttp` og `asyncio` for effektiv datahåndtering
- **Enkel oppstart:** Krever kun Python og en `.env`-fil

---

## 📂 Prosjektstruktur

```
crypto-bot/
├── main.py                 # Starter signalmotor og Telegram-varsling
├── test_run.py            # Manuell test av signalmotoren
├── data_collector.py      # Henter topp coins og historiske data fra CoinGecko
├── analyse_motor.py       # Analyserer prisendringer og beregner signal-score
├── telegram_handler.py    # Sender meldinger til Telegram
├── requirements.txt       # Python-avhengigheter
├── README.md              # Dokumentasjonen (denne filen)
├── .env.template          # Eksempel på miljøvariabler
```

---

## ⚙️ Miljøvariabler (.env)

Opprett en `.env`-fil med følgende innhold:

```
TELEGRAM_BOT_TOKEN=din_token
TELEGRAM_CHAT_ID=din_chat_id
```

---

## 🧪 Test lokalt

Installer krav først:
```bash
pip install -r requirements.txt
```

Deretter kjør:
```bash
python test_run.py
```
Du vil få Telegram-varsel med score, trend og vurdering.

---

## 📈 Hvordan fungerer signalmotoren?

- Henter topp 20 coins via CoinGecko
- For hvert coin:
  - Henter 48 timer med prisdata (1t intervall)
  - Beregner 24t, 6t og 1t prisendringer
  - Vurderer volatilitet (std-avvik på 12 siste datapunkter)
  - Returnerer score fra 0–100
- Kun signaler med score >= 70 sendes til Telegram
- Eksempel på melding:

```
🔥 BUY SIGNAL - SOL/USDT
Score: 85
24h: +6.7%, 6h: +2.1%, 1h: +0.7%
📈 Normal volatility
```

---

## 📦 Avhengigheter

Se `requirements.txt`:

```
aiohttp==3.9.3
ccxt==4.1.94
python-dotenv==1.0.1
numpy==1.26.4
```

Installer via:
```bash
pip install -r requirements.txt
```

---

## 🌐 Deploy til Render

Deploy som **Background Worker** med denne kommandoen:
```bash
python main.py
```

Sett opp `.env`-variabler inne i Render dashboardet (samme som lokal `.env`).

---

## 🔁 Cronjob på Render (anbefalt)

For å scanne automatisk hver time:
- Sett opp Render cron-jobb til å kjøre `python main.py`
- Frekvens: hver 60. minutt (eller tilpasses behov)

---

## 📌 Fremtidige forbedringer (planlagt)

- CoinMarketCal-eventfilter og signalforsterker ✅
- Google Trends-analyse ✅
- Nyhets-sentiment (f.eks. SerpAPI eller GNews)
- Live winrate-tracking og logging
- GUI-dashboard (Notion / HTML / Telegram-knapper)

---

## 🧠 Bakgrunn

Dette er en del av **MenBreakthroughs AI-drevne system** for å gjøre trading enklere, raskere og mer lønnsomt – selv for nybegynnere.

> Klar for å oppleve din neste Breakthrough. 🚀

---

**Lisens:** MIT




# Halal Stock Signal Bot

A Telegram bot that monitors global markets for halal (Shariah-compliant) equities, surfaces high-momentum opportunities, and reports market open/close status across key exchanges.

## Features

- ✅ Real-time commands for halal signals, market hours, and ticker intel.
- ✅ Global market schedule awareness with next open/close timestamps.
- ✅ Momentum-based signal engine using price action, volume, and RSI.
- ✅ Built-in halal universe sourced from screening data with the ability to extend.

## Commands

- `/start` – Welcome message and quick usage tips.
- `/signals` – Latest high momentum halal setups (auto-refreshed).
- `/open` – Market open/close status for major global exchanges.
- `/halal` – List of halal-screened tickers tracked by the bot.
- `/info TICKER` – Detailed view for a specific halal ticker.

## Requirements

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your Telegram bot token (and optionally override defaults):

```bash
export TELEGRAM_TOKEN="123456789:ABCDEF"
# Optional overrides
export SIGNAL_REFRESH_MINUTES=15
export DEFAULT_TICKERS="AAPL,MSFT,NVDA"
```

## Running the Bot

```bash
python bot.py
```

The bot runs continuously and periodically refreshes the signal list in the background. By default, the halal ticker universe is loaded from `halal_stock_bot/data/halal_tickers.csv`. You can supply your own dataset by setting `HALAL_TICKERS_FILE` to a CSV file that follows the same schema (`ticker,exchange,name,source`).

## Extending

- Plug a live halal screening API by replacing the CSV loader in `halal_stock_bot/screener.py`.
- Adjust the signal scoring logic in `halal_stock_bot/signals.py` to include additional technical or fundamental metrics.
- Add scheduled notifications using `Application.job_queue` from `python-telegram-bot` to push signals automatically.

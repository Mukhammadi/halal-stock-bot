"""Telegram command handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from .market_status import MarketStatusService
from .screener import HalalScreener
from .signals import Signal, SignalEngine


@dataclass(slots=True)
class BotState:
    screener: HalalScreener
    signal_engine: SignalEngine
    market_service: MarketStatusService
    watchlist: List[str]
    latest_signals: List[Signal] = field(default_factory=list)
    last_signal_refresh: datetime | None = None


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Assalamu alaikum! I monitor global halal stock opportunities 24/7.\n"
        "Use /signals for fresh ideas, /open for market hours, or /halal to browse the universe."
    )


async def halal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.application.bot_data["state"]
    lines = [f"{stock.ticker} – {stock.name} ({stock.exchange})" for stock in state.screener.stocks]
    await update.message.reply_text("📜 Halal universe:\n" + "\n".join(lines[:40]))


async def open_markets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.application.bot_data["state"]
    snapshot = state.market_service.snapshot()
    lines: List[str] = []
    for name, status in snapshot.items():
        status_emoji = "🟢" if status.is_open else "🔴"
        lines.append(
            f"{status_emoji} {name}: {'Open' if status.is_open else 'Closed'}\n"
            f"Next open: {status.next_open.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"Next close: {status.next_close.strftime('%Y-%m-%d %H:%M %Z')}"
        )
    await update.message.reply_text("\n\n".join(lines))


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.application.bot_data["state"]
    await _maybe_refresh_signals(context.application, state)
    if not state.latest_signals:
        await update.message.reply_text("No strong halal momentum setups right now. Check back soon!")
        return
    messages = [signal.summary() for signal in state.latest_signals]
    await update.message.reply_text(
        "🌙 Weekly halal momentum radar\n\n" + "\n\n".join(messages), parse_mode=ParseMode.MARKDOWN
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /info TICKER")
        return
    ticker = context.args[0].upper()
    state: BotState = context.application.bot_data["state"]
    stock = state.screener.get(ticker)
    if not stock:
        await update.message.reply_text("Ticker not found in the halal universe.")
        return
    await _maybe_refresh_signals(context.application, state)
    signal = next((sig for sig in state.latest_signals if sig.ticker == ticker), None)
    if signal:
        await update.message.reply_text(signal.summary())
        return
    await update.message.reply_text(f"{stock.ticker} ({stock.exchange}) is halal-screened but not triggering signals now.")


async def refresh(_: ContextTypes.DEFAULT_TYPE) -> None:
    return


async def _maybe_refresh_signals(app: Application, state: BotState) -> None:
    now = datetime.utcnow()
    if state.last_signal_refresh and (now - state.last_signal_refresh).seconds < 60:
        return
    tickers = state.watchlist
    state.latest_signals = await state.signal_engine.generate(tickers)
    state.last_signal_refresh = now


def register(application: Application, state: BotState) -> None:
    application.bot_data["state"] = state
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("halal", halal))
    application.add_handler(CommandHandler("open", open_markets))
    application.add_handler(CommandHandler("signals", signals))
    application.add_handler(CommandHandler("info", info))

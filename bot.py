"""Entry point for the Halal Stock Signal Bot."""

from __future__ import annotations

import asyncio
import logging

from telegram.ext import ApplicationBuilder, AIORateLimiter

from halal_stock_bot.config import Settings
from halal_stock_bot.handlers import BotState, register
from halal_stock_bot.market_status import MarketStatusService
from halal_stock_bot.screener import HalalScreener
from halal_stock_bot.signals import SignalEngine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def main() -> None:
    settings = Settings.load()
    screener = HalalScreener(settings.halal_tickers_file, settings.default_tickers)
    signal_engine = SignalEngine(screener)
    market_service = MarketStatusService()
    state = BotState(
        screener=screener,
        signal_engine=signal_engine,
        market_service=market_service,
        watchlist=screener.default_watchlist() or settings.default_tickers,
    )

    application = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .rate_limiter(AIORateLimiter())
        .concurrent_updates(True)
        .build()
    )

    register(application, state)

    logging.info("Halal Stock Signal Bot started")
    async with application:
        await application.start()
        await application.updater.start_polling()
        await application.updater.wait()


if __name__ == "__main__":
    asyncio.run(main())

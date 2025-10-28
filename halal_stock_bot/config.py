"""Application configuration and constants."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterable, List


def _env_list(name: str, default: Iterable[str]) -> List[str]:
    value = os.getenv(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    """Runtime configuration for the bot."""

    telegram_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN", ""))
    halal_tickers_file: str = field(default_factory=lambda: os.getenv("HALAL_TICKERS_FILE", "halal_stock_bot/data/halal_tickers.csv"))
    default_tickers: List[str] = field(default_factory=lambda: _env_list("DEFAULT_TICKERS", ["AAPL", "MSFT", "GOOGL", "NVDA", "ADBE", "INTC"]))
    signal_refresh_interval: timedelta = field(default_factory=lambda: timedelta(minutes=int(os.getenv("SIGNAL_REFRESH_MINUTES", "15"))))

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        if not settings.telegram_token:
            raise RuntimeError(
                "TELEGRAM_TOKEN environment variable is required to start the bot."
            )
        return settings

"""Halal stock screening utilities."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class HalalStock:
    ticker: str
    exchange: str
    name: str
    source: str


class HalalScreener:
    """Loads and filters halal stocks."""

    def __init__(self, csv_file: str, default_tickers: Iterable[str]) -> None:
        self.csv_path = Path(csv_file)
        self._default_tickers = list(default_tickers)
        self._stocks: Dict[str, HalalStock] = {}
        self._load()

    def _load(self) -> None:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Halal ticker file not found: {self.csv_path}")
        with self.csv_path.open("r", encoding="utf8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                ticker = row.get("ticker")
                if not ticker:
                    continue
                self._stocks[ticker.upper()] = HalalStock(
                    ticker=ticker.upper(),
                    exchange=row.get("exchange", ""),
                    name=row.get("name", ""),
                    source=row.get("source", ""),
                )

    @property
    def stocks(self) -> List[HalalStock]:
        return list(self._stocks.values())

    def get(self, ticker: str) -> HalalStock | None:
        return self._stocks.get(ticker.upper())

    def default_watchlist(self) -> List[str]:
        return [ticker for ticker in self._default_tickers if ticker in self._stocks]

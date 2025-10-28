"""Market open/close status utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Dict, Iterable, Mapping

import pytz


@dataclass(frozen=True)
class Market:
    """Represents a stock exchange trading schedule."""

    name: str
    timezone: pytz.timezone
    open_time: time
    close_time: time
    weekend: Iterable[int] = (5, 6)  # Saturday, Sunday by default

    def status(self, now: datetime) -> "MarketStatus":
        local_now = now.astimezone(self.timezone)
        is_weekend = local_now.weekday() in self.weekend
        opens_today = self.timezone.localize(datetime.combine(local_now.date(), self.open_time))
        closes_today = self.timezone.localize(datetime.combine(local_now.date(), self.close_time))

        if is_weekend or local_now < opens_today:
            return MarketStatus(
                is_open=False,
                next_open=_next_open(local_now, self),
                next_close=opens_today if local_now < opens_today else closes_today,
            )

        if opens_today <= local_now <= closes_today:
            return MarketStatus(is_open=True, next_open=_next_open(local_now, self), next_close=closes_today)

        # after close
        next_open = _next_open(local_now, self)
        return MarketStatus(is_open=False, next_open=next_open, next_close=_next_close(local_now, self))


@dataclass(frozen=True)
class MarketStatus:
    is_open: bool
    next_open: datetime
    next_close: datetime


def _next_open(reference: datetime, market: Market) -> datetime:
    local_date = reference.date()
    days_ahead = 0
    while True:
        candidate = local_date + timedelta(days=days_ahead)
        if (market.timezone.localize(datetime.combine(candidate, market.open_time))).weekday() not in market.weekend:
            candidate_open = market.timezone.localize(datetime.combine(candidate, market.open_time))
            if candidate_open > reference:
                return candidate_open
        days_ahead += 1


def _next_close(reference: datetime, market: Market) -> datetime:
    candidate = market.timezone.localize(datetime.combine(reference.date(), market.close_time))
    if candidate > reference:
        return candidate
    # move to next trading day
    days = 1
    while True:
        future = reference + timedelta(days=days)
        if future.weekday() not in market.weekend:
            return market.timezone.localize(datetime.combine(future.date(), market.close_time))
        days += 1


class MarketStatusService:
    """Provides status information for multiple markets."""

    def __init__(self, markets: Mapping[str, Market] | None = None) -> None:
        if markets is None:
            markets = _default_markets()
        self._markets: Dict[str, Market] = dict(markets)

    def snapshot(self, now: datetime | None = None) -> Dict[str, MarketStatus]:
        if now is None:
            now = datetime.utcnow().replace(tzinfo=pytz.utc)
        return {key: market.status(now) for key, market in self._markets.items()}


def _default_markets() -> Dict[str, Market]:
    return {
        "NYSE": Market("NYSE", pytz.timezone("America/New_York"), time(9, 30), time(16, 0)),
        "NASDAQ": Market("NASDAQ", pytz.timezone("America/New_York"), time(9, 30), time(16, 0)),
        "LSE": Market("LSE", pytz.timezone("Europe/London"), time(8, 0), time(16, 30)),
        "TSX": Market("TSX", pytz.timezone("America/Toronto"), time(9, 30), time(16, 0)),
        "TSE": Market("TSE", pytz.timezone("Asia/Tokyo"), time(9, 0), time(15, 0), weekend=(5, 6)),
        "BSE": Market("BSE", pytz.timezone("Asia/Kolkata"), time(9, 15), time(15, 30), weekend=(5, 6)),
        "DFM": Market("DFM", pytz.timezone("Asia/Dubai"), time(10, 0), time(14, 0), weekend=(4, 5)),
    }

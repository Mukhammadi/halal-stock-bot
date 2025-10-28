"""Signal generation for halal stocks."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import pandas as pd
import yfinance as yf

from .screener import HalalScreener, HalalStock


@dataclass(slots=True)
class Signal:
    ticker: str
    exchange: str
    name: str
    entry_price: float
    current_price: float
    recent_high: float
    recent_low: float
    percent_change: float
    rsi: float
    volume: float
    volume_ratio: float
    reason: str
    projected_target: float
    timestamp: datetime

    def summary(self) -> str:
        return (
            f"{self.ticker} ({self.exchange})\n"
            f"Entry: ${self.entry_price:,.2f} | Last: ${self.current_price:,.2f}\n"
            f"High/Low (5d): ${self.recent_high:,.2f} / ${self.recent_low:,.2f}\n"
            f"Change: {self.percent_change:.2f}% | RSI(14): {self.rsi:.1f}\n"
            f"Volume: {self.volume:,.0f} ({self.volume_ratio:.1f}× avg)\n"
            f"Reason: {self.reason}\n"
            f"Target (7d): ${self.projected_target:,.2f}"
        )


class SignalEngine:
    """Generates trading signals for halal stocks."""

    def __init__(self, screener: HalalScreener) -> None:
        self._screener = screener

    async def generate(self, tickers: Iterable[str], max_signals: int = 5) -> List[Signal]:
        tickers = [ticker.upper() for ticker in tickers]
        if not tickers:
            return []
        loop = asyncio.get_running_loop()
        data = await asyncio.to_thread(self._download_data, tickers)
        signals: List[Signal] = []
        for ticker in tickers:
            stock_meta = self._screener.get(ticker)
            if not stock_meta:
                continue
            df = data.get(ticker)
            if df is None or df.empty:
                continue
            try:
                signal = self._build_signal(stock_meta, df)
            except Exception:
                continue
            signals.append(signal)
        signals.sort(key=lambda s: (s.percent_change * s.volume_ratio), reverse=True)
        return signals[:max_signals]

    def _download_data(self, tickers: List[str]) -> dict[str, pd.DataFrame]:
        history = yf.download(
            tickers=tickers,
            period="5d",
            interval="1h",
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False,
        )
        result: dict[str, pd.DataFrame] = {}
        if isinstance(history.columns, pd.MultiIndex):
            for ticker in tickers:
                try:
                    df = history[ticker].dropna()
                    result[ticker] = df
                except KeyError:
                    continue
        else:
            result[tickers[0]] = history.dropna()
        return result

    def _build_signal(self, stock: HalalStock, df: pd.DataFrame) -> Signal:
        df = df.tail(40).copy()
        df.index = pd.to_datetime(df.index)
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        if len(close) < 15:
            raise ValueError("insufficient data")

        percent_change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
        avg_volume = volume[:-1].mean() or 1
        volume_ratio = volume.iloc[-1] / avg_volume
        rsi = _rsi(close, period=14)
        current_rsi = float(rsi.iloc[-1])
        entry_price = float(close.iloc[-2])
        current_price = float(close.iloc[-1])
        projected_target = current_price * (1 + max(percent_change, 2) / 100 * 0.7)
        reason = _reason(percent_change, volume_ratio, current_rsi)

        return Signal(
            ticker=stock.ticker,
            exchange=stock.exchange,
            name=stock.name,
            entry_price=entry_price,
            current_price=current_price,
            recent_high=float(high.max()),
            recent_low=float(low.min()),
            percent_change=float(percent_change),
            rsi=current_rsi,
            volume=float(volume.iloc[-1]),
            volume_ratio=float(volume_ratio),
            reason=reason,
            projected_target=float(projected_target),
            timestamp=datetime.utcnow(),
        )


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(method="bfill").fillna(50)


def _reason(percent_change: float, volume_ratio: float, rsi: float) -> str:
    components: List[str] = []
    if percent_change > 3:
        components.append("strong intraday breakout")
    elif percent_change > 1.5:
        components.append("steady bullish move")
    else:
        components.append("early momentum build-up")

    if volume_ratio > 2:
        components.append("unusual volume inflow")
    elif volume_ratio > 1.2:
        components.append("volume above average")

    if rsi < 30:
        components.append("oversold reversal potential")
    elif rsi > 70:
        components.append("overbought strength")

    return ", ".join(components)

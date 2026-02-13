"""
Infrastructure adapter for Interactive Brokers TWS/Gateway.

Implements the MarketDataProvider port using the ib_async library
(successor to ib_insync). All methods are async-native.

Usage:
    adapter = TWSAdapter()
    await adapter.connect(BrokerConnectionConfig(host="127.0.0.1", port=7497))
    bars = await adapter.get_historical_bars(contract, time_range, bar_size)
    await adapter.disconnect()
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional, Dict
import asyncio
from ib_async import IB, Stock, Option, Future, Index, Forex, Contract as IBContract
import logging
from server.trading.domain.aggregates.contract import Contract
from server.trading.domain.aggregates.candle_request import FetchHistoricalBarsRequest
from server.trading.domain.entities import BrokerConnectionConfig
from server.trading.domain.ports import MarketDataProvider
from server.trading.domain.value_objects import (
    BarSize,
    Currency,
    Exchange,
    OHLCV,
    SecurityType,
    TimeRange,
    Symbol,
)
from server.trading.domain.utils.decorators import logged


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

_BAR_SIZE_MAP: dict[str, str] = {
    "1s":  "1 secs",
    "5s":  "5 secs",
    "15s": "15 secs",
    "1m":  "1 min",
    "5m":  "5 mins",
    "15m": "15 mins",
    "1h":  "1 hour",
    "1d":  "1 day",
}

_EXCHANGE_MAP: dict[Exchange, str] = {
    Exchange.NYSE:   "NYSE",
    Exchange.NASDAQ: "NASDAQ",
    Exchange.AMEX:   "AMEX",
    Exchange.CBOE:   "CBOE",
    Exchange.CFE:    "CFE",
}


def _map_bar_size(bar_size: BarSize) -> str:
    try:
        return _BAR_SIZE_MAP[bar_size.value]
    except KeyError:
        raise ValueError(f"Unsupported bar size: {bar_size.value}")


def _compute_duration_str(time_range: TimeRange) -> str:
    """
    Derive an IB-compatible ``durationStr`` from a TimeRange.

    IB accepts durations like '60 S', '30 D', '13 W', '6 M', '10 Y'.
    """
    delta: timedelta = time_range.end - time_range.start
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        raise ValueError("TimeRange must have positive duration")

    if total_seconds <= 86_400:
        return f"{total_seconds} S"

    total_days = math.ceil(total_seconds / 86_400)

    if total_days <= 365:
        return f"{total_days} D"

    total_weeks = math.ceil(total_days / 7)
    if total_weeks <= 52 * 5:
        return f"{total_weeks} W"

    total_months = math.ceil(total_days / 30)
    if total_months <= 12 * 5:
        return f"{total_months} M"

    total_years = math.ceil(total_days / 365)
    return f"{total_years} Y"


def _build_ib_contract(contract: Contract) -> IBContract:
    """
    Map a domain Contract aggregate to an ib_async contract object.

    Uses SMART routing by default for stocks so IB picks the best
    execution venue, while keeping the primary exchange from the domain.
    """
    symbol = str(contract.symbol)
    currency = contract.currency.value
    exchange = _EXCHANGE_MAP.get(contract.exchange.value, "SMART")

    match contract.security_type:
        case SecurityType.STOCK:
            return Stock(
                symbol=symbol,
                exchange="SMART",
                currency=currency,
                primaryExchange=exchange,
            )
        case SecurityType.FUTURE:
            return Future(
                symbol=symbol,
                exchange=exchange,
                currency=currency,
            )
        case SecurityType.OPTION:
            return Option(
                symbol=symbol,
                exchange=exchange,
                currency=currency,
            )
        case SecurityType.INDEX:
            return Index(
                symbol=symbol,
                exchange=exchange,
                currency=currency,
            )
        case SecurityType.CURRENCY:
            return Forex(pair=symbol)
        case _:
            raise ValueError(
                f"Unsupported security type: {contract.security_type}"
            )


def _bars_to_ohlcv(ib_bars) -> List[OHLCV]:
    return [
        OHLCV(
            date=bar.date,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume if bar.volume >= 0 else None,
        )
        for bar in ib_bars
    ]


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class TWSAdapter(MarketDataProvider):
    """
    Concrete adapter that bridges the domain MarketDataProvider port
    with Interactive Brokers via *ib_async*.
    """

    def __init__(self, ib: Optional[IB] = None) -> None:
        self._ib = ib or IB()
        self._connected = False

    @logged(logger_name="trading.infrastructure.tws", level=logging.INFO)
    async def connect(self, config: BrokerConnectionConfig) -> None:
        if self._ib.isConnected():
            # ib_async exposes a synchronous disconnect(); there is no
            # disconnectAsync method, so we call the sync version here.
            self._ib.disconnect()

        await self._ib.connectAsync(
            host=config.host,
            port=config.port,
            clientId=config.client_id,
        )
        self._connected = True

    @logged(logger_name="trading.infrastructure.tws", level=logging.INFO)
    async def disconnect(self) -> None:
        if self._ib.isConnected():
            # Synchronous disconnect; safe to call from async context.
            self._ib.disconnect()
            self._connected = False

    async def __aenter__(self) -> TWSAdapter:
        await self.connect(BrokerConnectionConfig(host="127.0.0.1", port=7497))
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.disconnect()

    def _build_request(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        bar_size: BarSize,
        exchange: Exchange | None = None,
        currency: Currency | None = None,
        security_type: SecurityType | None = None,
    ) -> FetchHistoricalBarsRequest:
        """
        Helper to construct a domain FetchHistoricalBarsRequest from the
        high-level parameters passed into the adapter.
        """
        exchange = exchange or Exchange.SMART
        currency = currency or Currency.USD
        security_type = security_type or SecurityType.STOCK

        contract = Contract(
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            security_type=security_type,
        )

        return FetchHistoricalBarsRequest(
            contract=contract,
            time_range=time_range,
            bar_size=bar_size,
        )

    @logged(logger_name="trading.infrastructure.tws", level=logging.WARNING)
    async def get_historical_bars(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        bar_size: BarSize,
        exchange: Exchange | None = Exchange.SMART,
        currency: Currency | None = Currency.USD,
        security_type: SecurityType | None = SecurityType.STOCK,
    ) -> List[OHLCV]:

        if not self._connected:
            raise ValueError("Not connected to the broker")

        fetch_historical_bars_request = self._build_request(
            symbol=symbol,
            time_range=time_range,
            bar_size=bar_size,
            exchange=exchange,
            currency=currency,
            security_type=security_type,
        )

        ib_contract = _build_ib_contract(fetch_historical_bars_request.contract)
        ib_bar_size = _map_bar_size(fetch_historical_bars_request.bar_size)

        qualified = await self._ib.qualifyContractsAsync(ib_contract)
        if not qualified:
            raise ValueError(f"IB could not qualify contract: {fetch_historical_bars_request.contract}")
        ib_contract = qualified[0]

        all_ohlcv: List[OHLCV] = []
        current_end: datetime = fetch_historical_bars_request.time_range.end
        max_iterations = 200

        try:
            for _ in range(max_iterations):
                duration_str = _compute_duration_str(
                    TimeRange(start=fetch_historical_bars_request.time_range.start, end=current_end)
                )

                bars = await self._ib.reqHistoricalDataAsync(
                    contract=ib_contract,
                    endDateTime=current_end,
                    durationStr=duration_str,
                    barSizeSetting=ib_bar_size,
                    whatToShow="TRADES",
                    useRTH=True,
                    formatDate=2,
                )

                if not bars:
                    break

                chunk = _bars_to_ohlcv(bars)
                all_ohlcv = chunk + all_ohlcv

                earliest_bar_date = bars[0].date
                if isinstance(earliest_bar_date, str):
                    earliest_bar_date = datetime.fromisoformat(earliest_bar_date)
                elif isinstance(earliest_bar_date, date) and not isinstance(earliest_bar_date, datetime):
                    earliest_bar_date = datetime(
                        earliest_bar_date.year,
                        earliest_bar_date.month,
                        earliest_bar_date.day,
                        tzinfo=timezone.utc,
                    )

                if earliest_bar_date <= fetch_historical_bars_request.time_range.start:
                    break

                current_end = earliest_bar_date
        except Exception:
            return []

        return all_ohlcv

    @logged(logger_name="trading.infrastructure.tws", level=logging.INFO)
    async def get_historical_bars_multiple(
        self,
        symbols: List[Symbol],
        time_range: TimeRange,
        bar_size: BarSize,
        exchange: Exchange | None = None,
        currency: Currency | None = None,
        security_type: SecurityType | None = None,
        max_concurrent: int = 10,
    ) -> Dict[Symbol, List[OHLCV]]:

        if not self._connected:
            raise ValueError("Not connected to the broker")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _fetch_one(symbol: Symbol) -> tuple[Symbol, List[OHLCV]]:
            async with semaphore:
                try:
                    bars = await asyncio.wait_for(
                        self.get_historical_bars(
                            symbol=symbol,
                            time_range=time_range,
                            bar_size=bar_size,
                            exchange=exchange,
                            currency=currency,
                            security_type=security_type,
                        ),
                        timeout=100.0,
                    )
                except asyncio.TimeoutError:
                    return (symbol, [])
                return (symbol, bars)

        tasks = [_fetch_one(symbol) for symbol in symbols]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        results: Dict[Symbol, List[OHLCV]] = {}
        for result in completed:
            if isinstance(result, Exception):
                continue
            symbol, bars = result
            results[symbol] = bars

        return results


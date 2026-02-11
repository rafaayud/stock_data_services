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
from datetime import datetime, timedelta
from typing import List, Optional

from ib_async import IB, Stock, Option, Future, Index, Forex, Contract as IBContract

from trading.domain.aggregates.contract import Contract
from trading.domain.entities import BrokerConnectionConfig
from trading.domain.ports import MarketDataProvider
from trading.domain.value_objects import (
    BarSize,
    Currency,
    Exchange,
    OHLCV,
    SecurityType,
    TimeRange,
)
from trading.domain.utils.decorators import logged


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
    currency = contract.currency
    exchange = _EXCHANGE_MAP.get(contract.exchange, "SMART")

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

    @logged(logger_name="trading.infrastructure.tws")
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

    @logged(logger_name="trading.infrastructure.tws")
    async def disconnect(self) -> None:
        if self._ib.isConnected():
            # Synchronous disconnect; safe to call from async context.
            self._ib.disconnect()

    async def __aenter__(self) -> TWSAdapter:
        await self.connect(BrokerConnectionConfig(host="127.0.0.1", port=7497))
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.disconnect()

    @logged(logger_name="trading.infrastructure.tws")
    async def get_historical_bars(
        self,
        contract: Contract,
        time_range: TimeRange,
        bar_size: BarSize,
    ) -> List[OHLCV]:
    
        ib_contract = _build_ib_contract(contract)
        ib_bar_size = _map_bar_size(bar_size)

        qualified = await self._ib.qualifyContractsAsync(ib_contract)
        if not qualified:
            raise ValueError(f"IB could not qualify contract: {contract}")
        ib_contract = qualified[0]

        all_ohlcv: List[OHLCV] = []
        current_end: datetime = time_range.end
        max_iterations = 200

        for _ in range(max_iterations):
            duration_str = _compute_duration_str(
                TimeRange(start=time_range.start, end=current_end)
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

            if earliest_bar_date <= time_range.start:
                break

            current_end = earliest_bar_date

        return all_ohlcv
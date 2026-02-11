"""
Trading application use cases built on top of the domain layer.

These use cases are where you will later plug in a concrete
Interactive Brokers implementation of the `MarketDataProvider`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from trading.domain.entities import BarSize, Instrument, MarketDataBar
from trading.domain.ports import MarketDataProvider
from trading.domain.value_objects import TimeRange


@dataclass
class FetchHistoricalBarsRequest:
    instrument: Instrument
    time_range: TimeRange
    bar_size: BarSize


class FetchHistoricalBarsUseCase:
    """
    Application-level use case for fetching historical bars from a broker.
    """

    def __init__(self, market_data_provider: MarketDataProvider) -> None:
        self._market_data_provider = market_data_provider

    def execute(self, request: FetchHistoricalBarsRequest) -> Iterable[MarketDataBar]:
        return self._market_data_provider.get_historical_bars(
            instrument=request.instrument,
            start=request.time_range.start,
            end=request.time_range.end,
            bar_size=request.bar_size,
        )



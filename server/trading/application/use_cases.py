"""
Trading application use cases built on top of the domain layer.

These use cases orchestrate the domain ports to perform operations
like fetching historical market data from Interactive Brokers.

Designed to replicate the data-fetching needs from:
  - "Quantitative Trading" by Ernest P. Chan
  - "Algorithmic Trading" by Ernest P. Chan
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from trading.domain.aggregates.contract import Contract
from trading.domain.aggregates.candle_request import FetchHistoricalBarsRequest
from trading.domain.ports import MarketDataProvider
from trading.domain.value_objects import BarSize, OHLCV, TimeRange, Symbol



class FetchHistoricalBarsUseCase:
    """
    Application-level use case for fetching historical bars from a broker.

    Accepts a domain Contract and delegates to the MarketDataProvider port,
    which will be fulfilled by the TWSAdapter at runtime.
    """

    def __init__(self, market_data_provider: MarketDataProvider) -> None:
        self._provider = market_data_provider

    async def execute(self, request: FetchHistoricalBarsRequest) -> List[OHLCV]:
        """
        Fetch historical OHLCV data for the given contract and time window.

        Returns a chronologically ordered list of OHLCV bars.
        """
        return await self._provider.get_historical_bars(request)

    async def execute_multiple(self, requests: List[FetchHistoricalBarsRequest]) -> Dict[Symbol, List[OHLCV]]:
        return await self._provider.fetch_historicals_multiple(requests)


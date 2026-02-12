"""
Trading application use cases built on top of the domain layer.

These use cases orchestrate the domain ports to perform operations
like fetching historical market data from Interactive Brokers.

Designed to replicate the data-fetching needs from:
  - "Quantitative Trading" by Ernest P. Chan
  - "Algorithmic Trading" by Ernest P. Chan
"""

from __future__ import annotations

from typing import List, Dict

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

    async def execute(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        bar_size: BarSize,
        **kwargs,
    ) -> List[OHLCV]:
        """
        Fetch historical OHLCV data for the given symbol and time window.

        Extra keyword arguments are passed through to the underlying
        MarketDataProvider, allowing broker-specific options (exchange,
        currency, security_type, etc.).
        """
        return await self._provider.get_historical_bars(
            symbol=symbol,
            time_range=time_range,
            bar_size=bar_size,
            **kwargs,
        )

    async def execute_multiple(
        self,
        symbols: List[Symbol],
        time_range: TimeRange,
        bar_size: BarSize,
        **kwargs,
    ) -> Dict[Symbol, List[OHLCV]]:
        """
        Fetch historical OHLCV data for multiple symbols.
        """
        return await self._provider.get_historical_bars_multiple(
            symbols=symbols,
            time_range=time_range,
            bar_size=bar_size,
            **kwargs,
        )


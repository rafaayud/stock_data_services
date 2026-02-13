"""
Abstract interfaces (ports) for accessing market data.

Concrete implementations for Interactive Brokers or other brokers
should live in the infrastructure layer and implement these
interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Protocol, Dict

from ..entities import BrokerConnectionConfig
from ..value_objects import BarSize, OHLCV, TimeRange, Symbol, Exchange, Currency, SecurityType

class MarketDataProvider(ABC):
    """
    Port for requesting historical market data.
    """

    @abstractmethod
    async def connect(self, config: BrokerConnectionConfig) -> None:
        """
        Configure or reconfigure the underlying broker connection.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the broker.
        """

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        bar_size: BarSize,
        exchange: Exchange,
        currency: Currency,
        security_type: SecurityType,
    ) -> List[OHLCV]:
        """
        Retrieve historical bar data for a single symbol.

        Additional keyword arguments (kwargs) allow broker-specific
        configuration, such as exchange, currency or security type.
        """

    @abstractmethod
    async def get_historical_bars_multiple(
        self,
        symbols: List[Symbol],
        time_range: TimeRange,
        bar_size: BarSize,
        exchange: Exchange,
        currency: Currency,
        security_type: SecurityType,
    ) -> Dict[Symbol, List[OHLCV]]:
        """
        Retrieve historical bar data for multiple symbols.

        Additional keyword arguments (kwargs) allow broker-specific
        configuration, such as exchange, currency or security type,
        which will be applied to all symbols in the batch.
        """


class RealtimeTickHandler(Protocol):
    """
    Callback protocol for streaming real-time ticks.
    """

    


class RealtimeMarketDataProvider(ABC):
    """
    Port for subscribing to real-time market data.
    """

    @abstractmethod
    async def connect(self, config: BrokerConnectionConfig) -> None:
        """
        Configure or reconfigure the underlying broker connection.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the broker.
        """

    

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """
        Cancel an existing real-time subscription.
        """




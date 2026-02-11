"""
Abstract interfaces (ports) for accessing market data.

Concrete implementations for Interactive Brokers or other brokers
should live in the infrastructure layer and implement these
interfaces.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Protocol

from .entities import BrokerConnectionConfig
from .aggregates.contract import Contract
from .value_objects import BarSize, OHLCV, TimeRange

import asyncio

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
        contract: Contract,
        time_range: TimeRange,
        bar_size: BarSize) -> List[OHLCV]:
        """
        Retrieve historical bar data for an instrument between the given timestamps.
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



from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange, Symbol, Exchange, Currency, SecurityType, ExecutionMode, Signal
from server.trading.domain.strategies.base import PortfolioStrategy
from typing import Dict, List





class MeanReversion3_7(PortfolioStrategy):
    """
    Represents a mean reversion strategy.
    """
    def __init__(self,name: str, universe: Dict[Symbol, List[OHLCV]]) -> None:

        pass


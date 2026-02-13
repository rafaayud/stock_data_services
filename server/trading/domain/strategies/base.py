from abc import ABC, abstractmethod
from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange, Symbol, Exchange, Currency, SecurityType, ExecutionMode, Signal
from typing import List, Dict

class SingleAssetStrategy(ABC):
    """
    Base class for all strategies.
    
    Execution modes:
    - ON_CLOSE: Signal generated only when candle closes (safer, less noise)
    - ON_TICK: Signal generated on every price update (faster, more noise)
    
    Strategies work with Candle_static because they only need OHLCV.
    """
    
    def __init__(
        self, 
        name: str, 
        min_candles: int,
        mode: ExecutionMode = ExecutionMode.ON_CLOSE) -> None:

        self._name = name
        self._min_candles = min_candles
        self._mode = mode
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def min_candles_required(self) -> int:
        return self._min_candles
    
    @property
    def execution_mode(self) -> ExecutionMode:
        return self._mode
    
    @property
    def executes_on_tick(self) -> bool:
        """True if strategy should run on every tick."""
        return self._mode == ExecutionMode.ON_TICK
    
    @property
    def executes_on_close(self) -> bool:
        """True if strategy should run only on candle close."""
        return self._mode == ExecutionMode.ON_CLOSE
        
    @abstractmethod
    def generate_signal(self, list_ohlcv: List[OHLCV]) -> Signal:
        """
        Genera una señal de trading basada en las velas.
        
        Args:
            list_ohlcv: Lista de OHLCV (solo OHLCV, inmutables)
            
        Returns:
            Signal.BUY, Signal.SELL, o Signal.HOLD
        """
        pass



class PortfolioStrategy(ABC):
    """Strategy over a universe of assets → vector of weights."""
    
    def __init__(self, name: str) -> None:
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @abstractmethod
    def generate_weights(
        self, name: str,
        universe: Dict[Symbol, List[OHLCV]]) -> Dict[Symbol, float]:
        """
        Given the historical data of the entire universe,
        returns the weight (positive=long, negative=short)
        for each symbol.
        """
        pass
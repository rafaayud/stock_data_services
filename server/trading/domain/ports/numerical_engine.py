from abc import ABC, abstractmethod
from typing import Dict, List
from ..value_objects import OHLCV, Symbol



class NumericalEngine(ABC):
    """
    Represents a numerical engine.
    """
    @abstractmethod
    def returns(self, list_ohlcv: List[OHLCV]) -> List[float]:
        """
        Executes the numerical engine.
        """
        pass

    @abstractmethod
    def multiple_returns(self, universe: Dict[Symbol, List[OHLCV]]) -> Dict[Symbol, List[float]]:
        """
        Executes the numerical engine for multiple assets.
        """
        pass


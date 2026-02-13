import pandas as pd
from server.trading.domain.ports.numerical_engine import NumericalEngine

from typing import Dict, List
from server.trading.domain.value_objects import OHLCV, Symbol

from server.trading.domain.utils.decorators import logged
import logging



class PandasEngine(NumericalEngine):
    """
    Pandas engine for calculating returns.
    """

    @logged(logger_name="trading.infrastructure.pandas_engine", level=logging.INFO)
    def returns(self, list_ohlcv: List[OHLCV]) -> List[float]:
        """
        Calculates the returns for a single asset.
        """
        pass

    @logged(logger_name="trading.infrastructure.pandas_engine", level=logging.INFO)
    def multiple_returns(self, universe: Dict[Symbol, List[OHLCV]]) -> Dict[Symbol, List[float]]:
        """
        Calculates the returns for multiple assets.
        """
        pass
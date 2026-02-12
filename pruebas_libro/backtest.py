#%%
import sys
from pathlib import Path

# Ruta al root del proyecto: ...\nuevas_pruebas\codigos
PROJECT_ROOT = Path(__file__).resolve().parent.parent / "server"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# %%
from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange, Symbol, Exchange, Currency, SecurityType
from server.trading.domain.aggregates.contract import Contract
from server.trading.domain.aggregates.candle_request import FetchHistoricalBarsRequest
from typing import List, Dict
from datetime import datetime, timedelta

import asyncio
import numpy as np


#%%
async def datos(symbols: List[Symbol]) -> Dict[Symbol, List[OHLCV]]:

    for symbol in symbols:
        contract = Contract(symbol=symbol, exchange=Exchange.NASDAQ, currency=Currency.USD, security_type=SecurityType.STOCK)
        request = FetchHistoricalBarsRequest(contract=contract, time_range=TimeRange(start=datetime.now() - timedelta(days=365), end=datetime.now()), bar_size=BarSize.DAY)
        bars = await fetch(request)
        return {symbol: bars}






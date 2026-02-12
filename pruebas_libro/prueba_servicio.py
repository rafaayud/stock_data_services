from server.trading.infraestructure.tws_adapter import TWSAdapter
from server.trading.application.use_cases import FetchHistoricalBarsUseCase

from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange, Symbol, Currency, Exchange, SecurityType
from server.trading.domain.aggregates.contract import Contract
from server.trading.domain.aggregates.candle_request import FetchHistoricalBarsRequest
from typing import List, Dict
import asyncio
from datetime import datetime, timedelta

import pandas as pd
import kagglehub


async def fetch(contract: Contract, time_range: TimeRange, bar_size: BarSize) -> List[OHLCV]:

    request = FetchHistoricalBarsRequest(contract, time_range, bar_size)
    adapter = TWSAdapter()
    async with adapter as adapter:
        service = FetchHistoricalBarsUseCase(adapter)
        bars = await service.execute(request)
    return bars


async def fetch_multiple(requests: List[FetchHistoricalBarsRequest]) -> Dict[Symbol, List[OHLCV]]:
    
    adapterWS = TWSAdapter()
    async with adapterWS as adapter:
        service = FetchHistoricalBarsUseCase(adapter)
        bars = await service.execute_multiple(requests)
    return bars

# if __name__ == "__main__":

#     start = datetime(2024, 1, 1)
#     end = start + timedelta(days=5)
#     contract = Contract(symbol="AAPL", exchange="NASDAQ", currency="USD", security_type="STOCK") # type: ignore
#     time_range = TimeRange(start=start, end=end)
#     bar_size = BarSize(value="1d")
#     bars = asyncio.run(fetch(contract, time_range, bar_size))
#     for bar in bars:
#         print(bar)

if __name__ == "__main__":

    symbols = pd.read_csv("C:/Users/Rafa/Desktop/Algoritmic trading/sp500list.csv")["symbol"].tolist()[:50]

    currency = Currency.USD
    exchange = Exchange.SMART
    security_type = SecurityType.STOCK

    contracts = [Contract(symbol=Symbol(value=symbol), exchange=exchange, currency=currency, security_type=security_type) for symbol in symbols]
    time_range = TimeRange(start=datetime(2026, 1, 1), end=datetime.now())
    bar_size = BarSize(value="1d")
    requests = [FetchHistoricalBarsRequest(contract=contract, time_range=time_range, bar_size=bar_size) for contract in contracts]
    bars = asyncio.run(fetch_multiple(requests))

    for symbol, bars in bars.items():
        print(symbol, len(bars),bars)


from server.trading.infraestructure.tws_adapter import TWSAdapter
from server.trading.application.use_cases import FetchHistoricalBarsUseCase

from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange
from server.trading.domain.aggregates.contract import Contract
from server.trading.domain.aggregates.candle_request import FetchHistoricalBarsRequest
from typing import List
import asyncio
from datetime import datetime, timedelta


async def fetch(contract: Contract, time_range: TimeRange, bar_size: BarSize) -> List[OHLCV]:

    request = FetchHistoricalBarsRequest(contract, time_range, bar_size)
    adapter = TWSAdapter()
    async with adapter as adapter:
        service = FetchHistoricalBarsUseCase(adapter)
        bars = await service.execute(request)
    return bars



if __name__ == "__main__":

    start = datetime(2024, 1, 1)
    end = start + timedelta(days=5)
    contract = Contract(symbol="AAPL", exchange="NASDAQ", currency="USD", security_type="STOCK") # type: ignore
    time_range = TimeRange(start=start, end=end)
    bar_size = BarSize(value="1d")
    bars = asyncio.run(fetch(contract, time_range, bar_size))
    for bar in bars:
        print(bar)
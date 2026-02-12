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
#     contract = Contract(symbol="AAPL", exchange=Exchange.SMART, currency=Currency.USD, security_type="STOCK") # type: ignore
#     time_range = TimeRange(start=start, end=end)
#     bar_size = BarSize(value="1d")
#     bars = asyncio.run(fetch(contract, time_range, bar_size))
#     for bar in bars:
#         print(bar)



#Descargar datos para el periodo 2000-2010 para los 450 primeros símbolos de la lista, para poder hacer el 
#ejercicio Example 3.7 del libro "Quantitative Trading" de Ernest P. Chan
if __name__ == "__main__":
    symbols = pd.read_csv("C:/Users/Rafa/Desktop/Algoritmic trading/sp500list.csv")["symbol"].tolist()[:50]
    currency = Currency.USD
    exchange = Exchange.SMART
    security_type = SecurityType.STOCK
    contracts = [Contract(symbol=Symbol(value=symbol), exchange=exchange, currency=currency, security_type=security_type) for symbol in symbols]
    time_range = TimeRange(start=datetime(2000, 1, 1), end=datetime(2010, 12, 31))
    bar_size = BarSize(value="1d")
    requests = [FetchHistoricalBarsRequest(contract=contract, time_range=time_range, bar_size=bar_size) for contract in contracts]
    bars = asyncio.run(fetch_multiple(requests))

    # Construir DataFrame y guardar en CSV
    rows = []
    for symbol, ohlcv_list in bars.items():
        for bar in ohlcv_list:
            rows.append({
                "symbol": symbol.value,
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            })

    df = pd.DataFrame(rows)
    df.to_csv("C:/Users/Rafa/Desktop/Algoritmic trading/sp500_2000_2010_prueba.csv", index=False)
    print(f"Guardado {len(df)} filas, {df['symbol'].nunique()} símbolos")


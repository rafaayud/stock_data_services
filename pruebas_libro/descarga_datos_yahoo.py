
import yfinance as yf
import pandas as pd
from server.trading.domain.value_objects import Symbol, TimeRange, BarSize
from server.trading.infraestructure.yfinance_adapter import YahooFinanceAdapter
from server.trading.application.use_cases import FetchHistoricalBarsUseCase
import asyncio
import datetime

async def main():

    adapter = YahooFinanceAdapter()
    service = FetchHistoricalBarsUseCase(adapter)

    symbols = pd.read_csv("C:/Users/Rafa/Desktop/Algoritmic trading/sp500list.csv")["symbol"].tolist()[:500]
    time_range = TimeRange(start=datetime.datetime(2000, 1, 1), end=datetime.datetime(2010, 12, 31))
    bar_size = BarSize("1d")
    
    bars = await service.execute_multiple(symbols, time_range, bar_size)
    print(bars)




if __name__ == "__main__":
    asyncio.run(main())
from server.trading.domain.ports import MarketDataProvider

from server.trading.domain.value_objects import OHLCV, BarSize, TimeRange, Symbol

import yfinance as yf
from typing import List, Dict
from trading.domain.utils.decorators import logged
import logging


_BAR_SIZE_MAP: dict[str, str] = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "1h":  "1h",
    "1d":  "1d",
}


def _map_interval(bar_size: BarSize) -> str:
    try:
        return _BAR_SIZE_MAP[bar_size.value]
    except KeyError:
        raise ValueError(
            f"Unsupported bar size for Yahoo Finance: {bar_size.value}. "
            f"Supported: {list(_BAR_SIZE_MAP.keys())}"
        )


def _dataframe_to_ohlcv(df) -> List[OHLCV]:
    """Convert a yfinance DataFrame (single ticker) to a list of OHLCV."""
    results: List[OHLCV] = []
    for index, row in df.iterrows():
        results.append(
            OHLCV(
                date=index.to_pydatetime(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]) if row["Volume"] >= 0 else None,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class YahooFinanceAdapter(MarketDataProvider):
    """
    Concrete adapter that bridges the domain MarketDataProvider port
    with Yahoo Finance via yfinance.

    connect() and disconnect() are no-ops since yfinance doesn't
    require a persistent connection. They exist to satisfy the
    MarketDataProvider interface.
    """

    async def connect(self) -> None:  # type: ignore[override]
        # No persistent connection needed for yfinance.
        return None

    async def disconnect(self) -> None:  # type: ignore[override]
        # No persistent connection to close.
        return None

    @logged(logger_name="trading.infrastructure.yfinance", level=logging.WARNING)
    async def get_historical_bars(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        bar_size: BarSize,
        **_: dict,
    ) -> List[OHLCV]:
        """
        Fetch historical OHLCV data for a single contract from Yahoo Finance.
        """
        symbol_str = str(symbol)
        interval = _map_interval(bar_size)
        start = time_range.start
        end = time_range.end

        try:
            df = yf.download(
                symbol_str,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval=interval,
                progress=False,
            )

            if df.empty:
                return []

            # yf.download con un solo ticker puede devolver MultiIndex
            if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
                df = df.droplevel(level=1, axis=1)

            return _dataframe_to_ohlcv(df)

        except Exception as e:
            print(f"Error downloading {symbol_str}: {e}")
            return []
    @logged(logger_name="trading.infrastructure.yfinance", level=logging.WARNING)
    async def get_historical_bars_multiple(
        self,
        symbols: List[Symbol],
        time_range: TimeRange,
        bar_size: BarSize,
        **_: dict,
    ) -> Dict[Symbol, List[OHLCV]]:
        """
        Fetch historical data for multiple symbols in a single yfinance call.
        """
        if not symbols:
            return {}

        interval = _map_interval(bar_size)
        start = time_range.start.strftime("%Y-%m-%d")
        end = time_range.end.strftime("%Y-%m-%d")

        try:
            df = yf.download(
                [str(symbol) for symbol in symbols],
                start=start,
                end=end,
                interval=interval,
                progress=True,
            )

            if df.empty:
                return {}

            results: Dict[Symbol, List[OHLCV]] = {symbol: [] for symbol in symbols}

            for symbol in symbols:
                try:
                    symbol_df = df[str(symbol)]

                    symbol_df = symbol_df.dropna(subset=["Close"])

                    if not symbol_df.empty:
                        results[symbol] = _dataframe_to_ohlcv(symbol_df)
                    else:
                        results[symbol] = []

                except (KeyError, Exception) as e:
                    print(f"Error processing {symbol}: {e}")
                    results[symbol] = []

            return results

        except Exception as e:
            print(f"Error in bulk download: {e}")
            return {}
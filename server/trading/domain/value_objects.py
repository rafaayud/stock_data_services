"""
Value Objects for the trading domain.

These types encapsulate small concepts with their own invariants,
such as symbols, money amounts or time ranges.
"""


from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

@dataclass(frozen=True)
class Symbol:
    """
    Represents a normalized instrument symbol (e.g. 'AAPL', 'ES', 'EURUSD').
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

class Exchange(str, Enum):
    """
    Represents a stock exchange.
    """
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
    CBOE = "CBOE"
    CFE = "CFE"
    SMART = "SMART"

class Currency(str, Enum):
    """
    Represents a currency.
    """
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"


class SecurityType(str, Enum):
    """
    Represents a security type.
    """
    STOCK = "STOCK"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    INDEX = "INDEX"
    CURRENCY = "CURRENCY"


@dataclass(frozen=True)
class Money:
    """
    Monetary amount in a specific currency.
    """

    amount: float
    currency: str

    def __post_init__(self) -> None:
        if not self.currency:
            raise ValueError("Currency cannot be empty")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add Money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract Money with different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)


@dataclass(frozen=True)
class TimeRange:
    """
    Inclusive time range [start, end] used for historical queries.
    Always stored as UTC-aware datetimes.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("TimeRange end must be after start")
        if self.start.tzinfo is None:
            object.__setattr__(self, "start", self.start.replace(tzinfo=timezone.utc))
        if self.end.tzinfo is None:
            object.__setattr__(self, "end", self.end.replace(tzinfo=timezone.utc))


@dataclass(frozen=True)
class BarSize:
    """
    Size of a bar in time.
    """
    value: str
    def __post_init__(self) -> None:
        if self.value not in ["1s", "5s", "15s", "1m", "5m", "15m", "1h", "1d"]:
            raise ValueError("Invalid bar size")


@dataclass(frozen=True)
class OHLCV:
    """
    Open, High, Low, Close, Volume.
    """
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

    def __post_init__(self) -> None:
        if self.date is None or self.open is None or self.high is None or self.low is None or self.close is None:
            raise ValueError("OHLCV values cannot be None")


    def __str__(self) -> str:
        return f"OHLCV(date={self.date}, open={self.open}, high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
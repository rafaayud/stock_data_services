from dataclasses import dataclass
from typing import Optional
from trading.domain.value_objects import Symbol, Exchange, Currency, SecurityType

@dataclass(frozen=True)
class Contract:
    """
    Represents a contract in the domain.
    """
    symbol: Symbol
    exchange: Exchange
    currency: Currency
    security_type: SecurityType


    def __post_init__(self) -> None:
        if self.symbol is None or self.exchange is None or self.currency is None or self.security_type is None:
            raise ValueError("Contract values cannot be None")

    def __str__(self) -> str:
        return f"{self.symbol}-{self.exchange}-{self.currency}-{self.security_type}"

    def __repr__(self) -> str:
        return f"Contract(symbol={self.symbol}, exchange={self.exchange}, currency={self.currency}, security_type={self.security_type})"


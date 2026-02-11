"""
Domain entities for market data and broker configuration.

These classes are framework- and broker-agnostic; they should not
import anything from infrastructure or third-party SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .value_objects import Symbol


@dataclass(frozen=True)
class BrokerConnectionConfig:
    """
    Domain representation of a broker connection, decoupled from
    any specific SDK configuration object.
    """

    host: str = "127.0.0.1"
    port: int = 7497  # default TWS paper trading port
    client_id: int = 1


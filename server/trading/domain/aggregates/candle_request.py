from dataclasses import dataclass
from trading.domain.aggregates.contract import Contract
from trading.domain.value_objects import BarSize, TimeRange

@dataclass(frozen=True)
class FetchHistoricalBarsRequest:
    """Input DTO for the FetchHistoricalBars use case."""
    contract: Contract
    time_range: TimeRange
    bar_size: BarSize
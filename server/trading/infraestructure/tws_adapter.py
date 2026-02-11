from trading.domain.ports import MarketDataProvider
from tws import IBClient

class TWSAdapter(MarketDataProvider):
    def __init__(self, client: IBClient) -> None:
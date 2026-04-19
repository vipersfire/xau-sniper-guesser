from abc import ABC, abstractmethod
from dataclasses import dataclass
from engine.regime.regime_types import RegimeResult


@dataclass
class EntrySignal:
    direction: str      # buy | sell
    sl_pips: float
    tp_pips: float
    lot_size: float
    expiry_bars: int
    reason: str


class BaseRule(ABC):
    """Single strategy ruleset for a specific regime type."""

    supported_regimes: list[str] = []

    def supports(self, regime_type: str) -> bool:
        return regime_type in self.supported_regimes

    @abstractmethod
    def evaluate(
        self,
        regime: RegimeResult,
        features: dict,
        account_balance: float,
        anomaly_score: float,
    ) -> EntrySignal | None:
        """Return EntrySignal if conditions are met, else None."""
        ...

"""AnomalyDetector: consensus of 3 detectors. 2-of-3 flag → abstain."""
import logging
from datetime import datetime, timezone
from anomaly.isolation_forest import IsolationForestDetector
from anomaly.structural_detector import StructuralDeviationDetector
from anomaly.calendar_detector import CalendarDetector
from config.constants import ANOMALY_ABSTAIN_THRESHOLD

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self):
        self.iso_forest = IsolationForestDetector()
        self.structural = StructuralDeviationDetector()
        self.calendar = CalendarDetector()

    def update(self, features: dict[str, float]):
        """Call on each candle close to update detectors."""
        self.iso_forest.add_sample(features)
        self.structural.update(features)

    async def score(self, features: dict[str, float], dt: datetime | None = None) -> tuple[float, bool, list[str]]:
        """
        Returns (composite_score, should_abstain, flagged_detectors).
        2 of 3 detectors flagging → abstain.
        """
        flags = []

        iso_score = self.iso_forest.score(features)
        if iso_score >= 0.5:
            flags.append("isolation_forest")

        struct_score = self.structural.score(features)
        if self.structural.is_anomaly(features):
            flags.append("structural")

        cal_anomaly = await self.calendar.is_anomaly(dt)
        if cal_anomaly:
            flags.append("calendar")

        composite = max(iso_score, struct_score)
        if cal_anomaly:
            composite = max(composite, 0.7)

        n_flags = len(flags)
        should_abstain = n_flags >= ANOMALY_ABSTAIN_THRESHOLD

        if n_flags == 3:
            logger.warning("All 3 anomaly detectors flagged — abstain + reduce positions")
        elif n_flags == 2:
            logger.warning("2/3 anomaly detectors flagged (%s) — abstaining", flags)

        return float(composite), should_abstain, flags

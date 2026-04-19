"""ForexFactory calendar importer — rule-based HTML parser, no AI."""
import aiohttp
import logging
from datetime import datetime, timezone
from ingestion.base.importer import BaseImporter
from ingestion.parsers.html_parser import HTMLParser
from data.db import AsyncSessionLocal
from data.repositories.event_repo import EventRepository
from utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)

FF_CALENDAR_URL = "https://www.forexfactory.com/calendar"

IMPACT_MAP = {
    "red": "High",
    "ora": "Medium",
    "yel": "Low",
    "gry": "Holiday",
    "": "None",
}


class ForexFactoryImporter(BaseImporter):
    source_name = "forexfactory"
    run_interval = 86400  # daily

    async def fetch(self) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; XAUSniper/1.0)",
            "Accept": "text/html",
        }
        async with aiohttp.ClientSession(headers=headers) as http:
            return await async_retry_with_backoff(
                self._fetch_page, http, max_attempts=4, base_delay=2.0
            )

    async def _fetch_page(self, http: aiohttp.ClientSession) -> str:
        async with http.get(FF_CALENDAR_URL) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def parse(self, raw: str) -> list[dict]:
        parser = HTMLParser(raw)
        rows = parser.find_elements("tr.calendar__row")
        events = []
        current_date = None

        for row in rows:
            # Date cell appears once per day block
            date_el = row.select_one(".calendar__date")
            if date_el and date_el.get_text(strip=True):
                date_text = date_el.get_text(strip=True)
                try:
                    current_date = datetime.strptime(date_text, "%a%b %d").replace(
                        year=datetime.utcnow().year
                    )
                except ValueError:
                    pass

            time_el = row.select_one(".calendar__time")
            currency_el = row.select_one(".calendar__currency")
            impact_el = row.select_one(".calendar__impact span")
            title_el = row.select_one(".calendar__event-title")
            forecast_el = row.select_one(".calendar__forecast")
            previous_el = row.select_one(".calendar__previous")

            if not (currency_el and title_el):
                continue

            time_text = time_el.get_text(strip=True) if time_el else "00:00am"
            currency = currency_el.get_text(strip=True)
            impact_class = ""
            if impact_el:
                classes = impact_el.get("class", [])
                for c in classes:
                    for key in IMPACT_MAP:
                        if key and key in c:
                            impact_class = key
                            break
            impact = IMPACT_MAP.get(impact_class, "None")
            title = title_el.get_text(strip=True)
            forecast = forecast_el.get_text(strip=True) if forecast_el else None
            previous = previous_el.get_text(strip=True) if previous_el else None

            if current_date is None:
                continue

            try:
                time_obj = datetime.strptime(time_text.upper(), "%I:%M%p").time()
                event_time = datetime.combine(current_date.date(), time_obj).replace(tzinfo=timezone.utc)
            except ValueError:
                event_time = current_date.replace(tzinfo=timezone.utc)

            events.append({
                "event_time": event_time,
                "currency": currency,
                "impact": impact,
                "title": title,
                "forecast": forecast or None,
                "previous": previous or None,
                "actual": None,
                "source": "forexfactory",
            })

        return events

    async def store(self, data: list[dict]) -> int:
        async with AsyncSessionLocal() as session:
            repo = EventRepository(session)
            await repo.upsert_events(data)
        return len(data)

"""Rule-based RSS/Atom feed parser. No AI/LLM."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime


@dataclass
class RSSItem:
    title: str
    link: str
    published: datetime | None
    summary: str


def parse_rss(xml_text: str) -> list[RSSItem]:
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        pub_str = _text(item, "pubDate")
        summary = _text(item, "description") or ""
        published = _parse_date(pub_str)
        if title:
            items.append(RSSItem(title=title, link=link or "", published=published, summary=summary))

    # Atom
    for entry in root.findall(".//atom:entry", ns):
        title = _text(entry, "atom:title", ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href") if link_el is not None else ""
        pub_str = _text(entry, "atom:published", ns) or _text(entry, "atom:updated", ns)
        summary = _text(entry, "atom:summary", ns) or ""
        published = _parse_date_iso(pub_str)
        if title:
            items.append(RSSItem(title=title, link=link or "", published=published, summary=summary))

    return items


def _text(el, tag: str, ns: dict | None = None) -> str | None:
    found = el.find(tag, ns) if ns else el.find(tag)
    if found is not None and found.text:
        return found.text.strip()
    return None


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)
    except Exception:
        return None


def _parse_date_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.rstrip("Z"))
    except Exception:
        return None

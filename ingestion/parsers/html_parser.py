"""Rule-based deterministic HTML parser. No AI/LLM."""
from bs4 import BeautifulSoup


class HTMLParser:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def select_text(self, selector: str, index: int = 0) -> str | None:
        elements = self.soup.select(selector)
        if index < len(elements):
            return elements[index].get_text(strip=True)
        return None

    def select_all_text(self, selector: str) -> list[str]:
        return [el.get_text(strip=True) for el in self.soup.select(selector)]

    def select_attr(self, selector: str, attr: str, index: int = 0) -> str | None:
        elements = self.soup.select(selector)
        if index < len(elements):
            return elements[index].get(attr)
        return None

    def select_table_rows(self, table_selector: str) -> list[list[str]]:
        rows = []
        for tr in self.soup.select(f"{table_selector} tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        return rows

    def find_elements(self, selector: str) -> list:
        return self.soup.select(selector)

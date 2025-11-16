"""Structured data extraction from web pages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup


def _sanitize_text(text: str) -> str:
    """Remove control characters and clean up text for JSON serialization.

    Args:
        text: Raw text that may contain control characters

    Returns:
        Cleaned text safe for JSON encoding
    """
    if not text:
        return text

    # Remove control characters (except newline, carriage return, tab)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize whitespace
    text = " ".join(text.split())

    return text


@dataclass
class TableData:
    """Extracted table data."""

    caption: str | None
    headers: list[str]
    rows: list[dict[str, str]]


@dataclass
class ListData:
    """Extracted list data."""

    title: str | None
    items: list[str]
    nested: bool


class DataExtractor:
    """Extract structured data from HTML."""

    def extract_tables(self, html: str, max_tables: int = 5) -> list[TableData]:
        """Extract HTML tables.

        Args:
            html: Raw HTML content
            max_tables: Maximum number of tables to extract

        Returns:
            List of TableData objects with caption, headers, and rows
        """
        soup = BeautifulSoup(html, "html.parser")
        tables = []

        for table in soup.find_all("table")[:max_tables]:
            # Extract caption
            caption_elem = table.find("caption")
            caption = (
                _sanitize_text(caption_elem.get_text(strip=True))
                if caption_elem
                else None
            )

            # Extract headers
            headers = []
            header_row = table.find("thead")
            if header_row:
                headers = [
                    _sanitize_text(th.get_text(strip=True))
                    for th in header_row.find_all("th")
                ]
            else:
                # Try first row
                first_row = table.find("tr")
                if first_row:
                    headers = [
                        _sanitize_text(th.get_text(strip=True))
                        for th in first_row.find_all("th")
                    ]

            # If no headers found, use generic column names
            if not headers:
                first_row = table.find("tr")
                if first_row:
                    num_cols = len(first_row.find_all(["td", "th"]))
                    headers = [f"Column {i + 1}" for i in range(num_cols)]

            if not headers:
                continue

            # Extract rows
            rows = []
            tbody = table.find("tbody")
            row_elements = (
                tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
            )  # Skip header row if no tbody

            for tr in row_elements:
                cells = tr.find_all(["td", "th"])
                if cells and len(cells) == len(headers):
                    row_dict = {}
                    for i, cell in enumerate(cells):
                        row_dict[headers[i]] = _sanitize_text(cell.get_text(strip=True))
                    rows.append(row_dict)

            if rows:
                tables.append(TableData(caption=caption, headers=headers, rows=rows))

        return tables

    def extract_lists(self, html: str, max_lists: int = 5) -> list[ListData]:
        """Extract HTML lists (ul, ol, dl).

        Args:
            html: Raw HTML content
            max_lists: Maximum number of lists to extract

        Returns:
            List of ListData objects with title and items
        """
        soup = BeautifulSoup(html, "html.parser")
        lists = []

        for list_elem in soup.find_all(["ul", "ol", "dl"])[:max_lists]:
            # Try to find a title (preceding heading)
            title = None
            prev = list_elem.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            if prev:
                title = _sanitize_text(prev.get_text(strip=True))

            # Extract items
            items = []
            if list_elem.name in ["ul", "ol"]:
                for li in list_elem.find_all("li", recursive=False):
                    items.append(_sanitize_text(li.get_text(strip=True)))
            else:  # dl
                for dt in list_elem.find_all("dt"):
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        items.append(
                            f"{_sanitize_text(dt.get_text(strip=True))}: {_sanitize_text(dd.get_text(strip=True))}"
                        )

            if items:
                lists.append(
                    ListData(
                        title=title,
                        items=items,
                        nested=False,  # TODO: detect nested lists
                    )
                )

        return lists

    def extract_fields(
        self, html: str, selectors: dict[str, str]
    ) -> dict[str, str | list[str]]:
        """Extract specific fields using CSS selectors.

        Args:
            html: Raw HTML content
            selectors: Dict mapping field names to CSS selectors

        Returns:
            Dict with extracted field values (single string or list of strings)
        """
        soup = BeautifulSoup(html, "html.parser")
        data: dict[str, str | list[str]] = {}

        for field_name, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                if len(elements) == 1:
                    data[field_name] = _sanitize_text(elements[0].get_text(strip=True))
                else:
                    data[field_name] = [
                        _sanitize_text(el.get_text(strip=True)) for el in elements
                    ]

        return data

    def extract_json_ld(self, html: str) -> list[dict[str, Any]]:
        """Extract JSON-LD structured data.

        Args:
            html: Raw HTML content

        Returns:
            List of JSON-LD objects found in the page
        """
        soup = BeautifulSoup(html, "html.parser")
        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        data = []
        for script in json_ld_scripts:
            try:
                if script.string:
                    parsed = json.loads(script.string)
                    data.append(parsed)
            except json.JSONDecodeError:
                pass

        return data

    def auto_extract(self, html: str) -> dict[str, Any]:
        """Automatically detect and extract structured content.

        Args:
            html: Raw HTML content

        Returns:
            Dict containing all detected structured data (tables, lists, json_ld)
        """
        results: dict[str, Any] = {"tables": [], "lists": [], "json_ld": []}

        # Try JSON-LD first (highest quality)
        json_ld = self.extract_json_ld(html)
        if json_ld:
            results["json_ld"] = json_ld

        # Extract tables
        tables = self.extract_tables(html, max_tables=3)
        if tables:
            results["tables"] = [
                {"caption": t.caption, "headers": t.headers, "rows": t.rows}
                for t in tables
            ]

        # Extract lists
        lists = self.extract_lists(html, max_lists=3)
        if lists:
            results["lists"] = [{"title": li.title, "items": li.items} for li in lists]

        return results

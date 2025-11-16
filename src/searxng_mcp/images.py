"""Pixabay API client for stock image search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from .config import HTTP_TIMEOUT, PIXABAY_API_KEY, USER_AGENT


@dataclass(slots=True)
class StockImage:
    """Represents a stock image result from Pixabay."""

    id: int
    preview_url: str
    large_url: str
    full_url: str
    width: int
    height: int
    views: int
    downloads: int
    likes: int
    tags: str
    user: str
    user_id: int


class PixabayClient:
    """Client for searching stock images on Pixabay."""

    BASE_URL = "https://pixabay.com/api/"

    def __init__(self, api_key: str = PIXABAY_API_KEY, timeout: float = HTTP_TIMEOUT) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self._headers = {"User-Agent": USER_AGENT}

    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def search_images(
        self,
        query: str,
        *,
        image_type: Literal["all", "photo", "illustration", "vector"] = "all",
        orientation: Literal["all", "horizontal", "vertical"] = "all",
        category: str = "",
        min_width: int = 0,
        min_height: int = 0,
        colors: str = "",
        safe_search: bool = True,
        per_page: int = 20,
        page: int = 1,
    ) -> list[StockImage]:
        """
        Search for stock images on Pixabay.

        Args:
            query: Search term
            image_type: Type of image (all, photo, illustration, vector)
            orientation: Image orientation (all, horizontal, vertical)
            category: Category filter (backgrounds, fashion, nature, science, etc.)
            min_width: Minimum image width in pixels
            min_height: Minimum image height in pixels
            colors: Filter by color (red, orange, yellow, green, turquoise, blue, etc.)
            safe_search: Enable safe search
            per_page: Images per page (3-200)
            page: Page number

        Returns:
            List of StockImage objects
        """
        if not self.has_api_key():
            raise ValueError("Pixabay API key not configured")

        params = {
            "key": self.api_key,
            "q": query,
            "image_type": image_type,
            "per_page": min(200, max(3, per_page)),
            "page": page,
            "safesearch": "true" if safe_search else "false",
        }

        # Add optional filters
        if orientation != "all":
            params["orientation"] = orientation
        if category:
            params["category"] = category
        if min_width > 0:
            params["min_width"] = min_width
        if min_height > 0:
            params["min_height"] = min_height
        if colors:
            params["colors"] = colors

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        images = []
        for hit in data.get("hits", []):
            images.append(
                StockImage(
                    id=hit["id"],
                    preview_url=hit["previewURL"],
                    large_url=hit["largeImageURL"],
                    full_url=hit.get("fullHDURL") or hit["largeImageURL"],
                    width=hit["imageWidth"],
                    height=hit["imageHeight"],
                    views=hit["views"],
                    downloads=hit["downloads"],
                    likes=hit["likes"],
                    tags=hit["tags"],
                    user=hit["user"],
                    user_id=hit["user_id"],
                )
            )

        return images

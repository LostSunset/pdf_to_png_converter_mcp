"""Paper download module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiofiles  # type: ignore[import-untyped]
import httpx

logger = logging.getLogger("pdf-to-png-mcp.downloader")

# 常見的學術網站 User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# 預設超時設定（秒）
DEFAULT_TIMEOUT = 60.0


async def download_paper(
    url: str,
    output_path: Path,
    timeout: float = DEFAULT_TIMEOUT,
) -> Path:
    """從網路下載論文 PDF.

    Args:
        url: PDF 下載網址
        output_path: 儲存路徑
        timeout: 下載超時時間（秒）

    Returns:
        儲存的檔案路徑

    Raises:
        httpx.HTTPStatusError: HTTP 請求失敗
        httpx.TimeoutException: 下載超時
        IOError: 檔案寫入失敗
    """
    logger.info(f"開始下載: {url}")

    # 確保輸出目錄存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(timeout),
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

        # 檢查 Content-Type
        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            logger.warning(f"警告: Content-Type 不是 PDF ({content_type})，但仍嘗試儲存檔案")

        # 非同步寫入檔案
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(response.content)

        file_size = output_path.stat().st_size
        logger.info(f"下載完成: {output_path} ({file_size:,} bytes)")

        return output_path


async def search_paper(
    query: str,
    max_results: int = 5,
) -> list[dict[str, str]]:
    """搜尋學術論文（使用 Semantic Scholar API）.

    Args:
        query: 搜尋關鍵字
        max_results: 最大結果數量

    Returns:
        論文資訊列表，每個包含 title, authors, url, year 等
    """
    api_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params: dict[str, str | int] = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,venue,openAccessPdf",
    }

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = await client.get(api_url, params=params)
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        papers: list[dict[str, Any]] = data.get("data", [])

        results: list[dict[str, str]] = []
        for paper in papers:
            pdf_info: dict[str, str] = paper.get("openAccessPdf") or {}
            authors: list[dict[str, str]] = paper.get("authors", [])
            author_names = ", ".join(a.get("name", "") for a in authors[:3])
            if len(authors) > 3:
                author_names += " et al."

            results.append(
                {
                    "title": paper.get("title", "Unknown"),
                    "authors": author_names,
                    "year": str(paper.get("year", "")),
                    "venue": paper.get("venue", ""),
                    "pdf_url": pdf_info.get("url", ""),
                }
            )

        return results

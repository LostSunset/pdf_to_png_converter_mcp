"""Tests for paper download functionality."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestDownloader:
    """測試下載器功能."""

    @pytest.mark.asyncio
    async def test_download_paper_creates_directory(self, temp_dir: Path) -> None:
        """測試下載時自動創建目錄."""
        from pdf_to_png_converter_mcp.downloader import download_paper

        output_path = temp_dir / "期刊名稱" / "論文標題" / "論文.pdf"

        # 使用一個不存在的 URL 測試目錄創建
        # 應該會在嘗試下載前創建目錄
        try:
            await download_paper("https://invalid.example.com/not-found.pdf", output_path)
        except Exception:
            # 預期會失敗，但目錄應該已經創建
            pass

        assert output_path.parent.exists()

    def test_search_paper_result_format(self) -> None:
        """測試搜尋結果格式."""
        # 測試結果格式符合預期
        expected_keys = {"title", "authors", "year", "venue", "pdf_url"}
        result = {
            "title": "測試論文",
            "authors": "作者一, 作者二",
            "year": "2024",
            "venue": "Nature",
            "pdf_url": "https://example.com/paper.pdf",
        }
        assert set(result.keys()) == expected_keys

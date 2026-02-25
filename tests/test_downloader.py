"""Tests for paper download functionality."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pdf_to_png_converter_mcp.downloader import download_paper, search_paper

# ---------------------------------------------------------------------------
# Helper: build a mock httpx response
# ---------------------------------------------------------------------------


def _make_mock_response(
    status_code: int = 200,
    content: bytes = b"%PDF-1.4 fake content",
    content_type: str = "application/pdf",
    json_data: dict | None = None,
    raise_for_status_side_effect: Exception | None = None,
) -> MagicMock:
    """Create a reusable mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": content_type}
    resp.content = content
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    if raise_for_status_side_effect:
        resp.raise_for_status = MagicMock(side_effect=raise_for_status_side_effect)
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _patch_httpx_client(mock_client_cls: MagicMock, mock_response: MagicMock) -> AsyncMock:
    """Wire up the AsyncClient context-manager mock and return the inner client."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _patch_aiofiles(mock_aiofiles_open: MagicMock) -> AsyncMock:
    """Wire up aiofiles.open as an async context-manager and return the file mock."""
    mock_file = AsyncMock()
    mock_file.write = AsyncMock()
    mock_aiofiles_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
    mock_aiofiles_open.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_file


# ===========================================================================
# TestDownloadPaper
# ===========================================================================


class TestDownloadPaper:
    """Tests for the download_paper async function."""

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_success(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Successful download writes content and returns the output path."""
        pdf_bytes = b"%PDF-1.4 test content"
        mock_response = _make_mock_response(content=pdf_bytes)
        _patch_httpx_client(mock_client_cls, mock_response)
        mock_file = _patch_aiofiles(mock_aiofiles_open)

        output = tmp_path / "journal" / "paper.pdf"
        # Create the file so that output_path.stat() succeeds inside download_paper
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pdf_bytes)

        result = await download_paper("https://example.com/paper.pdf", output)

        assert result == output
        mock_response.raise_for_status.assert_called_once()
        mock_file.write.assert_awaited_once_with(pdf_bytes)

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_creates_parent_directory(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        """download_paper must create the parent directory tree if it does not exist."""
        pdf_bytes = b"%PDF-1.4 test"
        mock_response = _make_mock_response(content=pdf_bytes)
        _patch_httpx_client(mock_client_cls, mock_response)
        _patch_aiofiles(mock_aiofiles_open)

        # Use a deeply nested path that definitely does not exist yet
        output = tmp_path / "深層" / "子目錄" / "paper.pdf"
        assert not output.parent.exists(), "Parent dir should not exist before download"

        # We need the file to exist for stat() call inside download_paper.
        # Since aiofiles.open is mocked, the file won't really be written.
        # We must pre-create the file after mkdir would have run.
        # Patch output_path.stat instead: use a real Path but pre-create after function
        # starts.  Easiest: just let mkdir happen (real), then pre-create the file
        # *before* calling, so stat() works.  But parent doesn't exist yet...
        #
        # Strategy: let download_paper call the real mkdir (it will create parents),
        # then the mocked aiofiles won't write.  stat() will fail.
        # So we also patch Path.stat on the output.
        with patch.object(Path, "stat", return_value=MagicMock(st_size=len(pdf_bytes))):
            result = await download_paper("https://example.com/paper.pdf", output)

        # The key assertion: the parent directory was created by download_paper
        assert output.parent.exists()
        assert result == output

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_http_404(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A 404 response should raise httpx.HTTPStatusError."""
        request = httpx.Request("GET", "https://example.com/missing.pdf")
        response_404 = httpx.Response(status_code=404, request=request)
        error = httpx.HTTPStatusError(
            message="404 Not Found",
            request=request,
            response=response_404,
        )
        mock_response = _make_mock_response(
            status_code=404,
            raise_for_status_side_effect=error,
        )
        _patch_httpx_client(mock_client_cls, mock_response)
        _patch_aiofiles(mock_aiofiles_open)

        output = tmp_path / "paper.pdf"
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await download_paper("https://example.com/missing.pdf", output)

        assert exc_info.value.response.status_code == 404

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_http_500(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A 500 response should raise httpx.HTTPStatusError."""
        request = httpx.Request("GET", "https://example.com/error.pdf")
        response_500 = httpx.Response(status_code=500, request=request)
        error = httpx.HTTPStatusError(
            message="500 Internal Server Error",
            request=request,
            response=response_500,
        )
        mock_response = _make_mock_response(
            status_code=500,
            raise_for_status_side_effect=error,
        )
        _patch_httpx_client(mock_client_cls, mock_response)
        _patch_aiofiles(mock_aiofiles_open)

        output = tmp_path / "paper.pdf"
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await download_paper("https://example.com/error.pdf", output)

        assert exc_info.value.response.status_code == 500

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_timeout(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A timeout during client.get should raise httpx.TimeoutException."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        _patch_aiofiles(mock_aiofiles_open)

        output = tmp_path / "paper.pdf"
        with pytest.raises(httpx.TimeoutException):
            await download_paper("https://example.com/slow.pdf", output)

    @patch("pdf_to_png_converter_mcp.downloader.aiofiles.open")
    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_non_pdf_content_type(
        self,
        mock_client_cls: MagicMock,
        mock_aiofiles_open: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Non-PDF content-type should still succeed but emit a warning.

        The warning only triggers when *both* the content-type lacks 'pdf'
        AND the URL does not end with '.pdf'.
        """
        html_bytes = b"<html>not a pdf</html>"
        mock_response = _make_mock_response(
            content=html_bytes,
            content_type="text/html",
        )
        _patch_httpx_client(mock_client_cls, mock_response)
        mock_file = _patch_aiofiles(mock_aiofiles_open)

        # URL does NOT end with .pdf so the warning branch is taken
        output = tmp_path / "paper.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(html_bytes)

        with caplog.at_level(logging.WARNING, logger="pdf-to-png-mcp.downloader"):
            result = await download_paper("https://example.com/paper", output)

        assert result == output
        mock_file.write.assert_awaited_once_with(html_bytes)
        # Verify the warning was logged
        assert any("Content-Type" in record.message for record in caplog.records)


# ===========================================================================
# TestSearchPaper
# ===========================================================================


class TestSearchPaper:
    """Tests for the search_paper async function."""

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_success(self, mock_client_cls: MagicMock) -> None:
        """Successful search returns correctly formatted results."""
        api_data = {
            "data": [
                {
                    "title": "Attention Is All You Need",
                    "authors": [
                        {"name": "Ashish Vaswani"},
                        {"name": "Noam Shazeer"},
                    ],
                    "year": 2017,
                    "venue": "NeurIPS",
                    "openAccessPdf": {"url": "https://arxiv.org/pdf/1706.03762"},
                },
            ],
        }
        mock_response = _make_mock_response(json_data=api_data)
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("attention mechanism")

        assert len(results) == 1
        paper = results[0]
        assert paper["title"] == "Attention Is All You Need"
        assert paper["authors"] == "Ashish Vaswani, Noam Shazeer"
        assert paper["year"] == "2017"
        assert paper["venue"] == "NeurIPS"
        assert paper["pdf_url"] == "https://arxiv.org/pdf/1706.03762"

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_empty_results(self, mock_client_cls: MagicMock) -> None:
        """An empty result set from the API returns an empty list."""
        mock_response = _make_mock_response(json_data={"data": []})
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("xyzzy nonexistent topic 12345")

        assert results == []

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_api_error(self, mock_client_cls: MagicMock) -> None:
        """A 500 API error should propagate as httpx.HTTPStatusError."""
        request = httpx.Request("GET", "https://api.semanticscholar.org/graph/v1/paper/search")
        response_500 = httpx.Response(status_code=500, request=request)
        error = httpx.HTTPStatusError(
            message="500 Server Error",
            request=request,
            response=response_500,
        )
        mock_response = _make_mock_response(
            status_code=500,
            raise_for_status_side_effect=error,
        )
        _patch_httpx_client(mock_client_cls, mock_response)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await search_paper("test query")

        assert exc_info.value.response.status_code == 500

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_author_truncation(self, mock_client_cls: MagicMock) -> None:
        """Papers with more than 3 authors get truncated with 'et al.'."""
        api_data = {
            "data": [
                {
                    "title": "Big Collab Paper",
                    "authors": [
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"name": "Charlie"},
                        {"name": "Diana"},
                    ],
                    "year": 2024,
                    "venue": "ICML",
                    "openAccessPdf": None,
                },
            ],
        }
        mock_response = _make_mock_response(json_data=api_data)
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("big collaboration")

        assert len(results) == 1
        assert results[0]["authors"] == "Alice, Bob, Charlie et al."

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_three_authors_no_truncation(self, mock_client_cls: MagicMock) -> None:
        """Papers with exactly 3 authors should NOT have 'et al.' appended."""
        api_data = {
            "data": [
                {
                    "title": "Three Author Paper",
                    "authors": [
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"name": "Charlie"},
                    ],
                    "year": 2023,
                    "venue": "ACL",
                    "openAccessPdf": {"url": "https://example.com/paper.pdf"},
                },
            ],
        }
        mock_response = _make_mock_response(json_data=api_data)
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("three authors")

        assert len(results) == 1
        assert results[0]["authors"] == "Alice, Bob, Charlie"
        assert "et al." not in results[0]["authors"]

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_missing_fields(self, mock_client_cls: MagicMock) -> None:
        """Papers with missing/absent fields should use safe defaults.

        Keys that are entirely absent from the API response trigger the
        dict.get() defaults.  openAccessPdf set to None is handled by the
        ``or {}`` fallback in the source.
        """
        api_data = {
            "data": [
                {
                    # "title" key absent -> defaults to "Unknown"
                    "authors": [],  # empty authors -> ""
                    # "year" key absent  -> str("") == ""
                    # "venue" key absent -> ""
                    "openAccessPdf": None,  # None -> ``or {}`` -> pdf_url == ""
                },
            ],
        }
        mock_response = _make_mock_response(json_data=api_data)
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("missing fields")

        assert len(results) == 1
        paper = results[0]
        assert paper["title"] == "Unknown"
        assert paper["authors"] == ""
        assert paper["year"] == ""
        assert paper["venue"] == ""
        assert paper["pdf_url"] == ""

    @patch("pdf_to_png_converter_mcp.downloader.httpx.AsyncClient")
    async def test_paper_without_open_access(self, mock_client_cls: MagicMock) -> None:
        """Papers without openAccessPdf should have an empty pdf_url."""
        api_data = {
            "data": [
                {
                    "title": "Closed Access Paper",
                    "authors": [{"name": "Author One"}],
                    "year": 2022,
                    "venue": "Science",
                    # openAccessPdf key is entirely absent
                },
            ],
        }
        mock_response = _make_mock_response(json_data=api_data)
        _patch_httpx_client(mock_client_cls, mock_response)

        results = await search_paper("closed access")

        assert len(results) == 1
        assert results[0]["pdf_url"] == ""
        assert results[0]["title"] == "Closed Access Paper"
        assert results[0]["authors"] == "Author One"

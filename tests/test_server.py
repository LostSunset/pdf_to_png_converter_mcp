"""Tests for MCP server functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

from pdf_to_png_converter_mcp.server import (
    call_tool,
    handle_batch_convert,
    handle_convert_pdf,
    handle_download_and_convert,
    handle_download_paper,
    handle_search_paper,
    list_tools,
    sanitize_filename,
)


# ---------------------------------------------------------------------------
# TestSanitizeFilename — 保留全部 7 個既有測試
# ---------------------------------------------------------------------------
class TestSanitizeFilename:
    """測試檔案名稱清理功能."""

    def test_basic_filename(self) -> None:
        """測試基本檔案名稱."""
        assert sanitize_filename("test") == "test"
        assert sanitize_filename("hello world") == "hello world"

    def test_chinese_filename(self) -> None:
        """測試中文檔案名稱."""
        assert sanitize_filename("測試文件") == "測試文件"
        assert sanitize_filename("深度學習論文") == "深度學習論文"

    def test_invalid_characters(self) -> None:
        """測試無效字元被替換."""
        assert sanitize_filename("test:file") == "test_file"
        assert sanitize_filename("test<>file") == "test__file"
        assert sanitize_filename('test"file') == "test_file"
        assert sanitize_filename("test/file") == "test_file"
        assert sanitize_filename("test\\file") == "test_file"
        assert sanitize_filename("test|file") == "test_file"
        assert sanitize_filename("test?file") == "test_file"
        assert sanitize_filename("test*file") == "test_file"

    def test_strip_spaces_and_dots(self) -> None:
        """測試移除前後空白和點."""
        assert sanitize_filename("  test  ") == "test"
        assert sanitize_filename("...test...") == "test"
        assert sanitize_filename(". test .") == "test"

    def test_long_filename(self) -> None:
        """測試過長檔案名稱被截斷."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 200

    def test_empty_filename(self) -> None:
        """測試空檔案名稱."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"
        assert sanitize_filename("...") == "unnamed"

    def test_complex_filename(self) -> None:
        """測試複雜的檔案名稱."""
        result = sanitize_filename("Deep Learning: A Survey (2024)?")
        assert ":" not in result
        assert "?" not in result
        assert "Deep Learning" in result


# ---------------------------------------------------------------------------
# TestListTools
# ---------------------------------------------------------------------------
class TestListTools:
    """測試 MCP 服務器工具列表."""

    async def test_list_tools(self) -> None:
        """測試工具列表包含所有 5 個工具."""
        tools = await list_tools()
        tool_names = {tool.name for tool in tools}

        assert "convert_pdf_to_png" in tool_names
        assert "download_paper" in tool_names
        assert "download_and_convert" in tool_names
        assert "batch_convert_pdfs" in tool_names
        assert "search_paper" in tool_names

    async def test_tool_count(self) -> None:
        """測試工具數量為 5."""
        tools = await list_tools()
        assert len(tools) == 5

    async def test_tool_schemas(self) -> None:
        """測試工具 schema 格式正確."""
        tools = await list_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    async def test_search_paper_tool_schema(self) -> None:
        """測試 search_paper 工具 schema 包含 query 為必要欄位."""
        tools = await list_tools()
        search_tool = next(t for t in tools if t.name == "search_paper")

        schema = search_tool.inputSchema
        assert "required" in schema
        assert "query" in schema["required"]
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]


# ---------------------------------------------------------------------------
# TestCallTool
# ---------------------------------------------------------------------------
class TestCallTool:
    """測試 call_tool 路由與錯誤處理."""

    async def test_unknown_tool(self) -> None:
        """未知工具名稱應回傳 '未知的工具'."""
        result = await call_tool("nonexistent_tool", {})
        assert len(result) == 1
        assert "未知的工具" in result[0].text

    @patch("pdf_to_png_converter_mcp.server.handle_convert_pdf", new_callable=AsyncMock)
    async def test_routes_to_convert_pdf(self, mock_handler: AsyncMock) -> None:
        """verify call_tool routes convert_pdf_to_png to handle_convert_pdf."""
        mock_handler.return_value = "ok"
        args = {"pdf_path": "dummy.pdf"}

        result = await call_tool("convert_pdf_to_png", args)

        mock_handler.assert_awaited_once_with(args)
        assert result[0].text == "ok"

    @patch("pdf_to_png_converter_mcp.server.handle_search_paper", new_callable=AsyncMock)
    async def test_routes_to_search_paper(self, mock_handler: AsyncMock) -> None:
        """verify call_tool routes search_paper to handle_search_paper."""
        mock_handler.return_value = "search results"
        args = {"query": "deep learning"}

        result = await call_tool("search_paper", args)

        mock_handler.assert_awaited_once_with(args)
        assert result[0].text == "search results"

    @patch("pdf_to_png_converter_mcp.server.handle_download_paper", new_callable=AsyncMock)
    async def test_routes_to_download_paper(self, mock_handler: AsyncMock) -> None:
        """verify call_tool routes download_paper to handle_download_paper."""
        mock_handler.return_value = "downloaded"
        args = {"url": "http://x", "journal": "J", "title": "T"}

        result = await call_tool("download_paper", args)

        mock_handler.assert_awaited_once_with(args)
        assert result[0].text == "downloaded"

    @patch("pdf_to_png_converter_mcp.server.handle_download_and_convert", new_callable=AsyncMock)
    async def test_routes_to_download_and_convert(self, mock_handler: AsyncMock) -> None:
        """verify call_tool routes download_and_convert to handle_download_and_convert."""
        mock_handler.return_value = "done"
        args = {"url": "http://x", "journal": "J", "title": "T"}

        result = await call_tool("download_and_convert", args)

        mock_handler.assert_awaited_once_with(args)
        assert result[0].text == "done"

    @patch("pdf_to_png_converter_mcp.server.handle_batch_convert", new_callable=AsyncMock)
    async def test_routes_to_batch_convert(self, mock_handler: AsyncMock) -> None:
        """verify call_tool routes batch_convert_pdfs to handle_batch_convert."""
        mock_handler.return_value = "batch done"
        args = {"folder_path": "/tmp/pdfs"}

        result = await call_tool("batch_convert_pdfs", args)

        mock_handler.assert_awaited_once_with(args)
        assert result[0].text == "batch done"

    @patch("pdf_to_png_converter_mcp.server.handle_convert_pdf", new_callable=AsyncMock)
    async def test_exception_handling(self, mock_handler: AsyncMock) -> None:
        """handler 拋出例外時，call_tool 回傳包含 '錯誤:' 的訊息."""
        mock_handler.side_effect = RuntimeError("boom")

        result = await call_tool("convert_pdf_to_png", {"pdf_path": "x.pdf"})

        assert len(result) == 1
        assert "錯誤:" in result[0].text
        assert "boom" in result[0].text


# ---------------------------------------------------------------------------
# TestHandleConvertPdf
# ---------------------------------------------------------------------------
class TestHandleConvertPdf:
    """測試 handle_convert_pdf."""

    async def test_missing_file(self) -> None:
        """不存在的 PDF 路徑應回傳 '找不到'."""
        result = await handle_convert_pdf({"pdf_path": "/nonexistent/file.pdf"})
        assert "找不到" in result

    async def test_not_pdf_extension(self, tmp_path: Path) -> None:
        """副檔名不是 .pdf 的檔案應回傳 '不是 PDF'."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("hello", encoding="utf-8")

        result = await handle_convert_pdf({"pdf_path": str(txt_file)})
        assert "不是 PDF" in result

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_success(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """成功轉換應回傳 '成功' 和 'PNG'."""
        pdf_file = tmp_path / "sample.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_convert.return_value = [
            tmp_path / "sample-001.png",
            tmp_path / "sample-002.png",
        ]

        result = await handle_convert_pdf({"pdf_path": str(pdf_file)})
        assert "成功" in result
        assert "PNG" in result
        assert "2" in result
        mock_convert.assert_awaited_once()

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_conversion_exception(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """convert_pdf_to_png 拋出 RuntimeError 時，應回傳 '轉換失敗'."""
        pdf_file = tmp_path / "bad.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_convert.side_effect = RuntimeError("poppler not found")

        result = await handle_convert_pdf({"pdf_path": str(pdf_file)})
        assert "轉換失敗" in result
        assert "poppler not found" in result

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_custom_output_dir(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """指定 output_dir 時，應在該目錄建立輸出."""
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        output_dir = tmp_path / "custom_output"

        mock_convert.return_value = [output_dir / "doc-001.png"]

        result = await handle_convert_pdf(
            {
                "pdf_path": str(pdf_file),
                "output_dir": str(output_dir),
            }
        )

        assert "成功" in result
        # 確認 output_dir 被建立
        assert output_dir.exists()
        # 確認 convert_pdf_to_png 收到正確的 output_dir
        call_args = mock_convert.call_args
        assert call_args[0][1] == output_dir


# ---------------------------------------------------------------------------
# TestHandleDownloadPaper
# ---------------------------------------------------------------------------
class TestHandleDownloadPaper:
    """測試 handle_download_paper."""

    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_success(self, mock_dl: AsyncMock, tmp_path: Path) -> None:
        """成功下載應回傳 '成功下載'."""
        mock_dl.return_value = tmp_path / "Nature" / "My Paper" / "My Paper.pdf"

        result = await handle_download_paper(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Nature",
                "title": "My Paper",
                "base_dir": str(tmp_path),
            }
        )

        assert "成功下載" in result
        assert "My Paper" in result
        assert "Nature" in result
        mock_dl.assert_awaited_once()

    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_http_error(self, mock_dl: AsyncMock, tmp_path: Path) -> None:
        """HTTP 錯誤時回傳包含 'HTTP' 的訊息."""
        # 建立 httpx.HTTPStatusError
        request = httpx.Request("GET", "https://example.com/paper.pdf")
        response = httpx.Response(status_code=404, request=request)
        mock_dl.side_effect = httpx.HTTPStatusError("Not Found", request=request, response=response)

        result = await handle_download_paper(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Nature",
                "title": "My Paper",
                "base_dir": str(tmp_path),
            }
        )

        assert "HTTP" in result
        assert "404" in result

    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_generic_error(self, mock_dl: AsyncMock, tmp_path: Path) -> None:
        """一般例外應回傳 '下載失敗'."""
        mock_dl.side_effect = Exception("connection reset")

        result = await handle_download_paper(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Nature",
                "title": "My Paper",
                "base_dir": str(tmp_path),
            }
        )

        assert "下載失敗" in result
        assert "connection reset" in result

    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_sanitizes_filenames(self, mock_dl: AsyncMock, tmp_path: Path) -> None:
        """特殊字元應被清理，目錄與檔名不含非法字元."""
        mock_dl.return_value = tmp_path / "dummy.pdf"

        await handle_download_paper(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Nature: Reviews",
                "title": "Deep Learning? A Survey*",
                "base_dir": str(tmp_path),
            }
        )

        # 確認 download_paper 收到的路徑不含非法字元
        actual_path = mock_dl.call_args[0][1]
        assert ":" not in Path(actual_path).name
        assert "?" not in Path(actual_path).name
        assert "*" not in Path(actual_path).name


# ---------------------------------------------------------------------------
# TestHandleDownloadAndConvert
# ---------------------------------------------------------------------------
class TestHandleDownloadAndConvert:
    """測試 handle_download_and_convert."""

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_success(
        self, mock_dl: AsyncMock, mock_convert: AsyncMock, tmp_path: Path
    ) -> None:
        """下載和轉換都成功時，結果包含兩個 '✓'."""
        mock_dl.return_value = tmp_path / "paper.pdf"
        mock_convert.return_value = [
            tmp_path / "paper-001.png",
            tmp_path / "paper-002.png",
        ]

        result = await handle_download_and_convert(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Science",
                "title": "TestPaper",
                "base_dir": str(tmp_path),
            }
        )

        assert result.count("✓") == 2
        assert "成功下載" in result
        assert "成功轉換" in result
        mock_dl.assert_awaited_once()
        mock_convert.assert_awaited_once()

    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_download_fails(self, mock_dl: AsyncMock, tmp_path: Path) -> None:
        """下載失敗時直接回傳 '下載失敗'，不繼續轉換."""
        mock_dl.side_effect = Exception("network error")

        result = await handle_download_and_convert(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Science",
                "title": "TestPaper",
                "base_dir": str(tmp_path),
            }
        )

        assert "下載失敗" in result

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    @patch("pdf_to_png_converter_mcp.server.download_paper", new_callable=AsyncMock)
    async def test_convert_fails_after_download(
        self, mock_dl: AsyncMock, mock_convert: AsyncMock, tmp_path: Path
    ) -> None:
        """下載成功但轉換失敗時，結果包含 '✓' 下載 和 '✗' 轉換."""
        mock_dl.return_value = tmp_path / "paper.pdf"
        mock_convert.side_effect = RuntimeError("poppler crashed")

        result = await handle_download_and_convert(
            {
                "url": "https://example.com/paper.pdf",
                "journal": "Science",
                "title": "TestPaper",
                "base_dir": str(tmp_path),
            }
        )

        assert "✓" in result  # 下載成功
        assert "✗" in result  # 轉換失敗
        assert "轉換失敗" in result


# ---------------------------------------------------------------------------
# TestHandleBatchConvert
# ---------------------------------------------------------------------------
class TestHandleBatchConvert:
    """測試 handle_batch_convert."""

    async def test_folder_not_found(self) -> None:
        """不存在的資料夾應回傳 '找不到資料夾'."""
        result = await handle_batch_convert({"folder_path": "/nonexistent/folder"})
        assert "找不到資料夾" in result

    async def test_not_a_directory(self, tmp_path: Path) -> None:
        """傳入檔案路徑而非資料夾應回傳 '不是資料夾'."""
        file_path = tmp_path / "dummy.txt"
        file_path.write_text("hello", encoding="utf-8")

        result = await handle_batch_convert({"folder_path": str(file_path)})
        assert "不是資料夾" in result

    async def test_no_pdfs_found(self, tmp_path: Path) -> None:
        """空資料夾應回傳 '找不到任何 PDF'."""
        result = await handle_batch_convert({"folder_path": str(tmp_path)})
        assert "找不到任何 PDF" in result

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_batch_success(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """兩個 PDF 都成功轉換時，結果顯示成功數量為 2."""
        pdf1 = tmp_path / "a.pdf"
        pdf2 = tmp_path / "b.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")
        pdf2.write_bytes(b"%PDF-1.4 fake")

        mock_convert.return_value = [Path("dummy-001.png")]

        result = await handle_batch_convert({"folder_path": str(tmp_path)})

        assert "2/2" in result
        assert mock_convert.await_count == 2

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_batch_partial_failure(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """一個成功一個失敗時，結果顯示 1/2."""
        pdf1 = tmp_path / "good.pdf"
        pdf2 = tmp_path / "bad.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")
        pdf2.write_bytes(b"%PDF-1.4 fake")

        # 第一次呼叫成功，第二次拋出例外
        mock_convert.side_effect = [
            [Path("good-001.png")],
            RuntimeError("conversion failed"),
        ]

        result = await handle_batch_convert({"folder_path": str(tmp_path)})

        assert "1/2" in result
        assert "✓" in result
        assert "✗" in result

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_non_recursive(self, mock_convert: AsyncMock, tmp_path: Path) -> None:
        """recursive=False 時，子資料夾中的 PDF 不被搜尋."""
        subfolder = tmp_path / "sub"
        subfolder.mkdir()
        pdf_in_sub = subfolder / "hidden.pdf"
        pdf_in_sub.write_bytes(b"%PDF-1.4 fake")

        result = await handle_batch_convert(
            {
                "folder_path": str(tmp_path),
                "recursive": False,
            }
        )

        assert "找不到任何 PDF" in result
        mock_convert.assert_not_awaited()

    @patch("pdf_to_png_converter_mcp.server.convert_pdf_to_png", new_callable=AsyncMock)
    async def test_recursive_finds_subfolder_pdfs(
        self, mock_convert: AsyncMock, tmp_path: Path
    ) -> None:
        """recursive=True（預設）時，子資料夾中的 PDF 也被搜尋."""
        subfolder = tmp_path / "sub"
        subfolder.mkdir()
        pdf_in_sub = subfolder / "nested.pdf"
        pdf_in_sub.write_bytes(b"%PDF-1.4 fake")

        mock_convert.return_value = [Path("nested-001.png")]

        result = await handle_batch_convert({"folder_path": str(tmp_path)})

        assert "1/1" in result
        mock_convert.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestHandleSearchPaper
# ---------------------------------------------------------------------------
class TestHandleSearchPaper:
    """測試 handle_search_paper."""

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_success(self, mock_search: AsyncMock) -> None:
        """搜尋到結果時，回傳包含論文標題的格式化文字."""
        mock_search.return_value = [
            {
                "title": "Attention Is All You Need",
                "authors": "Vaswani, Shazeer, Parmar",
                "year": "2017",
                "venue": "NeurIPS",
                "pdf_url": "https://example.com/paper.pdf",
            },
        ]

        result = await handle_search_paper({"query": "transformer"})

        assert "Attention Is All You Need" in result
        assert "Vaswani" in result
        assert "2017" in result
        assert "NeurIPS" in result
        assert "transformer" in result
        mock_search.assert_awaited_once_with("transformer", 5)

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_no_results(self, mock_search: AsyncMock) -> None:
        """搜尋無結果時回傳 '找不到'."""
        mock_search.return_value = []

        result = await handle_search_paper({"query": "xyznonexistent"})

        assert "找不到" in result

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_search_error(self, mock_search: AsyncMock) -> None:
        """搜尋拋出例外時回傳 '搜尋失敗'."""
        mock_search.side_effect = Exception("API timeout")

        result = await handle_search_paper({"query": "deep learning"})

        assert "搜尋失敗" in result
        assert "API timeout" in result

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_custom_max_results(self, mock_search: AsyncMock) -> None:
        """指定 max_results 時，正確傳遞給 search_paper."""
        mock_search.return_value = []

        await handle_search_paper({"query": "GAN", "max_results": 10})

        mock_search.assert_awaited_once_with("GAN", 10)

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_multiple_results_formatted(self, mock_search: AsyncMock) -> None:
        """多筆結果時，每篇論文都被格式化輸出."""
        mock_search.return_value = [
            {
                "title": "Paper A",
                "authors": "Author A",
                "year": "2023",
                "venue": "ICML",
                "pdf_url": "https://example.com/a.pdf",
            },
            {
                "title": "Paper B",
                "authors": "Author B",
                "year": "2024",
                "venue": "",
                "pdf_url": "",
            },
        ]

        result = await handle_search_paper({"query": "test"})

        assert "Paper A" in result
        assert "Paper B" in result
        assert "2 篇" in result
        assert "ICML" in result
        # Paper B has no venue and no pdf_url — they should not appear
        # (the handler only prints them if truthy)

    @patch("pdf_to_png_converter_mcp.server.search_paper", new_callable=AsyncMock)
    async def test_paper_without_optional_fields(self, mock_search: AsyncMock) -> None:
        """論文缺少 year, venue, pdf_url 等可選欄位時仍正常格式化."""
        mock_search.return_value = [
            {
                "title": "Minimal Paper",
                "authors": "Someone",
                "year": "",
                "venue": "",
                "pdf_url": "",
            },
        ]

        result = await handle_search_paper({"query": "minimal"})

        assert "Minimal Paper" in result
        assert "Someone" in result
        # year, venue, pdf_url are empty => not printed
        assert "年份" not in result
        assert "期刊" not in result
        assert "PDF" not in result

"""Tests for MCP server functionality."""

from __future__ import annotations

import pytest

from pdf_to_png_converter_mcp.server import sanitize_filename


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


class TestServerTools:
    """測試 MCP 服務器工具列表."""

    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        """測試工具列表."""
        from pdf_to_png_converter_mcp.server import list_tools

        tools = await list_tools()
        tool_names = {tool.name for tool in tools}

        assert "convert_pdf_to_png" in tool_names
        assert "download_paper" in tool_names
        assert "download_and_convert" in tool_names
        assert "batch_convert_pdfs" in tool_names

    @pytest.mark.asyncio
    async def test_tool_schemas(self) -> None:
        """測試工具 schema 格式正確."""
        from pdf_to_png_converter_mcp.server import list_tools

        tools = await list_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

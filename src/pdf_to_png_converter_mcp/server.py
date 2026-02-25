"""MCP Server for PDF to PNG conversion and paper management."""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .converter import convert_pdf_to_png
from .downloader import download_paper, search_paper

# 設定 UTF-8 編碼
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("pdf-to-png-mcp")

# 創建 MCP 服務器
server = Server("pdf-to-png-converter")


def sanitize_filename(name: str) -> str:
    """清理檔案名稱，移除不合法字元."""
    # 移除或替換不合法字元
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", name)
    # 移除前後空白和點
    sanitized = sanitized.strip(" .")
    # 限制長度
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized or "unnamed"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具."""
    return [
        Tool(
            name="convert_pdf_to_png",
            description=(
                "將 PDF 檔案轉換為高品質 PNG 圖片。"
                "支援自訂 DPI（預設 1200），輸出圖片會放在與 PDF 相同的目錄。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDF 檔案的完整路徑",
                    },
                    "dpi": {
                        "type": "integer",
                        "description": "輸出解析度（DPI），預設 1200",
                        "default": 1200,
                        "minimum": 72,
                        "maximum": 2400,
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "輸出目錄（可選，預設與 PDF 同目錄）",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="download_paper",
            description=("從網路下載學術論文 PDF。會根據期刊名稱和論文標題自動建立資料夾結構。"),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "論文 PDF 的下載網址",
                    },
                    "journal": {
                        "type": "string",
                        "description": "期刊名稱（用於建立資料夾）",
                    },
                    "title": {
                        "type": "string",
                        "description": "論文標題（用於命名檔案和資料夾）",
                    },
                    "base_dir": {
                        "type": "string",
                        "description": "基礎目錄（可選，預設為當前目錄）",
                    },
                },
                "required": ["url", "journal", "title"],
            },
        ),
        Tool(
            name="download_and_convert",
            description=(
                "下載學術論文 PDF 並自動轉換為高品質 PNG 圖片。"
                "會根據期刊名稱和論文標題自動建立資料夾結構，"
                "並將 PDF 和 PNG 都放在該資料夾中。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "論文 PDF 的下載網址",
                    },
                    "journal": {
                        "type": "string",
                        "description": "期刊名稱（用於建立資料夾）",
                    },
                    "title": {
                        "type": "string",
                        "description": "論文標題（用於命名檔案和資料夾）",
                    },
                    "base_dir": {
                        "type": "string",
                        "description": "基礎目錄（可選，預設為當前目錄）",
                    },
                    "dpi": {
                        "type": "integer",
                        "description": "輸出解析度（DPI），預設 1200",
                        "default": 1200,
                        "minimum": 72,
                        "maximum": 2400,
                    },
                },
                "required": ["url", "journal", "title"],
            },
        ),
        Tool(
            name="batch_convert_pdfs",
            description=("批次轉換資料夾中的所有 PDF 檔案為 PNG 圖片。支援遞迴搜尋子資料夾。"),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "包含 PDF 檔案的資料夾路徑",
                    },
                    "dpi": {
                        "type": "integer",
                        "description": "輸出解析度（DPI），預設 1200",
                        "default": 1200,
                        "minimum": 72,
                        "maximum": 2400,
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否遞迴搜尋子資料夾，預設 True",
                        "default": True,
                    },
                },
                "required": ["folder_path"],
            },
        ),
        Tool(
            name="search_paper",
            description=(
                "搜尋學術論文（使用 Semantic Scholar API）。"
                "根據關鍵字搜尋論文，返回標題、作者、年份、期刊和 PDF 連結。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜尋關鍵字",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大結果數量，預設 5",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """執行指定的工具."""
    logger.info(f"執行工具: {name}，參數: {arguments}")

    try:
        if name == "convert_pdf_to_png":
            result = await handle_convert_pdf(arguments)
        elif name == "download_paper":
            result = await handle_download_paper(arguments)
        elif name == "download_and_convert":
            result = await handle_download_and_convert(arguments)
        elif name == "batch_convert_pdfs":
            result = await handle_batch_convert(arguments)
        elif name == "search_paper":
            result = await handle_search_paper(arguments)
        else:
            result = f"未知的工具: {name}"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.exception(f"工具執行失敗: {name}")
        return [TextContent(type="text", text=f"錯誤: {e!s}")]


async def handle_convert_pdf(arguments: dict[str, Any]) -> str:
    """處理 PDF 轉換請求."""
    pdf_path = Path(arguments["pdf_path"])
    dpi = arguments.get("dpi", 1200)
    output_dir = arguments.get("output_dir")

    if not pdf_path.exists():
        return f"錯誤: 找不到 PDF 檔案: {pdf_path}"

    if pdf_path.suffix.lower() != ".pdf":
        return f"錯誤: 檔案不是 PDF: {pdf_path}"

    output_path = Path(output_dir) if output_dir else pdf_path.parent
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        png_files = await convert_pdf_to_png(pdf_path, output_path, dpi)
        return (
            f"成功將 {pdf_path.name} 轉換為 {len(png_files)} 個 PNG 檔案\n"
            f"輸出目錄: {output_path}\n"
            f"DPI: {dpi}"
        )
    except Exception as e:
        return f"轉換失敗: {e!s}"


async def handle_download_paper(arguments: dict[str, Any]) -> str:
    """處理論文下載請求."""
    url = arguments["url"]
    journal = sanitize_filename(arguments["journal"])
    title = sanitize_filename(arguments["title"])
    base_dir = Path(arguments.get("base_dir", "."))

    # 建立目錄結構: base_dir/journal/title/
    paper_dir = base_dir / journal / title
    paper_dir.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"{title}.pdf"
    pdf_path = paper_dir / pdf_filename

    try:
        await download_paper(url, pdf_path)
        return f"成功下載論文\n標題: {title}\n期刊: {journal}\n儲存位置: {pdf_path}"
    except httpx.HTTPStatusError as e:
        return f"下載失敗 (HTTP {e.response.status_code}): {e!s}"
    except Exception as e:
        return f"下載失敗: {e!s}"


async def handle_download_and_convert(arguments: dict[str, Any]) -> str:
    """處理下載並轉換請求."""
    url = arguments["url"]
    journal = sanitize_filename(arguments["journal"])
    title = sanitize_filename(arguments["title"])
    base_dir = Path(arguments.get("base_dir", "."))
    dpi = arguments.get("dpi", 1200)

    # 建立目錄結構
    paper_dir = base_dir / journal / title
    paper_dir.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"{title}.pdf"
    pdf_path = paper_dir / pdf_filename

    results = []

    # 下載 PDF
    try:
        await download_paper(url, pdf_path)
        results.append(f"✓ 成功下載論文: {pdf_path}")
    except Exception as e:
        return f"下載失敗: {e!s}"

    # 轉換為 PNG
    try:
        png_files = await convert_pdf_to_png(pdf_path, paper_dir, dpi)
        results.append(f"✓ 成功轉換為 {len(png_files)} 個 PNG 檔案")
    except Exception as e:
        results.append(f"✗ 轉換失敗: {e!s}")

    return (
        f"處理完成\n"
        f"標題: {title}\n"
        f"期刊: {journal}\n"
        f"目錄: {paper_dir}\n"
        f"DPI: {dpi}\n"
        f"結果:\n" + "\n".join(results)
    )


async def handle_batch_convert(arguments: dict[str, Any]) -> str:
    """處理批次轉換請求."""
    folder_path = Path(arguments["folder_path"])
    dpi = arguments.get("dpi", 1200)
    recursive = arguments.get("recursive", True)

    if not folder_path.exists():
        return f"錯誤: 找不到資料夾: {folder_path}"

    if not folder_path.is_dir():
        return f"錯誤: 路徑不是資料夾: {folder_path}"

    # 搜尋 PDF 檔案
    if recursive:
        pdf_files = list(folder_path.rglob("*.pdf"))
    else:
        pdf_files = list(folder_path.glob("*.pdf"))

    if not pdf_files:
        return f"在 {folder_path} 中找不到任何 PDF 檔案"

    results = []
    success_count = 0

    for pdf_path in pdf_files:
        try:
            png_files = await convert_pdf_to_png(pdf_path, pdf_path.parent, dpi)
            results.append(f"✓ {pdf_path.name}: {len(png_files)} 個 PNG")
            success_count += 1
        except Exception as e:
            results.append(f"✗ {pdf_path.name}: {e!s}")

    return (
        f"批次轉換完成\n"
        f"成功: {success_count}/{len(pdf_files)}\n"
        f"DPI: {dpi}\n"
        f"詳細結果:\n" + "\n".join(results)
    )


async def handle_search_paper(arguments: dict[str, Any]) -> str:
    """處理論文搜尋請求."""
    query = arguments["query"]
    max_results = arguments.get("max_results", 5)

    try:
        results = await search_paper(query, max_results)

        if not results:
            return f"找不到與 '{query}' 相關的論文"

        lines = [f"搜尋 '{query}' 的結果（{len(results)} 篇）:\n"]
        for i, paper in enumerate(results, 1):
            lines.append(f"{i}. {paper['title']}")
            lines.append(f"   作者: {paper['authors']}")
            if paper.get("year"):
                lines.append(f"   年份: {paper['year']}")
            if paper.get("venue"):
                lines.append(f"   期刊: {paper['venue']}")
            if paper.get("pdf_url"):
                lines.append(f"   PDF: {paper['pdf_url']}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"搜尋失敗: {e!s}"


def main() -> None:
    """啟動 MCP 服務器."""
    logger.info("啟動 PDF to PNG MCP 服務器...")

    async def run_server() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(run_server())


if __name__ == "__main__":
    main()

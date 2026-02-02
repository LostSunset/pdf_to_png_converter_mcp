"""PDF to PNG conversion module."""

from __future__ import annotations

import asyncio
import functools
import logging
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PIL.Image import Image

logger = logging.getLogger("pdf-to-png-mcp.converter")

# Windows-specific flag for hiding console window
_CREATION_FLAGS: int = 0
if sys.platform == "win32":
    _CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


async def convert_pdf_to_png(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 1200,
) -> list[Path]:
    """將 PDF 檔案轉換為 PNG 圖片.

    Args:
        pdf_path: PDF 檔案路徑
        output_dir: 輸出目錄
        dpi: 輸出解析度（DPI）

    Returns:
        生成的 PNG 檔案路徑列表

    Raises:
        FileNotFoundError: 找不到 PDF 檔案或 pdftoppm/poppler
        RuntimeError: 轉換過程中發生錯誤
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF 檔案: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_base = output_dir / pdf_path.stem

    # 嘗試使用 pdf2image（Python 套件）或 pdftoppm（命令列工具）
    try:
        return await _convert_with_pdf2image(pdf_path, output_dir, dpi)
    except ImportError:
        logger.info("pdf2image 不可用，嘗試使用 pdftoppm")
    except Exception as e:
        logger.warning(f"pdf2image 轉換失敗: {e}，嘗試使用 pdftoppm")

    return await _convert_with_pdftoppm(pdf_path, output_base, dpi)


def _save_image(image: Image, path: Path) -> None:
    """Save image to file."""
    image.save(str(path), "PNG")


async def _convert_with_pdf2image(
    pdf_path: Path,
    output_dir: Path,
    dpi: int,
) -> list[Path]:
    """使用 pdf2image 套件轉換 PDF."""
    from pdf2image import convert_from_path

    # 在執行緒池中執行以避免阻塞
    loop = asyncio.get_event_loop()
    images: list[Any] = await loop.run_in_executor(
        None,
        functools.partial(convert_from_path, str(pdf_path), dpi=dpi),
    )

    png_files: list[Path] = []
    for i, image in enumerate(images, start=1):
        output_path = output_dir / f"{pdf_path.stem}-{i:03d}.png"
        await loop.run_in_executor(
            None,
            functools.partial(_save_image, image, output_path),
        )
        png_files.append(output_path)
        logger.info(f"已生成: {output_path.name}")

    return png_files


async def _convert_with_pdftoppm(
    pdf_path: Path,
    output_base: Path,
    dpi: int,
) -> list[Path]:
    """使用 pdftoppm 命令列工具轉換 PDF."""
    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        str(pdf_path),
        str(output_base),
    ]

    # 建立 subprocess 參數
    kwargs: dict[str, Any] = {
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
    }

    # 在 Windows 上隱藏命令視窗
    if sys.platform == "win32":
        kwargs["creationflags"] = _CREATION_FLAGS

    process = await asyncio.create_subprocess_exec(*cmd, **kwargs)

    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace").strip()
        if "not found" in error_msg.lower() or process.returncode == 1:
            raise FileNotFoundError(
                "找不到 pdftoppm 工具。請安裝 poppler-utils:\n"
                "  - Windows: 下載 poppler 並加入 PATH\n"
                "  - macOS: brew install poppler\n"
                "  - Linux: sudo apt install poppler-utils"
            )
        raise RuntimeError(f"pdftoppm 轉換失敗: {error_msg}")

    # 搜尋生成的 PNG 檔案
    output_dir = output_base.parent
    pattern = f"{output_base.name}*.png"
    png_files = sorted(output_dir.glob(pattern))

    if not png_files:
        raise RuntimeError("轉換完成但找不到輸出的 PNG 檔案")

    for png_file in png_files:
        logger.info(f"已生成: {png_file.name}")

    return png_files

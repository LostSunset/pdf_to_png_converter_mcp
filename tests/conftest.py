"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 確保 UTF-8 編碼
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """提供測試用的臨時目錄."""
    return tmp_path


@pytest.fixture
def sample_pdf_content() -> bytes:
    """提供一個最小的 PDF 內容（用於模擬）."""
    # 這是一個最小的有效 PDF
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
170
%%EOF"""


@pytest.fixture
def sample_pdf(temp_dir: Path, sample_pdf_content: bytes) -> Path:
    """創建一個測試用的 PDF 檔案."""
    pdf_path = temp_dir / "測試文件.pdf"  # 使用中文檔名測試 UTF-8
    pdf_path.write_bytes(sample_pdf_content)
    return pdf_path

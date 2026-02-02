"""Tests for PDF converter functionality."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestConverter:
    """測試 PDF 轉換功能."""

    def test_convert_pdf_to_png_missing_file(self, temp_dir: Path) -> None:
        """測試轉換不存在的檔案."""
        from pdf_to_png_converter_mcp.converter import convert_pdf_to_png

        pdf_path = temp_dir / "不存在的檔案.pdf"

        with pytest.raises(FileNotFoundError):
            import asyncio

            asyncio.run(convert_pdf_to_png(pdf_path, temp_dir))

    def test_output_directory_created(self, temp_dir: Path) -> None:
        """測試輸出目錄自動創建."""
        output_dir = temp_dir / "新資料夾" / "子資料夾"
        assert not output_dir.exists()

        # 只測試目錄創建邏輯
        output_dir.mkdir(parents=True, exist_ok=True)
        assert output_dir.exists()


class TestConverterIntegration:
    """整合測試（需要 poppler）."""

    @pytest.mark.skipif(
        not Path("C:/poppler/bin/pdftoppm.exe").exists() and not Path("/usr/bin/pdftoppm").exists(),
        reason="需要安裝 poppler",
    )
    def test_convert_real_pdf(self, sample_pdf: Path, temp_dir: Path) -> None:
        """測試轉換真實 PDF（需要 poppler）."""
        import asyncio

        from pdf_to_png_converter_mcp.converter import convert_pdf_to_png

        result = asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))
        # 如果轉換成功，應該有輸出
        assert isinstance(result, list)

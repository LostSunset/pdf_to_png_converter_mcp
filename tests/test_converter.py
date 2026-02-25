"""Tests for PDF converter functionality."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pdf_to_png_converter_mcp.converter import (
    _convert_with_pdf2image,
    _convert_with_pdftoppm,
    _save_image,
    convert_pdf_to_png,
)


class TestConvertPdfToPng:
    """Tests for the main convert_pdf_to_png function."""

    def test_file_not_found(self, temp_dir: Path) -> None:
        """Non-existent PDF raises FileNotFoundError."""
        pdf_path = temp_dir / "不存在的檔案.pdf"

        with pytest.raises(FileNotFoundError, match="找不到 PDF 檔案"):
            asyncio.run(convert_pdf_to_png(pdf_path, temp_dir))

    def test_creates_output_dir(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Output directory is created automatically when it does not exist."""
        output_dir = temp_dir / "新資料夾" / "子資料夾"
        assert not output_dir.exists()

        expected_paths = [Path("page-001.png")]

        with patch(
            "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
            new_callable=AsyncMock,
            return_value=expected_paths,
        ):
            asyncio.run(convert_pdf_to_png(sample_pdf, output_dir))

        assert output_dir.exists()

    def test_pdf2image_success(self, sample_pdf: Path, temp_dir: Path) -> None:
        """When pdf2image succeeds, its result is returned directly."""
        expected_paths = [
            temp_dir / "測試文件-001.png",
            temp_dir / "測試文件-002.png",
        ]

        with patch(
            "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
            new_callable=AsyncMock,
            return_value=expected_paths,
        ):
            result = asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))

        assert result == expected_paths

    def test_fallback_on_import_error(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Falls back to pdftoppm when pdf2image raises ImportError."""
        fallback_paths = [temp_dir / "測試文件-01.png"]

        with (
            patch(
                "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
                new_callable=AsyncMock,
                side_effect=ImportError("No module named 'pdf2image'"),
            ),
            patch(
                "pdf_to_png_converter_mcp.converter._convert_with_pdftoppm",
                new_callable=AsyncMock,
                return_value=fallback_paths,
            ) as mock_pdftoppm,
        ):
            result = asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))

        assert result == fallback_paths
        mock_pdftoppm.assert_awaited_once()

    def test_fallback_on_generic_error(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Falls back to pdftoppm when pdf2image raises a generic Exception."""
        fallback_paths = [temp_dir / "測試文件-01.png"]

        with (
            patch(
                "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
                new_callable=AsyncMock,
                side_effect=RuntimeError("pdf2image conversion failed"),
            ),
            patch(
                "pdf_to_png_converter_mcp.converter._convert_with_pdftoppm",
                new_callable=AsyncMock,
                return_value=fallback_paths,
            ) as mock_pdftoppm,
        ):
            result = asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))

        assert result == fallback_paths
        mock_pdftoppm.assert_awaited_once()

    def test_default_dpi(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Default DPI value of 1200 is passed to the converter."""
        with patch(
            "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_pdf2image:
            asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))

        mock_pdf2image.assert_awaited_once_with(sample_pdf, temp_dir, 1200)

    def test_custom_dpi(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Custom DPI value is forwarded to the converter."""
        with patch(
            "pdf_to_png_converter_mcp.converter._convert_with_pdf2image",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_pdf2image:
            asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir, dpi=300))

        mock_pdf2image.assert_awaited_once_with(sample_pdf, temp_dir, 300)


class TestSaveImage:
    """Tests for the _save_image helper function."""

    def test_save_image(self, temp_dir: Path) -> None:
        """Image.save is called with the string path and PNG format."""
        mock_image = MagicMock()
        output_path = temp_dir / "output.png"

        _save_image(mock_image, output_path)

        mock_image.save.assert_called_once_with(str(output_path), "PNG")

    def test_save_image_unicode_path(self, temp_dir: Path) -> None:
        """Image.save works with Unicode (Chinese) file paths."""
        mock_image = MagicMock()
        output_path = temp_dir / "測試圖片-001.png"

        _save_image(mock_image, output_path)

        mock_image.save.assert_called_once_with(str(output_path), "PNG")


class TestConvertWithPdf2image:
    """Tests for _convert_with_pdf2image."""

    @staticmethod
    def _patch_pdf2image(mock_convert_from_path: MagicMock):
        """Create a mock pdf2image module and inject it into sys.modules.

        The function under test does ``from pdf2image import convert_from_path``
        inside its body. We need a fake ``pdf2image`` module in sys.modules so
        that import resolves to our mock.
        """
        import types

        fake_module = types.ModuleType("pdf2image")
        fake_module.convert_from_path = mock_convert_from_path  # type: ignore[attr-defined]
        return patch.dict("sys.modules", {"pdf2image": fake_module})

    def test_success(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Returns correct output paths when convert_from_path succeeds."""
        mock_img1 = MagicMock()
        mock_img2 = MagicMock()
        mock_cfp = MagicMock(return_value=[mock_img1, mock_img2])

        with self._patch_pdf2image(mock_cfp):
            result = asyncio.run(_convert_with_pdf2image(sample_pdf, temp_dir, 1200))

        assert len(result) == 2
        assert result[0] == temp_dir / "測試文件-001.png"
        assert result[1] == temp_dir / "測試文件-002.png"

    def test_output_file_naming(self, temp_dir: Path) -> None:
        """Output files are named {stem}-{NNN}.png with zero-padded indices."""
        pdf_path = temp_dir / "my-document.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 minimal")

        mock_images = [MagicMock() for _ in range(3)]
        mock_cfp = MagicMock(return_value=mock_images)

        with self._patch_pdf2image(mock_cfp):
            result = asyncio.run(_convert_with_pdf2image(pdf_path, temp_dir, 300))

        assert len(result) == 3
        assert result[0].name == "my-document-001.png"
        assert result[1].name == "my-document-002.png"
        assert result[2].name == "my-document-003.png"

    def test_calls_save_image_for_each_page(self, sample_pdf: Path, temp_dir: Path) -> None:
        """_save_image is called once per page image."""
        mock_images = [MagicMock() for _ in range(2)]
        mock_cfp = MagicMock(return_value=mock_images)

        with (
            self._patch_pdf2image(mock_cfp),
            patch(
                "pdf_to_png_converter_mcp.converter._save_image",
            ) as mock_save,
        ):
            asyncio.run(_convert_with_pdf2image(sample_pdf, temp_dir, 1200))

        assert mock_save.call_count == 2

    def test_import_error_propagates(self, sample_pdf: Path, temp_dir: Path) -> None:
        """ImportError from pdf2image import propagates to caller."""
        # Setting sys.modules["pdf2image"] = None causes ``from pdf2image import ...``
        # to raise ImportError, simulating the package not being installed.
        with patch.dict("sys.modules", {"pdf2image": None}), pytest.raises(ImportError):
            asyncio.run(_convert_with_pdf2image(sample_pdf, temp_dir, 1200))


class TestConvertWithPdftoppm:
    """Tests for _convert_with_pdftoppm."""

    def _make_mock_process(
        self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""
    ) -> AsyncMock:
        """Create a mock async subprocess with given returncode and output."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(stdout, stderr))
        mock_proc.returncode = returncode
        return mock_proc

    def test_success(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Returns sorted PNG file paths on successful conversion."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(returncode=0)

        # Pre-create fake PNG output files that pdftoppm would generate
        png1 = temp_dir / f"{sample_pdf.stem}-01.png"
        png2 = temp_dir / f"{sample_pdf.stem}-02.png"
        png1.write_bytes(b"fake png 1")
        png2.write_bytes(b"fake png 2")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

        assert len(result) == 2
        assert result[0] == png1
        assert result[1] == png2

    def test_pdftoppm_not_found_via_stderr(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Raises FileNotFoundError when stderr contains 'not found'."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(
            returncode=127,
            stderr=b"pdftoppm: command not found",
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(FileNotFoundError, match="找不到 pdftoppm 工具"),
        ):
            asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

    def test_pdftoppm_not_found_via_returncode_1(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Raises FileNotFoundError when returncode is 1 (even without 'not found' in stderr)."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(
            returncode=1,
            stderr=b"some generic error",
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(FileNotFoundError, match="找不到 pdftoppm 工具"),
        ):
            asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

    def test_pdftoppm_runtime_error(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Raises RuntimeError for non-zero returncode that is not 1 and has no 'not found'."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(
            returncode=2,
            stderr=b"some other error occurred",
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(RuntimeError, match="pdftoppm 轉換失敗"),
        ):
            asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

    def test_no_output_files(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Raises RuntimeError when process succeeds but no PNG files are found."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(returncode=0)

        # Do NOT create any PNG files, simulating a successful exit but no output
        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(RuntimeError, match="找不到輸出"),
        ):
            asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

    def test_command_arguments(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Verifies the correct command-line arguments are passed to pdftoppm."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(returncode=0)

        # Create a PNG file so the function does not raise RuntimeError
        png = temp_dir / f"{sample_pdf.stem}-1.png"
        png.write_bytes(b"fake png")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 600))

        # Verify the positional arguments: pdftoppm -png -r <dpi> <pdf_path> <output_base>
        call_args = mock_exec.call_args
        positional = call_args.args
        assert positional[0] == "pdftoppm"
        assert positional[1] == "-png"
        assert positional[2] == "-r"
        assert positional[3] == "600"
        assert positional[4] == str(sample_pdf)
        assert positional[5] == str(output_base)

    def test_output_sorted(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Output PNG files are returned in sorted order."""
        output_base = temp_dir / sample_pdf.stem
        mock_proc = self._make_mock_process(returncode=0)

        # Create files in reverse order to ensure sorting works
        for i in [3, 1, 2]:
            png = temp_dir / f"{sample_pdf.stem}-{i:02d}.png"
            png.write_bytes(b"fake png")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = asyncio.run(_convert_with_pdftoppm(sample_pdf, output_base, 1200))

        assert len(result) == 3
        names = [p.name for p in result]
        assert names == sorted(names)


class TestConverterIntegration:
    """Integration tests (require poppler)."""

    @pytest.mark.skipif(
        not Path("C:/poppler/bin/pdftoppm.exe").exists() and not Path("/usr/bin/pdftoppm").exists(),
        reason="需要安裝 poppler",
    )
    def test_convert_real_pdf(self, sample_pdf: Path, temp_dir: Path) -> None:
        """Convert a real PDF file (requires poppler to be installed)."""
        result = asyncio.run(convert_pdf_to_png(sample_pdf, temp_dir))
        assert isinstance(result, list)

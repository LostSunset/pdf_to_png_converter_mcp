"""PDF to PNG Converter GUI.

使用 PySide6 建立 GUI，將資料夾內的 PDF 檔案轉換成 PNG。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Windows-specific flag for hiding console window
_CREATION_FLAGS: int = 0
if sys.platform == "win32":
    _CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


class ConvertWorker(QThread):
    """背景執行緒處理 PDF 轉換."""

    progress = Signal(int, int)  # current, total
    log = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, pdf_files: list[Path], dpi: int = 1200) -> None:
        super().__init__()
        self.pdf_files = pdf_files
        self.dpi = dpi
        self.is_cancelled = False

    def run(self) -> None:
        try:
            if not self.pdf_files:
                self.finished_signal.emit(False, "找不到任何 PDF 檔案")
                return

            total = len(self.pdf_files)
            self.log.emit(f"共 {total} 個 PDF 檔案待轉換")

            success_count = 0
            for i, pdf_path in enumerate(self.pdf_files):
                if self.is_cancelled:
                    self.finished_signal.emit(False, "轉換已取消")
                    return

                self.progress.emit(i + 1, total)
                self.log.emit(f"正在轉換: {pdf_path.name}")

                try:
                    output_base = pdf_path.parent / pdf_path.stem

                    cmd = [
                        "pdftoppm",
                        "-png",
                        "-r",
                        str(self.dpi),
                        str(pdf_path),
                        str(output_base),
                    ]

                    kwargs: dict[str, Any] = {
                        "capture_output": True,
                        "text": True,
                    }
                    if sys.platform == "win32":
                        kwargs["creationflags"] = _CREATION_FLAGS

                    result = subprocess.run(cmd, **kwargs)

                    if result.returncode == 0:
                        self.log.emit(f"✓ 成功: {pdf_path.name}")
                        success_count += 1
                    else:
                        self.log.emit(f"✗ 失敗: {pdf_path.name}")
                        if result.stderr:
                            self.log.emit(f"  錯誤: {result.stderr.strip()}")

                except FileNotFoundError:
                    self.log.emit("✗ 錯誤: 找不到 pdftoppm，請確認已安裝 poppler-utils")
                    self.finished_signal.emit(False, "找不到 pdftoppm 工具")
                    return
                except Exception as e:
                    self.log.emit(f"✗ 錯誤: {e!s}")

            self.finished_signal.emit(True, f"完成！成功轉換 {success_count}/{total} 個檔案")

        except Exception as e:
            self.finished_signal.emit(False, f"發生錯誤: {e!s}")

    def cancel(self) -> None:
        self.is_cancelled = True


class PDFConverterWindow(QMainWindow):
    """PDF 轉換器主視窗."""

    def __init__(self) -> None:
        super().__init__()
        self.worker: ConvertWorker | None = None
        self.selected_files: list[Path] = []
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle("PDF to PNG 轉換器")
        self.setMinimumSize(700, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 檔案選擇區域
        select_group = QGroupBox("選擇 PDF 來源")
        select_layout = QVBoxLayout(select_group)

        btn_row = QHBoxLayout()

        self.browse_folder_btn = QPushButton("📁 選擇資料夾")
        self.browse_folder_btn.clicked.connect(self.browse_folder)
        self.browse_folder_btn.setToolTip("選擇資料夾，將自動掃描所有 PDF 檔案（含子資料夾）")
        btn_row.addWidget(self.browse_folder_btn)

        self.browse_files_btn = QPushButton("📄 選擇檔案")
        self.browse_files_btn.clicked.connect(self.browse_files)
        self.browse_files_btn.setToolTip("選擇一個或多個 PDF 檔案")
        btn_row.addWidget(self.browse_files_btn)

        self.clear_btn = QPushButton("🗑️ 清除列表")
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setToolTip("清除已選擇的檔案")
        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()
        select_layout.addLayout(btn_row)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setMinimumHeight(120)
        self.file_list.setToolTip("已選擇的 PDF 檔案（可選取後按 Delete 移除）")
        select_layout.addWidget(self.file_list)

        self.file_count_label = QLabel("已選擇 0 個檔案")
        select_layout.addWidget(self.file_count_label)

        layout.addWidget(select_group)

        # DPI 設定區域
        settings_group = QGroupBox("設定")
        settings_layout = QHBoxLayout(settings_group)

        settings_layout.addWidget(QLabel("DPI:"))
        self.dpi_spinbox = QSpinBox()
        self.dpi_spinbox.setRange(72, 1200)
        self.dpi_spinbox.setValue(1200)
        self.dpi_spinbox.setSuffix(" dpi")
        self.dpi_spinbox.setToolTip("較高的 DPI 會產生更高解析度的圖片，但檔案更大")
        settings_layout.addWidget(self.dpi_spinbox)

        settings_layout.addStretch()

        preset_label = QLabel("預設:")
        settings_layout.addWidget(preset_label)

        for dpi_value in [150, 300, 600, 1200]:
            btn = QPushButton(f"{dpi_value}")
            btn.setFixedWidth(50)
            btn.clicked.connect(lambda checked, d=dpi_value: self.dpi_spinbox.setValue(d))
            settings_layout.addWidget(btn)

        layout.addWidget(settings_group)

        # 進度條
        progress_group = QGroupBox("進度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("等待開始...")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # 日誌區域
        log_group = QGroupBox("執行日誌")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 按鈕區域
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("開始轉換")
        self.start_btn.clicked.connect(self.start_conversion)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 10px; }"
        )
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 10px; }"
        )
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.file_list.keyPressEvent = self.file_list_key_press

    def file_list_key_press(self, event) -> None:  # type: ignore[no-untyped-def]
        """處理檔案列表的按鍵事件."""
        if event.key() == Qt.Key_Delete:
            self.remove_selected_files()
        else:
            QListWidget.keyPressEvent(self.file_list, event)

    def remove_selected_files(self) -> None:
        """移除選中的檔案."""
        selected_items = self.file_list.selectedItems()
        for item in reversed(selected_items):
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            del self.selected_files[row]
        self.update_file_count()

    def browse_folder(self) -> None:
        """選擇資料夾並掃描所有 PDF."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "選擇資料夾",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            pdf_files = list(Path(folder).rglob("*.pdf"))
            if pdf_files:
                self.add_files(pdf_files)
                self.append_log(f"從資料夾掃描到 {len(pdf_files)} 個 PDF 檔案")
            else:
                QMessageBox.information(self, "提示", "該資料夾中沒有找到 PDF 檔案")

    def browse_files(self) -> None:
        """選擇多個 PDF 檔案."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇 PDF 檔案",
            "",
            "PDF 檔案 (*.pdf);;所有檔案 (*.*)",
        )
        if files:
            pdf_files = [Path(f) for f in files]
            self.add_files(pdf_files)

    def add_files(self, pdf_files: list[Path]) -> None:
        """加入檔案到列表（避免重複）."""
        added_count = 0
        for pdf_path in pdf_files:
            if pdf_path not in self.selected_files:
                self.selected_files.append(pdf_path)
                self.file_list.addItem(str(pdf_path))
                added_count += 1

        if added_count > 0:
            self.update_file_count()
            self.log_text.clear()
            self.progress_bar.setValue(0)
            self.progress_label.setText("已選擇檔案，準備開始...")

    def clear_files(self) -> None:
        """清除所有已選擇的檔案."""
        self.selected_files.clear()
        self.file_list.clear()
        self.update_file_count()
        self.progress_bar.setValue(0)
        self.progress_label.setText("等待開始...")

    def update_file_count(self) -> None:
        """更新檔案數量顯示."""
        count = len(self.selected_files)
        self.file_count_label.setText(f"已選擇 {count} 個檔案")
        self.start_btn.setEnabled(count > 0)

    def start_conversion(self) -> None:
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "請選擇至少一個 PDF 檔案")
            return

        self.start_btn.setEnabled(False)
        self.browse_folder_btn.setEnabled(False)
        self.browse_files_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.dpi_spinbox.setEnabled(False)

        self.log_text.clear()
        self.progress_bar.setValue(0)

        self.worker = ConvertWorker(self.selected_files.copy(), self.dpi_spinbox.value())
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()

    def cancel_conversion(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.append_log("正在取消...")

    def update_progress(self, current: int, total: int) -> None:
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(f"處理中... {current}/{total}")

    def append_log(self, message: str) -> None:
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def conversion_finished(self, success: bool, message: str) -> None:
        self.start_btn.setEnabled(True)
        self.browse_folder_btn.setEnabled(True)
        self.browse_files_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.dpi_spinbox.setEnabled(True)

        self.progress_label.setText(message)
        self.append_log(f"\n{'=' * 50}")
        self.append_log(message)

        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "警告", message)


def main() -> None:
    """啟動 GUI 應用程式."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = PDFConverterWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

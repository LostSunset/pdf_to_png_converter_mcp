# PDF to PNG Converter MCP

[![CI](https://github.com/LostSunset/pdf_to_png_converter_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/LostSunset/pdf_to_png_converter_mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/LostSunset/pdf_to_png_converter_mcp.svg)](https://github.com/LostSunset/pdf_to_png_converter_mcp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/LostSunset/pdf_to_png_converter_mcp.svg)](https://github.com/LostSunset/pdf_to_png_converter_mcp/network)
[![GitHub issues](https://img.shields.io/github/issues/LostSunset/pdf_to_png_converter_mcp.svg)](https://github.com/LostSunset/pdf_to_png_converter_mcp/issues)

一個 MCP (Model Context Protocol) 服務器，讓 Claude Code 能夠：

- 將 PDF 檔案轉換為高品質 PNG 圖片（支援最高 1200 DPI）
- 從網路下載學術論文 PDF
- 根據期刊名稱和論文標題自動建立資料夾結構
- 下載論文後自動轉換為 PNG

## 功能特色

- **高品質轉換**：支援 72-2400 DPI，預設 1200 DPI
- **批次處理**：一次轉換整個資料夾的 PDF 檔案
- **自動整理**：根據期刊和標題自動建立資料夾結構
- **多平台支援**：Windows、macOS、Linux
- **GUI 介面**：提供獨立的圖形化介面（可選）

## 系統需求

- Python 3.10 或更高版本
- [Poppler](https://poppler.freedesktop.org/)（用於 PDF 處理）

### 安裝 Poppler

**Windows:**
1. 下載 [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases)
2. 解壓縮到任意位置（例如 `C:\poppler`）
3. 將 `bin` 資料夾加入系統 PATH（例如 `C:\poppler\bin`）

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install poppler-utils
```

## 快速安裝（推薦）

發布到 PyPI 後，只需一行指令即可在 Claude Code 中添加此 MCP：

```bash
# 使用 uvx（推薦）
claude mcp add pdf-to-png -- uvx pdf-to-png-converter-mcp

# 或使用 pipx
claude mcp add pdf-to-png -- pipx run pdf-to-png-converter-mcp
```

## 從源碼安裝

### 方法一：使用 uv（推薦）

```bash
# 克隆專案
git clone https://github.com/LostSunset/pdf_to_png_converter_mcp.git
cd pdf_to_png_converter_mcp

# 使用 uv 建立虛擬環境並安裝
uv venv .venv --python 3.12
uv pip install -e .
```

### 方法二：使用 pip

```bash
# 克隆專案
git clone https://github.com/LostSunset/pdf_to_png_converter_mcp.git
cd pdf_to_png_converter_mcp

# 建立虛擬環境並安裝
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

pip install -e .
```

## 在 Claude Code 中使用

### 設定 MCP 服務器

編輯 Claude Code 的設定檔（位於 `~/.claude/settings.json` 或專案目錄下的 `.claude/settings.json`）：

```json
{
  "mcpServers": {
    "pdf-to-png": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/pdf_to_png_converter_mcp",
        "pdf-to-png-mcp"
      ]
    }
  }
}
```

或使用 Python 直接執行：

```json
{
  "mcpServers": {
    "pdf-to-png": {
      "command": "/path/to/pdf_to_png_converter_mcp/.venv314/Scripts/python.exe",
      "args": [
        "-m",
        "pdf_to_png_converter_mcp.server"
      ]
    }
  }
}
```

### 可用工具

安裝並設定完成後，Claude Code 將可以使用以下工具：

#### 1. `convert_pdf_to_png`
將單個 PDF 檔案轉換為 PNG 圖片。

```
參數：
- pdf_path (必填): PDF 檔案的完整路徑
- dpi (選填): 輸出解析度，預設 1200
- output_dir (選填): 輸出目錄，預設與 PDF 同目錄
```

#### 2. `download_paper`
從網路下載學術論文 PDF。

```
參數：
- url (必填): 論文 PDF 的下載網址
- journal (必填): 期刊名稱（用於建立資料夾）
- title (必填): 論文標題（用於命名檔案和資料夾）
- base_dir (選填): 基礎目錄，預設為當前目錄
```

#### 3. `download_and_convert`
下載論文 PDF 並自動轉換為 PNG 圖片。

```
參數：
- url (必填): 論文 PDF 的下載網址
- journal (必填): 期刊名稱
- title (必填): 論文標題
- base_dir (選填): 基礎目錄
- dpi (選填): 輸出解析度，預設 1200
```

#### 4. `batch_convert_pdfs`
批次轉換資料夾中的所有 PDF 檔案。

```
參數：
- folder_path (必填): 包含 PDF 檔案的資料夾路徑
- dpi (選填): 輸出解析度，預設 1200
- recursive (選填): 是否遞迴搜尋子資料夾，預設 True
```

### 使用範例

在 Claude Code 中，你可以這樣使用：

```
請幫我把 C:\Papers\paper.pdf 轉換成 PNG，使用 1200 DPI
```

```
請下載這篇論文並轉換成 PNG：
URL: https://example.com/paper.pdf
期刊: Nature
標題: Deep Learning for Image Recognition
```

```
請把 D:\Research\Papers 資料夾中的所有 PDF 都轉換成 PNG
```

## GUI 介面

除了 MCP 服務器，本專案也提供獨立的 GUI 介面：

```bash
# 安裝 GUI 依賴
uv pip install -e ".[gui]" --python .venv314/Scripts/python.exe

# 啟動 GUI
pdf-to-png-gui
```

## 開發

### 安裝開發依賴

```bash
uv pip install -e ".[dev]" --python .venv314/Scripts/python.exe
```

### 執行測試

```bash
# 設定 UTF-8 編碼
set PYTHONIOENCODING=utf-8  # Windows
export PYTHONIOENCODING=utf-8  # macOS/Linux

# 執行測試
pytest
```

### 程式碼檢查

```bash
# 檢查並自動修復
ruff check --fix
ruff format
```

## 版本歷史

請參閱 [CHANGELOG.md](CHANGELOG.md)

## 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LostSunset/pdf_to_png_converter_mcp&type=Date)](https://star-history.com/#LostSunset/pdf_to_png_converter_mcp&Date)

---

**Version:** 0.1.3

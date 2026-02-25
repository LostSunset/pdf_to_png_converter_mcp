# PDF to PNG Converter MCP - 專案指南

這是一個 MCP (Model Context Protocol) 服務器專案，讓 Claude Code 能夠處理 PDF 轉 PNG 和論文下載功能。

## 專案結構

```
pdf_to_png_converter_mcp/
├── src/
│   └── pdf_to_png_converter_mcp/
│       ├── __init__.py       # 套件初始化和版本
│       ├── server.py         # MCP 服務器主程式
│       ├── converter.py      # PDF 轉 PNG 核心功能
│       ├── downloader.py     # 論文下載功能
│       └── gui.py            # GUI 介面（可選）
├── tests/                    # 測試檔案
├── .github/workflows/        # CI/CD 配置
├── .claude/
│   └── agents/
│       └── release.md        # Release agent 定義
├── pyproject.toml            # 專案配置
├── README.md                 # 專案說明
├── CHANGELOG.md              # 版本歷史
├── LICENSE                   # MIT 授權
└── CLAUDE.md                 # 此檔案
```

## 環境需求

- Python 3.10+（開發使用 Python 3.14）
- uv 套件管理器
- Poppler（用於 PDF 處理）

## 開發指令

### 安裝依賴
```bash
uv venv .venv314 --python 3.14
uv pip install -e ".[dev]" --python .venv314/Scripts/python.exe
```

### 執行測試
```bash
set PYTHONIOENCODING=utf-8
pytest -v
```

### 程式碼檢查
```bash
ruff check --fix .
ruff format .
```

### 啟動 MCP 服務器
```bash
pdf-to-png-mcp
```

## 版本控制規則

每次推送更新都要增加版本號：

| 類型 | 版本變更 | 範例 |
|------|----------|------|
| bug 修復或效能提升 | PATCH | v0.2.1 → v0.2.2 |
| 新功能 | MINOR | v0.2.1 → v0.3.0 |
| 重大變更 | MAJOR | v0.2.1 → v1.0.0 |

## 自動發布流程

### 使用 /release 指令

當你想要發布新版本時，可以使用 `/release` 指令：

```
/release patch  # bug 修復
/release minor  # 新功能
/release major  # 重大變更
```

Release agent 會自動執行以下步驟：

1. 執行測試確保程式碼品質
2. 執行 lint 檢查並自動修復
3. 更新版本號（`pyproject.toml` 和 `__init__.py`）
4. 更新 CHANGELOG.md
5. 更新 README.md 中的版本號
6. 提交變更
7. 創建 Git tag
8. 推送到 GitHub

### 手動發布

如果不使用 agent，可以手動執行以下步驟：

```bash
# 1. 確保測試通過
pytest -v

# 2. 執行 lint
ruff check --fix .
ruff format .

# 3. 更新版本號
# 編輯 pyproject.toml 和 src/pdf_to_png_converter_mcp/__init__.py

# 4. 更新 CHANGELOG.md

# 5. 提交並推送
git add -A
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## MCP 工具說明

### convert_pdf_to_png
將單個 PDF 檔案轉換為 PNG 圖片。

### download_paper
從網路下載學術論文 PDF。

### download_and_convert
下載論文 PDF 並自動轉換為 PNG 圖片。

### batch_convert_pdfs
批次轉換資料夾中的所有 PDF 檔案。

## UTF-8 編碼注意事項

- 所有程式碼檔案使用 UTF-8 編碼
- 測試時設定 `PYTHONIOENCODING=utf-8`
- Windows 上需要確保終端正確顯示中文

## 倉庫位址

- **GitHub**：https://github.com/LostSunset/pdf_to_png_converter_mcp

## 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

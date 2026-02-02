# Release Agent

自動執行發布流程的 agent。

## 觸發方式

使用 `/release` 指令觸發，支援以下參數：

- `/release patch` - bug 修復或效能提升 (v0.1.0 → v0.1.1)
- `/release minor` - 新功能 (v0.1.0 → v0.2.0)
- `/release major` - 重大變更 (v0.1.0 → v1.0.0)

## 執行步驟

當收到 release 指令時，請按照以下步驟執行：

### 1. 執行測試
```bash
cd "D:\SynologyDrive\Learning\00_PDF_Tool\pdf_to_png_converter_mcp"
set PYTHONIOENCODING=utf-8
.venv314/Scripts/pytest.exe -v
```

確保所有測試通過，如果失敗則停止發布流程。

### 2. 執行 Lint 檢查
```bash
.venv314/Scripts/ruff.exe check --fix .
.venv314/Scripts/ruff.exe format .
```

### 3. 讀取當前版本
讀取 `src/pdf_to_png_converter_mcp/__init__.py` 中的 `__version__`。

### 4. 計算新版本
根據指定的類型計算新版本號：
- patch: X.Y.Z → X.Y.(Z+1)
- minor: X.Y.Z → X.(Y+1).0
- major: X.Y.Z → (X+1).0.0

### 5. 更新版本號
更新以下檔案中的版本號：
- `pyproject.toml`: `version = "X.Y.Z"`
- `src/pdf_to_png_converter_mcp/__init__.py`: `__version__ = "X.Y.Z"`
- `README.md`: `**Version:** X.Y.Z`

### 6. 更新 CHANGELOG.md
在 CHANGELOG.md 中添加新版本的條目：

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added/Changed/Fixed
- 根據提交歷史自動生成變更說明
```

### 7. 提交變更
```bash
git add -A
git commit -m "$(cat <<'EOF'
Release vX.Y.Z

- Updated version to X.Y.Z
- Updated CHANGELOG.md

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### 8. 創建 Tag
```bash
git tag vX.Y.Z
```

### 9. 推送到 GitHub
```bash
git push origin main --tags
```

### 10. 完成報告
輸出發布摘要：
- 新版本號
- 變更列表
- GitHub 連結

## 錯誤處理

- 如果測試失敗，停止流程並報告錯誤
- 如果 lint 有無法自動修復的錯誤，停止流程並報告
- 如果 git 操作失敗，報告錯誤並提供手動修復指引

## 注意事項

- 確保所有檔案使用 UTF-8 編碼
- 版本號遵循 Semantic Versioning 規範
- 每次發布都要更新 CHANGELOG.md

# /release Command

自動發布新版本到 GitHub。

## 使用方式

```
/release <type>
```

其中 `<type>` 可以是：
- `patch` - bug 修復或效能提升
- `minor` - 新功能
- `major` - 重大變更

## 範例

```
/release patch   # v0.1.0 → v0.1.1
/release minor   # v0.1.0 → v0.2.0
/release major   # v0.1.0 → v1.0.0
```

## 執行流程

1. 執行測試 (`pytest -v`)
2. 執行 lint 檢查 (`ruff check --fix && ruff format`)
3. 更新版本號
4. 更新 CHANGELOG.md
5. 提交變更
6. 創建 Git tag
7. 推送到 GitHub

## Prompt

當用戶執行此指令時，請按照以下步驟操作：

$arguments 包含發布類型（patch/minor/major）

請嚴格按照 `.claude/agents/release.md` 中定義的步驟執行發布流程。

1. 首先讀取當前版本號
2. 根據指定的類型計算新版本號
3. 執行測試確保品質
4. 執行 lint 檢查
5. 更新所有版本號檔案
6. 更新 CHANGELOG.md
7. 提交、標記並推送

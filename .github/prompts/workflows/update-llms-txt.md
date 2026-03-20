# 更新 Foundry llms.txt 文件

從最新的 Microsoft Foundry 文件重新產生 llms.txt 和 llms-full.txt 檔案。

## 用途

此工作流程透過以下方式使我們的 Foundry 文件索引保持最新：
1. 從 Microsoft Learn 擷取最新的目錄 (Table of Contents)
2. 使用目前的文件連結重新產生 llms.txt
3. 如果有變更，則建立 PR (Pull Request)

## 步驟

1. **設定 Python 環境**
   - 安裝必要的套件：`pip install aiohttp`

2. **執行爬蟲 (Scraper)**
   - 執行 `python .github/scripts/scrape_foundry_docs.py` 以重新產生 llms.txt
   - 執行 `python .github/scripts/generate_llms_full.py` 以重新產生 llms-full.txt

3. **檢查變更**
   - 比較產生的檔案與現有檔案
   - 如果有變更，則建立包含更新的 pull request

4. **必要時建立 PR**
   - 標題："Update Foundry llms.txt documentation"
   - 包含變更摘要 (新頁面、移除的頁面、章節變更)

## 備註

- 爬蟲在從 Microsoft Learn 擷取資料時會遵守速率限制
- 僅在實際內容有變更時才會建立 PR
- llms.txt 遵循 LLM-friendly 文件的 llms.txt 規範

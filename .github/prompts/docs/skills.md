# Agent 技能

## 文件

- [概覽](https://agentskills.io/home.md)：一個簡單、開放的格式，用於賦予 Agent 新的能力和專業知識。
- [將技能整合到你的 Agent 中](https://agentskills.io/integrate-skills.md)：如何為你的 Agent 或工具新增 Agent Skills 支援。
- [規範](https://agentskills.io/specification.md)：Agent Skills 的完整格式規範。
- [什麼是技能？](https://agentskills.io/what-are-skills.md)：Agent Skills 是一個輕量、開放的格式，用於透過專門知識和工作流程擴充 AI Agent 的能力。
---
# 概覽 (Overview)

> 一個簡單、開放的格式，用於賦予 Agent 新的能力和專業知識。

export const LogoCarousel = () => {
    // 程式碼區塊保留原樣
};

Agent Skills 是由指令、腳本和資源組成的資料夾，Agent 可以發現並使用它們來更準確、有效地完成任務。

## 為什麼需要 Agent Skills？

Agent 的能力越來越強，但通常缺乏可靠地執行實際工作所需的 context。技能透過讓 Agent 存取程序性知識以及公司、團隊和使用者特定的 context (可依需求載入) 來解決這個問題。能夠存取一系列技能的 Agent 可以根據正在處理的任務擴充其能力。

**對於技能作者**：建置一次功能，並將其部署到多個 Agent 產品中。

**對於相容的 Agent**：對技能的支援讓終端使用者開箱即可賦予 Agent 新的能力。

**對於團隊和企業**：以可攜帶、版本控制的套件形式擷取組織知識。

## Agent Skills 可以促成什麼？

* **領域專業知識**：將專門知識打包成可重複使用的指令，從法律審查流程到資料分析管道。
* **新能力**：賦予 Agent 新的能力 (例如建立簡報、建置 MCP 伺服器、分析資料集)。
* **可重複的工作流程**：將多步驟任務轉化為一致且可稽核的工作流程。
* **互通性**：在不同相容技能的 Agent 產品中重複使用相同的技能。

## 採用

Agent Skills 受到頂尖 AI 開發工具的支援。

<LogoCarousel />

## 開放式開發

Agent Skills 格式最初由 [Anthropic](https://www.anthropic.com/) 開發，以開放標準發布，並已被越來越多的 Agent 產品採用。該標準對更廣泛的生態系統貢獻抱持開放態度。

[在 GitHub 上檢視](https://github.com/agentskills/agentskills)

## 開始使用

<CardGroup cols={3}>
  <Card title="什麼是技能？" icon="lightbulb" href="/what-are-skills">
    了解技能，它們如何運作，以及為什麼它們很重要。
  </Card>

  <Card title="規範" icon="file-code" href="/specification">
    SKILL.md 檔案的完整格式規範。
  </Card>

  <Card title="整合技能" icon="gear" href="/integrate-skills">
    為你的 Agent 或工具新增技能支援。
  </Card>

  <Card title="範例技能" icon="code" href="https://github.com/anthropics/skills">
    在 GitHub 上瀏覽範例技能。
  </Card>

  <Card title="參考函式庫" icon="wrench" href="https://github.com/agentskills/agentskills/tree/main/skills-ref">
    驗證技能並產生提示詞 XML。
  </Card>
</CardGroup>


---

# 什麼是技能？(What are skills?)

> Agent Skills 是一個輕量、開放的格式，用於透過專門知識和工作流程擴充 AI Agent 的能力。

核心概念上，技能是一個包含 `SKILL.md` 檔案的資料夾。此檔案包含中繼資料 (至少包含 `name` 和 `description`) 以及告訴 Agent 如何執行特定任務的指令。技能還可以包含腳本、範本和參考資料。

```directory  theme={null}
my-skill/
├── SKILL.md          # 必填：指令 + 中繼資料
├── scripts/          # 選填：可執行程式碼
├── references/       # 選填：文件
└── assets/           # 選填：範本、資源
```

## 技能如何運作

技能使用 **漸進式揭露 (progressive disclosure)** 以有效管理 context：

1. **發現 (Discovery)**：在啟動時，Agent 僅載入每個可用技能的名稱和描述，足以知道何時可能相關。

2. **啟動 (Activation)**：當任務符合技能的描述時，Agent 會將完整的 `SKILL.md` 指令讀入 context。

3. **執行 (Execution)**：Agent 遵循指令，依需求選擇性載入參考檔案或執行隨附的程式碼。

這種方法讓 Agent 保持快速，同時讓它們能依需求存取更多 context。

## SKILL.md 檔案

每個技能都以包含 YAML frontmatter 和 Markdown 指令的 `SKILL.md` 檔案開始：

```mdx  theme={null}
---
name: pdf-processing
description: 從 PDF 檔案擷取文字和表格，填寫表單，合併文件。
---

# PDF Processing

## 何時使用此技能
當使用者需要處理 PDF 檔案時使用此技能...

## 如何擷取文字
1. 使用 pdfplumber 進行文字擷取...

## 如何填寫表單
...
```

`SKILL.md` 頂部需要以下 frontmatter：

* `name`：短識別符
* `description`：何時使用此技能

Markdown 本文包含實際指令，對結構或內容沒有特定限制。

這個簡單的格式有一些關鍵優勢：

* **自我文件化**：技能作者或使用者可以閱讀 `SKILL.md` 並了解它的功能，使技能易於稽核和改進。

* **可擴充**：技能的複雜度範圍可以從僅文字指令到包含可執行程式碼、資產和範本。

* **可攜帶**：技能只是檔案，因此易於編輯、版本控制和分享。

## 下一步

* [檢視規範](/specification) 以了解完整格式。
* [為你的 Agent 新增技能支援](/integrate-skills) 以建置相容的用戶端。
* 在 GitHub 上 [檢視範例技能](https://github.com/anthropics/skills)。
* [閱讀撰寫最佳實踐](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) 以編寫有效的技能。
* [使用參考函式庫](https://github.com/agentskills/agentskills/tree/main/skills-ref) 驗證技能並產生提示詞 XML。


---

# 規範 (Specification)

> Agent Skills 的完整格式規範。

本文件定義 Agent Skills 格式。

## 目錄結構

技能是一個至少包含 `SKILL.md` 檔案的目錄：

```
skill-name/
└── SKILL.md          # 必填
```

<Tip>
  你可以選擇性包含 [其他目錄](#optional-directories) 如 `scripts/`、`references/` 和 `assets/` 來支援你的技能。
</Tip>

## SKILL.md 格式

`SKILL.md` 檔案必須包含 YAML frontmatter，後接 Markdown 內容。

### Frontmatter (必填)

```yaml  theme={null}
---
name: skill-name
description: 此技能的功能以及何時使用它的描述。
---
```

帶有選填欄位：

```yaml  theme={null}
---
name: pdf-processing
description: 從 PDF 檔案擷取文字和表格，填寫表單，合併文件。
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

| 欄位 | 必填 | 限制 |
| --- | --- | --- |
| `name` | 是 | 最多 64 個字元。僅限小寫字母、數字和連字號。不得以連字號開頭或結尾。 |
| `description` | 是 | 最多 1024 個字元。不得為空。描述此技能的功能以及何時使用它。 |
| `license` | 否 | 授權名稱或對隨附授權檔案的參考。 |
| `compatibility` | 否 | 最多 500 個字元。指出環境需求 (預期產品、系統套件、網路存取等)。 |
| `metadata` | 否 | 任意鍵值對應，用於額外的中繼資料。 |
| `allowed-tools` | 否 | 以空格分隔的預先核准工具列表，技能可以使用這些工具。(實驗性) |

#### `name` 欄位

必填的 `name` 欄位：

* 必須是 1-64 個字元
* 僅可包含 unicode 小寫英數字元和連字號 (`a-z` 和 `-`)
* 不得以 `-` 開頭或結尾
* 不得包含連續連字號 (`--`)
* 必須與父目錄名稱相符

#### `description` 欄位

必填的 `description` 欄位：

* 必須是 1-1024 個字元
* 應同時描述技能的功能以及何時使用它
* 應包含有助於 Agent 識別相關任務的特定關鍵字

#### `license` 欄位

選填的 `license` 欄位：

* 指定適用於此技能的授權

#### `compatibility` 欄位

選填的 `compatibility` 欄位：

* 若提供，必須是 1-500 個字元
* 僅當你的技能有特定環境需求時才應包含
* 可以指出預期產品、必要的系統套件、網路存取需求等

#### `metadata` 欄位

選填的 `metadata` 欄位：

* 字串鍵到字串值的映射
* 用戶端可以使用此欄位儲存 Agent Skills 規範未定義的額外屬性

#### `allowed-tools` 欄位

選填的 `allowed-tools` 欄位：

* 以空格分隔的工具列表，預先核准執行
* 實驗性。對此欄位的支援可能因 Agent 實作而異

### Body 內容 (Body content)

Frontmatter 之後的 Markdown 本文包含技能指令。沒有格式限制。寫下任何有助於 Agent 有效執行任務的內容。

推薦章節：

* 逐步指令
* 輸入和輸出範例
* 常見邊緣案例

請注意，一旦決定啟動技能，Agent 將載入整個檔案。考慮將較長的 `SKILL.md` 內容拆分成參考檔案。

## 選填目錄 (Optional directories)

### scripts/

包含 Agent 可以執行的程式碼。腳本應該：

* 自包含或清楚記錄依賴關係
* 包含有用的錯誤訊息
* 優雅地處理邊緣案例

### references/

包含 Agent 在需要時可以閱讀的額外文件：

* `REFERENCE.md` - 詳細技術參考
* `FORMS.md` - 表單範本或結構化資料格式
* 領域特定檔案 (`finance.md`, `legal.md` 等)

### assets/

包含靜態資源：

* 範本 (文件範本、設定範本)
* 圖片 (圖表、範例)
* 資料檔案 (查找表、架構)

## 漸進式揭露 (Progressive disclosure)

技能應結構化以有效使用 context：

1. **中繼資料** (\~100 tokens)：所有技能的 `name` 和 `description` 欄位在啟動時載入
2. **指令** (推薦 \< 5000 tokens)：技能啟動時載入完整的 `SKILL.md` 本文
3. **資源** (依需求)：檔案 (例如 `scripts/`, `references/`, 或 `assets/` 中的檔案) 僅在需要時載入

## 檔案參考 (File references)

在你的技能中參考其他檔案時，使用相對於技能根目錄的相對路徑：

```markdown  theme={null}
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

保持檔案參考從 `SKILL.md` 算起為一層深度。避免深層嵌套的參考鏈。

## 驗證 (Validation)

使用 [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) 參考函式庫驗證你的技能：

```bash  theme={null}
skills-ref validate ./my-skill
```

這會檢查你的 `SKILL.md` frontmatter 是否有效並遵循所有命名慣例。


---

# 將技能整合到你的 Agent 中 (Integrate skills into your agent)

> 如何為你的 Agent 或工具新增 Agent Skills 支援。

本指南說明如何為 AI Agent 或開發工具新增技能支援。

## 整合方法

整合技能的兩種主要方法是：

**基於檔案系統的 Agent (Filesystem-based agents)** 在電腦環境 (bash/unix) 中運作，代表最強大的選項。當模型發出如 `cat /path/to/my-skill/SKILL.md` 的 shell 指令時，技能就會啟動。隨附資源透過 shell 指令存取。

**基於工具的 Agent (Tool-based agents)** 在沒有專用電腦環境的情況下運作。相反地，它們實作允許模型觸發技能並存取隨附資產的工具。具體工具實作由開發者決定。

## 概覽

一個相容技能的 Agent 需要：

1. 在設定的目錄中 **發現** 技能
2. 在啟動時 **載入中繼資料** (名稱和描述)
3. 將使用者任務 **配對** 至相關技能
4. 透過載入完整指令 **啟動** 技能
5. 依需求 **執行** 腳本並存取資源

## 技能發現

技能是包含 `SKILL.md` 檔案的資料夾。你的 Agent 應該掃描設定的目錄以尋找有效的技能。

## 載入中繼資料

在啟動時，僅解析每個 `SKILL.md` 檔案的 frontmatter。這能保持初始 context 使用量低。

### 解析 Frontmatter

```
function parseMetadata(skillPath):
    content = readFile(skillPath + "/SKILL.md")
    frontmatter = extractYAMLFrontmatter(content)

    return {
        name: frontmatter.name,
        description: frontmatter.description,
        path: skillPath
    }
```

### 注入至 Context

將技能中繼資料包含在系統提示詞中，以便模型知道有哪些技能可用。

遵循你的平台關於系統提示詞更新的指引。例如，對於 Claude 模型，推薦的格式使用 XML：

```xml  theme={null}
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extracts text and tables from PDF files, fills forms, merges documents.</description>
    <location>/path/to/skills/pdf-processing/SKILL.md</location>
  </skill>
  <skill>
    <name>data-analysis</name>
    <description>Analyzes datasets, generates charts, and creates summary reports.</description>
    <location>/path/to/skills/data-analysis/SKILL.md</location>
  </skill>
</available_skills>
```

對於基於檔案系統的 Agent，包含帶有 `SKILL.md` 檔案絕對路徑的 `location` 欄位。對於基於工具的 Agent，可以省略 location。

保持中繼資料簡潔。每個技能應為 context 增加大約 50-100 個 tokens。

## 安全性考量

腳本執行會引入安全風險。請考慮：

* **沙盒化 (Sandboxing)**：在隔離環境中執行腳本
* **允許清單 (Allowlisting)**：僅執行來自受信任技能的腳本
* **確認 (Confirmation)**：在執行潛在危險操作前詢問使用者
* **日誌記錄 (Logging)**：記錄所有腳本執行以進行稽核

## 參考實作

[skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) 函式庫提供了用於處理技能的 Python 工具程式和 CLI。

例如：

**驗證技能目錄：**

```
skills-ref validate <path>
```

**產生用於 Agent 提示詞的 `<available_skills>` XML：**

```
skills-ref to-prompt <path>...
```

使用函式庫原始碼作為參考實作。

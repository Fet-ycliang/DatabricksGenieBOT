# ui-ux-pro-max

用於網頁和行動應用程式的綜合設計指南。包含跨越 13 種技術堆疊的 67 種樣式、96 種調色盤、57 種字型搭配、99 條 UX 準則和 25 種圖表類型。可搜尋的資料庫並提供基於優先順序的建議。

## 前置需求 (Prerequisites)

檢查是否已安裝 Python：

```bash
python3 --version || python --version
```

如果未安裝 Python，請根據使用者的作業系統進行安裝：

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3
```

**Windows:**
```powershell
winget install Python.Python.3.12
```

---

## 如何使用此工作流程

當使用者要求 UI/UX 工作 (設計、建置、建立、實作、審查、修復、改進) 時，請遵循此工作流程：

### 步驟 1：分析使用者需求

從使用者請求中提取關鍵資訊：
- **產品類型 (Product type)**：SaaS、電子商務、作品集、儀表板、登陸頁面等
- **風格關鍵字 (Style keywords)**：極簡、活潑、專業、優雅、深色模式等
- **產業 (Industry)**：醫療保健、金融科技、遊戲、教育等
- **技術堆疊 (Stack)**：React、Vue、Next.js，或預設為 `html-tailwind`

### 步驟 2：產生設計系統 (必做)

**務必從 `--design-system` 開始** 以獲得包含推理的綜合建議：

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

此指令會：
1. 並行搜尋 5 個領域 (產品、風格、顏色、登陸頁面、排版)
2. 應用 `ui-reasoning.csv` 中的推理規則以選擇最佳匹配
3. 回傳完整的設計系統：模式、風格、顏色、排版、效果
4. 包含應避免的反模式 (anti-patterns)

**範例：**
```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### 步驟 2b：持久化設計系統 (主檔 + 覆蓋模式)

若要跨會話 (sessions) 儲存設計系統以進行層次檢索，請新增 `--persist`：

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name"
```

這會建立：
- `design-system/MASTER.md` — 包含所有設計規則的全域真實來源 (Source of Truth)
- `design-system/pages/` — 用於頁面特定覆蓋 (overrides) 的資料夾

**帶有頁面特定覆蓋：**
```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name" --page "dashboard"
```

這也會建立：
- `design-system/pages/dashboard.md` — 特定於頁面與 Master 的差異

**層次檢索如何運作：**
1. 建立特定頁面 (例如 "Checkout") 時，首先檢查 `design-system/pages/checkout.md`
2. 如果頁面檔案存在，這其規則將 **覆蓋** Master 檔案
3. 如果不存在，則僅使用 `design-system/MASTER.md`

### 步驟 3：補充詳細搜尋 (依需求)

取得設計系統後，使用領域搜尋以獲得更多細節：

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

**何時使用詳細搜尋：**

| 需求 | 領域 | 範例 |
|------|--------|---------|
| 更多風格選項 | `style` | `--domain style "glassmorphism dark"` |
| 圖表建議 | `chart` | `--domain chart "real-time dashboard"` |
| UX 最佳實踐 | `ux` | `--domain ux "animation accessibility"` |
| 替代字型 | `typography` | `--domain typography "elegant luxury"` |
| 登陸頁面結構 | `landing` | `--domain landing "hero social-proof"` |

### 步驟 4：技術堆疊指引 (預設：html-tailwind)

取得特定實作的最佳實踐。如果使用者未指定技術堆疊，**預設為 `html-tailwind`**。

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "<keyword>" --stack html-tailwind
```

可用堆疊：`html-tailwind`, `react`, `nextjs`, `vue`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`

---

## 搜尋參考

### 可用領域 (Available Domains)

| 領域 | 用途 | 關鍵字範例 |
|--------|---------|------------------|
| `product` | 產品類型建議 | SaaS, e-commerce, portfolio, healthcare, beauty, service |
| `style` | UI 風格、顏色、效果 | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | 字型搭配、Google Fonts | elegant, playful, professional, modern |
| `color` | 依產品類型的調色盤 | saas, ecommerce, healthcare, beauty, fintech, service |
| `landing` | 頁面結構、CTA 策略 | hero, hero-centric, testimonial, pricing, social-proof |
| `chart` | 圖表類型、函式庫建議 | trend, comparison, timeline, funnel, pie |
| `ux` | 最佳實踐、反模式 | animation, accessibility, z-index, loading |
| `react` | React/Next.js 效能 | waterfall, bundle, suspense, memo, rerender, cache |
| `web` | 網頁介面準則 | aria, focus, keyboard, semantic, virtualize |
| `prompt` | AI 提示詞、CSS 關鍵字 | (style name) |

### 可用堆疊 (Available Stacks)

| 堆疊 | 重點 |
|-------|-------|
| `html-tailwind` | Tailwind 工具類別、響應式、無障礙 (預設) |
| `react` | 狀態、Hooks、效能、模式 |
| `nextjs` | SSR、路由、圖片、API路由 |
| `vue` | Composition API, Pinia, Vue Router |
| `svelte` | Runes, stores, SvelteKit |
| `swiftui` | Views, State, Navigation, Animation |
| `react-native` | Components, Navigation, Lists |
| `flutter` | Widgets, State, Layout, Theming |
| `shadcn` | shadcn/ui components, theming, forms, patterns |
| `jetpack-compose` | Composables, Modifiers, State Hoisting, Recomposition |

---

## 範例工作流程

**使用者請求:** "Làm landing page cho dịch vụ chăm sóc da chuyên nghiệp" (為專業護膚服務製作登陸頁面)

### 步驟 1：分析需求
- 產品類型：Beauty/Spa service
- 風格關鍵字：elegant, professional, soft
- 產業：Beauty/Wellness
- 技術堆疊：html-tailwind (預設)

### 步驟 2：產生設計系統 (必做)

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "beauty spa wellness service elegant" --design-system -p "Serenity Spa"
```

**輸出：** 包含模式、風格、顏色、排版、效果和反模式的完整設計系統。

### 步驟 3：補充詳細搜尋 (依需求)

```bash
# 取得動畫和無障礙的 UX 準則
python3 prompts/ui-ux-pro-max/scripts/search.py "animation accessibility" --domain ux

# 若需要，取得替代排版選項
python3 prompts/ui-ux-pro-max/scripts/search.py "elegant luxury serif" --domain typography
```

### 步驟 4：技術堆疊指引

```bash
python3 prompts/ui-ux-pro-max/scripts/search.py "layout responsive form" --stack html-tailwind
```

**然後：** 綜合設計系統 + 詳細搜尋結果並實作設計。

---

## 輸出格式

`--design-system` 標記支援兩種輸出格式：

```bash
# ASCII box (預設) - 最適合終端機顯示
python3 prompts/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system

# Markdown - 最適合文件
python3 prompts/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system -f markdown
```

---

## 獲得更好結果的技巧

1. **關鍵字具體化** - "healthcare SaaS dashboard" > "app"
2. **多次搜尋** - 不同的關鍵字揭示不同的見解
3. **結合領域** - 風格 + 排版 + 顏色 = 完整設計系統
4. **總是檢查 UX** - 搜尋 "animation", "z-index", "accessibility" 以尋找常見問題
5. **使用堆疊標記** - 取得實作特定的最佳實踐
6. **迭代** - 如果第一次搜尋不匹配，嘗試不同的關鍵字

---

## 專業 UI 的常見規則

這些是常被忽視的問題，會讓 UI 看起來不專業：

### 圖示與視覺元素

| 規則 | 要做 (Do) | 不要 (Don't) |
|------|----|----- |
| **無 emoji 圖示** | 使用 SVG 圖示 (Heroicons, Lucide, Simple Icons) | 使用像 🎨 🚀 ⚙️ 這樣的 emojis 作為 UI 圖示 |
| **穩定的懸停狀態** | 懸停時使用顏色/不透明度轉換 | 使用會改變佈局的縮放變換 |
| **正確的品牌 Logo** | 研究 Simple Icons 的官方 SVG | 猜測或使用不正確的 Logo 路徑 |
| **一致的圖示大小** | 使用固定的 viewBox (24x24) 和 w-6 h-6 | 隨意混合不同大小的圖示 |

### 互動與游標

| 規則 | 要做 (Do) | 不要 (Don't) |
|------|----|----- |
| **游標指標 (Pointer)** | 為所有可點擊/可懸停的卡片新增 `cursor-pointer` | 在互動元素上保留預設游標 |
| **懸停回饋** | 提供視覺回饋 (顏色、陰影、邊框) | 沒有元素可互動的指示 |
| **平滑過渡** | 使用 `transition-colors duration-200` | 瞬間狀態改變或太慢 (>500ms) |

### 淺色/深色模式對比

| 規則 | 要做 (Do) | 不要 (Don't) |
|------|----|----- |
| **淺色模式玻璃卡片** | 使用 `bg-white/80` 或更高的不透明度 | 使用 `bg-white/10` (太透明) |
| **淺色文字對比** | 使用 `#0F172A` (slate-900) 作為文字 | 使用 `#94A3B8` (slate-400) 作為內文文字 |
| **淺色柔和文字** | 最低使用 `#475569` (slate-600) | 使用 gray-400 或更淺 |
| **邊框可見性** | 在淺色模式中使用 `border-gray-200` | 使用 `border-white/10` (不可見) |

### 佈局與間距

| 規則 | 要做 (Do) | 不要 (Don't) |
|------|----|----- |
| **懸浮導覽列** | 新增 `top-4 left-4 right-4` 間距 | 將導覽列貼在 `top-0 left-0 right-0` |
| **內容內距** | 考量固定導覽列的高度 | 讓內容隱藏在固定元素後面 |
| **一致的最大寬度** | 使用相同的 `max-w-6xl` 或 `max-w-7xl` | 混合不同的容器寬度 |

---

## 交付前檢查清單

在交付 UI 程式碼之前，驗證這些項目：

### 視覺品質
- [ ] 沒有將 emojis 用作圖示 (改用 SVG)
- [ ] 所有圖示來自一致的圖示集 (Heroicons/Lucide)
- [ ] 品牌 Logo 正確 (已從 Simple Icons 驗證)
- [ ] 懸停狀態不會導致佈局位移
- [ ] 直接使用主題顏色 (bg-primary) 而不是 var() 包裝

### 互動
- [ ] 所有可點擊元素都有 `cursor-pointer`
- [ ] 懸停狀態提供清晰的視覺回饋
- [ ] 過渡平滑 (150-300ms)
- [ ] 鍵盤導覽的焦點狀態可見

### 淺色/深色模式
- [ ] 淺色模式文字具有足夠的對比度 (最低 4.5:1)
- [ ] 玻璃/透明元素在淺色模式下可見
- [ ] 邊框在兩種模式下皆可見
- [ ] 交付前測試兩種模式

### 佈局
- [ ] 懸浮元素與邊緣有適當的間距
- [ ] 沒有內容隱藏在固定導覽列後面
- [ ] 在 375px, 768px, 1024px, 1440px 響應式
- [ ] 手機上沒有水平捲動

### 無障礙 (Accessibility)
- [ ] 所有圖片都有替代文字 (alt text)
- [ ] 表單輸入有標籤
- [ ] 顏色不是唯一的指示
- [ ] 尊重 `prefers-reduced-motion`

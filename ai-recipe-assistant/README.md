# 🍳 AI 食譜檢索與創作小助手 (AI Recipe Assistant)

> 本專案為大學課程「和 AI 一起寫程式」期中專題報告作品。

一個隨時可用、支援手機與電腦 RWD 的智慧 Web 料理小助手。使用者只需輸入或勾選目前冰箱現有的食材與調味料，即可由 AI 自動檢索真實網路料理或創作全新美味食譜！

---

## 🌟 核心特色與功能亮點

### 1. 雙軌食材輸入機制
* **自由文字補充**：支持輸入如「半顆高麗菜、醬油、蠔油、大蒜」等自訂敘述與精確份量。
* **分類快速勾選清單**：涵蓋「蔬菜根莖、肉品海鮮、蛋豆奶類、主食穀物、基礎調味、辛香風味」六大常見分類，一鍵即點即選。
* **口味與料理偏好**：可自訂清淡少油、微辣開胃、減脂高蛋白、快速便當菜等限制。

### 2. 雙模式 AI 智能生成
* 🌐 **模式 A（網路真實食譜檢索）**：
  * 參考知名料理平台（如：愛料理 iCook、Cookpad、楊桃美食網、食譜自由配等）之經典熱門配方。
  * **嚴格標註參考來源出處與外部超連結**，確保料理具備真實可行性。
* 💡 **模式 B（AI 創意食譜實驗室）**：
  * 化身米其林創意主廚，根據手邊現有食材大膽激盪，設計出風味平衡且可行的新穎料理。
  * 附帶主廚點評與美味搭配秘訣。

### 3. 清楚結構化呈現與貼心 UX
* **材料清晰分離**：清楚區分「🟢 現有食材（已具備）」與「🛒 建議補充材料（若需要）」。
* **步驟教學與主廚小撇步**：具備料理時間、備料時間、難度星級與烹調 Tip 叮嚀。
* **一鍵功能**：支援「一鍵複製全文食譜至剪貼簿」與「友善列印/存為 PDF」。
* **動態 Loading 狀態**：生成期間提供料理小動畫與動態烹調小常識輪播，大幅提升等待體驗。

---

## 🛠️ 技術棧 (Tech Stack)

* **前端框架**：[Next.js](https://nextjs.org/) (App Router) + [React](https://react.dev/)
* **樣式與 RWD**：[Tailwind CSS](https://tailwindcss.com/)
* **圖示庫**：[Lucide React](https://lucide.dev/)
* **AI 核心**：Google Gemini API (`gemini-3.5-flash` / `gemini-3.1-flash-lite` 具備自動容錯機制)
* **資安防護**：後端 Route Handler 隔離敏感金鑰，前端無任何 API Key 暴露風險

---

## 🔒 資安與作業規範遵循

1. **環境變數金鑰保護**：本專案嚴格遵守金鑰不寫死原則，API Key 僅透過 `.env.local` 讀取，並已透過 `.gitignore` 排除，保證 push 到 GitHub 時絕對無洩漏疑慮。
2. **開源規範**：提供 `.env.example` 讓評分者或使用者能夠清楚如何設定環境。
3. **無個人學號與姓名**：全專案與 Git 提交記錄均無任何個人學號與敏感身分資訊。

---

## 🚀 快速開始 (Getting Started)

### 1. 複製專案與安裝依賴

```bash
# 安裝相依套件
npm install
```

### 2. 設定環境變數

複製 `.env.example` 並更名為 `.env.local`：

```bash
# Windows PowerShell
cp .env.example .env.local
```

打開 `.env.local` 填入您的 Gemini API Key：
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```
> ※ 可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請 API Key。

### 3. 啟動開發伺服器

```bash
npm run dev
```

在瀏覽器打開 [http://localhost:3000](http://localhost:3000) 即可開始體驗！

---

## 📂 專案架構 (Project Structure)

```text
ai-recipe-assistant/
├── .env.example              # 環境變數設定範本（可上傳至 GitHub）
├── .env.local                # 實際金鑰存放檔（.gitignore 嚴密防護）
├── .gitignore                # 排除 node_modules 與 .env*
├── package.json              # 專案套件設定
├── README.md                 # 專案完整說明文件
├── tailwind.config.ts        # Tailwind CSS 主題與調色盤配置
├── tsconfig.json             # TypeScript 配置
└── src/
    ├── app/
    │   ├── api/recipe/route.ts  # 後端 AI 安全路由端點（處理模式 A/B）
    │   ├── globals.css          # 全域樣式與動畫
    │   ├── layout.tsx           # 根佈局配置
    │   └── page.tsx             # 主應用頁面
    ├── components/
    │   ├── Header.tsx           # 頂部導航與資安驗證標章
    │   ├── ModeSelector.tsx     # 模式 A (真實) / 模式 B (創意) 切換器
    │   ├── IngredientSelector.tsx # 食材分類勾選與自由輸入區
    │   ├── LoadingState.tsx     # 生成等待動態與輪播提示
    │   └── RecipeCard.tsx       # 食譜卡片、材料清單、步驟、來源標註
    ├── data/
    │   └── ingredients.ts       # 常見食材分類預設資料庫
    └── types/
        └── recipe.ts            # 食譜與資料傳遞型別定義
```

import { NextRequest, NextResponse } from 'next/server';
import { GenerateRecipePayload, Recipe } from '@/types/recipe';

const GEMINI_MODELS = [
  'gemini-3.5-flash',
  'gemini-3.1-flash-lite',
  'gemini-3.7-flash',
  'gemini-3.8-flash',
];

export async function POST(req: NextRequest) {
  try {
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey || apiKey === 'your_gemini_api_key_here') {
      return NextResponse.json(
        { error: '尚未設定 GEMINI_API_KEY，請在 .env.local 檔案中填寫有效的 API Key。' },
        { status: 500 }
      );
    }

    const body: GenerateRecipePayload = await req.json();
    const { selectedIngredients = [], freeTextIngredients = '', mode = 'real', tastePreference = '' } = body;

    const hasSelected = selectedIngredients.length > 0;
    const hasFreeText = freeTextIngredients.trim().length > 0;

    if (!hasSelected && !hasFreeText) {
      return NextResponse.json(
        { error: '請至少選擇或輸入一項食材或調味料！' },
        { status: 400 }
      );
    }

    // Build prompt based on mode
    const selectedListStr = selectedIngredients.length > 0 ? selectedIngredients.join('、') : '無特別勾選';
    const freeTextStr = freeTextIngredients.trim() || '無額外手動輸入';
    const preferenceStr = tastePreference.trim() ? `【口味偏好/需求】：${tastePreference}` : '';

    let modeInstruction = '';
    if (mode === 'real') {
      modeInstruction = `
【生成模式：A - 網路真實食譜檢索】
1. 請以真實存在於知名料理平台（如：愛料理 iCook、Cookpad 台灣、楊桃美食網、食譜自由配等）上的真實經典食譜為依據。
2. 必須在 "sources" 陣列中，【明確標明來源名稱與參考連結】。
   - 範例格式：
     {
       "name": "愛料理 iCook - 經典蒜香高麗菜",
       "url": "https://icook.tw/search/蒜香高麗菜"
     }
3. 料理必須合理可行，不可捏造難以執行的做法。
`;
    } else {
      modeInstruction = `
【生成模式：B - AI 創意食譜實驗室】
1. 請以 AI 創意名廚身份，根據現有食材大膽發揮，構想出一道新穎、美味且烹調邏輯可行的創意料理。
2. 即使食材組合看似衝突（例如泡麵配起司番茄、或水果入鹹菜），也請運用廚藝技巧將其化為和諧美味的菜餚。
3. 在 "sources" 陣列中標明：
     {
       "name": "AI 創意主廚實驗室 (原創構思料理)",
       "url": ""
     }
4. 請在 "chefAdvice" 中特別點評這道料理的【風味碰撞巧思與料理秘訣】。
`;
    }

    const prompt = `
你是一位米其林等級的專業主廚兼食譜資料庫專家。使用者現有以下材料：

【勾選的現有材料】：${selectedListStr}
【額外補充/自由描述】：${freeTextStr}
${preferenceStr}

${modeInstruction}

請將使用者現有的食材與可能還需補充的材料清楚分類：
- "ownedIngredients"：包含使用者已有或勾選的食材。
- "additionalIngredients"：若此料理還需要額外常見配料（如水、少量蔥花等），列於此處，若不需要額外材料則回傳空陣列 []。

【輸出規範】：
必須【嚴格且僅能】輸出標準 JSON 物件，請勿包含任何 markdown 標記（如 \`\`\`json 或 \`\`\`），不要輸出任何 JSON 以外的文字。

JSON 資料規格定義：
{
  "id": "recipe_${Date.now()}",
  "title": "菜餚名稱",
  "summary": "一句話吸引人的菜色特色介紹（約 30-50 字）",
  "mode": "${mode}",
  "cookTime": "烹調時間（如：15 分鐘）",
  "prepTime": "備料時間（如：10 分鐘）",
  "difficulty": "簡單 | 中等 | 進階",
  "servings": "份量（如：2 人份）",
  "ownedIngredients": [
    { "name": "材料名稱", "amount": "份量（如：半顆、2大匙）", "isOwned": true }
  ],
  "additionalIngredients": [
    { "name": "材料名稱", "amount": "份量（如：適量、少許）", "isOwned": false }
  ],
  "steps": [
    {
      "stepNumber": 1,
      "title": "步驟小標題（如：食材清洗與切塊）",
      "instruction": "具體詳細的烹調操作說明",
      "tip": "此步驟的小撇步或注意事項（選填，若無可留空字串）"
    }
  ],
  "sources": [
    { "name": "來源網站名稱或食譜名", "url": "來源網址或搜尋網址" }
  ],
  "chefAdvice": "主廚建議與美味秘訣"
}
`;

    let recipeResult: Recipe | null = null;
    let lastError: any = null;

    // Try candidate models with fallback
    for (const model of GEMINI_MODELS) {
      try {
        const response = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
              generationConfig: {
                responseMimeType: 'application/json',
                temperature: mode === 'creative' ? 0.8 : 0.4,
              },
            }),
          }
        );

        if (!response.ok) {
          const errData = await response.text();
          console.warn(`Model ${model} returned error status ${response.status}:`, errData);
          lastError = `Model ${model} (${response.status}): ${errData}`;
          continue; // Try next model
        }

        const data = await response.json();
        const rawContent = data?.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!rawContent) {
          console.warn(`Model ${model} returned empty content.`);
          continue;
        }

        // Clean any accidental markdown fence
        let cleanJson = rawContent.trim();
        if (cleanJson.startsWith('```json')) {
          cleanJson = cleanJson.replace(/^```json\s*/, '').replace(/\s*```$/, '');
        } else if (cleanJson.startsWith('```')) {
          cleanJson = cleanJson.replace(/^```\s*/, '').replace(/\s*```$/, '');
        }

        const parsed = JSON.parse(cleanJson);
        parsed.id = parsed.id || `recipe_${Date.now()}`;
        parsed.mode = mode;
        recipeResult = parsed;
        break; // Successfully generated and parsed
      } catch (err: any) {
        console.warn(`Error attempting model ${model}:`, err.message);
        lastError = err.message;
      }
    }

    if (!recipeResult) {
      return NextResponse.json(
        {
          error: 'AI 服務目前連線繁忙或配額受限，請稍候 30 秒再試一次！',
          details: String(lastError)
        },
        { status: 503 }
      );
    }

    return NextResponse.json(recipeResult);
  } catch (error: any) {
    console.error('API Error in /api/recipe:', error);
    return NextResponse.json(
      { error: '伺服器處理發生錯誤，請稍後重試。', details: error.message },
      { status: 500 }
    );
  }
}

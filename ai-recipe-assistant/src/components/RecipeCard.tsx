'use client';

import React, { useState } from 'react';
import { Recipe } from '@/types/recipe';
import {
  Clock,
  Gauge,
  Users,
  CheckCircle,
  ShoppingCart,
  ExternalLink,
  Copy,
  Check,
  Printer,
  Sparkles,
  Globe,
  Lightbulb,
  Share2
} from 'lucide-react';

interface RecipeCardProps {
  recipe: Recipe;
  onReset: () => void;
}

export default function RecipeCard({ recipe, onReset }: RecipeCardProps) {
  const [copied, setCopied] = useState(false);

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case '簡單':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case '中等':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case '進階':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      default:
        return 'bg-stone-100 text-stone-800 border-stone-200';
    }
  };

  const handleCopyRecipe = () => {
    const text = `🍽️ 【${recipe.title}】
⏱️ 備料：${recipe.prepTime} | 烹調：${recipe.cookTime} | 難度：${recipe.difficulty} | 份量：${recipe.servings}

📝 【特色介紹】
${recipe.summary}

🥗 【現有食材】
${recipe.ownedIngredients.map((i) => `• ${i.name}：${i.amount}`).join('\n')}

🛒 【額外補充材料】
${recipe.additionalIngredients.length > 0 ? recipe.additionalIngredients.map((i) => `• ${i.name}：${i.amount}`).join('\n') : '無'}

👩‍🍳 【料理步驟】
${recipe.steps.map((s) => `${s.stepNumber}. 【${s.title}】${s.instruction} ${s.tip ? `(秘訣: ${s.tip})` : ''}`).join('\n\n')}

💡 【主廚秘訣】
${recipe.chefAdvice || '趁熱享用風味最佳！'}

${recipe.sources && recipe.sources.length > 0 && recipe.sources[0].url ? `🔗 【參考來源】：${recipe.sources.map((s) => `${s.name} (${s.url})`).join(', ')}` : ''}
`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <article className="bg-white rounded-3xl border border-stone-200/90 shadow-md overflow-hidden transition-all print:border-none print:shadow-none">
      {/* Top Banner / Mode & Actions */}
      <div className="bg-gradient-to-r from-orange-500 via-amber-500 to-amber-600 p-6 sm:p-8 text-white relative">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold tracking-wide">
            {recipe.mode === 'real' ? (
              <>
                <Globe className="w-3.5 h-3.5" />
                模式 A：網路真實食譜檢索
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                模式 B：AI 創意料理實驗室
              </>
            )}
          </div>

          <div className="flex items-center gap-2 print:hidden">
            <button
              type="button"
              onClick={handleCopyRecipe}
              className="text-xs px-3 py-1.5 rounded-xl bg-white/20 hover:bg-white/30 backdrop-blur-md transition-colors flex items-center gap-1.5 font-medium cursor-pointer"
              title="複製全文至剪貼簿"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-200" />
                  已複製！
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  複製食譜
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handlePrint}
              className="text-xs px-3 py-1.5 rounded-xl bg-white/20 hover:bg-white/30 backdrop-blur-md transition-colors flex items-center gap-1.5 font-medium cursor-pointer"
              title="友善列印"
            >
              <Printer className="w-3.5 h-3.5" />
              列印
            </button>
          </div>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight drop-shadow-xs">
          {recipe.title}
        </h1>
        <p className="text-amber-100 text-xs sm:text-sm mt-2 max-w-2xl leading-relaxed">
          {recipe.summary}
        </p>

        {/* Recipe Meta Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-5">
          <div className="bg-black/15 backdrop-blur-sm rounded-xl p-2.5 flex items-center gap-2.5">
            <Clock className="w-4 h-4 text-amber-200 shrink-0" />
            <div>
              <div className="text-[10px] text-amber-200 uppercase font-medium">烹調時間</div>
              <div className="text-xs sm:text-sm font-bold">{recipe.cookTime}</div>
            </div>
          </div>

          <div className="bg-black/15 backdrop-blur-sm rounded-xl p-2.5 flex items-center gap-2.5">
            <Clock className="w-4 h-4 text-amber-200 shrink-0" />
            <div>
              <div className="text-[10px] text-amber-200 uppercase font-medium">備料時間</div>
              <div className="text-xs sm:text-sm font-bold">{recipe.prepTime}</div>
            </div>
          </div>

          <div className="bg-black/15 backdrop-blur-sm rounded-xl p-2.5 flex items-center gap-2.5">
            <Gauge className="w-4 h-4 text-amber-200 shrink-0" />
            <div>
              <div className="text-[10px] text-amber-200 uppercase font-medium">料理難度</div>
              <div className="text-xs sm:text-sm font-bold">{recipe.difficulty}</div>
            </div>
          </div>

          <div className="bg-black/15 backdrop-blur-sm rounded-xl p-2.5 flex items-center gap-2.5">
            <Users className="w-4 h-4 text-amber-200 shrink-0" />
            <div>
              <div className="text-[10px] text-amber-200 uppercase font-medium">建議份量</div>
              <div className="text-xs sm:text-sm font-bold">{recipe.servings}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Body Content */}
      <div className="p-6 sm:p-8 space-y-8">
        {/* Ingredients Block: Owned vs Additional */}
        <section>
          <h2 className="text-lg font-bold text-stone-900 mb-4 flex items-center gap-2">
            <span>🥗</span> 食材與調味料清單
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Owned Ingredients */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4">
              <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm mb-3">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                現有食材 / 已具備材料 ({recipe.ownedIngredients.length})
              </div>
              <ul className="divide-y divide-emerald-100 text-xs sm:text-sm">
                {recipe.ownedIngredients.map((item, idx) => (
                  <li key={idx} className="py-2 flex items-center justify-between">
                    <span className="font-medium text-stone-800">{item.name}</span>
                    <span className="text-emerald-700 font-semibold bg-emerald-100/60 px-2 py-0.5 rounded-md">
                      {item.amount}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Additional / Optional Ingredients */}
            <div className="rounded-2xl border border-amber-200 bg-amber-50/40 p-4">
              <div className="flex items-center gap-2 text-amber-900 font-bold text-sm mb-3">
                <ShoppingCart className="w-4 h-4 text-amber-600" />
                建議補充材料 / 常備配料 ({recipe.additionalIngredients.length})
              </div>
              {recipe.additionalIngredients.length > 0 ? (
                <ul className="divide-y divide-amber-100 text-xs sm:text-sm">
                  {recipe.additionalIngredients.map((item, idx) => (
                    <li key={idx} className="py-2 flex items-center justify-between">
                      <span className="font-medium text-stone-800">{item.name}</span>
                      <span className="text-amber-800 font-semibold bg-amber-100/60 px-2 py-0.5 rounded-md">
                        {item.amount}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-stone-500 italic py-2">
                  太棒了！手邊現有食材已完全足夠，無需額外補充。
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Step-by-Step Instructions */}
        <section>
          <h2 className="text-lg font-bold text-stone-900 mb-4 flex items-center gap-2">
            <span>👩‍🍳</span> 詳細料理步驟
          </h2>

          <div className="space-y-4">
            {recipe.steps.map((step) => (
              <div
                key={step.stepNumber}
                className="rounded-2xl border border-stone-200 p-4 sm:p-5 bg-stone-50/50 hover:bg-stone-50 transition-colors"
              >
                <div className="flex items-start gap-3 sm:gap-4">
                  <div className="w-8 h-8 rounded-full bg-orange-500 text-white font-extrabold text-sm flex items-center justify-center shrink-0 shadow-xs">
                    {step.stepNumber}
                  </div>
                  <div className="flex-1 space-y-1.5">
                    <h3 className="font-bold text-stone-900 text-sm sm:text-base">
                      {step.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-stone-700 leading-relaxed">
                      {step.instruction}
                    </p>
                    {step.tip && (
                      <div className="mt-2 text-xs bg-amber-50 text-amber-900 border border-amber-200/80 rounded-xl p-2.5 flex items-start gap-2">
                        <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">主廚撇步：</span>
                          <span>{step.tip}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Chef Advice / Cooking Wisdom */}
        {recipe.chefAdvice && (
          <section className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl border border-orange-200 p-5">
            <h3 className="text-sm font-bold text-orange-950 flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-orange-600" />
              主廚點評與美味秘訣
            </h3>
            <p className="text-xs sm:text-sm text-orange-900/90 leading-relaxed">
              {recipe.chefAdvice}
            </p>
          </section>
        )}

        {/* Sources Attribution (Crucial for Requirement #2 Mode A) */}
        {recipe.sources && recipe.sources.length > 0 && (
          <section className="border-t border-stone-200 pt-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-stone-400" />
              食譜來源與參考出處：
            </h3>
            <div className="flex flex-wrap gap-2.5">
              {recipe.sources.map((src, idx) => (
                <div
                  key={idx}
                  className="inline-flex items-center gap-2 text-xs p-3 rounded-xl bg-stone-50 border border-stone-200 text-stone-800"
                >
                  <span className="font-medium">{src.name}</span>
                  {src.url ? (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-orange-600 hover:text-orange-700 hover:underline font-semibold ml-1 cursor-pointer"
                    >
                      開啟連結
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-stone-400 text-[11px]">(AI 原創生成無外部網址)</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Bottom Actions */}
        <div className="pt-4 border-t border-stone-100 flex flex-col sm:flex-row items-center justify-between gap-3 print:hidden">
          <p className="text-xs text-stone-400">
            想要調整食材或嘗試另一種模式？
          </p>
          <button
            type="button"
            onClick={onReset}
            className="w-full sm:w-auto text-xs sm:text-sm px-5 py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-white font-medium transition-colors cursor-pointer"
          >
            返回重新挑選食材
          </button>
        </div>
      </div>
    </article>
  );
}

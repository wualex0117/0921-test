'use client';

import React, { useState, useRef } from 'react';
import Header from '@/components/Header';
import ModeSelector from '@/components/ModeSelector';
import IngredientSelector from '@/components/IngredientSelector';
import LoadingState from '@/components/LoadingState';
import RecipeCard from '@/components/RecipeCard';
import { Recipe } from '@/types/recipe';
import { ChefHat, AlertCircle, Sparkles, ArrowRight } from 'lucide-react';

export default function Home() {
  const [selectedIngredients, setSelectedIngredients] = useState<string[]>(['高麗菜', '大蒜']);
  const [freeText, setFreeText] = useState<string>('醬油適量、五花肉片');
  const [mode, setMode] = useState<'real' | 'creative'>('real');
  const [tastePreference, setTastePreference] = useState<string>('清淡少油');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recipeSectionRef = useRef<HTMLDivElement>(null);

  const totalIngredientsCount = selectedIngredients.length + (freeText.trim() ? 1 : 0);

  const handleGenerate = async () => {
    if (totalIngredientsCount === 0) {
      setError('請至少選擇一項食材或在自由輸入框填寫現有材料！');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selectedIngredients,
          freeTextIngredients: freeText,
          mode,
          tastePreference,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || '生成失敗，請稍後重試。');
      }

      setRecipe(data);

      // Smooth scroll to recipe
      setTimeout(() => {
        recipeSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      console.error('Failed to generate recipe:', err);
      setError(err.message || '發生未知錯誤，請確認網路連線或稍後再試。');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setRecipe(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        <Header />

        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-8">
          {/* Hero Welcome Banner */}
          <div className="text-center space-y-2">
            <span className="inline-block text-xs font-semibold px-3 py-1 rounded-full bg-orange-100 text-orange-800 tracking-wide">
              🍳 大學專題 · AI 料理助手
            </span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
              今天冰箱有什麼？讓 AI 為你出好菜
            </h2>
            <p className="text-xs sm:text-sm text-stone-500 max-w-xl mx-auto">
              勾選或輸入你的現有食材，支援「模式 A 網路真實食譜檢索」與「模式 B AI 創意研發」，快速解決「今天吃什麼」！
            </p>
          </div>

          {/* Mode Selector */}
          <section>
            <ModeSelector mode={mode} onChange={setMode} />
          </section>

          {/* Ingredients Input & Selection */}
          <section>
            <IngredientSelector
              selectedIngredients={selectedIngredients}
              onChangeSelected={setSelectedIngredients}
              freeText={freeText}
              onChangeFreeText={setFreeText}
              tastePreference={tastePreference}
              onChangeTastePreference={setTastePreference}
            />
          </section>

          {/* Error Banner */}
          {error && (
            <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start gap-3 text-rose-900">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-bold">生成提醒</div>
                <div className="text-xs mt-0.5">{error}</div>
              </div>
            </div>
          )}

          {/* Submit CTA Button */}
          {!isLoading && (
            <div className="pt-2">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={totalIngredientsCount === 0}
                className={`w-full py-4 px-6 rounded-2xl font-bold text-base sm:text-lg flex items-center justify-center gap-3 transition-all duration-200 cursor-pointer shadow-md ${
                  totalIngredientsCount > 0
                    ? 'bg-gradient-to-r from-orange-500 via-orange-600 to-amber-500 text-white hover:opacity-95 shadow-orange-500/25 hover:shadow-orange-500/35 active:scale-[0.99]'
                    : 'bg-stone-200 text-stone-400 cursor-not-allowed shadow-none'
                }`}
              >
                <ChefHat className="w-5 h-5" />
                <span>
                  {mode === 'real'
                    ? '開始檢索網路真實食譜'
                    : '啟動 AI 創意料理生成'}
                </span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <p className="text-center text-[11px] text-stone-400 mt-2">
                已準備 {selectedIngredients.length} 項勾選食材 {freeText.trim() ? '+ 自由備註' : ''}
              </p>
            </div>
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <section className="pt-4">
              <LoadingState mode={mode} />
            </section>
          )}

          {/* Recipe Card Presentation */}
          <section ref={recipeSectionRef}>
            {recipe && !isLoading && (
              <div className="pt-4">
                <RecipeCard recipe={recipe} onReset={handleReset} />
              </div>
            )}
          </section>
        </main>
      </div>

      {/* Footer (Compliant with no personal info / no student ID) */}
      <footer className="border-t border-stone-200 bg-white py-6 mt-12 text-center text-xs text-stone-400 print:hidden">
        <div className="max-w-4xl mx-auto px-4 space-y-1">
          <p className="font-medium text-stone-600">
            AI 食譜檢索與創作網站 · 課程期中專題報告
          </p>
          <p className="text-[11px]">
            技術棧：Next.js + Tailwind CSS + Google Gemini API · 遵循開源與環境變數資安規範
          </p>
        </div>
      </footer>
    </div>
  );
}

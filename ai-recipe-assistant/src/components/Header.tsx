'use client';

import React from 'react';
import { ChefHat, Sparkles, ShieldCheck } from 'lucide-react';

export default function Header() {
  return (
    <header className="border-b border-stone-200 bg-white/80 backdrop-blur-md sticky top-0 z-30 shadow-xs">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-center sm:text-left">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-white shadow-md shadow-orange-500/20">
            <ChefHat className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <h1 className="text-xl font-bold text-stone-900 tracking-tight">AI 食譜檢索與創作小助手</h1>
              <span className="hidden md:inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium">
                <Sparkles className="w-3 h-3" /> 雙模式 AI
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-0.5">
              輸入冰箱現有食材，即刻檢索真實網路食譜或激發 AI 創意美味
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-3 py-1 rounded-full font-medium shadow-2xs">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            金鑰環境變數安全保護
          </span>
        </div>
      </div>
    </header>
  );
}

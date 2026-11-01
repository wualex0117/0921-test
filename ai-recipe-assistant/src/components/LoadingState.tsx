'use client';

import React, { useEffect, useState } from 'react';
import { Sparkles, Utensils, Search, Flame } from 'lucide-react';

interface LoadingStateProps {
  mode: 'real' | 'creative';
}

const REAL_MODE_TIPS = [
  '正在料理資料庫與知名網站中搜尋匹配配方...',
  '正在篩選評價最高且步驟清楚的經典家常做法...',
  '正在驗證食譜來源與食材準備清單...',
  '正在梳理步驟教學與烹調要訣，馬上就來...'
];

const CREATIVE_MODE_TIPS = [
  'AI 創意主廚正在啟動料理實驗室...',
  '正在計算現有食材的風味分子搭配...',
  '正在構思意想不到但極具可行性的美味作法...',
  '正在為您調配黃金醬汁比例與主廚獨門秘訣...'
];

export default function LoadingState({ mode }: LoadingStateProps) {
  const [tipIndex, setTipIndex] = useState(0);
  const tips = mode === 'real' ? REAL_MODE_TIPS : CREATIVE_MODE_TIPS;

  useEffect(() => {
    const timer = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % tips.length);
    }, 2800);
    return () => clearInterval(timer);
  }, [tips.length]);

  return (
    <div className="bg-white rounded-3xl border border-stone-200 p-8 sm:p-12 shadow-sm text-center flex flex-col items-center justify-center space-y-6">
      {/* Animated Pan / Icon */}
      <div className="relative">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-white shadow-lg shadow-orange-500/25 animate-bounce">
          {mode === 'real' ? (
            <Search className="w-10 h-10" />
          ) : (
            <Sparkles className="w-10 h-10" />
          )}
        </div>
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-orange-500"></span>
        </span>
      </div>

      <div className="space-y-2 max-w-md">
        <h3 className="text-lg sm:text-xl font-bold text-stone-900 flex items-center justify-center gap-2">
          <Flame className="w-5 h-5 text-orange-500 animate-pulse" />
          {mode === 'real' ? '正在為您檢索最佳真實食譜...' : 'AI 主廚正在創作專屬食譜...'}
        </h3>
        <p className="text-xs sm:text-sm text-stone-500 transition-all duration-300 min-h-[2.5rem] flex items-center justify-center">
          {tips[tipIndex]}
        </p>
      </div>

      {/* Progress Bar Animation */}
      <div className="w-48 sm:w-64 bg-stone-100 rounded-full h-2 overflow-hidden">
        <div className="bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 h-full rounded-full animate-pulse-slow w-3/4"></div>
      </div>
    </div>
  );
}

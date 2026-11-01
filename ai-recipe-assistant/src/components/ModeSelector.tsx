'use client';

import React from 'react';
import { Globe, Sparkles, CheckCircle2 } from 'lucide-react';

interface ModeSelectorProps {
  mode: 'real' | 'creative';
  onChange: (mode: 'real' | 'creative') => void;
}

export default function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="w-full">
      <label className="block text-sm font-semibold text-stone-700 mb-2">
        請選擇 AI 生成模式：
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Mode A */}
        <button
          type="button"
          onClick={() => onChange('real')}
          className={`relative p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-start gap-3.5 ${
            mode === 'real'
              ? 'bg-amber-50/70 border-amber-500 shadow-sm ring-2 ring-amber-500/20'
              : 'bg-white border-stone-200 hover:border-amber-300 hover:bg-stone-50/50'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              mode === 'real'
                ? 'bg-amber-500 text-white shadow-sm shadow-amber-500/30'
                : 'bg-stone-100 text-stone-600'
            }`}
          >
            <Globe className="w-5 h-5" />
          </div>

          <div className="flex-1 pr-6">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-stone-900 text-sm">模式 A：網路真實食譜</span>
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                附來源標註
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-1 leading-relaxed">
              檢索知名料理網站（如愛料理、Cookpad）的經典家常做法，明確標示來源網站與參考連結。
            </p>
          </div>

          {mode === 'real' && (
            <div className="absolute top-3.5 right-3.5 text-amber-600">
              <CheckCircle2 className="w-5 h-5 fill-amber-100" />
            </div>
          )}
        </button>

        {/* Mode B */}
        <button
          type="button"
          onClick={() => onChange('creative')}
          className={`relative p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-start gap-3.5 ${
            mode === 'creative'
              ? 'bg-orange-50/70 border-orange-500 shadow-sm ring-2 ring-orange-500/20'
              : 'bg-white border-stone-200 hover:border-orange-300 hover:bg-stone-50/50'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              mode === 'creative'
                ? 'bg-orange-500 text-white shadow-sm shadow-orange-500/30'
                : 'bg-stone-100 text-stone-600'
            }`}
          >
            <Sparkles className="w-5 h-5" />
          </div>

          <div className="flex-1 pr-6">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-stone-900 text-sm">模式 B：AI 創意食譜</span>
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-orange-100 text-orange-800">
                主廚靈感
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-1 leading-relaxed">
              根據現有食材大膽激盪，由 AI 名廚構思新穎、美味且兼具可行性的原創料理。
            </p>
          </div>

          {mode === 'creative' && (
            <div className="absolute top-3.5 right-3.5 text-orange-600">
              <CheckCircle2 className="w-5 h-5 fill-orange-100" />
            </div>
          )}
        </button>
      </div>
    </div>
  );
}

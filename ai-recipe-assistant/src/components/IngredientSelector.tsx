'use client';

import React, { useState } from 'react';
import { INGREDIENT_CATEGORIES } from '@/data/ingredients';
import { Plus, X, RotateCcw, Sparkles, Check, Edit3, Tag } from 'lucide-react';

interface IngredientSelectorProps {
  selectedIngredients: string[];
  onChangeSelected: (items: string[]) => void;
  freeText: string;
  onChangeFreeText: (text: string) => void;
  tastePreference: string;
  onChangeTastePreference: (pref: string) => void;
}

const PRESET_EXAMPLES = [
  '半顆高麗菜、豬肉片、大蒜、醬油',
  '雞蛋2顆、白飯1碗、青蔥、黑胡椒',
  '嫩豆腐1盒、豬絞肉、豆瓣醬、生薑',
  '義大利麵、培根2條、蒜頭、橄欖油'
];

const PRESET_PREFERENCES = [
  '清淡少油', '微辣開胃', '15分鐘快炒', '下酒好菜', '減脂高蛋白', '便當菜推薦'
];

export default function IngredientSelector({
  selectedIngredients,
  onChangeSelected,
  freeText,
  onChangeFreeText,
  tastePreference,
  onChangeTastePreference,
}: IngredientSelectorProps) {
  const [activeCategory, setActiveCategory] = useState<string>(INGREDIENT_CATEGORIES[0].id);

  const toggleItem = (item: string) => {
    if (selectedIngredients.includes(item)) {
      onChangeSelected(selectedIngredients.filter((i) => i !== item));
    } else {
      onChangeSelected([...selectedIngredients, item]);
    }
  };

  const handleClearAll = () => {
    onChangeSelected([]);
    onChangeFreeText('');
    onChangeTastePreference('');
  };

  const handleRandomInspiration = () => {
    const randomExample = PRESET_EXAMPLES[Math.floor(Math.random() * PRESET_EXAMPLES.length)];
    onChangeFreeText(randomExample);
  };

  return (
    <div className="bg-white rounded-3xl border border-stone-200/80 p-5 sm:p-7 shadow-xs space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-100 pb-4">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-stone-900 flex items-center gap-2">
            <span>🥕</span> 食材與調味料選擇
          </h2>
          <p className="text-xs text-stone-500 mt-0.5">
            可直接勾選常見食材，或在下方以文字自由補充份量與特殊調味
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleRandomInspiration}
            className="text-xs px-3 py-1.5 rounded-xl border border-orange-200 text-orange-700 bg-orange-50/70 hover:bg-orange-100/70 transition-colors flex items-center gap-1.5 font-medium cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            靈感範例
          </button>
          {(selectedIngredients.length > 0 || freeText || tastePreference) && (
            <button
              type="button"
              onClick={handleClearAll}
              className="text-xs px-3 py-1.5 rounded-xl border border-stone-200 text-stone-600 hover:bg-stone-100 transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              清空重選
            </button>
          )}
        </div>
      </div>

      {/* Selected Items summary tags */}
      {selectedIngredients.length > 0 && (
        <div className="bg-amber-50/50 rounded-2xl p-3 border border-amber-200/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
              <span>📌</span> 已勾選食材 ({selectedIngredients.length} 項)：
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {selectedIngredients.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-white border border-amber-300 text-stone-800 shadow-2xs font-medium"
              >
                {item}
                <button
                  type="button"
                  onClick={() => toggleItem(item)}
                  className="text-stone-400 hover:text-stone-700 ml-0.5 cursor-pointer"
                  title="移除此項"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2.5">
          常見食材/調味快速勾選清單：
        </label>
        <div className="flex flex-wrap gap-1.5 border-b border-stone-200 pb-3">
          {INGREDIENT_CATEGORIES.map((cat) => {
            const isCurrent = activeCategory === cat.id;
            const countInCat = cat.items.filter((i) => selectedIngredients.includes(i)).length;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setActiveCategory(cat.id)}
                className={`text-xs px-3 py-1.5 rounded-xl font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                  isCurrent
                    ? 'bg-stone-900 text-white shadow-xs'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200/80'
                }`}
              >
                <span>{cat.icon}</span>
                <span>{cat.name}</span>
                {countInCat > 0 && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                      isCurrent ? 'bg-orange-500 text-white' : 'bg-stone-300 text-stone-800'
                    }`}
                  >
                    {countInCat}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Category Items Pill Grid */}
        <div className="pt-3.5">
          {INGREDIENT_CATEGORIES.map((cat) => {
            if (cat.id !== activeCategory) return null;
            return (
              <div key={cat.id} className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {cat.items.map((item) => {
                  const isChecked = selectedIngredients.includes(item);
                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => toggleItem(item)}
                      className={`text-xs p-2.5 rounded-xl border text-left transition-all duration-150 flex items-center justify-between cursor-pointer ${
                        isChecked
                          ? 'bg-orange-50 border-orange-400 text-orange-950 font-semibold shadow-2xs'
                          : 'bg-stone-50/50 border-stone-200 text-stone-700 hover:bg-stone-100/70 hover:border-stone-300'
                      }`}
                    >
                      <span>{item}</span>
                      <div
                        className={`w-4 h-4 rounded-md flex items-center justify-center transition-colors ${
                          isChecked ? 'bg-orange-500 text-white' : 'border border-stone-300 bg-white'
                        }`}
                      >
                        {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Free Text Input Section */}
      <div className="pt-2 border-t border-stone-100 space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
          <Edit3 className="w-3.5 h-3.5 text-stone-400" />
          自由文字補充（特殊食材、精確份量或未在清單上的材料）：
        </label>
        <textarea
          rows={3}
          value={freeText}
          onChange={(e) => onChangeFreeText(e.target.value)}
          placeholder="例如：半顆高麗菜、醬油、蠔油、大蒜3瓣、剩餘的半罐玉米粒..."
          className="w-full text-sm p-3.5 rounded-2xl border border-stone-300 bg-stone-50/30 focus:bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-all placeholder:text-stone-400"
        />
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] text-stone-500">
          <span className="font-medium text-stone-600">快速填入範例：</span>
          {PRESET_EXAMPLES.map((ex, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onChangeFreeText(ex)}
              className="text-stone-600 hover:text-orange-600 underline decoration-stone-300 underline-offset-2 cursor-pointer"
            >
              {ex.split('、')[0]}...
            </button>
          ))}
        </div>
      </div>

      {/* Taste & Cooking Preference */}
      <div className="pt-2 border-t border-stone-100 space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
          <Tag className="w-3.5 h-3.5 text-stone-400" />
          口味偏好或料理限制（選填）：
        </label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {PRESET_PREFERENCES.map((pref) => {
            const isSelected = tastePreference === pref;
            return (
              <button
                key={pref}
                type="button"
                onClick={() => onChangeTastePreference(isSelected ? '' : pref)}
                className={`text-xs px-2.5 py-1 rounded-lg border transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-amber-100 border-amber-400 text-amber-900 font-medium'
                    : 'bg-white border-stone-200 text-stone-600 hover:bg-stone-50'
                }`}
              >
                {pref}
              </button>
            );
          })}
        </div>
        <input
          type="text"
          value={tastePreference}
          onChange={(e) => onChangeTastePreference(e.target.value)}
          placeholder="或自行輸入：如無辣、電鍋料理、一人份便當、高蛋白質..."
          className="w-full text-xs p-2.5 rounded-xl border border-stone-300 bg-stone-50/30 focus:bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-stone-400"
        />
      </div>
    </div>
  );
}

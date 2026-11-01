export interface RecipeIngredient {
  name: string;
  amount: string;
  isOwned: boolean;
}

export interface RecipeStep {
  stepNumber: number;
  title: string;
  instruction: string;
  tip?: string;
}

export interface RecipeSource {
  name: string;
  url: string;
}

export interface Recipe {
  id: string;
  title: string;
  summary: string;
  mode: 'real' | 'creative';
  cookTime: string;
  prepTime: string;
  difficulty: '簡單' | '中等' | '進階';
  servings: string;
  ownedIngredients: RecipeIngredient[];
  additionalIngredients: RecipeIngredient[];
  steps: RecipeStep[];
  sources: RecipeSource[];
  chefAdvice?: string;
}

export interface GenerateRecipePayload {
  selectedIngredients: string[];
  freeTextIngredients: string;
  mode: 'real' | 'creative';
  tastePreference?: string;
}

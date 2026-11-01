export interface IngredientCategory {
  id: string;
  name: string;
  icon: string;
  items: string[];
}

export const INGREDIENT_CATEGORIES: IngredientCategory[] = [
  {
    id: 'vegetables',
    name: '蔬菜根莖',
    icon: '🥦',
    items: [
      '高麗菜', '洋蔥', '胡蘿蔔', '番茄', '青蔥',
      '大蒜', '生薑', '花椰菜', '馬鈴薯', '香菇',
      '青椒', '玉米筍', '菠菜', '木耳'
    ]
  },
  {
    id: 'meat_seafood',
    name: '肉品海鮮',
    icon: '🥩',
    items: [
      '豬肉片', '牛肉片', '雞胸肉', '去骨雞腿肉', '豬絞肉',
      '培根', '香腸', '鮮蝦', '蛤蜊', '鮭魚片', '鯛魚片'
    ]
  },
  {
    id: 'egg_tofu',
    name: '蛋豆奶類',
    icon: '🍳',
    items: [
      '雞蛋', '嫩豆腐', '板豆腐', '豆皮', '起司片', '牛奶', '毛豆'
    ]
  },
  {
    id: 'staples',
    name: '主食穀物',
    icon: '🍚',
    items: [
      '白飯/隔夜飯', '麵條', '冬粉/粉條', '義大利麵', '白吐司', '烏龍麵'
    ]
  },
  {
    id: 'seasonings',
    name: '基礎調味',
    icon: '🧂',
    items: [
      '醬油', '蠔油', '食鹽', '白砂糖', '黑白胡椒',
      '料理米酒', '烏醋/白醋', '香油', '番茄醬', '沙茶醬'
    ]
  },
  {
    id: 'spices',
    name: '辛香風味',
    icon: '🌶️',
    items: [
      '生辣椒', '咖哩塊/咖哩粉', '辣椒醬/豆瓣醬', '義大利香料', '七味唐辛子', '味噌'
    ]
  }
];

import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Apple,
  Search,
  Scale,
  Sparkles,
  Flame,
  Wheat,
  Beef,
  Droplets,
  ShieldCheck,
  Languages,
  RefreshCw,
  X,
  ExternalLink,
  ChevronRight,
  Info,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  Download,
  Utensils
} from 'lucide-react';

const CATEGORIES = [
  'All',
  'Fruits and Fruit Juices',
  'Vegetables and Vegetable Products',
  'Dairy and Egg Products',
  'Poultry Products',
  'Finfish and Shellfish Products',
  'Cereal Grains and Pasta',
  'Nut and Seed Products',
  'Legumes and Legume Products'
];

const NutritionPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Comparison state
  const [compareList, setCompareList] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [comparing, setComparing] = useState(false);

  // AI Explanation state
  const [aiExplanation, setAiExplanation] = useState(null);
  const [aiLanguage, setAiLanguage] = useState('en');
  const [explaining, setExplaining] = useState(false);

  // Lab-Connected Nutrition Insights state
  const [labInsights, setLabInsights] = useState([]);
  const [loadingInsights, setLoadingInsights] = useState(false);

  const fetchLabInsights = async () => {
    try {
      setLoadingInsights(true);
      const res = await api.get('/nutrition/report-recommendations');
      setLabInsights(res.data?.insights || []);
    } catch (err) {
      console.error('Failed to load lab nutrition insights:', err);
    } finally {
      setLoadingInsights(false);
    }
  };

  const fetchFoods = async (query = '', category = 'All') => {
    try {
      setLoading(true);
      const params = {};
      if (query.trim()) params.query = query.trim();
      if (category !== 'All') params.category = category;
      params.limit = 20;

      const res = await api.get('/nutrition/search', { params });
      setSearchResults(res.data || []);
      if (res.data && res.data.length > 0 && !selectedFood) {
        setSelectedFood(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to search foods:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFoods(searchQuery, selectedCategory);
  }, [selectedCategory]);

  useEffect(() => {
    fetchLabInsights();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchFoods(searchQuery, selectedCategory);
  };

  const handleSelectFood = (food) => {
    setSelectedFood(food);
    setAiExplanation(null);
  };

  const handleToggleCompare = (food) => {
    if (compareList.some((f) => f.fdc_id === food.fdc_id)) {
      setCompareList((prev) => prev.filter((f) => f.fdc_id !== food.fdc_id));
    } else {
      if (compareList.length >= 4) {
        alert('You can compare up to 4 foods simultaneously.');
        return;
      }
      setCompareList((prev) => [...prev, food]);
    }
  };

  useEffect(() => {
    if (compareList.length > 0) {
      fetchComparison();
    } else {
      setComparisonData(null);
    }
  }, [compareList]);

  const fetchComparison = async () => {
    if (compareList.length === 0) return;
    try {
      setComparing(true);
      const fdc_ids = compareList.map((f) => f.fdc_id).join(',');
      const res = await api.get('/nutrition/compare', { params: { fdc_ids } });
      setComparisonData(res.data);
    } catch (err) {
      console.error('Failed to fetch comparison:', err);
    } finally {
      setComparing(false);
    }
  };

  const handleExplain = async (food, lang = aiLanguage) => {
    if (!food) return;
    try {
      setExplaining(true);
      setAiLanguage(lang);
      const res = await api.post('/nutrition/explain', {
        fdc_id: food.fdc_id,
        language: lang
      });
      setAiExplanation(res.data);
    } catch (err) {
      console.error('Failed to generate nutrition explanation:', err);
    } finally {
      setExplaining(false);
    }
  };

  const n = selectedFood?.nutrients || {};

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              USDA FoodData Central
            </span>
            <span className="text-xs text-slate-400">
              • Verified Whole Foods Intelligence
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            Nutrition Analysis & Hydration Monitoring
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl mt-0.5">
            Real-time dietary tracking, micronutrient density evaluation, and grounded trilingual clinical nutrition intelligence.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-xs font-semibold text-slate-500 flex items-center space-x-1.5 bg-white dark:bg-slate-800 px-3.5 py-2 rounded-xl border border-slate-200/90 dark:border-slate-700 shadow-2xs">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>USDA Verified Database</span>
          </span>
        </div>
      </div>

      {/* Top Nutrition & Hydration Cards matching nutrition.png */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Energy & Caloric Density */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Daily Caloric Target
            </span>
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-black text-slate-900 dark:text-white font-heading">
              1,840
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 2,200 kcal</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="bg-amber-500 h-2 rounded-full" style={{ width: '83%' }}></div>
          </div>
          <p className="text-[11px] text-slate-400">83% of daily metabolic benchmark achieved</p>
        </div>

        {/* Card 2: Hydration Intake */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Hydration Monitoring
            </span>
            <div className="p-2 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600">
              <Droplets className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-black text-slate-900 dark:text-white font-heading">
              2.4
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 3.0 Liters</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="bg-teal-500 h-2 rounded-full" style={{ width: '80%' }}></div>
          </div>
          <p className="text-[11px] text-emerald-600 font-bold">Optimal fluid balance maintained</p>
        </div>

        {/* Card 3: Macronutrient Ratio */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Macronutrient Balance
            </span>
            <div className="p-2 rounded-xl bg-sky-50 dark:bg-sky-950 text-sky-600">
              <Utensils className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-center space-x-2 pt-1 text-xs font-bold">
            <span className="text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded-md">Carbs 45%</span>
            <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">Protein 30%</span>
            <span className="text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md">Fat 25%</span>
          </div>
          <div className="w-full flex rounded-full h-2 overflow-hidden">
            <div className="bg-cyan-500 h-2" style={{ width: '45%' }}></div>
            <div className="bg-emerald-500 h-2" style={{ width: '30%' }}></div>
            <div className="bg-rose-500 h-2" style={{ width: '25%' }}></div>
          </div>
          <p className="text-[11px] text-slate-400">Nutritionally calibrated whole food intake</p>
        </div>
      </div>

      {/* Lab-Connected Nutrition Insights Section */}
      {labInsights && labInsights.length > 0 && (
        <div className="p-5 bg-gradient-to-br from-teal-50/80 to-emerald-50/60 dark:from-teal-950/40 dark:to-emerald-950/30 rounded-2xl border border-teal-200/90 dark:border-teal-800 shadow-2xs space-y-4 animate-in fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-teal-200/60 dark:border-teal-800/60">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                  Lab-Connected Nutrition Insights ({labInsights.length} Biomarkers Flagged)
                </h3>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Grounded whole food recommendations mapped from your verified clinical blood and laboratory reports.
                </p>
              </div>
            </div>
            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900 text-teal-800 dark:text-teal-200 border border-teal-300 dark:border-teal-700">
              USDA FoodData Grounded
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {labInsights.map((insight, idx) => (
              <div
                key={idx}
                className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-teal-200/80 dark:border-teal-800/80 shadow-2xs space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 bg-rose-50 dark:bg-rose-950/60 px-2 py-0.5 rounded-md border border-rose-200">
                      Below Reference Interval
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white mt-1">
                      {insight.canonical_name || insight.test_name}
                    </h4>
                    <p className="text-xs text-slate-500 font-medium">
                      Observed: <strong className="text-rose-600">{insight.observed_value} {insight.unit}</strong> • Ref: {insight.reference_range}
                    </p>
                  </div>
                </div>

                <p className="text-[11px] text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
                  <strong>{insight.relevant_nutrient}:</strong> {insight.nutrient_context}
                </p>

                <div>
                  <h5 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider">
                    Foods containing this nutrient (USDA):
                  </h5>
                  <div className="space-y-1.5">
                    {insight.suggested_foods.map((food, fIdx) => (
                      <div
                        key={fIdx}
                        className="p-2 rounded-lg bg-teal-50/50 dark:bg-slate-800/60 border border-teal-100 dark:border-slate-700 flex items-center justify-between text-xs"
                      >
                        <div className="min-w-0">
                          <span className="font-bold text-slate-800 dark:text-slate-200 block truncate">
                            {food.food_name}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            Serving: {food.serving_size} • {food.source}
                          </span>
                        </div>
                        <div className="text-right shrink-0 ml-2">
                          <span className="text-xs font-bold text-teal-700 dark:text-teal-300 block">
                            {food.nutrient_amount} {food.nutrient_unit}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {food.calories_kcal} kcal
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-100 dark:border-slate-800">
                  {insight.disclaimer}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Category Filter Bar */}
      <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search USDA food items (e.g. Apple, Salmon, Oats, Spinach, Almonds)..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/30"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-xl shrink-0 font-bold transition-colors ${
                selectedCategory === cat
                  ? 'bg-teal-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              {cat === 'All' ? 'All Categories' : cat.split(' and ')[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Main Workspace Split: Search Results & Detailed Nutrition Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Food List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-heading flex items-center justify-between">
              <span>Foundation Foods ({searchResults.length})</span>
              <span className="text-[10px] font-normal text-slate-400">Per 100g Edible</span>
            </h2>

            {searchResults.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                No matching foods found in USDA Foundation Foods.
              </p>
            ) : (
              <div className="space-y-1.5 max-h-[560px] overflow-y-auto pr-1">
                {searchResults.map((food) => {
                  const isSelected = selectedFood?.fdc_id === food.fdc_id;
                  const isCompared = compareList.some((f) => f.fdc_id === food.fdc_id);
                  return (
                    <div
                      key={food.fdc_id}
                      onClick={() => handleSelectFood(food)}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition-all flex items-center justify-between ${
                        isSelected
                          ? 'bg-teal-50/70 dark:bg-teal-950/60 border-teal-500 ring-1 ring-teal-500 shadow-2xs'
                          : 'bg-slate-50/60 dark:bg-slate-800/60 border-slate-200/80 dark:border-slate-800 hover:border-teal-300'
                      }`}
                    >
                      <div className="space-y-0.5 max-w-[190px]">
                        <p className="font-bold text-slate-900 dark:text-white truncate">
                          {food.common_name || food.food_name}
                        </p>
                        <p className="text-[10px] text-slate-400 truncate">
                          {food.food_category}
                        </p>
                      </div>

                      <div className="flex items-center space-x-1.5">
                        <span className="text-[11px] font-extrabold text-teal-700 dark:text-teal-400 font-mono">
                          {food.nutrients?.energy_kcal || 0} kcal
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleCompare(food);
                          }}
                          className={`p-1 rounded-lg text-[10px] font-bold ${
                            isCompared
                              ? 'bg-teal-600 text-white'
                              : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-teal-100'
                          }`}
                          title="Add to Compare"
                        >
                          <Scale className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Selected Food Detailed Nutrient Profile */}
        <div className="lg:col-span-2 space-y-4">
          {selectedFood ? (
            <div className="space-y-4">
              {/* Food Header Card */}
              <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white font-heading">
                      {selectedFood.common_name || selectedFood.food_name}
                    </h2>
                    <p className="text-xs text-slate-500">
                      {selectedFood.food_name}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleToggleCompare(selectedFood)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors inline-flex items-center space-x-1.5 ${
                        compareList.some((f) => f.fdc_id === selectedFood.fdc_id)
                          ? 'bg-teal-600 text-white shadow-xs'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200'
                      }`}
                    >
                      <Scale className="w-3.5 h-3.5" />
                      <span>
                        {compareList.some((f) => f.fdc_id === selectedFood.fdc_id)
                          ? 'In Comparison'
                          : 'Compare'}
                      </span>
                    </button>

                    <button
                      onClick={() => handleExplain(selectedFood, aiLanguage)}
                      disabled={explaining}
                      className="px-3.5 py-1.5 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 shadow-xs transition-all active:scale-95 disabled:opacity-50 inline-flex items-center space-x-1.5"
                    >
                      {explaining ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      <span>Explain with AI</span>
                    </button>
                  </div>
                </div>

                {/* Macro Badges Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-xl border border-amber-200/60 text-center">
                    <div className="flex items-center justify-center space-x-1 text-amber-700 dark:text-amber-400 mb-0.5">
                      <Flame className="w-3.5 h-3.5" />
                      <span className="text-[10px] font-bold uppercase">Energy</span>
                    </div>
                    <p className="text-base font-black text-amber-900 dark:text-amber-200 font-mono">
                      {n.energy_kcal || 0} <span className="text-[11px] font-normal">kcal</span>
                    </p>
                  </div>

                  <div className="p-3 bg-cyan-50 dark:bg-cyan-950/40 rounded-xl border border-cyan-200/60 text-center">
                    <div className="flex items-center justify-center space-x-1 text-cyan-700 dark:text-cyan-400 mb-0.5">
                      <Wheat className="w-3.5 h-3.5" />
                      <span className="text-[10px] font-bold uppercase">Carbohydrates</span>
                    </div>
                    <p className="text-base font-black text-cyan-900 dark:text-cyan-200 font-mono">
                      {n.carbohydrate_g || 0} <span className="text-[11px] font-normal">g</span>
                    </p>
                  </div>

                  <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200/60 text-center">
                    <div className="flex items-center justify-center space-x-1 text-emerald-700 dark:text-emerald-400 mb-0.5">
                      <Beef className="w-3.5 h-3.5" />
                      <span className="text-[10px] font-bold uppercase">Protein</span>
                    </div>
                    <p className="text-base font-black text-emerald-900 dark:text-emerald-200 font-mono">
                      {n.protein_g || 0} <span className="text-[11px] font-normal">g</span>
                    </p>
                  </div>

                  <div className="p-3 bg-rose-50 dark:bg-rose-950/40 rounded-xl border border-rose-200/60 text-center">
                    <div className="flex items-center justify-center space-x-1 text-rose-700 dark:text-rose-400 mb-0.5">
                      <Droplets className="w-3.5 h-3.5" />
                      <span className="text-[10px] font-bold uppercase">Total Fat</span>
                    </div>
                    <p className="text-base font-black text-rose-900 dark:text-rose-200 font-mono">
                      {n.fat_g || 0} <span className="text-[11px] font-normal">g</span>
                    </p>
                  </div>
                </div>

                {/* Detailed Nutrients Table */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase text-slate-500 tracking-wider font-heading">
                    Full Micronutrient Breakdown (Per 100g)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {[
                      { label: 'Dietary Fiber', val: n.fiber_g, unit: 'g' },
                      { label: 'Total Sugars', val: n.sugars_g, unit: 'g' },
                      { label: 'Potassium (K)', val: n.potassium_mg, unit: 'mg' },
                      { label: 'Calcium (Ca)', val: n.calcium_mg, unit: 'mg' },
                      { label: 'Iron (Fe)', val: n.iron_mg, unit: 'mg' },
                      { label: 'Sodium (Na)', val: n.sodium_mg, unit: 'mg' },
                      { label: 'Magnesium (Mg)', val: n.magnesium_mg, unit: 'mg' },
                      { label: 'Phosphorus (P)', val: n.phosphorus_mg, unit: 'mg' },
                      { label: 'Zinc (Zn)', val: n.zinc_mg, unit: 'mg' },
                      { label: 'Vitamin C (Ascorbic Acid)', val: n.vitamin_c_mg, unit: 'mg' },
                      { label: 'Vitamin A (RAE)', val: n.vitamin_a_ug, unit: 'µg' },
                      { label: 'Vitamin D', val: n.vitamin_d_ug, unit: 'µg' },
                    ].map((item, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-slate-50/70 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-800 flex items-center justify-between"
                      >
                        <span className="text-slate-600 dark:text-slate-300 font-medium">
                          {item.label}
                        </span>
                        <span className="font-bold text-slate-900 dark:text-white font-mono">
                          {item.val !== undefined && item.val !== null ? `${item.val} ${item.unit}` : 'Not available'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Source: <strong>{selectedFood.source_name}</strong></span>
                  <span>FDC ID: <strong>{selectedFood.fdc_id}</strong></span>
                </div>
              </div>

              {/* AI Multilingual Explanation Widget */}
              {aiExplanation && (
                <div className="p-5 bg-teal-50/60 dark:bg-teal-950/40 rounded-2xl border border-teal-200 dark:border-teal-800/60 shadow-2xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-teal-900 dark:text-teal-200 font-heading">
                        AI Nutrition Explanation — {aiExplanation.food_name}
                      </h4>
                    </div>

                    {/* Language Switcher */}
                    <div className="flex items-center space-x-1 bg-white dark:bg-slate-800 p-1 rounded-xl border border-teal-200 dark:border-slate-700 text-xs font-semibold">
                      <Languages className="w-3.5 h-3.5 text-teal-600 ml-1" />
                      {['en', 'ta', 'tanglish'].map((l) => (
                        <button
                          key={l}
                          onClick={() => handleExplain(selectedFood, l)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase transition-colors ${
                            aiLanguage === l
                              ? 'bg-teal-600 text-white'
                              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                          }`}
                        >
                          {l === 'en' ? 'English' : l === 'ta' ? 'தமிழ்' : 'Multilanguage'}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="p-3.5 bg-white/90 dark:bg-slate-900/90 rounded-xl border border-teal-100 dark:border-teal-900 text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans whitespace-pre-line">
                    {aiExplanation.explanation}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800">
              <Apple className="w-10 h-10 text-teal-600 mx-auto opacity-70 mb-2" />
              <p className="text-xs text-slate-500">Select a food item to inspect its verified nutritional profile.</p>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Matrix */}
      {comparisonData && comparisonData.foods.length > 0 && (
        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-teal-600" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                Food Comparison Matrix ({comparisonData.foods.length} Foods)
              </h2>
            </div>
            <button
              onClick={() => setCompareList([])}
              className="text-xs text-rose-600 hover:underline font-bold"
            >
              Clear Comparison
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-400 uppercase text-[11px]">
                  <th className="py-2.5 px-3 font-bold">Nutrient (per 100g)</th>
                  {comparisonData.foods.map((f) => (
                    <th key={f.fdc_id} className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                      <div className="flex items-center justify-between">
                        <span>{f.common_name || f.food_name}</span>
                        <button
                          onClick={() => handleToggleCompare(f)}
                          className="text-slate-400 hover:text-rose-600 ml-1"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                {[
                  { key: 'energy_kcal', label: 'Energy (kcal)' },
                  { key: 'protein_g', label: 'Protein (g)' },
                  { key: 'carbohydrate_g', label: 'Carbohydrates (g)' },
                  { key: 'fiber_g', label: 'Dietary Fiber (g)' },
                  { key: 'sugars_g', label: 'Sugars (g)' },
                  { key: 'fat_g', label: 'Total Fat (g)' },
                  { key: 'potassium_mg', label: 'Potassium (mg)' },
                  { key: 'calcium_mg', label: 'Calcium (mg)' },
                  { key: 'iron_mg', label: 'Iron (mg)' },
                  { key: 'vitamin_c_mg', label: 'Vitamin C (mg)' },
                ].map((row) => (
                  <tr key={row.key} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2 px-3 font-sans font-medium text-slate-600 dark:text-slate-300">
                      {row.label}
                    </td>
                    {comparisonData.foods.map((f) => {
                      const val = f.nutrients?.[row.key];
                      return (
                        <td key={f.fdc_id} className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                          {val !== undefined && val !== null ? val : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default NutritionPage;

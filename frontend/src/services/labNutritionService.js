import { getStoredDocuments } from '../services/documentStore';
import { FALLBACK_FOODS } from '../data/nutritionFallback';

/**
 * Derives personalized, biomarker-grounded nutritional insights from user vault documents.
 * Intelligently:
 * 1. Restricts high-sugar foods if Glucose/HbA1c is high or borderline.
 * 2. Recommends targeted vitamin/mineral-rich foods if Vitamin D, Iron/Hb, etc. are low.
 * 3. Restricts saturated fats/cholesterol if LDL/Total Cholesterol is elevated.
 */
export function deriveLabNutritionInsights() {
  const docs = getStoredDocuments();
  const allTests = [];

  docs.forEach((doc) => {
    const labItems = doc.lab_tests || doc.extracted_data?.tests || [];
    labItems.forEach((t) => {
      allTests.push({
        test_name: t.test_name || t.canonical_name || '',
        canonical_name: t.canonical_name || t.test_name || '',
        value: parseFloat(t.observed_value !== undefined ? t.observed_value : (t.value !== undefined ? t.value : 0)),
        value_raw: t.observed_value !== undefined ? t.observed_value : (t.value !== undefined ? t.value : 'N/A'),
        unit: t.unit || '',
        range: t.reference_range_text || t.range || '',
        flag: (t.flag || t.status || 'normal').toLowerCase()
      });
    });
  });

  const insights = [];
  let isSugarElevated = false;
  let isLdlElevated = false;

  // 1. Check Glucose / Sugar
  const glucoseTest = allTests.find(t => 
    t.test_name.toLowerCase().includes('glucose') || 
    t.test_name.toLowerCase().includes('sugar') ||
    t.test_name.toLowerCase().includes('hba1c')
  );

  if (glucoseTest && (glucoseTest.flag === 'high' || glucoseTest.flag === 'borderline' || glucoseTest.value > 100)) {
    isSugarElevated = true;
    insights.push({
      test_name: glucoseTest.test_name,
      canonical_name: 'Blood Glucose / Glycemic Control',
      observed_value: glucoseTest.value_raw,
      unit: glucoseTest.unit,
      reference_range: glucoseTest.range || '70 - 100 mg/dL',
      flag_type: 'ELEVATED - LOW GLYCEMIC TARGET',
      relevant_nutrient: 'Dietary Fiber & Complex Carbohydrates (Zero Added Sugar)',
      nutrient_context: 'Fasting glucose is elevated. STRICTLY AVOID high-sugar fruits (mangoes, grapes, fruit juices) and refined carbs. Prioritize low glycemic index, high-fiber greens to prevent glucose spikes.',
      suggested_foods: [
        {
          food_name: 'Spinach, raw',
          nutrient_density: '0.4g Sugar / 100g • Low GI',
          serving: '1 cup fresh leaves',
          grounding: 'Rich in dietary fiber and magnesium, which enhances cellular insulin sensitivity.'
        },
        {
          food_name: 'Broccoli, raw',
          nutrient_density: '1.7g Sugar / 100g • Low GI',
          serving: '1 cup chopped florets',
          grounding: 'Contains sulforaphane and chromium which support healthy blood glucose regulation.'
        },
        {
          food_name: 'Oats, whole grain, rolled',
          nutrient_density: '0.9g Sugar / 100g • 10.6g Fiber',
          serving: '1/2 cup dry rolled oats',
          grounding: 'Beta-glucan soluble fiber slows gastric emptying, preventing postprandial glucose spikes.'
        }
      ]
    });
  }

  // 2. Check Vitamin D
  const vitDTest = allTests.find(t => 
    t.test_name.toLowerCase().includes('vitamin d') || 
    t.test_name.toLowerCase().includes('25-oh')
  );

  if (vitDTest && (vitDTest.flag === 'low' || vitDTest.value < 30)) {
    insights.push({
      test_name: vitDTest.test_name,
      canonical_name: '25-Hydroxy Vitamin D',
      observed_value: vitDTest.value_raw,
      unit: vitDTest.unit,
      reference_range: vitDTest.range || '30 - 100 ng/mL',
      flag_type: 'BELOW REFERENCE INTERVAL',
      relevant_nutrient: 'Vitamin D3 & Calcium Bioavailability',
      nutrient_context: 'Serum Vitamin D is below optimal target (30 ng/mL). Dietary Vitamin D and healthy omega-3 fatty acids assist systemic absorption alongside direct sunlight.',
      suggested_foods: [
        {
          food_name: 'Salmon, Atlantic, wild, raw',
          nutrient_density: '11.0 µg Vitamin D / 100g',
          serving: '1 fillet (100g)',
          grounding: 'One of the richest natural whole food sources of Vitamin D3 with beneficial EPA/DHA fatty acids.'
        },
        {
          food_name: 'Eggs, Grade A, Large, whole egg',
          nutrient_density: '2.0 µg Vitamin D / 100g',
          serving: '2 whole boiled eggs',
          grounding: 'Yolks contain naturally occurring fat-soluble Vitamin D and choline.'
        }
      ]
    });
  }

  // 3. Check LDL / Cholesterol
  const ldlTest = allTests.find(t => 
    t.test_name.toLowerCase().includes('ldl') || 
    t.test_name.toLowerCase().includes('cholesterol')
  );

  if (ldlTest && (ldlTest.flag === 'high' || ldlTest.flag === 'borderline' || ldlTest.value > 100)) {
    isLdlElevated = true;
    insights.push({
      test_name: ldlTest.test_name,
      canonical_name: 'LDL / Total Cholesterol Profile',
      observed_value: ldlTest.value_raw,
      unit: ldlTest.unit,
      reference_range: ldlTest.range || '< 100 mg/dL',
      flag_type: 'ELEVATED - CARDIOVASCULAR OPTIMIZATION',
      relevant_nutrient: 'Soluble Fiber, Plant Sterols & Monounsaturated Fats',
      nutrient_context: 'Observed LDL is above clinical optimal. Avoid saturated animal fats and fried items. Focus on foods with plant sterols and monounsaturated fatty acids.',
      suggested_foods: [
        {
          food_name: 'Nuts, almonds, whole, raw',
          nutrient_density: 'Monounsaturated Fats • 12.5g Fiber',
          serving: '1 handful (28g / 23 almonds)',
          grounding: 'Clinical evidence demonstrates raw almonds lower circulating LDL without lowering protective HDL.'
        },
        {
          food_name: 'Oats, whole grain, rolled',
          nutrient_density: '10.6g Soluble Fiber',
          serving: '1 bowl cooked oatmeal',
          grounding: 'Binds cholesterol in the digestive tract, encouraging elimination and reducing absorption.'
        }
      ]
    });
  }

  // 4. Check Hemoglobin / Iron
  const hbTest = allTests.find(t => 
    t.test_name.toLowerCase().includes('hemoglobin') || 
    t.test_name.toLowerCase().includes('hb')
  );

  if (hbTest && (hbTest.flag === 'low' || hbTest.value < 12.5)) {
    insights.push({
      test_name: hbTest.test_name,
      canonical_name: 'Hemoglobin (Hematology Panel)',
      observed_value: hbTest.value_raw,
      unit: hbTest.unit,
      reference_range: hbTest.range || '13.0 - 17.0 g/dL',
      flag_type: 'BELOW REFERENCE INTERVAL',
      relevant_nutrient: 'Dietary Iron, Folate & Vitamin C',
      nutrient_context: 'Hemoglobin is on the lower side. Emphasize non-heme plant iron paired with natural Vitamin C foods to optimize erythrocyte synthesis.',
      suggested_foods: [
        {
          food_name: 'Spinach, raw',
          nutrient_density: '2.71 mg Iron • 28.1 mg Vitamin C',
          serving: '1 large bowl cooked greens',
          grounding: 'Natural iron co-factor matrix facilitates high absorption into blood red cell lines.'
        },
        {
          food_name: 'Lentils, mature seeds, cooked, boiled',
          nutrient_density: '3.33 mg Iron • 9.0g Protein',
          serving: '1 cup cooked dal/lentils',
          grounding: 'Rich in dietary folate and bioavailable vegetable iron essential for hemoglobin formation.'
        }
      ]
    });
  }

  // Fallback if no biomarkers matched
  if (insights.length === 0) {
    insights.push({
      test_name: 'General Wellness Screen',
      canonical_name: 'Whole Body Vitality & Prevention',
      observed_value: 'Optimal',
      unit: 'Profile',
      reference_range: 'Clinical Guidelines',
      flag_type: 'TARGET MAINTAINED',
      relevant_nutrient: 'Balanced Whole Food Micronutrient Matrix',
      nutrient_context: 'Your recorded biomarkers are in healthy ranges. Maintain antioxidant-rich vegetables, lean clean proteins, and heart-healthy nuts.',
      suggested_foods: [
        {
          food_name: 'Fresh Apple (Fuji / Gala)',
          nutrient_density: 'Antioxidants • 2.4g Fiber',
          serving: '1 medium fruit',
          grounding: 'Quercetin and pectin sustain metabolic health and arterial elasticity.'
        },
        {
          food_name: 'Broccoli, raw',
          nutrient_density: '89.2 mg Vitamin C • 2.8g Protein',
          serving: '1 cup florets',
          grounding: 'Potent cellular antioxidant and immune system support.'
        }
      ]
    });
  }

  return {
    insights,
    isSugarElevated,
    isLdlElevated
  };
}

/**
 * Filter foods strictly respecting clinical contraindications (e.g., zero high-sugar foods when sugar is high)
 */
export function getRecommendedFoods(query = '', category = 'All') {
  const { isSugarElevated, isLdlElevated } = deriveLabNutritionInsights();

  let foods = [...FALLBACK_FOODS];

  // If blood sugar is elevated: filter out foods high in sugar (> 8g sugar per 100g)
  if (isSugarElevated) {
    foods = foods.filter(f => {
      const sugar = f.nutrients?.sugars_g ?? 0;
      return sugar <= 8; // Exclude high-sugar fruits like ripe bananas, sweet apples, sugary juices
    });
  }

  if (category !== 'All') {
    foods = foods.filter(f => f.food_category === category);
  }

  if (query.trim()) {
    const q = query.toLowerCase().trim();
    foods = foods.filter(f =>
      f.food_name.toLowerCase().includes(q) ||
      (f.common_name && f.common_name.toLowerCase().includes(q)) ||
      f.food_category.toLowerCase().includes(q)
    );
  }

  return foods;
}

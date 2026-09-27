import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.nutrition import NutritionFoodItem
from backend.app.services.multilingual_explanation_service import multilingual_explanation_service
from backend.app.core.logging import logger

# Embedded fallback USDA Foundation Foods dataset for zero-filesystem failure resilience
EMBEDDED_USDA_FOUNDATION_FOODS = [
    {
        "fdc_id": 1102597,
        "food_name": "Apples, raw, with skin (Includes USDA commodity foods)",
        "common_name": "Apple",
        "food_category": "Fruits and Fruit Juices",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 52.0, "protein_g": 0.26, "fat_g": 0.17, "carbohydrate_g": 13.81,
            "fiber_g": 2.4, "sugars_g": 10.39, "calcium_mg": 6.0, "iron_mg": 0.12,
            "magnesium_mg": 5.0, "phosphorus_mg": 11.0, "potassium_mg": 107.0, "sodium_mg": 1.0,
            "zinc_mg": 0.04, "vitamin_c_mg": 4.6, "vitamin_a_ug": 3.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 1102653,
        "food_name": "Bananas, raw",
        "common_name": "Banana",
        "food_category": "Fruits and Fruit Juices",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 89.0, "protein_g": 1.09, "fat_g": 0.33, "carbohydrate_g": 22.84,
            "fiber_g": 2.6, "sugars_g": 12.23, "calcium_mg": 5.0, "iron_mg": 0.26,
            "magnesium_mg": 27.0, "phosphorus_mg": 22.0, "potassium_mg": 358.0, "sodium_mg": 1.0,
            "zinc_mg": 0.15, "vitamin_c_mg": 8.7, "vitamin_a_ug": 4.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 1103193,
        "food_name": "Spinach, raw",
        "common_name": "Spinach",
        "food_category": "Vegetables and Vegetable Products",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 23.0, "protein_g": 2.86, "fat_g": 0.39, "carbohydrate_g": 3.63,
            "fiber_g": 2.2, "sugars_g": 0.42, "calcium_mg": 99.0, "iron_mg": 2.71,
            "magnesium_mg": 79.0, "phosphorus_mg": 49.0, "potassium_mg": 558.0, "sodium_mg": 79.0,
            "zinc_mg": 0.53, "vitamin_c_mg": 28.1, "vitamin_a_ug": 469.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 1103773,
        "food_name": "Oranges, raw, all commercial varieties",
        "common_name": "Orange",
        "food_category": "Fruits and Fruit Juices",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 47.0, "protein_g": 0.94, "fat_g": 0.12, "carbohydrate_g": 11.75,
            "fiber_g": 2.4, "sugars_g": 9.35, "calcium_mg": 40.0, "iron_mg": 0.10,
            "magnesium_mg": 10.0, "phosphorus_mg": 14.0, "potassium_mg": 181.0, "sodium_mg": 0.0,
            "zinc_mg": 0.07, "vitamin_c_mg": 53.2, "vitamin_a_ug": 11.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 1103847,
        "food_name": "Broccoli, raw",
        "common_name": "Broccoli",
        "food_category": "Vegetables and Vegetable Products",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 34.0, "protein_g": 2.82, "fat_g": 0.37, "carbohydrate_g": 6.64,
            "fiber_g": 2.6, "sugars_g": 1.70, "calcium_mg": 47.0, "iron_mg": 0.73,
            "magnesium_mg": 21.0, "phosphorus_mg": 66.0, "potassium_mg": 316.0, "sodium_mg": 33.0,
            "zinc_mg": 0.41, "vitamin_c_mg": 89.2, "vitamin_a_ug": 31.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 170567,
        "food_name": "Lentils, mature seeds, cooked, boiled, without salt",
        "common_name": "Lentils",
        "food_category": "Legumes and Legume Products",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 116.0, "protein_g": 9.02, "fat_g": 0.38, "carbohydrate_g": 20.13,
            "fiber_g": 7.9, "sugars_g": 1.80, "calcium_mg": 19.0, "iron_mg": 3.33,
            "magnesium_mg": 36.0, "phosphorus_mg": 180.0, "potassium_mg": 369.0, "sodium_mg": 2.0,
            "zinc_mg": 1.27, "vitamin_c_mg": 1.5, "vitamin_a_ug": 2.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 171287,
        "food_name": "Almonds, raw",
        "common_name": "Almonds",
        "food_category": "Nut and Seed Products",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 579.0, "protein_g": 21.15, "fat_g": 49.93, "carbohydrate_g": 21.55,
            "fiber_g": 12.5, "sugars_g": 4.35, "calcium_mg": 269.0, "iron_mg": 3.71,
            "magnesium_mg": 270.0, "phosphorus_mg": 481.0, "potassium_mg": 733.0, "sodium_mg": 1.0,
            "zinc_mg": 3.12, "vitamin_c_mg": 0.0, "vitamin_a_ug": 0.0, "vitamin_d_ug": 0.0
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    },
    {
        "fdc_id": 173430,
        "food_name": "Yogurt, plain, low fat",
        "common_name": "Yogurt",
        "food_category": "Dairy and Egg Products",
        "serving_size": 100.0,
        "serving_unit": "g",
        "nutrients": {
            "energy_kcal": 63.0, "protein_g": 5.25, "fat_g": 1.55, "carbohydrate_g": 7.04,
            "fiber_g": 0.0, "sugars_g": 7.04, "calcium_mg": 183.0, "iron_mg": 0.08,
            "magnesium_mg": 17.0, "phosphorus_mg": 144.0, "potassium_mg": 234.0, "sodium_mg": 70.0,
            "zinc_mg": 0.89, "vitamin_c_mg": 0.8, "vitamin_a_ug": 14.0, "vitamin_d_ug": 0.1
        },
        "source_name": "USDA FoodData Central — Foundation Foods",
        "dataset_name": "USDA FoodData Central",
        "dataset_version": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets.html",
        "license": "Public Domain / CC0-1.0"
    }
]

class NutritionService:
    """
    Evidence-based Nutrition Intelligence Service using USDA FoodData Central Foundation Foods.
    Provides fast food search, nutrient profile inspection, food comparison, and multilingual AI explanations.
    """

    def _resolve_dataset_path(self) -> Optional[str]:
        """Finds the dataset JSON across multiple potential deployment paths."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        candidates = [
            base_dir / "data" / "processed" / "nutrition" / "foundation_foods_processed.json",
            base_dir / "data" / "nutrition" / "food_database.json",
            Path("/app/data/processed/nutrition/foundation_foods_processed.json"),
            Path("data/processed/nutrition/foundation_foods_processed.json"),
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return str(p)
        return None

    def ensure_database_populated(self, db: Session):
        """Seeds database from processed JSON or embedded fallback dataset if table is empty."""
        count = db.query(NutritionFoodItem).count()
        if count > 0:
            return

        json_path = self._resolve_dataset_path()
        items_to_insert = []

        if json_path:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    items_to_insert = json.load(f)
                logger.info(f"Loaded {len(items_to_insert)} USDA foods from {json_path}")
            except Exception as e:
                logger.warning(f"Failed to read USDA json from {json_path}: {e}")

        if not items_to_insert:
            items_to_insert = EMBEDDED_USDA_FOUNDATION_FOODS
            logger.info("Using embedded USDA Foundation Foods dataset.")

        for item in items_to_insert:
            db_item = NutritionFoodItem(
                fdc_id=item["fdc_id"],
                food_name=item["food_name"],
                common_name=item.get("common_name", item["food_name"]),
                food_category=item.get("food_category", "General"),
                serving_size=item.get("serving_size", 100.0),
                serving_unit=item.get("serving_unit", "g"),
                nutrients=item.get("nutrients", {}),
                source_name=item.get("source_name", "USDA FoodData Central — Foundation Foods"),
                dataset_name=item.get("dataset_name", "USDA FoodData Central"),
                dataset_version=item.get("dataset_version", "2026-04-30"),
                source_url=item.get("source_url", "https://fdc.nal.usda.gov/download-datasets.html"),
                license=item.get("license", "Public Domain / CC0-1.0")
            )
            db.add(db_item)
        db.commit()

    def search_food(
        self,
        db: Session,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[NutritionFoodItem]:
        self.ensure_database_populated(db)
        q_lower = query.strip().lower()

        base_query = db.query(NutritionFoodItem)
        if category and category.strip():
            base_query = base_query.filter(NutritionFoodItem.food_category.ilike(f"%{category.strip()}%"))

        if not q_lower:
            return base_query.limit(limit).all()

        # Substring search across common_name and food_name
        results = base_query.filter(
            (NutritionFoodItem.common_name.ilike(f"%{q_lower}%")) |
            (NutritionFoodItem.food_name.ilike(f"%{q_lower}%"))
        ).limit(limit).all()

        if not results:
            import re
            tokens = [w for w in re.findall(r'\w+', q_lower) if len(w) >= 3 and w not in {
                "what", "is", "the", "are", "nutritional", "nutrition", "information", "info", "value", "values", "profile", "tell", "about", "contain", "contains"
            }]
            for tok in tokens:
                matches = base_query.filter(
                    (NutritionFoodItem.common_name.ilike(f"%{tok}%")) |
                    (NutritionFoodItem.food_name.ilike(f"%{tok}%"))
                ).limit(limit).all()
                if matches:
                    results = matches
                    break

        return results

    def get_food_by_fdc_id(self, db: Session, fdc_id: int) -> Optional[NutritionFoodItem]:
        self.ensure_database_populated(db)
        return db.query(NutritionFoodItem).filter(NutritionFoodItem.fdc_id == fdc_id).first()

    def search_by_nutrient(
        self,
        db: Session,
        nutrient_key: str,
        min_amount: float = 0.0,
        limit: int = 10
    ) -> List[NutritionFoodItem]:
        self.ensure_database_populated(db)
        all_foods = db.query(NutritionFoodItem).all()
        scored = []
        for f in all_foods:
            nutrients = f.nutrients or {}
            val = nutrients.get(nutrient_key, 0.0)
            if isinstance(val, (int, float)) and val >= min_amount:
                scored.append((val, f))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def compare_foods(self, db: Session, fdc_ids: List[int]) -> List[NutritionFoodItem]:
        self.ensure_database_populated(db)
        return db.query(NutritionFoodItem).filter(NutritionFoodItem.fdc_id.in_(fdc_ids)).all()

    def generate_nutrition_explanation(
        self,
        food: NutritionFoodItem,
        language: str = "en"
    ) -> str:
        nut = food.nutrients or {}
        cals = nut.get("energy_kcal", 0)
        prot = nut.get("protein_g", 0)
        carbs = nut.get("carbohydrate_g", 0)
        fiber = nut.get("fiber_g", 0)
        fat = nut.get("fat_g", 0)
        iron = nut.get("iron_mg", 0)
        calc = nut.get("calcium_mg", 0)
        pot = nut.get("potassium_mg", 0)
        vit_c = nut.get("vitamin_c_mg", 0)

        name = food.common_name or food.food_name

        if language == "ta":
            return (
                f"**{name} ஊட்டச்சத்து விவரம் (USDA Foundation Foods):**\n"
                f"• ஆற்றல் (Calories): {cals} kcal ({food.serving_size} {food.serving_unit}-க்கு)\n"
                f"• புரதம்: {prot} g | நார்ச்சத்து: {fiber} g | கொழுப்பு: {fat} g | கார்போஹைட்ரேட்: {carbs} g\n"
                f"• தாதுக்கள்: இரும்புச்சத்து {iron} mg, கால்சியம் {calc} mg, பொட்டாசியம் {pot} mg, வைட்டமின் சி {vit_c} mg.\n\n"
                f"*ஆதாரம்: USDA FoodData Central Foundation Foods (பொதுக் கள உரிமம்). மருத்துவ ஆலோசனைக்கு மாற்றாகாது.*"
            )
        elif language == "tanglish":
            return (
                f"**{name} Nutrition Values (USDA Foundation Foods):**\n"
                f"• Energy: {cals} kcal per {food.serving_size} {food.serving_unit}\n"
                f"• Protein: {prot} g | Fiber: {fiber} g | Fat: {fat} g | Carbs: {carbs} g\n"
                f"• Micronutrients: Iron {iron} mg, Calcium {calc} mg, Potassium {pot} mg, Vitamin C {vit_c} mg.\n\n"
                f"*Source: USDA FoodData Central Foundation Foods. Non-diagnostic informational reference only.*"
            )
        else:
            return (
                f"**{name} Nutritional Profile (USDA Foundation Foods):**\n"
                f"• Energy: {cals} kcal per {food.serving_size} {food.serving_unit} serving\n"
                f"• Macronutrients: Protein: {prot} g | Dietary Fiber: {fiber} g | Total Fat: {fat} g | Carbohydrates: {carbs} g\n"
                f"• Key Micronutrients: Iron: {iron} mg | Calcium: {calc} mg | Potassium: {pot} mg | Vitamin C: {vit_c} mg\n\n"
                f"*Source: USDA FoodData Central — Foundation Foods (Public Domain / CC0-1.0). Informational reference only; not a substitute for clinical medical nutrition therapy.*"
            )

    def get_lab_connected_nutrition_insights(
        self,
        db: Session,
        user_id: int,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Connects verified medical lab biomarkers to USDA nutrition recommendations.
        Identifies parameters flagged below reference intervals and suggests nutrient-dense foods.
        """
        from backend.app.models.clinical import LabTest

        self.ensure_database_populated(db)

        query = db.query(LabTest).filter(LabTest.user_id == user_id)
        if document_id:
            query = query.filter(LabTest.document_id == document_id)
        
        lab_tests = query.order_by(LabTest.test_date.desc()).all()

        NUTRIENT_MAP = {
            "hemoglobin": {
                "nutrient_key": "iron_mg",
                "nutrient_name": "Iron (Fe)",
                "description": "Iron is a core structural component of hemoglobin, essential for systemic oxygen delivery."
            },
            "serum_iron": {
                "nutrient_key": "iron_mg",
                "nutrient_name": "Iron (Fe)",
                "description": "Dietary iron replenishes serum transferrin saturation and ferritin stores."
            },
            "ferritin": {
                "nutrient_key": "iron_mg",
                "nutrient_name": "Iron (Fe)",
                "description": "Ferritin represents stored cellular iron."
            },
            "calcium": {
                "nutrient_key": "calcium_mg",
                "nutrient_name": "Calcium (Ca)",
                "description": "Calcium supports bone mineral density, neuromuscular signaling, and enzymatic function."
            },
            "potassium": {
                "nutrient_key": "potassium_mg",
                "nutrient_name": "Potassium (K)",
                "description": "Potassium helps regulate vascular tone, fluid balance, and cardiac electrophysiology."
            }
        }

        insights = []
        for lab in lab_tests:
            c_name = (lab.canonical_name or "").lower()
            t_name = (lab.test_name or "").lower()

            matched_mapping = None
            for key, mapping in NUTRIENT_MAP.items():
                if key in c_name or key in t_name:
                    matched_mapping = mapping
                    break

            if not matched_mapping:
                continue

            is_below_ref = False
            if lab.flag and str(lab.flag).lower() in {"low", "critical_low"}:
                is_below_ref = True
            elif lab.numeric_value is not None and lab.reference_range_min is not None:
                if lab.numeric_value < lab.reference_range_min:
                    is_below_ref = True

            if is_below_ref:
                suggested_foods_raw = self.search_by_nutrient(
                    db=db,
                    nutrient_key=matched_mapping["nutrient_key"],
                    min_amount=0.2,
                    limit=5
                )

                foods_payload = []
                for sf in suggested_foods_raw:
                    nutrients = sf.nutrients or {}
                    amount = nutrients.get(matched_mapping["nutrient_key"], 0.0)
                    calories = nutrients.get("energy_kcal", 0.0)
                    foods_payload.append({
                        "fdc_id": sf.fdc_id,
                        "food_name": sf.common_name or sf.food_name,
                        "category": sf.food_category,
                        "calories_kcal": calories,
                        "nutrient_amount": amount,
                        "nutrient_unit": "mg" if "mg" in matched_mapping["nutrient_key"] else "g",
                        "serving_size": f"{sf.serving_size} {sf.serving_unit}",
                        "source": sf.source_name
                    })

                insights.append({
                    "lab_test_id": lab.id,
                    "test_name": lab.test_name,
                    "canonical_name": lab.canonical_name,
                    "observed_value": lab.observed_value,
                    "unit": lab.unit,
                    "reference_range": lab.reference_range_text or f"{lab.reference_range_min} - {lab.reference_range_max} {lab.unit}",
                    "flag": str(lab.flag or "low"),
                    "status_description": "Your report shows a value below the reference range.",
                    "relevant_nutrient": matched_mapping["nutrient_name"],
                    "nutrient_context": matched_mapping["description"],
                    "suggested_foods": foods_payload,
                    "disclaimer": "Nutritional food suggestions are derived from the USDA FoodData Central Foundation Foods dataset for informational reference only. They do not constitute personalized medical nutrition therapy or replace physician prescriptions."
                })

        return {
            "total_insights": len(insights),
            "insights": insights,
            "source_dataset": "USDA FoodData Central — Foundation Foods (Public Domain / CC0-1.0)"
        }

nutrition_service = NutritionService()

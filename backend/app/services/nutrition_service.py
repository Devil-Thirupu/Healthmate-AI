import os
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.nutrition import NutritionFoodItem
from backend.app.services.multilingual_explanation_service import multilingual_explanation_service

PROCESSED_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data", "processed", "nutrition", "foundation_foods_processed.json"
)

class NutritionService:
    """
    Evidence-based Nutrition Intelligence Service using USDA FoodData Central Foundation Foods.
    Provides fast food search, nutrient profile inspection, food comparison, and multilingual AI explanations.
    """

    def ensure_database_populated(self, db: Session):
        """Seeds SQLite database from processed JSON if table is empty."""
        count = db.query(NutritionFoodItem).count()
        if count > 0:
            return

        if not os.path.exists(PROCESSED_JSON_PATH):
            return

        with open(PROCESSED_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
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

        # Exact / Substring search across common_name and food_name
        results = base_query.filter(
            (NutritionFoodItem.common_name.ilike(f"%{q_lower}%")) |
            (NutritionFoodItem.food_name.ilike(f"%{q_lower}%"))
        ).limit(limit).all()

        if not results:
            # Token-level matching for conversational / natural language queries (e.g. "What is the nutritional information of apple?")
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
        for food in all_foods:
            nutrients = food.nutrients or {}
            val = nutrients.get(nutrient_key)
            if val is not None and val >= min_amount:
                scored.append((food, val))

        # Sort descending by nutrient amount
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:limit]]

    def compare_foods(self, db: Session, fdc_ids: List[int]) -> List[NutritionFoodItem]:
        self.ensure_database_populated(db)
        if not fdc_ids:
            return []
        return db.query(NutritionFoodItem).filter(NutritionFoodItem.fdc_id.in_(fdc_ids)).all()

    def generate_nutrition_explanation(
        self,
        food: NutritionFoodItem,
        language: str = "en"
    ) -> str:
        """
        Generates an objective, evidence-grounded nutritional explanation from USDA Foundation Foods.
        Strictly preserves food names, nutrient names, numerical values, and units across EN, TA, and Tanglish.
        """
        lang = multilingual_explanation_service.normalize_language(language)
        n = food.nutrients or {}
        
        energy = n.get("energy_kcal", 0.0)
        protein = n.get("protein_g", 0.0)
        carbs = n.get("carbohydrate_g", 0.0)
        fat = n.get("fat_g", 0.0)
        fiber = n.get("fiber_g", 0.0)
        sugars = n.get("sugars_g", 0.0)
        potassium = n.get("potassium_mg")
        calcium = n.get("calcium_mg")
        iron = n.get("iron_mg")
        vit_c = n.get("vitamin_c_mg")

        lines = []

        if lang == "ta":
            lines.append(f"USDA FoodData Central (FDC ID: {food.fdc_id}) ஆய்வக பதிவுகளின்படி, 100g {food.common_name or food.food_name} ஊட்டச்சத்து விவரங்கள்:")
            lines.append(f"• Energy (ஆற்றல்): {energy} kcal")
            lines.append(f"• Carbohydrate: {carbs} g (Fiber: {fiber} g, Sugars: {sugars} g)")
            lines.append(f"• Protein (புரதம்): {protein} g")
            lines.append(f"• Total Fat (கொழுப்பு): {fat} g")
            if potassium is not None:
                lines.append(f"• Potassium (பொட்டாசியம்): {potassium} mg")
            if calcium is not None:
                lines.append(f"• Calcium (கால்சியம்): {calcium} mg")
            if iron is not None:
                lines.append(f"• Iron (இரும்புச்சத்து): {iron} mg")
            if vit_c is not None:
                lines.append(f"• Vitamin C: {vit_c} mg")
            lines.append("\n* ஆதாரம்: USDA FoodData Central — Foundation Foods (Public Domain). இந்த தகவல் பொது உணவு அறிவிற்காக மட்டுமே; மருத்துவ உணவு பரிந்துரை அல்ல.")

        elif lang == "tanglish":
            lines.append(f"USDA FoodData Central (FDC ID: {food.fdc_id}) records padi, 100g {food.common_name or food.food_name}-il ulla nutrition values:")
            lines.append(f"• Energy: {energy} kcal")
            lines.append(f"• Carbohydrate: {carbs} g (Fiber: {fiber} g, Sugars: {sugars} g)")
            lines.append(f"• Protein: {protein} g")
            lines.append(f"• Total Fat: {fat} g")
            if potassium is not None:
                lines.append(f"• Potassium: {potassium} mg")
            if calcium is not None:
                lines.append(f"• Calcium: {calcium} mg")
            if iron is not None:
                lines.append(f"• Iron: {iron} mg")
            if vit_c is not None:
                lines.append(f"• Vitamin C: {vit_c} mg")
            lines.append("\n* Source: USDA FoodData Central — Foundation Foods (Public Domain). Idhu general nutrition information mattume; personalized medical diet prescription illai.")

        else: # English
            lines.append(f"According to USDA FoodData Central (FDC ID: {food.fdc_id}), the nutritional profile of 100g {food.common_name or food.food_name} contains:")
            lines.append(f"• Energy: {energy} kcal")
            lines.append(f"• Carbohydrate: {carbs} g (Dietary Fiber: {fiber} g, Sugars: {sugars} g)")
            lines.append(f"• Protein: {protein} g")
            lines.append(f"• Total Lipid (Fat): {fat} g")
            if potassium is not None:
                lines.append(f"• Potassium: {potassium} mg")
            if calcium is not None:
                lines.append(f"• Calcium: {calcium} mg")
            if iron is not None:
                lines.append(f"• Iron: {iron} mg")
            if vit_c is not None:
                lines.append(f"• Vitamin C: {vit_c} mg")
            lines.append("\n* Source: USDA FoodData Central — Foundation Foods (Public Domain / CC0-1.0). Nutritional values are for informational reference only and do not constitute clinical dietary therapy.")

        return "\n".join(lines)

    def get_lab_connected_nutrition_insights(
        self,
        db: Session,
        user_id: int,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Connects verified medical lab biomarkers to USDA nutrition recommendations.
        Identifies parameters flagged below reference intervals and suggests nutrient-rich foods.
        """
        from backend.app.models.clinical import LabTest
        from backend.app.models.document import Document

        self.ensure_database_populated(db)

        # Retrieve relevant lab tests
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

            # If below reference range or explicitly flagged low
            if is_below_ref:
                suggested_foods_raw = self.search_by_nutrient(
                    db=db,
                    nutrient_key=matched_mapping["nutrient_key"],
                    min_amount=0.5,
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

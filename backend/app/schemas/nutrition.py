from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class NutrientProfile(BaseModel):
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbohydrate_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugars_g: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_a_ug: Optional[float] = None
    vitamin_d_ug: Optional[float] = None

class NutritionFoodItemResponse(BaseModel):
    id: int
    fdc_id: int
    food_name: str
    common_name: Optional[str] = None
    food_category: str
    serving_size: float = 100.0
    serving_unit: str = "g"
    nutrients: Dict[str, Any]
    source_name: str
    dataset_name: str
    dataset_version: str
    source_url: str
    license: str

    model_config = ConfigDict(from_attributes=True)

class FoodComparisonItem(BaseModel):
    fdc_id: int
    food_name: str
    common_name: Optional[str] = None
    food_category: str
    serving_size: float
    serving_unit: str
    nutrients: Dict[str, Any]
    source_name: str

class FoodComparisonResponse(BaseModel):
    foods: List[FoodComparisonItem]
    comparison_nutrients: List[str]
    source_attribution: str = "USDA FoodData Central — Foundation Foods"

class NutritionExplainRequest(BaseModel):
    fdc_id: Optional[int] = None
    food_name: Optional[str] = None
    language: Optional[str] = "en"

class NutritionExplainResponse(BaseModel):
    food_name: str
    fdc_id: Optional[int] = None
    explanation: str
    language: str
    source: str = "USDA FoodData Central — Foundation Foods"
    license: str = "Public Domain / CC0-1.0"

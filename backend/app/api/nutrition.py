from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.nutrition_service import nutrition_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.nutrition import (
    NutritionFoodItemResponse,
    FoodComparisonResponse,
    FoodComparisonItem,
    NutritionExplainRequest,
    NutritionExplainResponse
)

router = APIRouter()

@router.get("/search", response_model=List[NutritionFoodItemResponse])
def search_foods(
    query: Optional[str] = Query("", description="Food or fruit name search keyword"),
    category: Optional[str] = Query(None, description="Optional food category filter"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Searches official USDA Foundation Foods by name and category."""
    return nutrition_service.search_food(db=db, query=query, category=category, limit=limit)

@router.get("/food/{fdc_id}", response_model=NutritionFoodItemResponse)
def get_food_details(
    fdc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieves verified nutritional profile for a specific USDA FDC ID."""
    food = nutrition_service.get_food_by_fdc_id(db=db, fdc_id=fdc_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item with FDC ID {fdc_id} not found in USDA Foundation Foods dataset."
        )
    return food

@router.get("/compare", response_model=FoodComparisonResponse)
def compare_foods(
    fdc_ids: str = Query(..., description="Comma-separated FDC IDs to compare (e.g. 1102597,1102653)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns side-by-side comparative nutritional values for selected USDA food items."""
    try:
        id_list = [int(x.strip()) for x in fdc_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid fdc_ids format.")

    if not id_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide at least one FDC ID.")

    foods = nutrition_service.compare_foods(db=db, fdc_ids=id_list)
    if not foods:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching foods found.")

    comparison_items = [
        FoodComparisonItem(
            fdc_id=f.fdc_id,
            food_name=f.food_name,
            common_name=f.common_name,
            food_category=f.food_category,
            serving_size=f.serving_size,
            serving_unit=f.serving_unit,
            nutrients=f.nutrients or {},
            source_name=f.source_name
        )
        for f in foods
    ]

    key_nutrients = [
        "energy_kcal", "protein_g", "carbohydrate_g", "fiber_g", "sugars_g", "fat_g",
        "calcium_mg", "iron_mg", "potassium_mg", "sodium_mg", "vitamin_c_mg", "vitamin_a_ug", "vitamin_d_ug"
    ]

    return FoodComparisonResponse(
        foods=comparison_items,
        comparison_nutrients=key_nutrients,
        source_attribution="USDA FoodData Central — Foundation Foods (April 2026 Release)"
    )

@router.post("/explain", response_model=NutritionExplainResponse)
def explain_nutrition(
    req: NutritionExplainRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generates evidence-grounded AI explanations of USDA nutritional profiles
    supporting English, Tamil, and Tanglish.
    """
    food = None
    if req.fdc_id:
        food = nutrition_service.get_food_by_fdc_id(db=db, fdc_id=req.fdc_id)
    elif req.food_name:
        results = nutrition_service.search_food(db=db, query=req.food_name, limit=1)
        if results:
            food = results[0]

    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The available nutrition dataset does not contain enough information about this food."
        )

    explanation = nutrition_service.generate_nutrition_explanation(
        food=food,
        language=req.language or "en"
    )

    audit_service.log_event(
        db=db,
        action="NUTRITION_AI_EXPLAIN",
        resource_type="nutrition_food",
        user_id=current_user.id,
        resource_id=str(food.fdc_id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"food_name": food.common_name or food.food_name, "language": req.language}
    )

    return NutritionExplainResponse(
        food_name=food.common_name or food.food_name,
        fdc_id=food.fdc_id,
        explanation=explanation,
        language=req.language or "en",
        source="USDA FoodData Central — Foundation Foods",
        license="Public Domain / CC0-1.0"
    )

@router.get("/report-recommendations")
def get_lab_nutrition_recommendations(
    document_id: Optional[int] = Query(None, description="Optional document ID to focus analysis on"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Connects the patient's verified medical laboratory test results to USDA nutritional recommendations.
    Provides food suggestions with calorie and nutrient densities for flagged/low biomarkers.
    """
    return nutrition_service.get_lab_connected_nutrition_insights(
        db=db,
        user_id=current_user.id,
        document_id=document_id
    )

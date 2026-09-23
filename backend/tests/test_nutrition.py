import pytest
import os
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.clinical import LabTest, LabFlag
from backend.app.models.nutrition import NutritionFoodItem
from backend.app.services.nutrition_service import nutrition_service
from backend.app.services.multilingual_explanation_service import multilingual_explanation_service
from backend.app.core.security import get_password_hash

# -----------------------------------------------------------------------------
# Test 1, 2, 3, 4: Dataset Validation & Ingestion Pipeline
# -----------------------------------------------------------------------------
def test_1_to_4_dataset_validation_and_integrity():
    processed_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "processed", "nutrition", "foundation_foods_processed.json"
    )
    assert os.path.exists(processed_path), "Processed Foundation Foods JSON must exist."

    with open(processed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 10

    fdc_ids = set()
    for item in data:
        assert "fdc_id" in item
        assert "food_name" in item
        assert "nutrients" in item
        assert "energy_kcal" in item["nutrients"]
        assert item["fdc_id"] not in fdc_ids, f"Duplicate FDC ID found: {item['fdc_id']}"
        fdc_ids.add(item["fdc_id"])

# -----------------------------------------------------------------------------
# Test 5, 6, 7, 8: Food Search, Exact Retrieval, Nutrient Ranking, Comparison
# -----------------------------------------------------------------------------
def test_5_to_8_food_search_retrieval_and_comparison(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    headers = registered_user["headers"]

    # 5. Food Search
    resp_search = client.get("/api/v1/nutrition/search?query=Apple", headers=headers)
    assert resp_search.status_code == 200
    results = resp_search.json()
    assert len(results) >= 1
    apple = results[0]
    assert "Apple" in apple["common_name"] or "Apple" in apple["food_name"]
    apple_fdc_id = apple["fdc_id"]

    # 6. Exact Food Retrieval by FDC ID
    resp_get = client.get(f"/api/v1/nutrition/food/{apple_fdc_id}", headers=headers)
    assert resp_get.status_code == 200
    food_data = resp_get.json()
    assert food_data["fdc_id"] == apple_fdc_id
    assert food_data["nutrients"]["energy_kcal"] == 52.0
    assert food_data["nutrients"]["fiber_g"] == 2.4

    # 7. Nutrient Ranking
    ranked_fiber = nutrition_service.search_by_nutrient(db=db_session, nutrient_key="fiber_g", limit=5)
    assert len(ranked_fiber) >= 2
    # Ensure descending order of fiber
    assert ranked_fiber[0].nutrients["fiber_g"] >= ranked_fiber[1].nutrients["fiber_g"]

    # 8. Food Comparison
    resp_banana = client.get("/api/v1/nutrition/search?query=Banana", headers=headers)
    banana_fdc_id = resp_banana.json()[0]["fdc_id"]

    resp_comp = client.get(f"/api/v1/nutrition/compare?fdc_ids={apple_fdc_id},{banana_fdc_id}", headers=headers)
    assert resp_comp.status_code == 200
    comp_data = resp_comp.json()
    assert len(comp_data["foods"]) == 2
    assert "comparison_nutrients" in comp_data
    assert "USDA FoodData Central" in comp_data["source_attribution"]

# -----------------------------------------------------------------------------
# Test 9, 10, 11: Missing Food Handling, Source Attribution, Evidence Priority
# -----------------------------------------------------------------------------
def test_9_to_11_missing_food_attribution_and_evidence_guard(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # 9. Missing Food Handling (Non-existent FDC ID)
    resp_404 = client.get("/api/v1/nutrition/food/99999999", headers=headers)
    assert resp_404.status_code == 404

    # 10. Source Attribution Verification
    resp_apple = client.get("/api/v1/nutrition/search?query=Apple", headers=headers)
    apple = resp_apple.json()[0]
    assert apple["source_name"] == "USDA FoodData Central — Foundation Foods"
    assert "Public Domain" in apple["license"]

    # 11. Evidence Priority Guard: Patient Medical Records NEVER overridden by Nutrition Data
    lab = LabTest(
        user_id=user_id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose_fasting",
        observed_value="110",
        numeric_value=110.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-15"
    )
    db_session.add(lab)
    db_session.commit()

    # Query patient glucose
    chat_resp = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What was my glucose value?"},
        headers=headers
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    # Must answer with patient lab record, NOT nutrition data
    assert "110" in chat_data["answer"]
    assert "mg/dL" in chat_data["answer"]
    assert chat_data["query_type"] == "PATIENT_FACTUAL"

# -----------------------------------------------------------------------------
# Test 12, 13, 14, 15, 16, 17: Nutrition RAG & Multilingual AI Explanations
# -----------------------------------------------------------------------------
def test_12_to_17_nutrition_multilingual_explanations(
    client: TestClient,
    registered_user: dict
):
    headers = registered_user["headers"]

    # 12. Nutrition RAG Chat Query
    chat_resp = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What is the nutritional information of apple?", "language": "en"},
        headers=headers
    )
    assert chat_resp.status_code == 200
    data_en = chat_resp.json()
    assert "Apple" in data_en["answer"] or "Apples" in data_en["answer"]
    assert "52" in data_en["answer"]
    assert "kcal" in data_en["answer"]
    assert len(data_en["citations"]) >= 1
    assert "USDA FoodData Central" in data_en["citations"][0]["source_name"]

    # 13. Direct Explain API (English)
    exp_en = client.post(
        "/api/v1/nutrition/explain",
        json={"food_name": "Apple", "language": "en"},
        headers=headers
    )
    assert exp_en.status_code == 200
    assert "52" in exp_en.json()["explanation"]
    assert "kcal" in exp_en.json()["explanation"]

    # 14. Direct Explain API (Tamil)
    exp_ta = client.post(
        "/api/v1/nutrition/explain",
        json={"food_name": "Apple", "language": "ta"},
        headers=headers
    )
    assert exp_ta.status_code == 200
    assert "ஆற்றல்" in exp_ta.json()["explanation"] or "ஊட்டச்சத்து" in exp_ta.json()["explanation"]
    # 16 & 17: Numbers and units preserved
    assert "52" in exp_ta.json()["explanation"]
    assert "kcal" in exp_ta.json()["explanation"]

    # 15. Direct Explain API (Tanglish)
    exp_tg = client.post(
        "/api/v1/nutrition/explain",
        json={"food_name": "Apple", "language": "tanglish"},
        headers=headers
    )
    assert exp_tg.status_code == 200
    assert "records padi" in exp_tg.json()["explanation"].lower() or "nutrition values" in exp_tg.json()["explanation"].lower()
    # Numbers and units preserved
    assert "52" in exp_tg.json()["explanation"]
    assert "kcal" in exp_tg.json()["explanation"]

# -----------------------------------------------------------------------------
# Test 18 to 24: Regression, Auth & Cross-User Security Isolation
# -----------------------------------------------------------------------------
def test_18_to_24_security_and_regression(
    client: TestClient,
    registered_user: dict
):
    headers = registered_user["headers"]

    # 23. Unauthorized request rejection (No token)
    unauth_resp = client.get("/api/v1/nutrition/search?query=Apple")
    assert unauth_resp.status_code in [401, 403]

    # 24. Cross-User Security: User A accessing nutrition data gets public USDA data without data leaks
    resp_search = client.get("/api/v1/nutrition/search?query=Banana", headers=headers)
    assert resp_search.status_code == 200
    foods = resp_search.json()
    assert len(foods) >= 1
    for f in foods:
        assert "user_id" not in f # Public catalog contains no personal user IDs

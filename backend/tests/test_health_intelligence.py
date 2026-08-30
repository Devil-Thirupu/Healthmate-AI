import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory, OCRStatus
from backend.app.models.clinical import LabTest, Prescription, LabFlag
from backend.app.services.health_intelligence_service import health_intelligence_service

# -----------------------------------------------------------------------------
# 1. Calculation Unit Tests
# -----------------------------------------------------------------------------
def test_calculation_positive_change():
    """105 mg/dL -> 120 mg/dL: change = +15 mg/dL, pct = +14.29%, trend = Increased."""
    change, pct, trend = health_intelligence_service.calculate_change(105.0, 120.0, "mg/dL", "mg/dL")
    assert change == "+15 mg/dL"
    assert pct == "+14.29%"
    assert trend == "Increased"

def test_calculation_negative_change():
    """140 mg/dL -> 110 mg/dL: change = -30 mg/dL, pct = -21.43%, trend = Decreased."""
    change, pct, trend = health_intelligence_service.calculate_change(140.0, 110.0, "mg/dL", "mg/dL")
    assert change == "-30 mg/dL"
    assert pct == "-21.43%"
    assert trend == "Decreased"

def test_calculation_zero_change():
    """100 mg/dL -> 100 mg/dL: change = 0.0 mg/dL, pct = 0.00%, trend = Stable."""
    change, pct, trend = health_intelligence_service.calculate_change(100.0, 100.0, "mg/dL", "mg/dL")
    assert change == "0.0 mg/dL"
    assert pct == "0.00%"
    assert trend == "Stable"

def test_calculation_previous_value_zero():
    """Division by zero protection: previous = 0.0 -> pct = 'Not available'."""
    change, pct, trend = health_intelligence_service.calculate_change(0.0, 15.0, "mg/dL", "mg/dL")
    assert change == "+15 mg/dL"
    assert pct == "Not available"
    assert trend == "Increased"

def test_calculation_missing_and_non_numeric():
    """Missing or None values return 'Not available' and 'Insufficient data'."""
    change, pct, trend = health_intelligence_service.calculate_change(None, 120.0, "mg/dL", "mg/dL")
    assert change == "Not available"
    assert pct == "Not available"
    assert trend == "Insufficient data"

    change2, pct2, trend2 = health_intelligence_service.calculate_change(105.0, None, "mg/dL", "mg/dL")
    assert change2 == "Not available"
    assert pct2 == "Not available"
    assert trend2 == "Insufficient data"

# -----------------------------------------------------------------------------
# 2. Unit Compatibility Tests
# -----------------------------------------------------------------------------
def test_unit_compatibility_identical():
    """Case-insensitive identical units are compatible."""
    assert health_intelligence_service.are_units_compatible("mg/dL", "mg/dL") is True
    assert health_intelligence_service.are_units_compatible("mg/dl", "MG/DL") is True
    assert health_intelligence_service.are_units_compatible("%", "%") is True

def test_unit_compatibility_incompatible():
    """Incompatible units are rejected without invented conversions."""
    assert health_intelligence_service.are_units_compatible("mg/dL", "mmol/L") is False
    assert health_intelligence_service.are_units_compatible("g/dL", "mg/dL") is False
    
    change, pct, trend = health_intelligence_service.calculate_change(100.0, 5.5, "mg/dL", "mmol/L")
    assert change == "Incompatible units"
    assert pct == "Not available"
    assert trend == "Insufficient data"

def test_unit_compatibility_missing():
    """Missing or N/A units cannot be safely compared."""
    assert health_intelligence_service.are_units_compatible(None, "mg/dL") is False
    assert health_intelligence_service.are_units_compatible("", "") is False
    assert health_intelligence_service.are_units_compatible("N/A", "N/A") is False

# -----------------------------------------------------------------------------
# 3. Reference Range Evaluation Tests
# -----------------------------------------------------------------------------
def test_reference_range_within():
    """Value within min and max bounds."""
    status, text = health_intelligence_service.evaluate_reference_range(90.0, 70.0, 99.0, "70 - 99 mg/dL")
    assert status == "Within available reference range"
    assert text == "70 - 99 mg/dL"

def test_reference_range_outside():
    """Value outside min or max bounds."""
    status_high, _ = health_intelligence_service.evaluate_reference_range(125.0, 70.0, 99.0)
    assert status_high == "Outside available reference range"

    status_low, _ = health_intelligence_service.evaluate_reference_range(55.0, 70.0, 99.0)
    assert status_low == "Outside available reference range"

def test_reference_range_missing():
    """Missing reference range returns 'Not available in source'."""
    status, text = health_intelligence_service.evaluate_reference_range(100.0, None, None, None)
    assert status == "Not available in source"
    assert text is None

# -----------------------------------------------------------------------------
# 4. Trend Tolerance Tests (1% Relative Difference)
# -----------------------------------------------------------------------------
def test_trend_stability_tolerance():
    """Values within <= 1% relative difference are categorized as 'Stable'."""
    # 100.0 -> 100.8 is +0.8% difference -> Stable
    change, pct, trend = health_intelligence_service.calculate_change(100.0, 100.8, "mg/dL", "mg/dL")
    assert trend == "Stable"
    assert pct == "+0.80%"

    # 100.0 -> 101.5 is +1.5% difference -> Increased
    change2, pct2, trend2 = health_intelligence_service.calculate_change(100.0, 101.5, "mg/dL", "mg/dL")
    assert trend2 == "Increased"

    # 100.0 -> 99.2 is -0.8% difference -> Stable
    change3, pct3, trend3 = health_intelligence_service.calculate_change(100.0, 99.2, "mg/dL", "mg/dL")
    assert trend3 == "Stable"

# -----------------------------------------------------------------------------
# 5. Full Health Intelligence API & Report Comparison Integration Tests
# -----------------------------------------------------------------------------
def test_health_intelligence_summary_and_trends_api(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # 1. Create Report 1 (March 2026)
    doc1 = Document(
        user_id=user_id,
        original_filename="blood_test_mar.pdf",
        stored_filename="doc_mar_1.pdf",
        file_path="uploads/doc_mar_1.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_doc_mar_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="Diagnostic Panel March 2026",
        document_date="2026-03-10",
        clinic_or_lab="City Diagnostics"
    )
    db_session.add(doc1)
    db_session.commit()
    db_session.refresh(doc1)

    lab1_glucose = LabTest(
        document_id=doc1.id,
        user_id=user_id,
        test_name="Fasting Blood Sugar (FBS)",
        canonical_name="glucose_fasting",
        test_category="Diabetes",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        reference_range_min=70.0,
        reference_range_max=99.0,
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10",
        original_ocr_snippet="Fasting Blood Sugar: 105 mg/dL (Ref: 70-99)"
    )
    lab1_hba1c = LabTest(
        document_id=doc1.id,
        user_id=user_id,
        test_name="HbA1c",
        canonical_name="hba1c",
        test_category="Diabetes",
        observed_value="6.2",
        numeric_value=6.2,
        unit="%",
        reference_range_min=4.0,
        reference_range_max=5.6,
        reference_range_text="4.0 - 5.6 %",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10"
    )
    db_session.add_all([lab1_glucose, lab1_hba1c])
    db_session.commit()

    # 2. Create Report 2 (June 2026)
    doc2 = Document(
        user_id=user_id,
        original_filename="blood_test_jun.pdf",
        stored_filename="doc_jun_2.pdf",
        file_path="uploads/doc_jun_2.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_doc_jun_2",
        category=DocumentCategory.LAB_REPORT.value,
        title="Diagnostic Panel June 2026",
        document_date="2026-06-15",
        clinic_or_lab="City Diagnostics"
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    lab2_glucose = LabTest(
        document_id=doc2.id,
        user_id=user_id,
        test_name="Fasting Blood Sugar (FBS)",
        canonical_name="glucose_fasting",
        test_category="Diabetes",
        observed_value="120",
        numeric_value=120.0,
        unit="mg/dL",
        reference_range_min=70.0,
        reference_range_max=99.0,
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-06-15",
        original_ocr_snippet="Fasting Blood Sugar: 120 mg/dL"
    )
    lab2_hba1c = LabTest(
        document_id=doc2.id,
        user_id=user_id,
        test_name="HbA1c",
        canonical_name="hba1c",
        test_category="Diabetes",
        observed_value="5.8",
        numeric_value=5.8,
        unit="%",
        reference_range_min=4.0,
        reference_range_max=5.6,
        reference_range_text="4.0 - 5.6 %",
        flag=LabFlag.HIGH.value,
        test_date="2026-06-15"
    )
    db_session.add_all([lab2_glucose, lab2_hba1c])
    db_session.commit()

    # Test GET /api/v1/health-intelligence/summary
    sum_resp = client.get("/api/v1/health-intelligence/summary", headers=headers)
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["tracked_biomarkers_count"] == 2
    assert summary["total_measurements_count"] == 4
    
    # Check glucose change calculation (+15 mg/dL, +14.29%, Increased)
    glucose_item = next((c for c in summary["recent_changes"] if c["canonical_name"] == "glucose_fasting"), None)
    assert glucose_item is not None
    assert glucose_item["change"] == "+15 mg/dL"
    assert glucose_item["percentage_change"] == "+14.29%"
    assert glucose_item["trend_direction"] == "Increased"
    assert glucose_item["reference_range_status"] == "Outside available reference range"
    assert glucose_item["source_document_id"] == doc2.id

    # Check HbA1c change calculation (-0.4 %, -6.45%, Decreased)
    hba1c_item = next((c for c in summary["recent_changes"] if c["canonical_name"] == "hba1c"), None)
    assert hba1c_item is not None
    assert hba1c_item["change"] == "-0.4 %"
    assert hba1c_item["trend_direction"] == "Decreased"

    # Test GET /api/v1/health-intelligence/trends
    trend_resp = client.get("/api/v1/health-intelligence/trends", headers=headers)
    assert trend_resp.status_code == 200
    trends = trend_resp.json()
    assert len(trends) >= 2
    glucose_series = next((s for s in trends if s["canonical_name"] == "glucose_fasting"), None)
    assert glucose_series is not None
    assert len(glucose_series["data_points"]) == 2
    assert glucose_series["data_points"][0]["numeric_value"] == 105.0
    assert glucose_series["data_points"][1]["numeric_value"] == 120.0

    # Test POST /api/v1/health-intelligence/compare-reports (comparing doc1 and doc2)
    compare_resp = client.post(
        "/api/v1/health-intelligence/compare-reports",
        json={"document_ids": [doc1.id, doc2.id]},
        headers=headers
    )
    assert compare_resp.status_code == 200
    matrix = compare_resp.json()
    assert matrix["total_tests_compared"] == 2
    assert len(matrix["compared_documents"]) == 2

    # Test GET /api/v1/health-intelligence/timeline
    time_resp = client.get("/api/v1/health-intelligence/timeline", headers=headers)
    assert time_resp.status_code == 200
    timeline = time_resp.json()
    assert len(timeline) >= 2

# -----------------------------------------------------------------------------
# 6. Cross-User Security & Authorization Isolation
# -----------------------------------------------------------------------------
def test_cross_user_health_intelligence_isolation(client: TestClient, registered_user: dict, db_session: Session):
    # Register User 2
    u2_resp = client.post("/api/v1/auth/register", json={
        "email": "user2_hi@example.com",
        "password": "SecurePassword123!",
        "full_name": "Second Patient",
        "role": "patient"
    })
    user2_id = u2_resp.json()["user"]["id"]
    headers1 = registered_user["headers"]

    # Create private doc & lab test for User 2
    doc_u2 = Document(
        user_id=user2_id,
        original_filename="user2_confidential.pdf",
        stored_filename="u2_doc_1.pdf",
        file_path="uploads/u2_doc_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_u2_doc",
        category=DocumentCategory.LAB_REPORT.value,
        title="User 2 Secret Lipid Panel",
        document_date="2026-07-01"
    )
    db_session.add(doc_u2)
    db_session.commit()
    db_session.refresh(doc_u2)

    lab_u2 = LabTest(
        document_id=doc_u2.id,
        user_id=user2_id,
        test_name="Total Cholesterol",
        canonical_name="cholesterol_total",
        observed_value="240",
        numeric_value=240.0,
        unit="mg/dL",
        test_date="2026-07-01"
    )
    db_session.add(lab_u2)
    db_session.commit()

    # User 1 attempts to compare User 2's document ID -> 404
    comp_resp = client.post(
        "/api/v1/health-intelligence/compare-reports",
        json={"document_ids": [doc_u2.id, 99999]},
        headers=headers1
    )
    assert comp_resp.status_code == 404

"""
Student Performance API — Comprehensive Test Suite
===================================================
Tests the /predict endpoint with valid, invalid, and edge-case inputs.
Run:  python test_api.py
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"
PREDICT_URL = f"{BASE_URL}/predict"

# --- Valid test payload (matches model's expected features) ---
VALID_PAYLOAD = {
    "school": "GP",
    "sex": "M",
    "age": 18,
    "address": "U",
    "famsize": "GT3",
    "Pstatus": "T",
    "Medu": 3,
    "Fedu": 3,
    "Mjob": "services",
    "Fjob": "other",
    "reason": "course",
    "guardian": "mother",
    "traveltime": 2,
    "studytime": 2,
    "failures": 0,
    "schoolsup": "no",
    "famsup": "yes",
    "paid": "no",
    "activities": "yes",
    "nursery": "yes",
    "higher": "yes",
    "internet": "yes",
    "romantic": "no",
    "famrel": 4,
    "freetime": 3,
    "goout": 3,
    "Dalc": 1,
    "Walc": 1,
    "health": 3,
    "absences": 4,
}

HEADERS = {"Content-Type": "application/json"}

passed = 0
failed = 0


def report(test_name, success, detail=""):
    global passed, failed
    status = "✅ PASS" if success else "❌ FAIL"
    if success:
        passed += 1
    else:
        failed += 1
    print(f"  {status}  {test_name}")
    if detail:
        print(f"         ↳ {detail}")


def test_health_check():
    """TC-01: GET / should return 200."""
    print("\n─── TC-01: Health Check (GET /) ───")
    try:
        r = requests.get(BASE_URL, timeout=5)
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Body contains running msg", "Running" in r.text, r.text[:80])
    except requests.ConnectionError:
        report("Server reachable", False, "Connection refused — is the server running?")


def test_valid_prediction():
    """TC-02: POST /predict with valid payload should return a prediction."""
    print("\n─── TC-02: Valid Prediction ───")
    try:
        r = requests.post(PREDICT_URL, json=VALID_PAYLOAD, headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'prediction' key", "prediction" in data, str(data))
        if "prediction" in data:
            val = data["prediction"]
            report("Prediction is float", isinstance(val, (int, float)), f"type={type(val).__name__}, value={val}")
            report("Prediction in range [0, 20]", 0 <= val <= 20, f"value={val}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_missing_field():
    """TC-03: Missing a required field should return 422."""
    print("\n─── TC-03: Missing Field ('school' removed) ───")
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "school"}
    try:
        r = requests.post(PREDICT_URL, json=payload, headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
        report("Lists missing fields", "missing_fields" in data, str(data.get("missing_fields", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_wrong_keys():
    """TC-04: Completely wrong keys (original test JSON) should fail."""
    print("\n─── TC-04: Wrong Keys (original user-provided JSON) ───")
    wrong_payload = {
        "hours_studied": 6, "attendance": 88, "previous_scores": 72,
        "sleep_hours": 7, "motivation_level": 4, "internet_access": 1,
        "family_income": 2, "teacher_quality": 3, "school_type": 1,
        "peer_influence": 3, "physical_activity": 2, "learning_disabilities": 0,
        "parental_education_level": 2, "distance_from_home": 5, "gender": 1,
    }
    try:
        r = requests.post(PREDICT_URL, json=wrong_payload, headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error (expected)", "error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_invalid_categorical_value():
    """TC-05: Invalid value for a categorical feature."""
    print("\n─── TC-05: Invalid Categorical Value (school='INVALID') ───")
    payload = {**VALID_PAYLOAD, "school": "INVALID"}
    try:
        r = requests.post(PREDICT_URL, json=payload, headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
        report("Shows allowed values", "allowed_values" in data, str(data.get("allowed_values", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_type_mismatch():
    """TC-06: Numeric field sent as string should return 422."""
    print("\n─── TC-06: Type Mismatch (age as string) ───")
    payload = {**VALID_PAYLOAD, "age": "eighteen"}
    try:
        r = requests.post(PREDICT_URL, json=payload, headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_empty_body():
    """TC-07: Empty body should return 400."""
    print("\n─── TC-07: Empty Request Body ───")
    try:
        r = requests.post(PREDICT_URL, data="", headers=HEADERS, timeout=5)
        data = r.json()
        report("Status 400", r.status_code == 400, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_wrong_method():
    """TC-08: GET /predict should not be allowed."""
    print("\n─── TC-08: Wrong HTTP Method (GET /predict) ───")
    try:
        r = requests.get(PREDICT_URL, timeout=5)
        report("Returns 405 Method Not Allowed", r.status_code == 405, f"status={r.status_code}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_extra_fields():
    """TC-09: Extra unexpected fields should be ignored gracefully."""
    print("\n─── TC-09: Extra Fields ───")
    payload = {**VALID_PAYLOAD, "extra_field": 999, "bonus": "test"}
    try:
        r = requests.post(PREDICT_URL, json=payload, headers=HEADERS, timeout=5)
        data = r.json()
        report("Still returns prediction", "prediction" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_health_endpoint():
    """TC-10: GET /health should return status."""
    print("\n─── TC-10: Health Endpoint (GET /health) ───")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'status' key", "status" in data, str(data))
        report("Has 'model_features' key", "model_features" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_schema_endpoint():
    """TC-11: GET /schema should return feature schema."""
    print("\n─── TC-11: Schema Endpoint (GET /schema) ───")
    try:
        r = requests.get(f"{BASE_URL}/schema", timeout=5)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'required_features'", "required_features" in data, f"{len(data.get('required_features', []))} features")
        report("Has 'categorical_features'", "categorical_features" in data, f"{len(data.get('categorical_features', {}))} categories")
        report("Has 'numeric_features'", "numeric_features" in data, f"{len(data.get('numeric_features', []))} numeric")
    except Exception as e:
        report("Request succeeded", False, str(e))


if __name__ == "__main__":
    print("=" * 60)
    print("  Student Performance API — Test Suite")
    print("=" * 60)

    test_health_check()
    test_valid_prediction()
    test_missing_field()
    test_wrong_keys()
    test_invalid_categorical_value()
    test_type_mismatch()
    test_empty_body()
    test_wrong_method()
    test_extra_fields()
    test_health_endpoint()
    test_schema_endpoint()

    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    sys.exit(1 if failed else 0)

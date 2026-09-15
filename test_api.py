"""
Student Performance API — Comprehensive Test Suite
===================================================
Tests /predict/holistic and /predict/grade with valid, invalid, and
edge-case inputs, plus model-isolation checks that verify each endpoint
is actually backed by its own model artifacts (not whichever .pkl
happens to be on disk).
Run:  python test_api.py
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"
HOLISTIC_URL = f"{BASE_URL}/predict/holistic"
GRADE_URL = f"{BASE_URL}/predict/grade"
LEGACY_URL = f"{BASE_URL}/predict"

HEADERS = {"Content-Type": "application/json"}

# --- Valid Holistic payload: no G1/G2 ---
VALID_HOLISTIC_PAYLOAD = {
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

# --- Valid Grade-Based payload: same student + G1/G2 ---
VALID_GRADE_PAYLOAD = {**VALID_HOLISTIC_PAYLOAD, "G1": 12, "G2": 13}

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


def post(url, payload=None, raw_data=None):
    if raw_data is not None:
        return requests.post(url, data=raw_data, headers=HEADERS, timeout=5)
    return requests.post(url, json=payload, headers=HEADERS, timeout=5)


# ───────────────────────── Basic health / schema ─────────────────────────

def test_health_check():
    """TC-01: GET / should return 200."""
    print("\n─── TC-01: Health Check (GET /) ───")
    try:
        r = requests.get(BASE_URL, timeout=5)
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Body contains running msg", "Running" in r.text, r.text[:80])
    except requests.ConnectionError:
        report("Server reachable", False, "Connection refused — is the server running?")


def test_health_endpoint():
    """TC-02: GET /health should report both models."""
    print("\n─── TC-02: Health Endpoint (GET /health) ───")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'status' key", "status" in data, str(data))
        report("Reports holistic model", "holistic" in data.get("models", {}), str(data))
        report("Reports grade model", "grade" in data.get("models", {}), str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_schema_endpoints():
    """TC-03: GET /schema, /schema/holistic, /schema/grade."""
    print("\n─── TC-03: Schema Endpoints ───")
    try:
        r = requests.get(f"{BASE_URL}/schema", timeout=5)
        data = r.json()
        report("Combined /schema has both models", "holistic" in data and "grade" in data, str(list(data.keys())))

        r_h = requests.get(f"{BASE_URL}/schema/holistic", timeout=5)
        data_h = r_h.json()
        report("/schema/holistic has 30 features, no G1/G2",
               len(data_h.get("required_features", [])) == 30
               and "G1" not in data_h.get("required_features", [])
               and "G2" not in data_h.get("required_features", []),
               f"{len(data_h.get('required_features', []))} features")

        r_g = requests.get(f"{BASE_URL}/schema/grade", timeout=5)
        data_g = r_g.json()
        report("/schema/grade has 32 features, incl. G1/G2",
               len(data_g.get("required_features", [])) == 32
               and "G1" in data_g.get("required_features", [])
               and "G2" in data_g.get("required_features", []),
               f"{len(data_g.get('required_features', []))} features")
    except Exception as e:
        report("Request succeeded", False, str(e))


# ───────────────────────── Holistic endpoint ─────────────────────────

def test_holistic_valid_prediction():
    """TC-04: POST /predict/holistic with valid payload."""
    print("\n─── TC-04: Holistic — Valid Prediction ───")
    try:
        r = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'prediction' key", "prediction" in data, str(data))
        report("Reports model=holistic", data.get("model") == "holistic", str(data))
        if "prediction" in data:
            val = data["prediction"]
            report("Prediction is float", isinstance(val, (int, float)), f"type={type(val).__name__}")
            report("Prediction in range [0, 20]", 0 <= val <= 20, f"value={val}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_holistic_missing_field():
    """TC-05: Holistic — missing a required field → 422."""
    print("\n─── TC-05: Holistic — Missing Field ('school' removed) ───")
    payload = {k: v for k, v in VALID_HOLISTIC_PAYLOAD.items() if k != "school"}
    try:
        r = post(HOLISTIC_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
        report("Lists missing fields", "missing_fields" in data, str(data.get("missing_fields", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_holistic_invalid_categorical():
    """TC-06: Holistic — invalid categorical value → 422."""
    print("\n─── TC-06: Holistic — Invalid Categorical Value (school='INVALID') ───")
    payload = {**VALID_HOLISTIC_PAYLOAD, "school": "INVALID"}
    try:
        r = post(HOLISTIC_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Shows allowed values", "allowed_values" in data, str(data.get("allowed_values", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_holistic_type_mismatch():
    """TC-07: Holistic — numeric field sent as string → 422."""
    print("\n─── TC-07: Holistic — Type Mismatch (age as string) ───")
    payload = {**VALID_HOLISTIC_PAYLOAD, "age": "eighteen"}
    try:
        r = post(HOLISTIC_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_holistic_g1_g2_not_required():
    """TC-08: Holistic — omitting G1/G2 is fine (they aren't part of its schema)."""
    print("\n─── TC-08: Holistic — G1/G2 Not Required ───")
    try:
        assert "G1" not in VALID_HOLISTIC_PAYLOAD and "G2" not in VALID_HOLISTIC_PAYLOAD
        r = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD)
        data = r.json()
        report("Predicts successfully without G1/G2", r.status_code == 200 and "prediction" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


# ───────────────────────── Grade-based endpoint ─────────────────────────

def test_grade_valid_prediction():
    """TC-09: POST /predict/grade with valid payload."""
    print("\n─── TC-09: Grade — Valid Prediction ───")
    try:
        r = post(GRADE_URL, VALID_GRADE_PAYLOAD)
        data = r.json()
        report("Status 200", r.status_code == 200, f"status={r.status_code}")
        report("Has 'prediction' key", "prediction" in data, str(data))
        report("Reports model=grade", data.get("model") == "grade", str(data))
        if "prediction" in data:
            val = data["prediction"]
            report("Prediction in range [0, 20]", 0 <= val <= 20, f"value={val}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_missing_g1():
    """TC-10: Grade — missing G1 → 422."""
    print("\n─── TC-10: Grade — Missing G1 ───")
    payload = {k: v for k, v in VALID_GRADE_PAYLOAD.items() if k != "G1"}
    try:
        r = post(GRADE_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Lists G1 as missing", "G1" in data.get("missing_fields", []), str(data.get("missing_fields", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_missing_g2():
    """TC-11: Grade — missing G2 → 422."""
    print("\n─── TC-11: Grade — Missing G2 ───")
    payload = {k: v for k, v in VALID_GRADE_PAYLOAD.items() if k != "G2"}
    try:
        r = post(GRADE_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Lists G2 as missing", "G2" in data.get("missing_fields", []), str(data.get("missing_fields", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_invalid_categorical():
    """TC-12: Grade — invalid categorical value → 422."""
    print("\n─── TC-12: Grade — Invalid Categorical Value (Mjob='INVALID') ───")
    payload = {**VALID_GRADE_PAYLOAD, "Mjob": "INVALID"}
    try:
        r = post(GRADE_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Shows allowed values", "allowed_values" in data, str(data.get("allowed_values", [])))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_type_mismatch():
    """TC-13: Grade — G1 sent as string → 422."""
    print("\n─── TC-13: Grade — Type Mismatch (G1 as string) ───")
    payload = {**VALID_GRADE_PAYLOAD, "G1": "twelve"}
    try:
        r = post(GRADE_URL, payload)
        data = r.json()
        report("Status 422", r.status_code == 422, f"status={r.status_code}")
        report("Returns error key", "error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_g1_g2_required():
    """TC-14: Grade — G1/G2 are mandatory, confirmed via schema + rejection above."""
    print("\n─── TC-14: Grade — G1/G2 Required (cross-check via schema) ───")
    try:
        r = requests.get(f"{BASE_URL}/schema/grade", timeout=5)
        data = r.json()
        required = data.get("required_features", [])
        report("G1 listed as required", "G1" in required, str(required))
        report("G2 listed as required", "G2" in required, str(required))
    except Exception as e:
        report("Request succeeded", False, str(e))


# ───────────────────────── Explainable AI (SHAP) ─────────────────────────

def test_holistic_explanation_present_and_valid():
    """TC-20: Holistic prediction includes a real SHAP explanation."""
    print("\n─── TC-20: Holistic — Explanation Present & Valid ───")
    try:
        r = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD)
        data = r.json()
        explanation = data.get("explanation")
        report("Response has 'explanation' key", explanation is not None, str(explanation is not None))
        if explanation:
            features = explanation.get("features", [])
            names = [f["feature"] for f in features]
            report("Explanation has exactly 30 features (Holistic)", len(names) == 30, f"{len(names)} features")
            report("G1 not in explanation", "G1" not in names, str(names))
            report("G2 not in explanation", "G2" not in names, str(names))
            report(
                "All SHAP impacts are numeric",
                all(isinstance(f["impact"], (int, float)) for f in features),
                str([type(f["impact"]).__name__ for f in features[:3]]),
            )
            report(
                "Feature values match submitted data",
                all(f["value"] == VALID_HOLISTIC_PAYLOAD.get(f["feature"]) for f in features),
                "sample: " + str(features[0]) if features else "no features",
            )
            report("Has 'base_value'", isinstance(explanation.get("base_value"), (int, float)), str(explanation.get("base_value")))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_grade_explanation_present_and_valid():
    """TC-21: Grade prediction includes a real SHAP explanation, G1/G2 may appear."""
    print("\n─── TC-21: Grade — Explanation Present & Valid ───")
    try:
        r = post(GRADE_URL, VALID_GRADE_PAYLOAD)
        data = r.json()
        explanation = data.get("explanation")
        report("Response has 'explanation' key", explanation is not None, str(explanation is not None))
        if explanation:
            features = explanation.get("features", [])
            names = [f["feature"] for f in features]
            report("Explanation has exactly 32 features (Grade)", len(names) == 32, f"{len(names)} features")
            report("G1 can appear in explanation", "G1" in names, str(names))
            report("G2 can appear in explanation", "G2" in names, str(names))
            report(
                "All SHAP impacts are numeric",
                all(isinstance(f["impact"], (int, float)) for f in features),
                str([type(f["impact"]).__name__ for f in features[:3]]),
            )
            report(
                "Explanation contains only Grade model features",
                set(names) <= set(VALID_GRADE_PAYLOAD.keys()),
                str(names),
            )
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_shap_math_validation():
    """TC-22: base_value + sum(SHAP contributions) ≈ prediction, for both models."""
    print("\n─── TC-22: SHAP Mathematical Validation ───")
    try:
        r_h = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD).json()
        exp_h = r_h.get("explanation") or {}
        total_h = exp_h.get("base_value", 0) + sum(f["impact"] for f in exp_h.get("features", []))
        report(
            "Holistic: base_value + sum(shap) ≈ prediction",
            abs(total_h - r_h.get("prediction", float("inf"))) < 1e-3,
            f"total={total_h}, prediction={r_h.get('prediction')}",
        )

        r_g = post(GRADE_URL, VALID_GRADE_PAYLOAD).json()
        exp_g = r_g.get("explanation") or {}
        total_g = exp_g.get("base_value", 0) + sum(f["impact"] for f in exp_g.get("features", []))
        report(
            "Grade: base_value + sum(shap) ≈ prediction",
            abs(total_g - r_g.get("prediction", float("inf"))) < 1e-3,
            f"total={total_g}, prediction={r_g.get('prediction')}",
        )
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_prediction_survives_explanation_failure_contract():
    """TC-23: contract check — a healthy response's explanation shape never
    breaks the prediction field, and the null-explanation shape (if it
    ever occurs) still carries a usable prediction. Forced-failure
    injection is covered in test_xai.py (pytest) via monkeypatching."""
    print("\n─── TC-23: Explanation Failure Contract (see test_xai.py for injected-failure test) ───")
    try:
        r = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD)
        data = r.json()
        report("Prediction present regardless of explanation outcome", isinstance(data.get("prediction"), (int, float)), str(data.get("prediction")))
        if data.get("explanation") is None:
            report("Null explanation carries explanation_error", "explanation_error" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


# ───────────────────────── Shared error handling ─────────────────────────

def test_empty_body():
    """TC-15: Empty body on either endpoint → 400."""
    print("\n─── TC-15: Empty Request Body (both endpoints) ───")
    try:
        r1 = post(HOLISTIC_URL, raw_data="")
        report("Holistic: status 400", r1.status_code == 400, f"status={r1.status_code}")
        r2 = post(GRADE_URL, raw_data="")
        report("Grade: status 400", r2.status_code == 400, f"status={r2.status_code}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_wrong_method():
    """TC-16: GET on a /predict/* route should not be allowed."""
    print("\n─── TC-16: Wrong HTTP Method (GET /predict/holistic) ───")
    try:
        r = requests.get(HOLISTIC_URL, timeout=5)
        report("Returns 405 Method Not Allowed", r.status_code == 405, f"status={r.status_code}")
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_extra_fields():
    """TC-17: Extra unexpected fields are ignored gracefully."""
    print("\n─── TC-17: Extra Fields (Holistic) ───")
    payload = {**VALID_HOLISTIC_PAYLOAD, "extra_field": 999, "bonus": "test"}
    try:
        r = post(HOLISTIC_URL, payload)
        data = r.json()
        report("Still returns prediction", "prediction" in data, str(data))
    except Exception as e:
        report("Request succeeded", False, str(e))


def test_legacy_predict_requires_model_field():
    """TC-18: Legacy /predict must not silently pick a model — requires an explicit 'model' field."""
    print("\n─── TC-18: Legacy /predict — Explicit Model Selection ───")
    try:
        r = post(LEGACY_URL, VALID_HOLISTIC_PAYLOAD)  # no "model" field
        data = r.json()
        report("Ambiguous request rejected (422)", r.status_code == 422, f"status={r.status_code}")
        report("Explains how to disambiguate", "model" in data.get("field", ""), str(data))

        r2 = post(LEGACY_URL, {**VALID_HOLISTIC_PAYLOAD, "model": "holistic"})
        data2 = r2.json()
        report("Explicit model=holistic routes correctly", data2.get("model") == "holistic", str(data2))

        r3 = post(LEGACY_URL, {**VALID_GRADE_PAYLOAD, "model": "grade"})
        data3 = r3.json()
        report("Explicit model=grade routes correctly", data3.get("model") == "grade", str(data3))
    except Exception as e:
        report("Request succeeded", False, str(e))


# ───────────────────────── Model isolation ─────────────────────────

def test_model_isolation():
    """TC-19: /predict/holistic and /predict/grade must use their own model —
    never fall back to, or share weights/features with, the other one."""
    print("\n─── TC-19: Model Isolation ───")
    try:
        # A payload without G1/G2 must be rejected by the grade endpoint,
        # proving it did not silently reuse the holistic model/schema.
        r_g_missing = post(GRADE_URL, VALID_HOLISTIC_PAYLOAD)
        report(
            "Grade endpoint rejects a Holistic-shaped payload (needs G1/G2)",
            r_g_missing.status_code == 422,
            f"status={r_g_missing.status_code}",
        )

        # A payload with G1/G2 still works on the holistic endpoint (extra
        # fields ignored) but the schema/feature count it reports must stay 30.
        r_h_schema = requests.get(f"{BASE_URL}/schema/holistic", timeout=5).json()
        r_g_schema = requests.get(f"{BASE_URL}/schema/grade", timeout=5).json()
        report(
            "Holistic and Grade schemas are distinct feature sets",
            set(r_h_schema["required_features"]) != set(r_g_schema["required_features"]),
            f"holistic={len(r_h_schema['required_features'])} grade={len(r_g_schema['required_features'])}",
        )

        # Same student, scored by both endpoints, must not produce
        # identical model objects' predictions purely by coincidence —
        # check the responses explicitly tag which model answered.
        r_h = post(HOLISTIC_URL, VALID_HOLISTIC_PAYLOAD).json()
        r_g = post(GRADE_URL, VALID_GRADE_PAYLOAD).json()
        report(
            "Holistic response tagged model=holistic",
            r_h.get("model") == "holistic",
            str(r_h),
        )
        report(
            "Grade response tagged model=grade",
            r_g.get("model") == "grade",
            str(r_g),
        )
    except Exception as e:
        report("Request succeeded", False, str(e))


if __name__ == "__main__":
    print("=" * 60)
    print("  Student Performance API — Test Suite")
    print("=" * 60)

    test_health_check()
    test_health_endpoint()
    test_schema_endpoints()

    test_holistic_valid_prediction()
    test_holistic_missing_field()
    test_holistic_invalid_categorical()
    test_holistic_type_mismatch()
    test_holistic_g1_g2_not_required()

    test_grade_valid_prediction()
    test_grade_missing_g1()
    test_grade_missing_g2()
    test_grade_invalid_categorical()
    test_grade_type_mismatch()
    test_grade_g1_g2_required()

    test_holistic_explanation_present_and_valid()
    test_grade_explanation_present_and_valid()
    test_shap_math_validation()
    test_prediction_survives_explanation_failure_contract()

    test_empty_body()
    test_wrong_method()
    test_extra_fields()
    test_legacy_predict_requires_model_field()

    test_model_isolation()

    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    sys.exit(1 if failed else 0)

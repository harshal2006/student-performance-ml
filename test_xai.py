"""
Pytest suite for the SHAP-based explanation layer added to /predict/holistic
and /predict/grade.

Uses Flask's in-process test client (no running server / port needed —
avoids the local macOS AirPlay-on-5000 issue entirely), importing the real
`app` module so these tests exercise the actual loaded model artifacts,
not a mock.

Run with:  pytest test_xai.py
"""

import math

import pytest

from app import app as flask_app

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

VALID_GRADE_PAYLOAD = {**VALID_HOLISTIC_PAYLOAD, "G1": 12, "G2": 13}


@pytest.fixture
def client():
    return flask_app.test_client()


# ───────────────────────── Holistic ─────────────────────────

def test_holistic_prediction_has_explanation(client):
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    assert r.status_code == 200
    data = r.get_json()
    assert data["explanation"] is not None
    assert "explanation_error" not in data


def test_holistic_explanation_features_are_valid_model_features(client):
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    data = r.get_json()
    names = [entry["feature"] for entry in data["explanation"]["features"]]
    assert len(names) == 30
    assert len(set(names)) == 30  # no duplicates


def test_holistic_explanation_never_contains_g1_g2(client):
    # Even if the caller tries to smuggle G1/G2 in, the Holistic model's
    # own artifacts never had those columns — they can't appear.
    payload = {**VALID_HOLISTIC_PAYLOAD, "G1": 20, "G2": 20}
    r = client.post("/predict/holistic", json=payload)
    data = r.get_json()
    names = [entry["feature"] for entry in data["explanation"]["features"]]
    assert "G1" not in names
    assert "G2" not in names


def test_holistic_shap_values_are_numeric(client):
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    data = r.get_json()
    for entry in data["explanation"]["features"]:
        assert isinstance(entry["impact"], (int, float))
        assert entry["direction"] in ("positive", "negative")
        assert (entry["impact"] >= 0) == (entry["direction"] == "positive")


def test_holistic_explanation_values_match_submitted_data(client):
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    data = r.get_json()
    for entry in data["explanation"]["features"]:
        assert entry["value"] == VALID_HOLISTIC_PAYLOAD[entry["feature"]]


def test_holistic_shap_math_validation(client):
    """base_value + sum(shap contributions) ≈ prediction."""
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    data = r.get_json()
    exp = data["explanation"]
    total = exp["base_value"] + sum(f["impact"] for f in exp["features"])
    assert math.isclose(total, data["prediction"], abs_tol=1e-3)


# ───────────────────────── Grade-Based ─────────────────────────

def test_grade_prediction_has_explanation(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    assert r.status_code == 200
    data = r.get_json()
    assert data["explanation"] is not None


def test_grade_explanation_can_include_g1_g2(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    names = [entry["feature"] for entry in data["explanation"]["features"]]
    assert "G1" in names
    assert "G2" in names


def test_grade_explanation_features_are_valid_model_features(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    names = [entry["feature"] for entry in data["explanation"]["features"]]
    assert len(names) == 32
    assert len(set(names)) == 32


def test_grade_shap_values_are_numeric(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    for entry in data["explanation"]["features"]:
        assert isinstance(entry["impact"], (int, float))


def test_grade_shap_math_validation(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    exp = data["explanation"]
    total = exp["base_value"] + sum(f["impact"] for f in exp["features"])
    assert math.isclose(total, data["prediction"], abs_tol=1e-3)


def test_grade_g1_g2_not_forced_important(client):
    """G1/G2 must reflect their REAL SHAP contribution, however small —
    never artificially inflated. This just asserts they're present with
    a real (possibly small) numeric impact, not that they rank first."""
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    by_name = {f["feature"]: f for f in data["explanation"]["features"]}
    assert isinstance(by_name["G1"]["impact"], float)
    assert isinstance(by_name["G2"]["impact"], float)


# ───────────────────────── Sorting ─────────────────────────

def test_explanation_features_sorted_by_absolute_impact(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    impacts = [abs(f["impact"]) for f in data["explanation"]["features"]]
    assert impacts == sorted(impacts, reverse=True)


# ───────────────────────── Error handling ─────────────────────────

def test_prediction_survives_explanation_failure(client, monkeypatch):
    """If SHAP itself blows up, the prediction must still come back —
    with explanation: null and an explanation_error, never a fake value."""

    def boom(self, encoded_row):
        raise RuntimeError("forced failure for test")

    monkeypatch.setattr("xai.ModelExplainer.explain", boom)

    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data["prediction"], float)
    assert data["explanation"] is None
    assert "explanation_error" in data
    assert isinstance(data["explanation_error"], str)


def test_grade_prediction_survives_explanation_failure(client, monkeypatch):
    def boom(self, encoded_row):
        raise RuntimeError("forced failure for test")

    monkeypatch.setattr("xai.ModelExplainer.explain", boom)

    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data["prediction"], float)
    assert data["explanation"] is None
    assert "explanation_error" in data


# ───────────────────────── Prediction unchanged by XAI ─────────────────────────

def test_holistic_prediction_value_unchanged(client):
    """Same input must give the same prediction as before XAI existed."""
    r = client.post("/predict/holistic", json=VALID_HOLISTIC_PAYLOAD)
    data = r.get_json()
    assert math.isclose(data["prediction"], 10.678376197814941, abs_tol=1e-6)


def test_grade_prediction_value_unchanged(client):
    r = client.post("/predict/grade", json=VALID_GRADE_PAYLOAD)
    data = r.get_json()
    assert math.isclose(data["prediction"], 13.538524627685547, abs_tol=1e-6)

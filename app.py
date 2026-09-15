from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np

from xai import ModelExplainer, build_explanation

app = Flask(__name__)

# Smallest reasonable CORS setup: allow any origin to call the JSON API
# endpoints (no cookies/credentials are used), so a local React/Vite dev
# server can reach Flask without needing a proxy.
CORS(app, resources={r"/*": {"origins": "*"}})


def load_model_bundle(model_path, encoders_path, features_path):
    """Load one model's artifacts and derive its schema. Isolated per model
    so the Holistic and Grade-Based models can never share state."""
    model = pickle.load(open(model_path, "rb"))
    encoders = pickle.load(open(encoders_path, "rb"))
    features = pickle.load(open(features_path, "rb"))
    categorical_allowed = {col: list(encoders[col].classes_) for col in encoders}
    numeric_features = [f for f in features if f not in encoders]
    # Built once here, from this model alone, so a Holistic explanation can
    # never see the Grade-Based model's trees (or vice versa) — the same
    # per-model isolation the prediction path already has.
    explainer = ModelExplainer(model, features)
    return {
        "model": model,
        "encoders": encoders,
        "features": features,
        "categorical_allowed": categorical_allowed,
        "numeric_features": numeric_features,
        "explainer": explainer,
    }


# Each variant's artifacts are loaded once at startup, from distinct files,
# so the two models coexist independently — no shared filenames, no
# ambiguity about which model is being served.
MODELS = {
    "holistic": load_model_bundle(
        "xgb_model_holistic.pkl", "encoders_holistic.pkl", "features_holistic.pkl"
    ),
    "grade": load_model_bundle(
        "xgb_model_grade.pkl", "encoders_grade.pkl", "features_grade.pkl"
    ),
}


@app.route("/")
def home():
    return "API Running 🚀"


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "models": {
            variant: {"model_features": len(bundle["features"])}
            for variant, bundle in MODELS.items()
        },
    })


def schema_for(variant):
    bundle = MODELS[variant]
    return {
        "model": variant,
        "required_features": bundle["features"],
        "categorical_features": bundle["categorical_allowed"],
        "numeric_features": bundle["numeric_features"],
    }


@app.route("/schema")
def schema():
    """Combined schema for both models, so a caller can fetch either in one request."""
    return jsonify({variant: schema_for(variant) for variant in MODELS})


@app.route("/schema/holistic")
def schema_holistic():
    return jsonify(schema_for("holistic"))


@app.route("/schema/grade")
def schema_grade():
    return jsonify(schema_for("grade"))


def run_prediction(variant):
    bundle = MODELS[variant]
    features = bundle["features"]
    encoders = bundle["encoders"]
    categorical_allowed = bundle["categorical_allowed"]
    numeric_features = bundle["numeric_features"]

    # --- 1. Check for valid JSON body ---
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # --- 2. Check for missing fields ---
    missing = [f for f in features if f not in data]
    if missing:
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing,
            "hint": f"Send GET /schema/{variant} for the full list of expected features"
        }), 422

    # --- 3. Validate categorical values ---
    for col, allowed in categorical_allowed.items():
        val = data[col]
        if val not in allowed:
            return jsonify({
                "error": f"Invalid value for '{col}'",
                "received": val,
                "allowed_values": allowed
            }), 422

    # --- 4. Validate numeric types ---
    for col in numeric_features:
        if not isinstance(data[col], (int, float)):
            return jsonify({
                "error": f"Field '{col}' must be a number",
                "received": data[col],
                "received_type": type(data[col]).__name__
            }), 422

    # --- 5. Encode & predict (operates on a local copy; never mutates
    #         the other model's state) ---
    try:
        encoded = dict(data)
        for col in encoders:
            encoded[col] = encoders[col].transform([encoded[col]])[0]

        # Feature ordering is preserved by iterating `features` in the
        # exact order the model was trained on.
        input_data = [encoded[col] for col in features]
        final_input = np.array(input_data).reshape(1, -1)

        prediction = bundle["model"].predict(final_input)

    except Exception as e:
        app.logger.error(f"Prediction failed ({variant}): {e}")
        return jsonify({
            "error": "Prediction failed due to an internal error"
        }), 500

    response = {
        "model": variant,
        "prediction": float(prediction[0]),
    }

    # SHAP runs on the exact same encoded row the model just predicted
    # from. A failure here must never take down an otherwise-successful
    # prediction — it degrades to explanation: null, not a fake explanation.
    try:
        shap_row, base_value = bundle["explainer"].explain(final_input)
        response["explanation"] = build_explanation(features, shap_row, base_value, data)
    except Exception as e:
        app.logger.error(f"Explanation failed ({variant}): {e}")
        response["explanation"] = None
        response["explanation_error"] = "Explanation could not be generated for this prediction."

    return jsonify(response)


@app.route("/predict/holistic", methods=["POST"])
def predict_holistic():
    return run_prediction("holistic")


@app.route("/predict/grade", methods=["POST"])
def predict_grade():
    return run_prediction("grade")


@app.route("/predict", methods=["POST"])
def predict_legacy():
    """Backward-compatible route. Does NOT guess which model to use from
    whatever happens to be on disk — it requires an explicit `model` field
    (`"holistic"` or `"grade"`) in the request body and delegates to the
    matching endpoint, so the ambiguity the audit flagged cannot recur."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    variant = data.get("model")
    if variant not in MODELS:
        return jsonify({
            "error": "Request must specify which model to use",
            "field": "model",
            "allowed_values": list(MODELS.keys()),
            "hint": "Or call /predict/holistic or /predict/grade directly"
        }), 422

    return run_prediction(variant)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)

# Load model, encoders, and feature order
model = pickle.load(open("xgb_model.pkl", "rb"))
encoders = pickle.load(open("encoders.pkl", "rb"))
features = pickle.load(open("features.pkl", "rb"))

# Build allowed values for categorical features
CATEGORICAL_ALLOWED = {col: list(encoders[col].classes_) for col in encoders}
NUMERIC_FEATURES = [f for f in features if f not in encoders]


@app.route("/")
def home():
    return "API Running 🚀"


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "model_features": len(features)})


@app.route("/schema")
def schema():
    """Return the expected input schema so consumers know what to send."""
    return jsonify({
        "required_features": features,
        "categorical_features": CATEGORICAL_ALLOWED,
        "numeric_features": NUMERIC_FEATURES,
    })


@app.route("/predict", methods=["POST"])
def predict():
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
            "hint": "Send GET /schema for the full list of expected features"
        }), 422

    # --- 3. Validate categorical values ---
    for col, allowed in CATEGORICAL_ALLOWED.items():
        val = data[col]
        if val not in allowed:
            return jsonify({
                "error": f"Invalid value for '{col}'",
                "received": val,
                "allowed_values": allowed
            }), 422

    # --- 4. Validate numeric types ---
    for col in NUMERIC_FEATURES:
        if not isinstance(data[col], (int, float)):
            return jsonify({
                "error": f"Field '{col}' must be a number",
                "received": data[col],
                "received_type": type(data[col]).__name__
            }), 422

    # --- 5. Encode & predict ---
    try:
        for col in encoders:
            data[col] = encoders[col].transform([data[col]])[0]

        input_data = [data[col] for col in features]
        final_input = np.array(input_data).reshape(1, -1)

        prediction = model.predict(final_input)

        return jsonify({
            "prediction": float(prediction[0])
        })

    except Exception as e:
        app.logger.error(f"Prediction failed: {e}")
        return jsonify({
            "error": "Prediction failed due to an internal error"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
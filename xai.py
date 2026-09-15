"""
Explainable AI (SHAP) service for the two independently-trained XGBoost
models (Holistic, Grade-Based).

This module does not touch model training, hyperparameters, or the
research pipeline in any way. It only explains predictions that the
already-trained models produce, using the exact same encoded feature
vector the model itself receives at prediction time.

Each model gets its own ModelExplainer, built once (at app startup, when
the model artifact is loaded) from that model alone — so a Holistic
explanation can structurally never reference G1/G2, and a Grade-Based
explanation can never be confused with the Holistic model's behavior.
"""

import numpy as np
import shap


class ModelExplainer:
    """Wraps one trained XGBoost model's SHAP TreeExplainer.

    Built once per model (at load time) and reused for every prediction
    request — shap.TreeExplainer(model) inspects the booster's trees to
    build its explainer state, which is the expensive, model-only part;
    it does not depend on any particular input, so there is no reason to
    rebuild it per request.
    """

    def __init__(self, model, features):
        self.features = features
        self._explainer = shap.TreeExplainer(model)

    def explain(self, encoded_row):
        """
        encoded_row: 2D numpy array, shape (1, n_features), in the exact
        column order `self.features` — i.e. the same array the model's
        own `.predict()` call receives. Returns (shap_values, base_value)
        for that single row, as a 1D numpy array and a plain float.
        """
        raw_shap_values = self._explainer.shap_values(encoded_row)
        raw_base_value = self._explainer.expected_value

        # Normalize shape/type across SHAP versions and explainer configs:
        # for a single-output regressor these are usually already a plain
        # (1, n_features) array and a scalar, but guard defensively rather
        # than assume.
        shap_row = np.asarray(raw_shap_values).reshape(-1, len(self.features))[0]

        if isinstance(raw_base_value, (list, np.ndarray)):
            base_value = float(np.asarray(raw_base_value).reshape(-1)[0])
        else:
            base_value = float(raw_base_value)

        return shap_row, base_value


def build_explanation(features, shap_row, base_value, raw_input_values):
    """
    Maps a model's real SHAP contributions back to feature names and the
    student's actual submitted (human-facing, pre-encoding) value for
    each one. `features` and `shap_row` must be the same length and in
    the same order (the model's training feature order).

    Returns:
        {
          "base_value": float,
          "features": [
            {"feature": str, "value": <raw submitted value>,
             "impact": float, "direction": "positive" | "negative"},
            ...
          ]  # sorted by absolute SHAP magnitude, largest first
        }
    """
    entries = []
    for feature, impact in zip(features, shap_row):
        impact = float(impact)
        entries.append({
            "feature": feature,
            "value": raw_input_values.get(feature),
            "impact": impact,
            "direction": "positive" if impact >= 0 else "negative",
        })

    entries.sort(key=lambda entry: abs(entry["impact"]), reverse=True)

    return {
        "base_value": base_value,
        "features": entries,
    }

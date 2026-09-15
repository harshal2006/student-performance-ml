import { MODES } from "../config/modes";

// `result` is the raw JSON body returned by /predict/holistic or
// /predict/grade: { model: "holistic" | "grade", prediction: number }.
// The displayed value always comes straight from that response.
export default function PredictionResult({ result }) {
  if (!result) return null;

  const mode = MODES[result.model];
  const predictionValue =
    typeof result.prediction === "number" ? result.prediction : null;

  return (
    <div className="result-card">
      <span className="result-card__eyebrow">Predicted Final Performance</span>
      <span className="result-card__value">
        {predictionValue !== null ? predictionValue.toFixed(2) : "—"}
        <span className="result-card__scale"> / 20</span>
      </span>
      <span className="result-card__stage">{mode ? mode.label : result.model}</span>
      <span className="result-card__model">{mode ? mode.modelName : "Unknown model"}</span>
    </div>
  );
}

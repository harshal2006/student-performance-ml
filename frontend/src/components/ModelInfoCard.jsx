import { MODES } from "../config/modes";

// Anchored to result.model (what the backend actually used), not just the
// UI's currently-selected mode — so the card always reflects the model
// that produced the prediction on screen.
export default function ModelInfoCard({ result }) {
  if (!result) return null;
  const mode = MODES[result.model];
  if (!mode) return null;

  return (
    <dl className="model-info-card">
      <div className="model-info-card__row">
        <dt>Prediction Stage</dt>
        <dd>{mode.label}</dd>
      </div>
      <div className="model-info-card__row">
        <dt>Model</dt>
        <dd>{mode.modelName}</dd>
      </div>
      <div className="model-info-card__row">
        <dt>Interim Grades</dt>
        <dd>{mode.key === "grade" ? "G1 + G2 included" : "Not used"}</dd>
      </div>
    </dl>
  );
}

import { labelFor } from "../config/fieldMeta";
import { categoryLabelFor } from "../config/categoryLabels";
import StatusBanner from "./StatusBanner";

const MAX_BARS = 10;

function displayValue(field, value, schema) {
  const isCategorical = schema && Object.prototype.hasOwnProperty.call(schema.categorical_features, field);
  if (isCategorical) return categoryLabelFor(field, value);
  return String(value);
}

function ContributionBar({ entry, maxAbsImpact }) {
  const pct = maxAbsImpact > 0 ? (Math.abs(entry.impact) / maxAbsImpact) * 100 : 0;
  const sign = entry.impact >= 0 ? "+" : "";
  return (
    <div className="shap-bar-row">
      <span className="shap-bar-row__label" title={entry.feature}>
        {labelFor(entry.feature)}
      </span>
      <span className="shap-bar-row__track">
        <span
          className={`shap-bar-row__fill shap-bar-row__fill--${entry.direction}`}
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className={`shap-bar-row__value shap-bar-row__value--${entry.direction}`}>
        {sign}
        {entry.impact.toFixed(2)}
      </span>
    </div>
  );
}

// This is a REAL SHAP-based local explanation for the specific prediction
// just returned by Flask — nothing here is computed, guessed, or
// hardcoded in the frontend. If the backend could not produce one, that
// is shown honestly instead of a fabricated result.
export default function ExplanationPanel({ result, schema }) {
  if (!result) {
    return (
      <section className="info-section info-section--placeholder">
        <h2>Explainable AI</h2>
        <p>Predict a result to see why the model reached that prediction.</p>
      </section>
    );
  }

  if (!result.explanation) {
    return (
      <section className="info-section">
        <h2>Why this prediction?</h2>
        <StatusBanner tone="info">
          Prediction available, but an explanation could not be generated.
          {result.explanation_error ? ` (${result.explanation_error})` : ""}
        </StatusBanner>
      </section>
    );
  }

  const { base_value, features } = result.explanation;
  const maxAbsImpact = Math.max(...features.map((f) => Math.abs(f.impact)), 0);
  const topThree = features.slice(0, 3);

  return (
    <section className="info-section explanation-panel">
      <h2>Why this prediction?</h2>
      <p className="explanation-panel__scope">Local explanation for this student's input.</p>

      <p className="explanation-panel__summary">
        The prediction was influenced most strongly by:
      </p>
      <ol className="explanation-panel__ranking">
        {topThree.map((entry) => (
          <li key={entry.feature}>{labelFor(entry.feature)}</li>
        ))}
      </ol>

      <div className="shap-chart">
        {features.slice(0, MAX_BARS).map((entry) => (
          <ContributionBar key={entry.feature} entry={entry} maxAbsImpact={maxAbsImpact} />
        ))}
      </div>

      <details className="explanation-panel__details">
        <summary>Full contribution breakdown ({features.length} features)</summary>
        <div className="explanation-table-wrap">
          <table className="explanation-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Student value</th>
                <th>Contribution</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              {features.map((entry) => (
                <tr key={entry.feature}>
                  <td>{labelFor(entry.feature)}</td>
                  <td>{displayValue(entry.feature, entry.value, schema)}</td>
                  <td className={`explanation-table__impact--${entry.direction}`}>
                    {entry.impact >= 0 ? "+" : ""}
                    {entry.impact.toFixed(3)}
                  </td>
                  <td>{entry.direction === "positive" ? "Positive" : "Negative"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="explanation-panel__base">Base value (typical prediction before this student's specifics): {base_value.toFixed(2)}</p>
      </details>

      <p className="explanation-panel__disclaimer">
        Each contribution shows how much that feature pushed this specific model's prediction up or
        down for this student — this reflects the model's association with the outcome, not a causal
        claim about what determines a student's grade.
      </p>
    </section>
  );
}

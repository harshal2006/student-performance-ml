import { MODES } from "../config/modes";

export default function ModeSelector({ activeMode, onSelect, disabled }) {
  return (
    <div className="mode-selector" role="tablist" aria-label="Prediction mode">
      {Object.values(MODES).map((mode) => (
        <button
          key={mode.key}
          type="button"
          role="tab"
          aria-selected={activeMode === mode.key}
          className={`mode-card ${activeMode === mode.key ? "mode-card--active" : ""}`}
          onClick={() => onSelect(mode.key)}
          disabled={disabled}
        >
          <span className="mode-card__label">{mode.label}</span>
          <span className="mode-card__description">{mode.description}</span>
          <span className="mode-card__badge">{mode.gradesNote}</span>
          <span className="mode-card__purpose">{mode.purpose}</span>
          <span className="mode-card__model">{mode.modelName}</span>
        </button>
      ))}
    </div>
  );
}

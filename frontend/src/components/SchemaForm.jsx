import { useMemo, useState } from "react";
import { groupFields, labelFor } from "../config/fieldMeta";
import { categoryLabelFor } from "../config/categoryLabels";
import { numericHintFor } from "../config/numericFieldHints";

function initialValues(schema) {
  const values = {};
  for (const field of schema.required_features) {
    values[field] = "";
  }
  return values;
}

function FieldControl({ field, schema, value, onChange, error }) {
  const isCategorical = Object.prototype.hasOwnProperty.call(schema.categorical_features, field);

  if (isCategorical) {
    const options = schema.categorical_features[field];
    return (
      <select
        id={`field-${field}`}
        value={value}
        onChange={(e) => onChange(field, e.target.value)}
        aria-invalid={Boolean(error)}
      >
        <option value="" disabled>
          Select…
        </option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {categoryLabelFor(field, opt)}
          </option>
        ))}
      </select>
    );
  }

  // Numeric field. The schema itself declares no min/max, so the backend
  // remains authoritative on what it accepts; `hint` below is UX guidance
  // sourced from the UCI dataset's published attribute documentation, not
  // enforced as a hard block beyond the browser's own number-input check.
  const hint = numericHintFor(field);
  return (
    <>
      <input
        id={`field-${field}`}
        type="number"
        inputMode="decimal"
        step="any"
        min={hint?.min}
        max={hint?.max}
        value={value}
        onChange={(e) => onChange(field, e.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={hint ? `hint-${field}` : undefined}
      />
      {hint && (
        <span id={`hint-${field}`} className="field-hint">
          {hint.hint}
        </span>
      )}
    </>
  );
}

export default function SchemaForm({ schema, onSubmit, submitting }) {
  const [values, setValues] = useState(() => initialValues(schema));
  const [fieldErrors, setFieldErrors] = useState({});

  const groups = useMemo(() => groupFields(schema.required_features), [schema]);

  function handleChange(field, raw) {
    setValues((prev) => ({ ...prev, [field]: raw }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  }

  function validate() {
    const errors = {};
    for (const field of schema.required_features) {
      const raw = values[field];
      const isCategorical = Object.prototype.hasOwnProperty.call(schema.categorical_features, field);
      if (raw === "" || raw === undefined || raw === null) {
        errors[field] = "Required";
        continue;
      }
      if (!isCategorical && Number.isNaN(Number(raw))) {
        errors[field] = "Must be a number";
      }
    }
    return errors;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    const payload = {};
    for (const field of schema.required_features) {
      const isCategorical = Object.prototype.hasOwnProperty.call(schema.categorical_features, field);
      payload[field] = isCategorical ? values[field] : Number(values[field]);
    }
    onSubmit(payload);
  }

  return (
    <form className="schema-form" onSubmit={handleSubmit} noValidate>
      <h2>Student Information</h2>

      {groups.map((group) => (
        <fieldset className="field-group" key={group.title}>
          <legend>{group.title}</legend>
          <div className="field-grid">
            {group.fields.map((field) => (
              <div className="field" key={field}>
                <label htmlFor={`field-${field}`}>{labelFor(field)}</label>
                <FieldControl
                  field={field}
                  schema={schema}
                  value={values[field]}
                  onChange={handleChange}
                  error={fieldErrors[field]}
                />
                {fieldErrors[field] && <span className="field-error">{fieldErrors[field]}</span>}
              </div>
            ))}
          </div>
        </fieldset>
      ))}

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={submitting}>
          {submitting ? "Generating prediction…" : "Predict"}
        </button>
      </div>
    </form>
  );
}

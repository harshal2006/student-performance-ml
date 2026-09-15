// Presentation-only guidance for numeric fields, sourced from the UCI
// "Student Performance" dataset's published attribute documentation (the
// same dataset this project trains on) — NOT invented, and NOT declared
// by the backend schema (which only lists field names, no ranges).
//
// `min`/`max` are applied as HTML attributes for a helpful number-input
// UX; the backend remains the authority on what it actually accepts, and
// its own validation errors still surface as-is if a value is rejected.
// A field with no entry here just renders as a plain number input.

export const NUMERIC_FIELD_HINTS = {
  age: { hint: "Typical range: 15–22", min: 15, max: 22 },
  Medu: {
    hint: "0 = none, 1 = primary (4th grade), 2 = 5th–9th grade, 3 = secondary, 4 = higher education",
    min: 0,
    max: 4,
  },
  Fedu: {
    hint: "0 = none, 1 = primary (4th grade), 2 = 5th–9th grade, 3 = secondary, 4 = higher education",
    min: 0,
    max: 4,
  },
  traveltime: {
    hint: "1 = <15 min, 2 = 15–30 min, 3 = 30 min–1 hour, 4 = >1 hour",
    min: 1,
    max: 4,
  },
  studytime: {
    hint: "1 = <2 hours, 2 = 2–5 hours, 3 = 5–10 hours, 4 = >10 hours",
    min: 1,
    max: 4,
  },
  failures: { hint: "Number of past class failures, 0–4", min: 0, max: 4 },
  famrel: { hint: "Scale: 1 (very bad) – 5 (excellent)", min: 1, max: 5 },
  freetime: { hint: "Scale: 1 (very low) – 5 (very high)", min: 1, max: 5 },
  goout: { hint: "Scale: 1 (very low) – 5 (very high)", min: 1, max: 5 },
  Dalc: { hint: "Workday alcohol use, 1 (very low) – 5 (very high)", min: 1, max: 5 },
  Walc: { hint: "Weekend alcohol use, 1 (very low) – 5 (very high)", min: 1, max: 5 },
  health: { hint: "Scale: 1 (very bad) – 5 (very good)", min: 1, max: 5 },
  absences: { hint: "Typical range: 0–93", min: 0, max: 93 },
  G1: { hint: "Grade scale: 0–20", min: 0, max: 20 },
  G2: { hint: "Grade scale: 0–20", min: 0, max: 20 },
};

export function numericHintFor(field) {
  return NUMERIC_FIELD_HINTS[field] || null;
}

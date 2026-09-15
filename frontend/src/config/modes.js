// Static UI copy for the two prediction modes. Does not encode any model
// behavior — the actual feature set for each mode always comes from its
// live schema endpoint, and the "model" field on every prediction response
// is what the UI trusts to label which model actually answered.

export const MODES = {
  holistic: {
    key: "holistic",
    label: "Early Warning",
    description: "Predict student performance using information available before interim grades.",
    gradesNote: "G1/G2 not used",
    purpose: "Early-stage academic performance prediction.",
    modelName: "XGBoost — Holistic",
    schemaEndpoint: "/schema/holistic",
    predictEndpoint: "/predict/holistic",
  },
  grade: {
    key: "grade",
    label: "Grade Forecast",
    description: "Forecast final performance using interim grades and student information.",
    gradesNote: "G1 + G2 included",
    purpose: "Mid-semester performance forecasting.",
    modelName: "XGBoost — Grade-Based",
    schemaEndpoint: "/schema/grade",
    predictEndpoint: "/predict/grade",
  },
};

export const DEFAULT_MODE = "holistic";

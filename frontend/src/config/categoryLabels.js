// Presentation-only display text for categorical option VALUES (the short
// codes the UCI dataset/backend actually use, e.g. "U", "GT3", "T"). The
// <select> still submits the exact raw value the schema returned — this
// only changes what the user reads in the dropdown.
//
// If a schema ever returns a value not listed here, categoryLabelFor()
// falls back to the raw value itself, so nothing is ever hidden or broken
// by an unrecognized option.

export const CATEGORY_LABELS = {
  school: {
    GP: "Gabriel Pereira (GP)",
    MS: "Mousinho da Silveira (MS)",
  },
  sex: {
    F: "Female",
    M: "Male",
  },
  address: {
    U: "Urban",
    R: "Rural",
  },
  famsize: {
    LE3: "3 or fewer (≤ 3)",
    GT3: "More than 3 (> 3)",
  },
  Pstatus: {
    T: "Living together",
    A: "Living apart",
  },
  Mjob: {
    teacher: "Teacher",
    health: "Health care related",
    services: "Civil services (e.g. administrative, police)",
    at_home: "Stay at home",
    other: "Other",
  },
  Fjob: {
    teacher: "Teacher",
    health: "Health care related",
    services: "Civil services (e.g. administrative, police)",
    at_home: "Stay at home",
    other: "Other",
  },
  reason: {
    home: "Close to home",
    reputation: "School reputation",
    course: "Course preference",
    other: "Other",
  },
  guardian: {
    mother: "Mother",
    father: "Father",
    other: "Other",
  },
  schoolsup: { yes: "Yes", no: "No" },
  famsup: { yes: "Yes", no: "No" },
  paid: { yes: "Yes", no: "No" },
  activities: { yes: "Yes", no: "No" },
  nursery: { yes: "Yes", no: "No" },
  higher: { yes: "Yes", no: "No" },
  internet: { yes: "Yes", no: "No" },
  romantic: { yes: "Yes", no: "No" },
};

export function categoryLabelFor(field, rawValue) {
  return CATEGORY_LABELS[field]?.[rawValue] ?? rawValue;
}

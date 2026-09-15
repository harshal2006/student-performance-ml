// Presentation-only metadata: human-readable labels and UI grouping for
// the UCI Student Performance attribute names. This does NOT define which
// fields exist, what values are valid, or what's required — that all
// comes from the live /schema/holistic and /schema/grade responses.
//
// If the backend schema ever returns a field name not listed here, it is
// still rendered (via FALLBACK_GROUP) with its raw field name as the
// label — nothing is dropped, and nothing is invented.

export const FIELD_LABELS = {
  school: "School",
  sex: "Sex",
  age: "Age",
  address: "Home Address Type",
  famsize: "Family Size",
  Pstatus: "Parents' Cohabitation Status",
  Medu: "Mother's Education",
  Fedu: "Father's Education",
  Mjob: "Mother's Job",
  Fjob: "Father's Job",
  guardian: "Student's Guardian",
  famsup: "Family Educational Support",
  reason: "Reason for Choosing School",
  traveltime: "Home-to-School Travel Time",
  studytime: "Weekly Study Time",
  failures: "Past Class Failures",
  schoolsup: "Extra School Educational Support",
  paid: "Extra Paid Classes",
  higher: "Wants Higher Education",
  absences: "Number of School Absences",
  activities: "Extracurricular Activities",
  nursery: "Attended Nursery School",
  internet: "Internet Access at Home",
  romantic: "In a Romantic Relationship",
  famrel: "Family Relationship Quality",
  freetime: "Free Time After School",
  goout: "Going Out With Friends",
  Dalc: "Workday Alcohol Consumption",
  Walc: "Weekend Alcohol Consumption",
  health: "Current Health Status",
  G1: "First Period Grade (G1)",
  G2: "Second Period Grade (G2)",
};

export function labelFor(fieldName) {
  return FIELD_LABELS[fieldName] || fieldName;
}

// Ordered groups. Each group only ever shows fields that (a) are listed
// here AND (b) are actually present in the schema response for the
// currently selected model — a group with none of its fields present is
// skipped entirely.
export const FIELD_GROUPS = [
  { title: "Demographics", fields: ["school", "sex", "age", "address", "famsize", "Pstatus"] },
  { title: "Family Background", fields: ["Medu", "Fedu", "Mjob", "Fjob", "guardian", "famsup"] },
  {
    title: "Academic",
    fields: ["reason", "traveltime", "studytime", "failures", "schoolsup", "paid", "higher", "absences"],
  },
  {
    title: "Lifestyle / Behaviour",
    fields: ["activities", "nursery", "internet", "romantic", "famrel", "freetime", "goout", "Dalc", "Walc", "health"],
  },
  { title: "Interim Grades", fields: ["G1", "G2"] },
];

export const FALLBACK_GROUP_TITLE = "Other";

// Buckets the schema's required_features into the groups above, in group
// order, preserving each group's field order; anything not covered by a
// known group falls into a trailing "Other" bucket in schema order.
export function groupFields(requiredFeatures) {
  const remaining = new Set(requiredFeatures);
  const groups = [];

  for (const group of FIELD_GROUPS) {
    const present = group.fields.filter((f) => remaining.has(f));
    if (present.length > 0) {
      groups.push({ title: group.title, fields: present });
      present.forEach((f) => remaining.delete(f));
    }
  }

  if (remaining.size > 0) {
    groups.push({
      title: FALLBACK_GROUP_TITLE,
      fields: requiredFeatures.filter((f) => remaining.has(f)),
    });
  }

  return groups;
}

// Single point of contact with the Flask backend. Every network call in
// the app goes through this module — components never call fetch directly.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

class ApiError extends Error {
  constructor(message, { status, body, isNetworkError = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.isNetworkError = isNetworkError;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (networkError) {
    throw new ApiError(
      "Unable to connect to the prediction server. Make sure Flask is running.",
      { isNetworkError: true }
    );
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // Response wasn't valid JSON — body stays null, handled below.
  }

  if (!response.ok) {
    const message =
      (body && typeof body.error === "string" && body.error) ||
      `Request failed with status ${response.status}`;
    throw new ApiError(message, { status: response.status, body });
  }

  if (body === null) {
    throw new ApiError("Received an unexpected (non-JSON) response from the server.", {
      status: response.status,
    });
  }

  return body;
}

function postJson(path, data) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getHealth() {
  return request("/health");
}

export function getHolisticSchema() {
  return request("/schema/holistic");
}

export function getGradeSchema() {
  return request("/schema/grade");
}

export function predictHolistic(data) {
  return postJson("/predict/holistic", data);
}

export function predictGrade(data) {
  return postJson("/predict/grade", data);
}

export { ApiError, API_BASE_URL };

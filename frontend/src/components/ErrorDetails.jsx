// Renders whatever useful detail Flask sent back with a validation error
// (missing_fields, allowed_values, received value, etc.) alongside the
// message. Falls back gracefully if the error body is missing or shaped
// unexpectedly — the page must never crash on a malformed response.
export default function ErrorDetails({ error }) {
  if (!error) return null;

  const body = error.body && typeof error.body === "object" ? error.body : null;

  return (
    <StatusBannerWrapper>
      <strong>{error.message}</strong>
      {body?.missing_fields && Array.isArray(body.missing_fields) && (
        <div className="error-detail">
          Missing: {body.missing_fields.join(", ")}
        </div>
      )}
      {body?.allowed_values && Array.isArray(body.allowed_values) && (
        <div className="error-detail">
          Allowed values: {body.allowed_values.join(", ")}
          {body.received !== undefined && <> (received "{String(body.received)}")</>}
        </div>
      )}
      {body?.received_type && (
        <div className="error-detail">
          Received type: {body.received_type}
        </div>
      )}
    </StatusBannerWrapper>
  );
}

function StatusBannerWrapper({ children }) {
  return <div className="status-banner status-banner--error">{children}</div>;
}

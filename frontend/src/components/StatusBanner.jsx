// Generic status line for loading/error/unavailable states. Kept as one
// component so every "something isn't ready" message looks the same.
export default function StatusBanner({ tone = "info", children }) {
  return <div className={`status-banner status-banner--${tone}`}>{children}</div>;
}

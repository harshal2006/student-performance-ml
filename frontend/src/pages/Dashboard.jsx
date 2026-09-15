import { useEffect, useState } from "react";
import Header from "../components/Header";
import ModeSelector from "../components/ModeSelector";
import SchemaForm from "../components/SchemaForm";
import PredictionResult from "../components/PredictionResult";
import ModelInfoCard from "../components/ModelInfoCard";
import ResearchContext from "../components/ResearchContext";
import FutureWork from "../components/FutureWork";
import ExplanationPanel from "../components/ExplanationPanel";
import StatusBanner from "../components/StatusBanner";
import ErrorDetails from "../components/ErrorDetails";
import { MODES, DEFAULT_MODE } from "../config/modes";
import {
  getHealth,
  getHolisticSchema,
  getGradeSchema,
  predictHolistic,
  predictGrade,
} from "../services/api";

const SCHEMA_LOADERS = {
  holistic: getHolisticSchema,
  grade: getGradeSchema,
};

const PREDICTORS = {
  holistic: predictHolistic,
  grade: predictGrade,
};

export default function Dashboard() {
  const [backendUnavailable, setBackendUnavailable] = useState(false);
  const [checkingBackend, setCheckingBackend] = useState(true);

  const [mode, setMode] = useState(DEFAULT_MODE);
  const [schema, setSchema] = useState(null);
  const [schemaLoading, setSchemaLoading] = useState(true);
  const [schemaError, setSchemaError] = useState(null);

  const [resetCount, setResetCount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [predictError, setPredictError] = useState(null);
  const [result, setResult] = useState(null);

  // One-time backend reachability check via /health.
  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then(() => {
        if (!cancelled) setBackendUnavailable(false);
      })
      .catch((err) => {
        if (!cancelled) setBackendUnavailable(Boolean(err.isNetworkError));
      })
      .finally(() => {
        if (!cancelled) setCheckingBackend(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Load the schema for whichever mode is active. This is the sole source
  // of truth for what fields the form renders — nothing is hardcoded.
  useEffect(() => {
    let cancelled = false;
    setSchema(null);
    setSchemaLoading(true);
    setSchemaError(null);

    SCHEMA_LOADERS[mode]()
      .then((data) => {
        if (!cancelled) setSchema(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setSchemaError(err);
          if (err.isNetworkError) setBackendUnavailable(true);
        }
      })
      .finally(() => {
        if (!cancelled) setSchemaLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [mode]);

  function handleModeSelect(nextMode) {
    if (nextMode === mode) return;
    setMode(nextMode);
    setResult(null);
    setPredictError(null);
  }

  function handleReset() {
    setResetCount((c) => c + 1);
    setResult(null);
    setPredictError(null);
  }

  async function handleSubmit(payload) {
    setSubmitting(true);
    setPredictError(null);
    setResult(null);
    try {
      const data = await PREDICTORS[mode](payload);
      if (typeof data?.prediction !== "number" || !data?.model) {
        throw new Error("Received an unexpected response from the server.");
      }
      setResult(data);
    } catch (err) {
      setPredictError(err);
      if (err.isNetworkError) setBackendUnavailable(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-shell">
      <Header />

      <ModeSelector activeMode={mode} onSelect={handleModeSelect} disabled={submitting} />

      {checkingBackend && <StatusBanner tone="info">Checking connection to the prediction server…</StatusBanner>}

      {backendUnavailable && (
        <StatusBanner tone="error">
          Unable to connect to the prediction server. Make sure Flask is running.
        </StatusBanner>
      )}

      <main className="workspace">
        <section className="workspace__form">
          {schemaLoading && <StatusBanner tone="info">Loading model schema…</StatusBanner>}

          {!schemaLoading && schemaError && (
            <StatusBanner tone="error">
              Could not load the {MODES[mode].label} schema: {schemaError.message}
            </StatusBanner>
          )}

          {!schemaLoading && schema && (
            <>
              <SchemaForm key={`${mode}-${resetCount}`} schema={schema} onSubmit={handleSubmit} submitting={submitting} />
              <div className="form-actions form-actions--secondary">
                <button type="button" className="btn btn--ghost" onClick={handleReset} disabled={submitting}>
                  Reset
                </button>
              </div>
            </>
          )}
        </section>

        <section className="workspace__result">
          {submitting && <StatusBanner tone="info">Generating prediction…</StatusBanner>}
          {!submitting && predictError && <ErrorDetails error={predictError} />}
          {!submitting && !predictError && result && (
            <>
              <PredictionResult result={result} />
              <ModelInfoCard result={result} />
            </>
          )}
          {!submitting && !predictError && !result && (
            <StatusBanner tone="info">Fill in the form and press Predict to see a result.</StatusBanner>
          )}
        </section>
      </main>

      <ResearchContext />
      <ExplanationPanel result={result} schema={schema} />
      <FutureWork />
    </div>
  );
}

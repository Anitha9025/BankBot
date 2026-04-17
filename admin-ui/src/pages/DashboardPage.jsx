import React, { useEffect, useState, useRef } from "react";
import api from "../services/api";
import "./PageStyles.css";
import "./DashboardPage.css";

function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card" style={{ "--card-color": color }}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-body">
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value ?? "—"}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats]           = useState(null);
  const [retraining, setRetraining] = useState(false);
  const [retainMsg, setRetainMsg]   = useState("");
  const [retainLog, setRetainLog]   = useState("");
  const [retainDone, setRetainDone] = useState(false);
  const [retainError, setRetainError] = useState("");
  const [error, setError]           = useState("");
  const logRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    api.get("/api/dashboard")
      .then((r) => setStats(r.data))
      .catch(() => setError("Could not load dashboard stats."));
  }, []);

  // Auto-scroll log box to bottom
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [retainLog]);

  const startPolling = () => {
    pollRef.current = setInterval(async () => {
      try {
        const r = await api.get("/api/retrain/status");
        const { running, log, error: trainErr } = r.data;
        if (log) setRetainLog(log);
        if (!running) {
          clearInterval(pollRef.current);
          setRetraining(false);
          setRetainDone(true);
          if (trainErr) {
            setRetainError(trainErr);
          } else {
            setRetainMsg(" Retraining complete! Restart your Rasa server to load the new model.");
            // Refresh stats
            api.get("/api/dashboard").then((r) => setStats(r.data));
          }
        }
      } catch { clearInterval(pollRef.current); }
    }, 2000);
  };

  const handleRetrain = async () => {
    setRetraining(true);
    setRetainMsg("");
    setRetainLog("");
    setRetainDone(false);
    setRetainError("");
    try {
      const r = await api.post("/api/retrain");
      setRetainMsg(r.data.message);
      startPolling();
    } catch (e) {
      setRetainMsg(e.response?.data?.message || "Retrain request failed.");
      setRetraining(false);
    }
  };

  useEffect(() => () => clearInterval(pollRef.current), []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">BankBot system overview</p>
        </div>
        <button className="btn-primary" onClick={handleRetrain} disabled={retraining}>
          {retraining ? " Training…" : "🔁 Retrain Model"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* ── Retrain Status Panel ───────────────────────── */}
      {(retraining || retainDone) && (
        <div className="retrain-panel">
          <div className="retrain-header">
            <span className="retrain-title">
              {retraining
                ? <><span className="pulse-dot" /> Training in progress…</>
                : retainError ? " Training Failed" : " Training Complete"}
            </span>
            {retainDone && (
              <button className="retrain-close" onClick={() => { setRetainDone(false); setRetainLog(""); }}>✕</button>
            )}
          </div>

          {retainMsg && (
            <div className={retainError ? "retrain-error-msg" : "retrain-success-msg"}>
              {retainError || retainMsg}
            </div>
          )}

          {retainLog && (
            <>
              <p className="retrain-log-label"> Training Log:</p>
              <pre className="retrain-log" ref={logRef}>{retainLog}</pre>
            </>
          )}

          {retraining && !retainLog && (
            <div className="retrain-waiting">
              <span className="spinner" /> Writing YAML files from database and starting <code>rasa train</code>… this takes 2–5 minutes.
            </div>
          )}

          {retainDone && !retainError && (
            <div className="retrain-next-steps">
              <strong>Next step:</strong> Restart the Rasa server to load the new model:
              <code className="retrain-cmd">rasa run --enable-api --cors "*"</code>
            </div>
          )}
        </div>
      )}

      {/* ── Stats Grid ──────────────────────────────────── */}
      <div className="stats-grid">
        <StatCard label="Total Queries"     value={stats?.total_queries}                           icon="" color="#6366f1" />
        <StatCard label="Success Rate"      value={stats ? `${stats.success_rate}%` : null}        icon="" color="#22c55e" />
        <StatCard label="Unique Intents"    value={stats?.intent_count}                            icon="" color="#f59e0b" />
        <StatCard label="Avg Confidence"    value={stats?.avg_confidence}                          icon="" color="#06b6d4" />
        <StatCard label="Total FAQs"        value={stats?.total_faqs}                              icon="" color="#ec4899" />
        <StatCard label="Training Examples" value={stats?.total_training}                          icon="" color="#8b5cf6" />
      </div>
    </div>
  );
}

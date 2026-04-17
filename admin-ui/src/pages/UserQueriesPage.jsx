import React, { useEffect, useState } from "react";
import api from "../services/api";
import "./PageStyles.css";

export default function UserQueriesPage() {
  const [logs,  setLogs]  = useState([]);
  const [total, setTotal] = useState(0);
  const [page,  setPage]  = useState(1);
  const [error, setError] = useState("");

  const PER_PAGE = 20;

  const fetchLogs = (p) => {
    api.get(`/api/logs?page=${p}&per_page=${PER_PAGE}`)
      .then((r) => { setLogs(r.data.logs); setTotal(r.data.total); })
      .catch(() => setError("Failed to load logs."));
  };

  useEffect(() => { fetchLogs(page); }, [page]);

  const handleExport = async () => {
    try {
      const token = localStorage.getItem("admin_token");
      const url   = `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/logs/export`;
      const res   = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob  = await res.blob();
      const link  = document.createElement("a");
      link.href   = URL.createObjectURL(blob);
      link.download = "user_logs.csv";
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (e) {
      setError("CSV export failed. Please try again.");
    }
  };


  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">User Queries</h1>
          <p className="page-subtitle">{total} total logs recorded</p>
        </div>
        <button className="btn-secondary" onClick={handleExport}> Export CSV</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Message</th>
              <th>Intent</th>
              <th>Confidence</th>
              <th>Bot Response</th>
              <th>Timestamp</th>
            </tr>
          </thead>

          <tbody>
            {logs.length === 0 && (
              <tr><td colSpan={6} className="empty-cell">No logs yet. Start chatting with BankBot!</td></tr>
            )}
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="id-cell">{log.id}</td>
                <td className="message-cell">{log.message}</td>
                <td><span className="intent-badge">{log.intent || "—"}</span></td>
                <td>
                  <span className={`conf-badge ${log.confidence > 0.7 ? "conf-high" : "conf-low"}`}>
                    {log.confidence ? `${(log.confidence * 100).toFixed(1)}%` : "—"}
                  </span>
                </td>
                <td className="response-cell" title={log.response}>
                  {log.response ? log.response.slice(0, 80) + (log.response.length > 80 ? "…" : "") : "—"}
                </td>
                <td className="time-cell">{log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}</td>
              </tr>
            ))}

          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Prev</button>
        <span>Page {page} of {totalPages || 1}</span>
        <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next →</button>
      </div>
    </div>
  );
}

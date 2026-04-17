import React, { useEffect, useState } from "react";
import api from "../services/api";
import "./PageStyles.css";

const EMPTY = { intent: "", example_text: "" };

export default function TrainingDataPage() {
  const [data,    setData]    = useState([]);
  const [modal,   setModal]   = useState(null);
  const [current, setCurrent] = useState(EMPTY);
  const [error,   setError]   = useState("");
  const [saving,  setSaving]  = useState(false);
  const [filter,  setFilter]  = useState("");

  const load = () => api.get("/api/training").then((r) => setData(r.data.training_data)).catch(() => setError("Failed to load training data."));
  useEffect(() => { load(); }, []);

  const openAdd  = () => { setCurrent(EMPTY); setModal("add"); };
  const openEdit = (row) => { setCurrent({ ...row }); setModal("edit"); };
  const close    = () => { setModal(null); setError(""); };

  const save = async () => {
    if (!current.intent.trim() || !current.example_text.trim()) { setError("Both fields required."); return; }
    setSaving(true);
    try {
      if (modal === "add") await api.post("/api/training", current);
      else                  await api.put(`/api/training/${current.id}`, current);
      close(); load();
    } catch { setError("Save failed."); }
    finally  { setSaving(false); }
  };

  const deleteRow = async (id) => {
    if (!confirm("Delete this training example?")) return;
    await api.delete(`/api/training/${id}`);
    load();
  };

  const filtered = filter
    ? data.filter((r) => r.intent.toLowerCase().includes(filter.toLowerCase()))
    : data;

  // Group by intent
  const grouped = filtered.reduce((acc, row) => {
    (acc[row.intent] = acc[row.intent] || []).push(row);
    return acc;
  }, {});

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Training Data</h1>
          <p className="page-subtitle">{data.length} examples across {Object.keys(grouped).length} intents</p>
        </div>
        <button className="btn-primary" onClick={openAdd}>+ Add Example</button>
      </div>

      <input
        className="search-input"
        placeholder="Filter by intent…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      {Object.entries(grouped).map(([intent, rows]) => (
        <div key={intent} className="intent-group">
          <h3 className="intent-label">{intent} <span className="intent-count">({rows.length})</span></h3>
          <div className="table-card">
            <table className="data-table">
              <thead><tr><th>#</th><th>Example Text</th><th>Actions</th></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td className="id-cell">{r.id}</td>
                    <td>{r.example_text}</td>
                    <td>
                      <div className="action-btns">
                        <button className="btn-edit"   onClick={() => openEdit(r)}>Edit</button>
                        <button className="btn-delete" onClick={() => deleteRow(r.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {filtered.length === 0 && <div className="empty-state">No training examples found.</div>}

      {modal && (
        <div className="modal-overlay" onClick={close}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{modal === "add" ? "Add Training Example" : "Edit Training Example"}</h2>
            {error && <div className="error-banner">{error}</div>}
            <div className="field-group">
              <label>Intent Name</label>
              <input value={current.intent} onChange={(e) => setCurrent({ ...current, intent: e.target.value })} placeholder="e.g. check_balance" />
            </div>
            <div className="field-group">
              <label>Example Text</label>
              <input value={current.example_text} onChange={(e) => setCurrent({ ...current, example_text: e.target.value })} placeholder="e.g. What is my balance?" />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={close} disabled={saving}>Cancel</button>
              <button className="btn-primary"   onClick={save}  disabled={saving}>{saving ? "Saving…" : "Save"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

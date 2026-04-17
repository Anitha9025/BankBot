import React, { useEffect, useState } from "react";
import api from "../services/api";
import "./PageStyles.css";

const EMPTY = { question: "", answer: "" };

export default function FAQsPage() {
  const [faqs,    setFaqs]    = useState([]);
  const [modal,   setModal]   = useState(null);   // null | "add" | "edit"
  const [current, setCurrent] = useState(EMPTY);
  const [error,   setError]   = useState("");
  const [saving,  setSaving]  = useState(false);

  const load = () => api.get("/api/faqs").then((r) => setFaqs(r.data.faqs)).catch(() => setError("Failed to load FAQs."));
  useEffect(() => { load(); }, []);

  const openAdd  = () => { setCurrent(EMPTY); setModal("add"); };
  const openEdit = (faq) => { setCurrent({ ...faq }); setModal("edit"); };
  const close    = () => { setModal(null); setError(""); };

  const save = async () => {
    if (!current.question.trim() || !current.answer.trim()) { setError("Both fields required."); return; }
    setSaving(true);
    try {
      if (modal === "add") await api.post("/api/faqs", current);
      else                  await api.put(`/api/faqs/${current.id}`, current);
      close(); load();
    } catch { setError("Save failed. Please try again."); }
    finally  { setSaving(false); }
  };

  const deleteFaq = async (id) => {
    if (!confirm("Delete this FAQ?")) return;
    await api.delete(`/api/faqs/${id}`);
    load();
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">FAQ Management</h1>
          <p className="page-subtitle">{faqs.length} FAQs in database</p>
        </div>
        <button className="btn-primary" onClick={openAdd}>+ Add FAQ</button>
      </div>

      <div className="table-card">
        <table className="data-table">
          <thead><tr><th>#</th><th>Question</th><th>Answer</th><th>Actions</th></tr></thead>
          <tbody>
            {faqs.length === 0 && <tr><td colSpan={4} className="empty-cell">No FAQs yet.</td></tr>}
            {faqs.map((f) => (
              <tr key={f.id}>
                <td className="id-cell">{f.id}</td>
                <td>{f.question}</td>
                <td className="answer-cell">{f.answer}</td>
                <td>
                  <div className="action-btns">
                    <button className="btn-edit" onClick={() => openEdit(f)}>Edit</button>
                    <button className="btn-delete" onClick={() => deleteFaq(f.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modal && (
        <div className="modal-overlay" onClick={close}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{modal === "add" ? "Add FAQ" : "Edit FAQ"}</h2>
            {error && <div className="error-banner">{error}</div>}
            <div className="field-group">
              <label>Question</label>
              <input value={current.question} onChange={(e) => setCurrent({ ...current, question: e.target.value })} placeholder="Enter question" />
            </div>
            <div className="field-group">
              <label>Answer</label>
              <textarea rows={4} value={current.answer} onChange={(e) => setCurrent({ ...current, answer: e.target.value })} placeholder="Enter answer" />
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

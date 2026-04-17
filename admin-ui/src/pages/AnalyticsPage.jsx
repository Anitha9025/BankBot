import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import api from "../services/api";
import "./PageStyles.css";

const COLORS = ["#6366f1","#22c55e","#f59e0b","#06b6d4","#ec4899","#8b5cf6","#ef4444","#14b8a6","#f97316","#84cc16"];

export default function AnalyticsPage() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/analytics")
      .then((r) => setData(r.data))
      .catch(() => setError("Failed to load analytics."));
  }, []);

  if (error) return <div className="page"><div className="error-banner">{error}</div></div>;
  if (!data)  return <div className="page"><p className="loading-text">Loading analytics…</p></div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">Intent usage and performance metrics</p>
        </div>
      </div>

      <div className="charts-grid">
        {/* Bar chart — intent frequency */}
        <div className="chart-card">
          <h3 className="chart-title">Top Intents by Frequency</h3>
          {data.intent_frequency.length === 0
            ? <p className="empty-state">No data yet.</p>
            : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.intent_frequency} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="intent" tick={{ fill: "#94a3b8", fontSize: 11 }} angle={-25} textAnchor="end" height={55} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #374151", color: "#e2e8f0" }} />
                  <Bar dataKey="count" fill="#6366f1" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>

        {/* Pie chart — intent distribution */}
        <div className="chart-card">
          <h3 className="chart-title">Intent Distribution</h3>
          {data.intent_frequency.length === 0
            ? <p className="empty-state">No data yet.</p>
            : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={data.intent_frequency} dataKey="count" nameKey="intent" cx="50%" cy="50%" outerRadius={90} label={({ intent }) => intent}>
                    {data.intent_frequency.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #374151", color: "#e2e8f0" }} />
                  <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            )
          }
        </div>

        {/* Bar chart — daily volume */}
        <div className="chart-card chart-card--full">
          <h3 className="chart-title">Daily Query Volume (Last 14 Days)</h3>
          {data.daily_volume.length === 0
            ? <p className="empty-state">No data for the past 14 days.</p>
            : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.daily_volume}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #374151", color: "#e2e8f0" }} />
                  <Bar dataKey="count" fill="#22c55e" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>
      </div>
    </div>
  );
}

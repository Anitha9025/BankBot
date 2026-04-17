import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Layout.css";

const NAV_ITEMS = [
  { path: "/",          label: "Dashboard",    icon: "" },
  { path: "/queries",   label: "User Queries", icon: "" },
  { path: "/faqs",      label: "FAQs",         icon: "" },
  { path: "/training",  label: "Training Data", icon: "" },
  { path: "/analytics", label: "Analytics",    icon: "" },
];

export default function Layout({ children }) {
  const { username, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="admin-layout">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon"></span>
          <span className="brand-text">BankBot Admin</span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="admin-user"> {username}</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────── */}
      <main className="main-content">{children}</main>
    </div>
  );
}

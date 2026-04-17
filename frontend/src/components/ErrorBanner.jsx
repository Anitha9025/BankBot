import React from "react";
import "./ErrorBanner.css";

/**
 * Dismissible error banner shown on network/server failures.
 * @param {Object} props
 * @param {string} props.message
 * @param {Function} props.onDismiss
 */
function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert">
      <span className="error-icon">⚠️</span>
      <span className="error-text">{message}</span>
      <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss error">
        ✕
      </button>
    </div>
  );
}

export default ErrorBanner;

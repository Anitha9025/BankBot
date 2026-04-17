import React from "react";
import "./TypingIndicator.css";

/**
 * Animated typing indicator (three bouncing dots) shown while waiting for bot.
 */
function TypingIndicator() {
  return (
    <div className="typing-wrapper" aria-label="Bot is typing">
      <div className="bot-avatar">🏦</div>
      <div className="typing-bubble">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
}

export default TypingIndicator;

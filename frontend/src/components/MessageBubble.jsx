import React from "react";
import "./MessageBubble.css";

/**
 * Renders a single chat message bubble.
 * @param {Object} props
 * @param {'user'|'bot'} props.sender
 * @param {string} props.text
 * @param {string} props.timestamp
 * @param {string} [props.image]
 */
function MessageBubble({ sender, text, timestamp, image }) {
  const isUser = sender === "user";

  return (
    <div className={`bubble-wrapper ${isUser ? "bubble-user" : "bubble-bot"}`}>
      {!isUser && (
        <div className="bot-avatar" aria-label="Bot">
          🏦
        </div>
      )}
      <div className={`bubble ${isUser ? "bubble--user" : "bubble--bot"}`}>
        {image && (
          <img
            src={image}
            alt="bot attachment"
            className="bubble-image"
            onError={(e) => (e.target.style.display = "none")}
          />
        )}
        {text && <p className="bubble-text">{text}</p>}
        <span className="bubble-time">{timestamp}</span>
      </div>
      {isUser && (
        <div className="user-avatar" aria-label="You">
          👤
        </div>
      )}
    </div>
  );
}

export default MessageBubble;

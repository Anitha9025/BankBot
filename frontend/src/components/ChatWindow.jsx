import React, { useState, useEffect, useRef, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import ChatInput from "./ChatInput";
import ErrorBanner from "./ErrorBanner";
import { sendMessage } from "../services/rasaApi";
import "./ChatWindow.css";

// Stable session ID for the lifetime of the page
const SESSION_ID = uuidv4();

function getTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function ChatWindow() {
  const [messages, setMessages] = useState([
    {
      id: uuidv4(),
      sender: "bot",
      text: "👋 Hello! I'm your BankBot assistant. How can I help you today?",
      timestamp: getTimestamp(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = useCallback(async () => {
    const text = inputValue.trim();
    if (!text) {
      setError("Please type a message before sending.");
      return;
    }

    // Clear previous error
    setError(null);

    // Append user message immediately
    const userMsg = { id: uuidv4(), sender: "user", text, timestamp: getTimestamp() };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    try {
      const botResponses = await sendMessage(SESSION_ID, text);

      if (botResponses.length === 0) {
        // Rasa returned empty array — show a fallback
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: "I'm not sure how to respond to that. Could you rephrase?",
            timestamp: getTimestamp(),
          },
        ]);
      } else {
        // Map each Rasa response object to a message bubble
        const botMsgs = botResponses.map((resp) => ({
          id: uuidv4(),
          sender: "bot",
          text: resp.text || null,
          image: resp.image || null,
          timestamp: getTimestamp(),
        }));
        setMessages((prev) => [...prev, ...botMsgs]);
      }
    } catch (err) {
      let friendlyMsg;
      if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        friendlyMsg = "⏱️ The server took too long to respond. Please try again.";
      } else if (err.response) {
        friendlyMsg = `🚫 Server error (${err.response.status}). Please try again later.`;
      } else if (err.message === "Network Error" || !navigator.onLine) {
        friendlyMsg = "📡 No network connection. Please check your internet and try again.";
      } else {
        friendlyMsg = `❌ ${err.message || "Something went wrong. Please try again."}`;
      }
      setError(friendlyMsg);
    } finally {
      setIsTyping(false);
    }
  }, [inputValue]);

  return (
    <div className="chat-container">
      {/* ── Header ────────────────────────────────────── */}
      <header className="chat-header">
        <div className="header-logo">🏦</div>
        <div className="header-info">
          <h1 className="header-title">BankBot</h1>
          <span className="header-status">
            <span className="status-dot" />
            Online
          </span>
        </div>
      </header>

      {/* ── Error Banner ──────────────────────────────── */}
      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {/* ── Messages ─────────────────────────────────── */}
      <main className="chat-messages" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            sender={msg.sender}
            text={msg.text}
            image={msg.image}
            timestamp={msg.timestamp}
          />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </main>

      {/* ── Input ─────────────────────────────────────── */}
      <footer className="chat-footer">
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          disabled={isTyping}
        />
        <p className="chat-disclaimer">
          Secured connection · BankBot may make mistakes. Verify important info.
        </p>
      </footer>
    </div>
  );
}

export default ChatWindow;

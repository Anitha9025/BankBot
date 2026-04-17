import axios from "axios";

const BASE_URL = import.meta.env.VITE_FLASK_URL || "http://localhost:8000";

const rasaClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // 10 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Send a user message to the Flask REST proxy.
 * @param {string} senderId - Unique session identifier for the user.
 * @param {string} message  - The text message typed by the user.
 * @returns {Promise<Array>} Array of bot response objects: [{ text, image, ... }]
 */
export async function sendMessage(senderId, message) {
  if (!message || !message.trim()) {
    throw new Error("Message cannot be empty.");
  }

  const payload = {
    sender: senderId,
    message: message.trim(),
  };

  const response = await rasaClient.post("/api/chat", payload);

  // Flask proxy returns the Rasa array; could be empty if no response
  if (!Array.isArray(response.data)) {
    throw new Error("Unexpected response format from server.");
  }

  return response.data;
}

export default rasaClient;

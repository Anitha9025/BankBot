# Module 3 – UI Integration & Chat Interface

## Overview
A responsive **React + Vite** chat frontend that connects to your Rasa REST API. It features a modern dark banking UI, real-time messaging, typing indicator, input validation, and graceful error handling.

---

## Project Structure

```
BankBot/
├── frontend/                ← Module 3 React app
│   ├── .env                 ← Rasa backend URL config
│   ├── index.html           ← HTML entry point
│   └── src/
│       ├── main.jsx         ← React DOM entry
│       ├── App.jsx          ← Root component
│       ├── index.css        ← Global design system (dark theme)
│       ├── services/
│       │   └── rasaApi.js   ← Axios API service
│       └── components/
│           ├── ChatWindow.jsx        ← Main orchestrator
│           ├── ChatWindow.css
│           ├── MessageBubble.jsx     ← User / Bot bubbles
│           ├── MessageBubble.css
│           ├── TypingIndicator.jsx   ← Animated dots
│           ├── TypingIndicator.css
│           ├── ChatInput.jsx         ← Textarea + Send button
│           ├── ChatInput.css
│           ├── ErrorBanner.jsx       ← Dismissible error
│           └── ErrorBanner.css
├── actions/
├── data/
├── domain.yml
├── config.yml
└── ... (Rasa backend files)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | ≥ 18 |
| npm | ≥ 9 |
| Python | 3.10 (for Rasa) |
| Rasa | 3.x |

---

## Running the Application

### Step 1 — Start the Rasa Backend

Open a terminal in `e:\BankBot`:

```bash
# Activate virtual environment
banking_env\Scripts\activate

# Start Rasa server with REST API enabled and CORS open for local dev
rasa run --enable-api --cors "*" --port 5005
```

> **Action Server** (if using custom actions):
> ```bash
> # In a second terminal
> banking_env\Scripts\activate
> rasa run actions --port 5055
> ```

### Step 2 — Configure the Frontend

Edit `e:\BankBot\frontend\.env` if your Rasa server runs on a different host/port:

```env
VITE_RASA_URL=http://localhost:5005
```

### Step 3 — Start the React Dev Server

```bash
cd e:\BankBot\frontend
npm run dev
```

Open your browser at **http://localhost:5173**

---

## API Integration

### Endpoint Used

```
POST /webhooks/rest/webhook
```

### Example Request

```json
{
  "sender": "user-abc123",
  "message": "What is my account balance?"
}
```

### Example Response

```json
[
  {
    "recipient_id": "user-abc123",
    "text": "Your current account balance is ₹25,450.00."
  }
]
```

### Rasa API Flow

```
User types message
      ↓
ChatInput validates (non-empty)
      ↓
rasaApi.js  →  POST /webhooks/rest/webhook
      ↓
Rasa NLU + Dialogue Manager processes intent
      ↓
Response array returned
      ↓
MessageBubble(s) rendered in ChatWindow
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty message | Validation error shown; no request sent |
| Network down | "📡 No network connection" banner |
| Server timeout (>10s) | "⏱️ Server took too long" banner |
| HTTP 4xx / 5xx | "🚫 Server error (code)" banner |
| Empty Rasa response | Fallback "I'm not sure…" bubble shown |

---

## Building for Production

```bash
cd e:\BankBot\frontend
npm run build
```

The optimized static files are output to `frontend/dist/`. Serve them with any static web server or configure Nginx/Apache.

> **HTTPS in Production**: Deploy behind a reverse proxy (Nginx/Caddy) with SSL certificates. Update `.env` to use `https://your-domain.com` for the Rasa URL.

---

## Security Notes

- **CORS**: The `--cors "*"` flag in development is intentionally permissive. In production, restrict CORS to your specific frontend domain.
- **HTTPS**: Always use HTTPS in production for both the frontend and Rasa backend.
- **Input Validation**: The frontend validates that messages are non-empty and ≤500 characters before sending.

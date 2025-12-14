# Friday - AI-Powered Google Workspace Assistant

**Python Mini-Project**  
An intelligent assistant that manages Google Workspace operations (Gmail, Drive, Calendar) using Google Gemini AI.

## 🌟 Features

- **📧 Email Management**: Send, read, delete, mark, and reply to emails
- **📁 Drive Operations**: Create, search, share, and manage files  
- **📅 Calendar Management**: Create, update, delete, and list events
- **🤖 AI-Powered**: Uses Google Gemini 1.5 Flash for natural language processing
- **💬 Conversational UI**: React-based web interface with real-time chat

## 🏗️ Architecture

```
Frontend (React + Vite + Tailwind)
        ↓
Backend (FastAPI Server)
        ↓
Friday Agent (Multi-Agent System)
    ├── EmailAgent
    ├── DriveAgent  
    └── CalendarAgent
        ↓
Google APIs (Gmail, Drive, Calendar) + Gemini REST API
```

## 🛠️ Tech Stack

**Backend:**
- Python 3.x
- FastAPI (Web Framework)
- Google APIs (Gmail, Drive, Calendar)
- Gemini AI (REST API for Python 3.14+ compatibility)

**Frontend:**
- React + Vite
- Tailwind CSS
- Axios (HTTP client)

## 📋 Prerequisites

1. **Python 3.8+** (tested with Python 3.14)
2. **Node.js 16+** (for frontend)
3. **Google Cloud Project** with Gmail, Drive, and Calendar APIs enabled
4. **Gemini API Key** from Google AI Studio

## ⚙️ Installation

### 1. Clone/Extract the Project

```bash
cd "Python skl projects"
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google API Credentials

See [SETUP.md](SETUP.md) for detailed instructions on:
- Creating a Google Cloud Project
- Enabling APIs
- Creating OAuth 2.0 credentials
- Getting a Gemini API key

### 4. Configure API Keys

Create `config.py`:
```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Place your `credentials.json` (from Google Cloud Console) in the project root.

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend Server

```bash
python server.py
```
Server will run on `http://localhost:8000`

### Start Frontend (in a new terminal)

```bash
cd frontend
npm run dev
```
Frontend will run on `http://localhost:5173`

### Access the Application

Open your browser to `http://localhost:5173`

On first run, you'll be prompted to authenticate with Google.

## 💡 Usage Examples

**Email:**
- "Send an email to john@example.com about tomorrow's meeting"
- "List my recent emails"
- "Mark the last email as read"

**Drive:**
- "Create a file called notes.txt with some content"
- "Search for files containing 'report'"
- "List my recent files"

**Calendar:**
- "Create a meeting event tomorrow at 3 PM"
- "Show my upcoming events"
- "List my calendar events"

**General Chat:**
- "Hello!"
- "How do I share a file?"

## 📁 Project Structure

```
Python skl projects/
├── Friday1.0.py          # Main agent logic (REST API)
├── server.py             # FastAPI backend server
├── config.py             # API keys configuration
├── credentials.json      # Google OAuth credentials
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── SETUP.md             # Setup instructions
└── frontend/
    ├── src/
    │   ├── App.jsx      # Main React component
    │   └── index.css    # Tailwind styles
    ├── package.json     # Node dependencies
    └── vite.config.js   # Vite configuration
```

## 🔧 Technical Details

### REST API vs gRPC

This project uses **REST API** for Gemini AI instead of the default gRPC:
- ✅ **Better compatibility** with Python 3.12+
- ✅ **No SSL/TLS handshake issues** on Windows
- ✅ **Easier to debug** (standard HTTP)
- ⚠️ Slightly slower (~200ms) than gRPC

### Multi-Agent Architecture

The system uses specialized agents for each service:
- **EmailAgent**: Parses email intents and executes Gmail operations
- **DriveAgent**: Handles file management in Google Drive
- **CalendarAgent**: Manages calendar events
- **Main Agent**: Routes requests to appropriate sub-agents

### AI Capabilities

Uses Gemini 1.5 Flash for:
- Intent classification (EMAIL/DRIVE/CALENDAR/CHAT)
- Parameter extraction (to, subject, filename, etc.)
- Natural language understanding
- Context-aware responses

## 🐛 Troubleshooting

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**"credentials.json not found":**
- Make sure you've downloaded OAuth credentials from Google Cloud Console
- Place it in the project root directory

**"Invalid API key":**
- Check your `config.py` has the correct Gemini API key
- Generate a new key at https://aistudio.google.com/app/apikey

**Frontend won't start:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

## 📝 Notes

- First run will open a browser for Google OAuth authentication
- Credentials are saved in `token.pickle` for future use
- Quota: Gemini 1.5 Flash allows 1,500 requests/day (free tier)
- The frontend chat interface shows debug logs in the browser console

## 👨‍💻 Author

**Python Mini-Project Submission**  
Multi-Agent Google Workspace Assistant with AI Integration

## 📄 License

Educational project for academic submission.

# Google API Setup Guide

This guide walks you through setting up the required API credentials for the Friday Google Workspace Assistant.

## 📋 What You Need

1. **Google Cloud Project** (free)
2. **OAuth 2.0 Credentials** (for Gmail, Drive, Calendar)
3. **Gemini API Key** (for AI features)

---

## 🔧 Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Enter project name: `friday-workspace-assistant`
4. Click "Create"

---

## 🌐 Step 2: Enable Required APIs

In your Google Cloud Project:

### Enable Gmail API
1. Go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click **Enable**

### Enable Google Drive API
1. Search for "Google Drive API"
2. Click **Enable**

### Enable Google Calendar API
1. Search for "Google Calendar API"
2. Click **Enable**

---

## 🔑 Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, click **CONFIGURE CONSENT SCREEN**:
   - User Type: **External**
   - Click **Create**
   - App name: `Friday Assistant`
   - User support email: *your email*
   - Developer contact: *your email*
   - Click **Save and Continue**
   - Scopes: Skip for now (click **Save and Continue**)
   - Test users: Add your email
   - Click **Save and Continue**
4. Back to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: `Friday Desktop Client`
   - Click **Create**
5. Click **Download JSON**
6. Rename downloaded file to `credentials.json`
7. Move `credentials.json` to your project folder

Your `credentials.json` should look like:
```json
{
  "installed": {
    "client_id": "xxxxx.apps.googleusercontent.com",
    "project_id": "friday-workspace-assistant",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    ...
  }
}
```

---

## 🤖 Step 4: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Select your Google Cloud Project (or create a new one)
4. Click **Create API key in new project** or use existing
5. Copy the API key (starts with `AIza...`)

### Create config.py

In your project folder, create `config.py`:

```python
GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Replace with your actual API key.

---

## ✅ Verify Setup

Your project folder should now have:

```
Python skl projects/
├── Friday1.0.py
├── server.py
├── credentials.json    ← Downloaded from Google Cloud
├── config.py           ← Created with your Gemini API key
└── requirements.txt
```

---

## 🚀 First Run Authentication

When you run the app for the first time:

1. Run `python server.py`
2. A browser window will open
3. Sign in with your Google account
4. Click **Allow** to grant permissions
5. The credentials will be saved in `token.pickle`

**Next time**, authentication is automatic (uses `token.pickle`).

---

## 🔒 Security Notes

⚠️ **IMPORTANT:**
- Never commit `credentials.json` to Git
- Never share your `config.py` with API keys
- Add to `.gitignore`:
  ```
  credentials.json
  token.pickle
  config.py
  ```

---

## 🆘 Troubleshooting

### "Credentials not found"
- Make sure `credentials.json` is in the project root
- Check the filename is exactly `credentials.json`

### "Invalid grant" error
- Delete `token.pickle`
- Run the app again to re-authenticate

### "API not enabled" error
- Go back to Google Cloud Console
- Enable the missing API (Gmail/Drive/Calendar)

### "Quota exceeded"
- Gemini free tier: 1,500 requests/day
- Create a new API key if needed
- Or upgrade to paid tier

---

## 📚 Additional Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Drive API Documentation](https://developers.google.com/drive)
- [Calendar API Documentation](https://developers.google.com/calendar)
- [Gemini API Documentation](https://ai.google.dev/docs)

---

## ✨ Done!

You're all set! Run `python server.py` to start your Friday assistant.

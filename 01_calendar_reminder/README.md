# 🗓️ Google Calendar Assistant

An AI-powered Google Calendar management application with a React frontend and FastAPI backend.

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://docker.com/products/docker-desktop) installed and running

### Setup (3 Easy Steps)

1. **Add your API keys**:
   - Open `env.example` file
   - Replace `your_openai_api_key_here` with your actual [OpenAI API key](https://platform.openai.com/api-keys)
   - Replace `your_serper_api_key_here` with your [Serper API key](https://serper.dev/)
   - (Optional) Add your Telegram bot token for reminders

2. **Run the startup script**:
   - docker compose up -d

3. **Open your browser**:
   - Go to [http://localhost:3000](http://localhost:3000)

### Docker Commands

```bash
# Start the application
docker compose up -d

# View logs
docker compose logs -f

# Stop the application
docker compose down

# Restart services
docker compose restart

# Rebuild after code changes
docker compose build --no-cache
```

## 🔐 Google Calendar Credentials Setup

Before using the application, you need to set up Google Calendar API credentials:

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter a project name (e.g., "Calendar Assistant")
4. Click **"Create"**

### 2. Enable Google Calendar API

1. In your project, go to **APIs & Services** → **Library**
2. Search for **"Google Calendar API"**
3. Click on it and press **"Enable"**

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - Choose **"External"** user type
   - Fill in required fields (App name, User support email, Developer email)
   - Add your email to test users
   - Save and continue through all steps

4. For the OAuth client ID:
   - **Application type**: Select **"Desktop application"**
   - **Name**: Enter a name (e.g., "Calendar Assistant Desktop")
   - Click **"Create"**

### 4. Download and Save Credentials

1. After creating the OAuth client, click the **download button** (⬇️) next to your credential
2. This downloads a JSON file (usually named like `client_secret_xxxxx.json`)
3. **Important**: Rename this file to exactly `client_secrets.json`
4. Place the file in the `calendar_credentials/` folder in your project:
   ```
   01_calendar_reminder/
   ├── calendar_credentials/
   │   └── client_secrets.json  ← Your downloaded credentials file
   ```

### 5. Configure Authorized Redirect URIs

1. Back in Google Cloud Console, click on your OAuth client ID to edit it
2. In the **"Authorized redirect URIs"** section, add:
   ```
   http://localhost:8000/auth/callback
   ```
3. Click **"Save"**

### ✅ Verification

Your `calendar_credentials/client_secrets.json` should look something like this:
```json
{
  "installed": {
    "client_id": "your-client-id.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

> **Note**: Keep this file secure and never commit it to version control!

## 🛠️ Manual Setup (Alternative)

If you prefer not to use Docker:

1. **Install dependencies**: Python 3.11+ and Node.js 18+
2. **Add API keys**: Edit `env.example` with your keys
3. **Run startup script**:
   - **Mac/Linux**: `./start.sh`
   - **Windows**: Double-click `start.bat`

## 📋 Features

- ✅ Google Calendar integration with OAuth
- ✅ AI-powered event creation from natural language
- ✅ Smart chatbot for calendar management
- ✅ Telegram reminders and notifications
- ✅ Modern React UI with calendar visualization
- ✅ Background scheduling for daily reminders

## 🔑 Required API Keys

- **OpenAI API Key**: For AI features and chatbot
- **Serper API Key**: For web search in chatbot
- **Telegram Bot Token**: (Optional) For reminder notifications

## 🆘 Troubleshooting

### Docker Issues
- Make sure Docker Desktop is running
- Try `docker compose down` then `docker compose up -d`
- Check logs with `docker compose logs -f`

### API Key Issues
- Verify your keys are correctly added to the `.env` file
- Make sure there are no extra spaces or quotes around the keys
- Check the API key is active and has sufficient credits

### Port Conflicts
- If ports 8000 or 5173 are in use, stop other services or modify the ports in `docker-compose.yml`

## 📞 Support

For issues or questions, check the logs first:
- Docker: `docker compose logs -f`
- Manual setup: Check `backend.log` and `frontend.log` 
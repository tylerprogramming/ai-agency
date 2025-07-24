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
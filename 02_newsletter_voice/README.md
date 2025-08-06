# Voice Agent - AI-Powered Newsletter Generator

A modular Python application that automatically creates audio newsletters by searching for content, generating articles using AI, converting them to speech, and distributing via Telegram.

## Features

- 🔍 **Smart Content Search**: Uses Firecrawl to search and scrape relevant web content
- 🤖 **AI Article Generation**: Creates professional newsletter articles using OpenAI GPT
- 🎙️ **High-Quality Audio**: Converts articles to natural-sounding speech using ElevenLabs
- 📱 **Telegram Integration**: Automatically sends voice messages via Telegram
- 🏗️ **Clean Architecture**: Modular design with proper separation of concerns
- ⚡ **Multiple Usage Modes**: Interactive CLI, direct topic input, or search-only mode

## Installation

1. Clone the repository and navigate to the voice agent directory:
```bash
cd 02_newsletter_voice
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables by creating a `.env` file:
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional Configuration
SEARCH_LIMIT=5
SEARCH_TIME_FILTER=qdr:d
OPENAI_MODEL=gpt-4.1
ELEVENLABS_MODEL=eleven_multilingual_v2
AUDIO_FORMAT=mp3_44100_128
```

## Usage

### Interactive Mode
```bash
python main.py
```

### Direct Topic Input
```bash
python main.py "AI agents and memory systems"
```

### With Options
```bash
# Don't send via Telegram
python main.py --topic "blockchain technology" --no-telegram

# Custom output filename
python main.py "machine learning trends" --output ml_newsletter.mp3

# Search only (no audio generation)
python main.py "quantum computing" --search-only

# Enable debug logging
python main.py "data science" --debug
```

## Architecture

The application follows clean architecture principles with clear separation of concerns:

```
02_voice_agent/
├── main.py              # CLI interface and application entry point
├── voice_agent.py       # Main application orchestrator
├── services.py          # Service classes for different responsibilities
├── config.py            # Configuration management
├── exceptions.py        # Custom exception classes
├── telegram.py          # Telegram messaging utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Key Components

- **VoiceAgent**: Main orchestrator class that coordinates all services
- **SearchService**: Handles web content search and scraping
- **ContentGenerationService**: Manages AI-powered article generation
- **AudioGenerationService**: Converts text to high-quality speech
- **MessagingService**: Handles Telegram voice message delivery
- **VoiceAgentConfig**: Centralized configuration with validation

## Configuration

All configuration is managed through environment variables with sensible defaults:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `FIRECRAWL_API_KEY` | Firecrawl API key | Yes | - |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | Yes | - |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID | Yes | - |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes | - |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | Yes | - |
| `SEARCH_LIMIT` | Number of search results | No | 5 |
| `SEARCH_TIME_FILTER` | Time filter for search | No | qdr:d |
| `OPENAI_MODEL` | OpenAI model to use | No | gpt-4.1 |
| `ELEVENLABS_MODEL` | ElevenLabs model | No | eleven_multilingual_v2 |
| `AUDIO_FORMAT` | Audio output format | No | mp3_44100_128 |

## Error Handling

The application includes comprehensive error handling with custom exception types:

- `ConfigurationError`: Issues with configuration or missing API keys
- `SearchError`: Problems with content search or scraping
- `ContentGenerationError`: AI content generation failures
- `AudioGenerationError`: Text-to-speech conversion issues
- `MessagingError`: Telegram delivery problems

## Logging

Logs are written to both console and `voice_agent.log` file. Use `--debug` flag for detailed logging.

## API Keys Setup

### OpenAI
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to your `.env` file

### Firecrawl
1. Visit [Firecrawl](https://firecrawl.dev)
2. Sign up and get your API key
3. Add to your `.env` file

### ElevenLabs
1. Visit [ElevenLabs](https://elevenlabs.io)
2. Create account and get API key
3. Select a voice and get the voice ID
4. Add both to your `.env` file

### Telegram
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Get your chat ID (message your bot and check updates)
4. Add both to your `.env` file

## Contributing

This codebase follows Python best practices:

- **Type Hints**: All functions include proper type annotations
- **Documentation**: Comprehensive docstrings for all classes and methods
- **Error Handling**: Robust exception handling with custom exception types
- **Logging**: Structured logging throughout the application
- **Configuration**: Centralized configuration with validation
- **Separation of Concerns**: Each service has a single responsibility
- **Clean Code**: Readable, maintainable, and well-organized code structure

## License

This project is part of the AI Automations Agency toolkit. 
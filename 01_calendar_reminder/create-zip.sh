#!/bin/bash

# Google Calendar Assistant - Create Distribution Zip
# This script creates a clean zip file with only the essential project files

ZIP_NAME="google-calendar-assistant-$(date +%Y%m%d).zip"
TEMP_DIR="temp_zip_staging"

echo "🗂️  Creating clean distribution zip: $ZIP_NAME"

# Create temporary staging directory
mkdir -p "$TEMP_DIR"

# Copy essential files and directories
echo "📁 Copying project files..."

# Root level files
cp README.md "$TEMP_DIR/"
cp docker-compose.yml "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp Dockerfile.backend "$TEMP_DIR/"
cp Dockerfile.frontend "$TEMP_DIR/"
cp .dockerignore "$TEMP_DIR/"
cp calendar_retriever.py "$TEMP_DIR/"

# Backend (excluding __pycache__)
echo "🐍 Copying backend..."
mkdir -p "$TEMP_DIR/backend"
cp -r backend/* "$TEMP_DIR/backend/"
find "$TEMP_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true

# Frontend (excluding node_modules and build artifacts)
echo "⚛️  Copying frontend source..."
mkdir -p "$TEMP_DIR/_frontend"
cp _frontend/package.json "$TEMP_DIR/_frontend/"
cp _frontend/package-lock.json "$TEMP_DIR/_frontend/"
cp _frontend/vite.config.ts "$TEMP_DIR/_frontend/"
cp _frontend/tsconfig*.json "$TEMP_DIR/_frontend/"
cp _frontend/tailwind.config.js "$TEMP_DIR/_frontend/"
cp _frontend/postcss.config.js "$TEMP_DIR/_frontend/"
cp _frontend/eslint.config.js "$TEMP_DIR/_frontend/"
cp _frontend/index.html "$TEMP_DIR/_frontend/"
cp _frontend/.gitignore "$TEMP_DIR/_frontend/"

# Copy frontend src directory
cp -r _frontend/src "$TEMP_DIR/_frontend/"

# Calendar credentials directory (create empty directory with README)
echo "🔑 Setting up credentials directory..."
mkdir -p "$TEMP_DIR/calendar_credentials"
cat > "$TEMP_DIR/calendar_credentials/README.md" << EOF
# Calendar Credentials

Place your Google Calendar API credentials here:

1. Download your OAuth 2.0 credentials from Google Cloud Console
2. Rename the file to \`client_secrets.json\`
3. Place it in this directory

The file should be named exactly: \`client_secrets.json\`

⚠️ **Never commit actual credentials to version control!**
EOF

# Create example environment file
echo "⚙️  Creating environment template..."
cat > "$TEMP_DIR/env.example" << EOF
# API Keys - Replace with your actual keys
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Optional: Telegram Bot Token for reminders
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Calendar Settings (usually don't need to change)
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Server Settings (usually don't need to change)
HOST=0.0.0.0
PORT=8000
DEBUG=false
EOF

# Create zip file
echo "📦 Creating zip file..."
cd "$TEMP_DIR"
zip -r "../$ZIP_NAME" . -x "*.DS_Store" "*/.*" 
cd ..

# Cleanup
rm -rf "$TEMP_DIR"

# Calculate size
ZIP_SIZE=$(du -h "$ZIP_NAME" | cut -f1)

echo "✅ Successfully created: $ZIP_NAME ($ZIP_SIZE)"
echo ""
echo "📋 Zip contains:"
echo "   ✓ All source code (backend + frontend)"
echo "   ✓ Docker configuration"
echo "   ✓ Documentation (README.md)"
echo "   ✓ Environment template"
echo "   ✓ Empty credentials directory with instructions"
echo ""
echo "❌ Excluded:"
echo "   ✗ node_modules/ (saves ~200MB+)"
echo "   ✗ __pycache__/ (Python cache files)"
echo "   ✗ .git/ (git history)"
echo "   ✗ Actual API keys/credentials"
echo ""
echo "🚀 Recipients can run: docker compose up -d" 
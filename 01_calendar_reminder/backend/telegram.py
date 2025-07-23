import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Default to environment variables, but allow override
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_text_message(message, bot_token=None, chat_id=None):
    """Sends a text message to Telegram."""
    token = bot_token or TELEGRAM_BOT_TOKEN
    chat = chat_id or TELEGRAM_CHAT_ID
    
    if not token or not chat:
        raise ValueError("Bot token and chat ID are required")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat, 
        "text": message
    }
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print("✅ Telegram text message sent!")
        return True
    else:
        print(f"❌ Failed to send Telegram text message: {response.text}")
        return False


def send_telegram_voice_message(speech_file_path=None):
    """Sends a voice message to Telegram."""
    send_audio_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice'
    if speech_file_path:
        files = {'voice': open(speech_file_path, 'rb')}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        
        response = requests.post(send_audio_url, files=files, data=data)
        
        if response.status_code == 200:
            print("✅ Telegram voice message sent!")
        else:
            print(f"❌ Failed to send Telegram voice message: {response.text}")


def send_telegram_message(message, speech_file_path = None):
    """Sends a message to Telegram."""

    send_audio_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice'

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    if speech_file_path:
        files = {'voice': open(speech_file_path, 'rb')}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        response = requests.post(send_audio_url, files=files, data=data)
    else:
        response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print("✅ Telegram message sent!")
    else:
        print(f"❌ Failed to send Telegram message: {response.text}") 
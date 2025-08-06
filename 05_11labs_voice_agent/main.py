import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
agent_id = os.getenv("AGENT_ID")

if agent_id is None:
    raise ValueError("AGENT_ID must be set in environment")

# Initialize client
client = ElevenLabs(api_key=api_key)

# Create audio interface (uses your microphone and speaker)
audio_interface = DefaultAudioInterface()

# Set up conversation session
conversation = Conversation(
    client,
    agent_id,
    requires_auth=bool(api_key),
    audio_interface=audio_interface,
    callback_user_transcript=lambda t: print(f"User (transcript): {t}"),
    callback_agent_response=lambda resp: print(f"Agent says: {resp}"),
    callback_agent_response_correction=lambda orig, corr: print(f"Agent corrected: {orig} → {corr}")
)

print("Starting voice conversation — press Ctrl+C to stop.")
conversation.start_session()
conversation.wait_for_session_end()
print(f"Conversation ended. Conversation ID: {conversation.conversation_id}")
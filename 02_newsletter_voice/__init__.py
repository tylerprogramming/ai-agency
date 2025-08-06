"""
Voice Agent - AI-Powered Newsletter Generator

A modular application for creating AI-generated audio newsletters.
"""

from .voice_agent import VoiceAgent
from .config import VoiceAgentConfig

__version__ = "1.0.0"
__all__ = [
    "VoiceAgent",
    "VoiceAgentConfig"
] 
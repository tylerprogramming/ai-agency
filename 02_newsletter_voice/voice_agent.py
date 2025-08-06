"""Main Voice Agent application class."""

import logging
from pathlib import Path
from typing import Optional

from config import VoiceAgentConfig
from services import (
    SearchService,
    ContentGenerationService, 
    AudioGenerationService,
    MessagingService
)

logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    Main Voice Agent application that coordinates content search, 
    AI generation, audio synthesis, and messaging.
    """
    
    def __init__(self, config: Optional[VoiceAgentConfig] = None):
        """
        Initialize the Voice Agent.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        try:
            self.config = config or VoiceAgentConfig.from_environment()
            self.config.validate()
        except Exception as e:
            raise Exception(f"Configuration error: {e}")
        
        # Initialize services
        self.search_service = SearchService(self.config)
        self.content_service = ContentGenerationService(self.config)
        self.audio_service = AudioGenerationService(self.config)
        self.messaging_service = MessagingService(self.config)
        
        logger.info("Voice Agent initialized successfully")
    
    def create_newsletter_audio(
        self, 
        topic: str, 
        output_filename: str = "newsletter.mp3",
        send_telegram: bool = True
    ) -> Path:
        """
        Create a newsletter audio file from a topic and optionally send via Telegram.
        
        Args:
            topic: The topic to create a newsletter about
            output_filename: Name of the output audio file
            send_telegram: Whether to send the audio via Telegram
            
        Returns:
            Path to the generated audio file
            
        Raises:
            SearchError: If content search fails
            ContentGenerationError: If AI content generation fails
            AudioGenerationError: If audio generation fails
            MessagingError: If Telegram messaging fails
        """
        logger.info(f"Creating newsletter audio for topic: {topic}")

        # Step 1: Search for content
        logger.info("Step 1: Searching for content...")
        search_results = self.search_service.search_content(topic)
        
        if not search_results:
            raise Exception(f"No content found for topic: {topic}")
        
        # Step 2: Generate newsletter article
        logger.info("Step 2: Generating newsletter article...")
        article = self.content_service.generate_newsletter_article(topic, search_results)
        
        # Step 3: Generate audio
        logger.info("Step 3: Generating audio...")
        audio_path = self.audio_service.generate_audio(article, output_filename)
        
        # Step 4: Send via Telegram (optional)
        if send_telegram:
            logger.info("Step 4: Sending via Telegram...")
            success = self.messaging_service.send_voice_message(audio_path)
            if not success:
                raise Exception("Failed to send voice message via Telegram")
        
        logger.info(f"Newsletter audio creation completed: {audio_path}")
        return audio_path
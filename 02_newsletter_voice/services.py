"""Service classes for the Voice Agent application."""

import logging
from pathlib import Path

from elevenlabs import ElevenLabs, save
from firecrawl import FirecrawlApp, ScrapeOptions
from openai import OpenAI

from .config import VoiceAgentConfig

logger = logging.getLogger(__name__)

class SearchService:
    """Service for web search and content scraping."""
    
    def __init__(self, config: VoiceAgentConfig):
        self.config = config
        self.firecrawl_app = FirecrawlApp(api_key=config.firecrawl_api_key)
    
    def search_content(self, query: str) -> str:
        """
        Search for content related to the query and return aggregated markdown.
        
        Args:
            query: The search query string
            
        Returns:
            Aggregated markdown content from search results
            
        Raises:
            Exception: If search fails
        """
        try:
            logger.info(f"Searching for content: {query}")
            
            search_result = self.firecrawl_app.search(
                query=query,
                limit=self.config.search_limit,
                tbs=self.config.search_time_filter,
                scrape_options=ScrapeOptions(formats=["markdown", "links"])
            )
            
            if not search_result.data:
                logger.warning(f"No search results found for query: {query}")
                return ""
            
            markdown_text = ""
            for result in search_result.data:
                if result.get('markdown'):
                    markdown_text += result['markdown'] + "\n\n"
            
            logger.info(f"Retrieved {len(search_result.data)} search results")
            return markdown_text.strip()
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise Exception(f"Failed to search content: {e}")


class ContentGenerationService:
    """Service for AI-powered content generation."""
    
    def __init__(self, config: VoiceAgentConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
    
    def generate_newsletter_article(self, topic: str, source_content: str) -> str:
        """
        Generate a newsletter article based on the topic and source content.
        
        Args:
            topic: The main topic for the newsletter
            source_content: Source content to base the article on
            
        Returns:
            Generated newsletter article text
            
        Raises:
            Exception: If content generation fails
        """
        try:
            logger.info(f"Generating newsletter article for topic: {topic}")
            
            prompt = self._create_newsletter_prompt(topic, source_content)
            
            completion = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            article = completion.choices[0].message.content
            logger.info("Newsletter article generated successfully")
            return article
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise Exception(f"Failed to generate content: {e}")
    
    def _create_newsletter_prompt(self, topic: str, source_content: str) -> str:
        """Create a well-structured prompt for newsletter generation."""
        return f"""
        Take the following title about: {topic} and create an amazing newsletter article about it using this information: {source_content}.

        Guidelines:
        - Summarize the content concisely and professionally
        - Write in the style of a professional newsletter writer
        - Keep it engaging but not too long
        - Focus on the main points and key insights
        - Do not include any code examples
        - Make it accessible to a general audience
        - Include actionable takeaways where relevant
        
        The article should be informative, well-structured, and engaging.
        """


class AudioGenerationService:
    """Service for text-to-speech audio generation."""
    
    def __init__(self, config: VoiceAgentConfig):
        self.config = config
        self.client = ElevenLabs(api_key=config.elevenlabs_api_key)
    
    def generate_audio(self, text: str, output_filename: str) -> Path:
        """
        Generate audio from text and save to file.
        
        Args:
            text: Text content to convert to speech
            output_filename: Name of the output audio file
            
        Returns:
            Path to the generated audio file
            
        Raises:
            Exception: If audio generation fails
        """
        try:
            logger.info(f"Generating audio for text (length: {len(text)} chars)")
            
            audio = self.client.text_to_speech.convert(
                voice_id=self.config.elevenlabs_voice_id,
                output_format=self.config.audio_format,
                text=text,
                model_id=self.config.elevenlabs_model,
            )
            
            output_path = Path(output_filename)
            save(audio, str(output_path))
            
            logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise Exception(f"Failed to generate audio: {e}")


class MessagingService:
    """Service for sending messages via Telegram."""
    
    def __init__(self, config: VoiceAgentConfig):
        self.config = config
    
    def send_voice_message(self, audio_file_path: Path) -> bool:
        """
        Send voice message via Telegram.
        
        Args:
            audio_file_path: Path to the audio file to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending voice message: {audio_file_path}")
            
            # Import telegram module - it's in the same directory
            import telegram
            
            telegram.send_telegram_voice_message(
                speech_file_path=str(audio_file_path)
            )
            
            logger.info("Voice message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send voice message: {e}")
            return False 
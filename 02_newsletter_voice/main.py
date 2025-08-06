import sys

from voice_agent import VoiceAgent


def get_topic_interactive() -> str:
    """Get topic from user input interactively."""
    print("\n🎙️ Voice Agent - AI Newsletter Generator")
    print("=" * 50)
    
    while True:
        topic = input("\nEnter the topic for your newsletter (or 'quit' to exit): ").strip()
        
        if topic.lower() in ('quit', 'exit', 'q'):
            print("Goodbye! 👋")
            sys.exit(0)
        
        if topic:
            return topic
        
        print("⚠️  Please enter a valid topic.")

def main() -> None:
    """Main application entry point."""

    topic = get_topic_interactive()
    agent = VoiceAgent()
    
    # Create newsletter audio
    print(f"\n🎯 Creating newsletter about: {topic}")
    print("⏳ This may take a few minutes...")
    
    audio_path = agent.create_newsletter_audio(
        topic=topic,
        output_filename="output/newsletter.mp3",
        send_telegram=True
    )
    
    print(f"\n✅ Newsletter created successfully!")
    print(f"📁 Audio file: {audio_path}")
  
if __name__ == "__main__":
    main()
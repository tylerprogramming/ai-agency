#!/usr/bin/env python3
"""
Start the Submagic File Monitor
Installs dependencies and starts monitoring for video files.
"""

import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists with required API key."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Create a .env file with your SUBMAGIC_API_KEY:")
        print("SUBMAGIC_API_KEY=your_api_key_here")
        return False
    
    # Check if SUBMAGIC_API_KEY is in the file
    env_content = env_path.read_text()
    if "SUBMAGIC_API_KEY" not in env_content:
        print("❌ SUBMAGIC_API_KEY not found in .env file!")
        print("Add this line to your .env file:")
        print("SUBMAGIC_API_KEY=your_api_key_here")
        return False
    
    print("✅ Environment configuration found")
    return True

def main():
    """Main startup function."""
    print("🎬 Submagic File Monitor Startup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check environment
    if not check_env_file():
        return
    
    print("\n" + "=" * 40)
    print("🚀 Starting file monitor...")
    
    # Start the monitor
    try:
        from file_monitor import main as monitor_main
        monitor_main()
    except ImportError as e:
        print(f"❌ Failed to import file monitor: {e}")
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
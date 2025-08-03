#!/usr/bin/env python3
"""
File Monitor for Submagic Flow
Watches /Users/tylerreed/files_to_submagic for new MP4/MOV files
and automatically triggers the submagic processing flow.
"""

import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from submagic_flow.src.submagic_flow.main import kickoff as submagic_kickoff

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
WATCH_FOLDER = "/Users/tylerreed/files_to_submagic"
SUPPORTED_EXTENSIONS = {'.mp4', '.mov', '.MP4', '.MOV'}
PROCESSED_FILES = set()  # Keep track of processed files to avoid duplicates

class VideoFileHandler(FileSystemEventHandler):
    """Handle file system events for video files."""
    
    def __init__(self):
        super().__init__()
        self.processing = False
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        self.process_file(event.src_path)
    
    def on_moved(self, event):
        """Handle file move events (like when download completes)."""
        if event.is_directory:
            return
            
        self.process_file(event.dest_path)
    
    def process_file(self, file_path):
        """Process a potentially new video file."""
        try:
            file_path = Path(file_path)
            
            # Check if it's a video file we care about
            if file_path.suffix not in SUPPORTED_EXTENSIONS:
                return
            
            # Check if we've already processed this file
            if str(file_path) in PROCESSED_FILES:
                return
            
            # Wait a moment to ensure file is fully written
            logger.info(f"📹 New video file detected: {file_path.name}")
            logger.info("⏳ Waiting 2 seconds to ensure file is complete...")
            time.sleep(2)
            
            # Verify file exists and is readable
            if not file_path.exists():
                logger.warning(f"❌ File no longer exists: {file_path}")
                return
            
            if file_path.stat().st_size == 0:
                logger.warning(f"❌ File is empty: {file_path}")
                return
            
            # Mark as processing to avoid duplicates
            PROCESSED_FILES.add(str(file_path))
            
            # Trigger submagic processing
            logger.info(f"🚀 Starting Submagic processing for: {file_path.name}")
            
            try:
                submagic_kickoff(str(file_path.name))
                
                logger.info(f"✅ Successfully uploaded to Submagic!")
                logger.info(f"📁 File: {file_path.name}")
                
            except Exception as upload_error:
                logger.error(f"❌ Failed to upload {file_path.name}: {upload_error}")
                # Remove from processed set so we can retry later
                PROCESSED_FILES.discard(str(file_path))
                
        except Exception as e:
            logger.error(f"❌ Error processing file {file_path}: {e}")
    
    def move_processed_file(self, file_path):
        """Optionally move processed files to a 'processed' subfolder."""
        try:
            processed_folder = file_path.parent / "processed"
            processed_folder.mkdir(exist_ok=True)
            
            new_path = processed_folder / file_path.name
            file_path.rename(new_path)
            
            logger.info(f"📂 Moved processed file to: {new_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to move processed file: {e}")


def ensure_watch_folder_exists():
    """Create the watch folder if it doesn't exist."""
    watch_path = Path(WATCH_FOLDER)
    if not watch_path.exists():
        logger.info(f"📁 Creating watch folder: {WATCH_FOLDER}")
        watch_path.mkdir(parents=True, exist_ok=True)
    return watch_path


def scan_existing_files(watch_path):
    """Scan for existing files in the folder on startup."""
    logger.info("🔍 Scanning for existing video files...")
    
    existing_files = []
    for file_path in watch_path.iterdir():
        if file_path.is_file() and file_path.suffix in SUPPORTED_EXTENSIONS:
            existing_files.append(file_path)
    
    if existing_files:
        logger.info(f"📹 Found {len(existing_files)} existing video files")
        for file_path in existing_files:
            logger.info(f"  - {file_path.name}")
        
        # Optionally process existing files
        process_existing = input("🤔 Process existing files? (y/N): ").strip().lower()
        if process_existing == 'y':
            handler = VideoFileHandler()
            for file_path in existing_files:
                handler.process_file(str(file_path))
    else:
        logger.info("📂 No existing video files found")


def main():
    """Main monitoring function."""
    logger.info("🎬 Starting Submagic File Monitor")
    logger.info(f"📁 Watching: {WATCH_FOLDER}")
    logger.info(f"🎯 Supported files: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    # Ensure watch folder exists
    watch_path = ensure_watch_folder_exists()
    
    # Scan for existing files
    scan_existing_files(watch_path)
    
    # Setup file system observer
    event_handler = VideoFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=False)
    
    # Start monitoring
    observer.start()
    logger.info("👀 File monitoring started. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping file monitor...")
        observer.stop()
    
    observer.join()
    logger.info("✅ File monitor stopped.")


if __name__ == "__main__":
    main()
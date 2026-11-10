# 🎬 Submagic File Monitor

Automatically processes MP4/MOV files with Submagic when they're added to a watched folder.

## 🚀 Quick Start

1. **Install the dependencies (Python 3.10-3.13):**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create the watch folder:**
   ```bash
   mkdir -p /Users/tylerreed/files_to_submagic
   ```

3. **Make sure you have your Submagic API key in `.env`:**
   ```bash
   echo "SUBMAGIC_API_KEY=your_api_key_here" >> .env
   ```

4. **Start the monitor:**
   ```bash
   python start_monitor.py
   ```

## 📁 How it Works

- **Watches:** `/Users/tylerreed/files_to_submagic`
- **Triggers on:** New `.mp4`, `.mov`, `.MP4`, `.MOV` files
- **Action:** Automatically uploads to Submagic using the "Hormozi 2" template
- **Logs:** Everything is logged to `file_monitor.log`

## 🎯 Usage

1. Start the monitor script
2. Drop MP4/MOV files into `/Users/tylerreed/files_to_submagic`
3. Watch the magic happen! ✨

## 📋 Features

- ✅ Automatic file detection
- ✅ Duplicate prevention
- ✅ File completion verification
- ✅ Detailed logging
- ✅ Error handling
- ✅ Existing file processing option

## 🛑 Stop Monitor

Press `Ctrl+C` to stop the monitoring.

## 📊 Monitor Output

```
📹 New video file detected: my_video.mp4
⏳ Waiting 2 seconds to ensure file is complete...
🚀 Starting Submagic processing for: my_video.mp4
✅ Successfully uploaded to Submagic!
🔗 Project ID: proj_abc123
📁 File: my_video.mp4
```

## 🔧 Customization

Edit `file_monitor.py` to:
- Change the watch folder location
- Modify Submagic template settings
- Add file processing options
- Customize logging behavior
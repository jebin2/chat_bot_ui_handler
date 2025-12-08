import sqlite3
import time
import os
from datetime import datetime

from chat_bot_ui_handler import BraveAISearch
from browser_manager.browser_manager import BrowserConfig

POLL_INTERVAL = 3  # seconds

def process_image(file_id, filepath):
    """Process image file using BraveAISearch and return the caption"""
    try:
        print(f"🔄 Generating caption for: {os.path.abspath(filepath)}")
        
        # Configure browser
        config = BrowserConfig()
        config.use_neko = False
        config.browser_executable = os.environ.get('BROWSER_PATH', '/usr/bin/chromium')
        config.headless = True
        
        # Run caption generation
        baseUIChat = BraveAISearch(config)
        result = baseUIChat.chat(
            user_prompt=(
                "Describe what is happening in this video frame as if you're telling a story. "
                "Focus on the main subjects, their actions, the setting, and any important "
                "details that would help someone understand the scene's context. "
                "Keep your description to exactly 100 words or fewer."
            ),
            system_prompt="follow user prompt",
            file_path=os.path.abspath(filepath)
        )
        
        # Extract caption text
        caption = result if isinstance(result, str) else str(result)
        
        return caption, None
        
    except Exception as e:
        print(f"❌ Error processing file {file_id}: {str(e)}")
        return None, str(e)

def update_status(file_id, status, caption=None, error=None):
    """Update the status of a file in the database"""
    conn = sqlite3.connect('image_captions.db')
    c = conn.cursor()
    
    if status == 'completed':
        c.execute('''UPDATE image_files 
                     SET status = ?, caption = ?, processed_at = ?
                     WHERE id = ?''',
                  (status, caption, datetime.now().isoformat(), file_id))
    elif status == 'failed':
        c.execute('''UPDATE image_files 
                     SET status = ?, caption = ?, processed_at = ?
                     WHERE id = ?''',
                  (status, f"Error: {error}", datetime.now().isoformat(), file_id))
    else:
        c.execute('UPDATE image_files SET status = ? WHERE id = ?', (status, file_id))
    
    conn.commit()
    conn.close()

def worker_loop():
    """Main worker loop that processes image files"""
    print("🤖 Caption Generator Worker started. Monitoring for new image files...")
    print("🗑️  Image files will be deleted after successful processing\n")
    
    while True:
        try:
            # Get next unprocessed file
            conn = sqlite3.connect('image_captions.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''SELECT * FROM image_files 
                         WHERE status = 'not_started' 
                         ORDER BY created_at ASC 
                         LIMIT 1''')
            row = c.fetchone()
            conn.close()
            
            if row:
                file_id = row['id']
                filepath = row['filepath']
                filename = row['filename']
                
                print(f"\n{'='*60}")
                print(f"🖼️  Processing: {filename}")
                print(f"📝 ID: {file_id}")
                print(f"{'='*60}")
                
                # Update status to processing
                update_status(file_id, 'processing')
                
                # Process the image file
                caption, error = process_image(file_id, filepath)
                
                if caption:
                    print(f"✅ Successfully processed: {filename}")
                    print(f"📄 Caption preview: {caption[:100]}...")
                    update_status(file_id, 'completed', caption=caption)
                    
                    # Delete the image file after successful processing
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        print(f"🗑️  Deleted image file: {filepath}")
                else:
                    print(f"❌ Failed to process: {filename}")
                    print(f"Error: {error}")
                    update_status(file_id, 'failed', error=error)
                    # Don't delete file on failure (for debugging)
            else:
                # No files to process, sleep for a bit
                time.sleep(POLL_INTERVAL)
                
        except Exception as e:
            print(f"⚠️  Worker error: {str(e)}")
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists('image_captions.db'):
        print("❌ Database not found. Please run app.py first to initialize.")
    else:
        print("\n" + "="*60)
        print("🚀 Starting Caption Generator Worker (Standalone Mode)")
        print("="*60)
        print("⚠️  Note: Worker is now embedded in app.py")
        print("⚠️  This standalone mode is for testing/debugging only")
        print("="*60 + "\n")
        worker_loop()
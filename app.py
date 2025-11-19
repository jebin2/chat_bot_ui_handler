from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Uncomment when you have the actual imports
from chat_bot_ui_handler import GoogleAISearchChat
from browser_manager.browser_manager import BrowserConfig

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("uploads")
STATIC_DIR = Path("static")
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Thread pool for running sync code
executor = ThreadPoolExecutor(max_workers=1)  # Use single worker to avoid conflicts

def generate_caption_sync(file_path: str, prompt: str) -> str:
    """Synchronous function to generate caption using GoogleAISearchChat"""
    baseUIChat = None
    try:
        # Create fresh instances for each request
        source = GoogleAISearchChat
        config = BrowserConfig()
        baseUIChat = source(config)
        
        # Generate caption
        result = baseUIChat.chat(
            user_prompt=prompt,
            file_path=file_path
        )
        
        return result
    except Exception as e:
        print(f"Error in generate_caption_sync: {e}")
        raise
    finally:
        # Ensure cleanup happens even if there's an error
        if baseUIChat is not None:
            try:
                # Try to close/cleanup the browser instance
                if hasattr(baseUIChat, 'close'):
                    baseUIChat.close()
                elif hasattr(baseUIChat, 'cleanup'):
                    baseUIChat.cleanup()
                elif hasattr(baseUIChat, 'stop'):
                    baseUIChat.stop()
                elif hasattr(baseUIChat, '__del__'):
                    del baseUIChat
            except Exception as cleanup_error:
                print(f"Cleanup error (non-critical): {cleanup_error}")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return html_file.read_text()
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Caption Generator</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="grain-overlay"></div>
    
    <div class="container">
        <header class="header">
            <div class="logo">
                <span class="logo-icon">✨</span>
                <h1 class="logo-text">CAPTION<span class="highlight">CRAFT</span></h1>
            </div>
        </header>

        <div class="main-grid">
            <!-- UPLOAD SECTION -->
            <div class="card upload-card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">📤</span>
                        Upload Image
                    </h2>
                </div>

                <form id="captionForm" class="upload-form">
                    <div class="upload-zone" id="uploadZone">
                        <div class="upload-content">
                            <div class="upload-icon-wrapper">
                                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </div>
                            <p class="upload-text">Drop your image here</p>
                            <p class="upload-subtext">or click to browse</p>
                            <span class="upload-badge">JPG, PNG, GIF</span>
                        </div>
                        <input type="file" id="fileInput" name="file" accept="image/*" required>
                    </div>

                    <div class="preview-container" id="previewContainer">
                        <button type="button" class="preview-close" id="removeImage">×</button>
                        <img id="previewImage" src="" alt="Preview">
                    </div>

                    <div class="form-group">
                        <label for="userPrompt" class="form-label">
                            <span class="label-icon">💬</span>
                            Custom Instructions
                            <span class="optional-badge">Optional</span>
                        </label>
                        <textarea 
                            id="userPrompt" 
                            name="user_prompt" 
                            class="form-textarea"
                            placeholder="e.g., Focus on emotions, describe the colors, mention the setting..."
                            rows="3"
                        ></textarea>
                    </div>

                    <button type="submit" class="btn btn-primary" id="generateBtn">
                        <span class="btn-icon">⚡</span>
                        <span class="btn-text">Generate Caption</span>
                    </button>
                </form>
            </div>

            <!-- RESULT SECTION -->
            <div class="card result-card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">📝</span>
                        Generated Caption
                    </h2>
                </div>

                <div class="result-container">
                    <!-- Placeholder State -->
                    <div class="result-placeholder" id="placeholder">
                        <div class="placeholder-icon">🎨</div>
                        <p class="placeholder-text">Your AI-generated caption will appear here</p>
                        <p class="placeholder-subtext">Upload an image to get started</p>
                    </div>

                    <!-- Loading State -->
                    <div class="result-loading" id="loader">
                        <div class="spinner"></div>
                        <p class="loading-text">Crafting your caption...</p>
                        <p class="loading-subtext">This may take a moment</p>
                    </div>

                    <!-- Success State -->
                    <div class="result-content" id="resultContent">
                        <div class="result-text" id="resultText"></div>
                        <div class="result-actions">
                            <button type="button" class="btn btn-primary" id="copyBtn">
                                <span class="btn-icon">📋</span>
                                Copy
                            </button>
                            <button type="button" class="btn btn-primary" id="newCaptionBtn">
                                <span class="btn-icon">🔄</span>
                                New Caption
                            </button>
                        </div>
                    </div>

                    <!-- Error State -->
                    <div class="result-error" id="errorMessage">
                        <div class="error-icon">⚠️</div>
                        <p class="error-text" id="errorText"></p>
                        <button type="button" class="btn-secondary" id="retryBtn">Try Again</button>
                    </div>
                </div>
            </div>
        </div>

        <footer class="footer">
            <p>Powered by AI • Made with ❤️</p>
        </footer>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
    """

@app.post("/generate-caption")
async def generate_caption(
    file: UploadFile = File(...),
    user_prompt: str = Form("")
):
    file_path = None
    try:
        # Save uploaded file with unique name to avoid conflicts
        import time
        timestamp = int(time.time() * 1000)
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        unique_filename = f"image_{timestamp}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Build the prompt
        base_prompt = (
            "Describe what is happening in this video frame as if you're telling a story. "
            "Focus on the main subjects, their actions, the setting, and any important "
            "details that would help someone understand the scene's context. "
            "Keep your description to exactly 100 words or fewer."
        )
        
        final_prompt = base_prompt
        if user_prompt.strip():
            final_prompt = f"{base_prompt}\n\nAdditional context: {user_prompt}"
        
        # Run the synchronous chat function in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            generate_caption_sync,
            str(file_path),
            final_prompt
        )
        
        # Clean up uploaded file
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"File cleanup error (non-critical): {e}")
        
        return JSONResponse(content={"caption": result})
        
    except Exception as e:
        # Clean up uploaded file on error
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except:
            pass
            
        print(f"Error in generate_caption endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8123)
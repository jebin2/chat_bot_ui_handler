from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
import json_repair
from dotenv import load_dotenv
import os

if os.path.exists(".env"):
    load_dotenv()

# --- Global Selectors ---
SELECTORS = {
    'system_instructions_button': 'button[aria-label="System instructions"]',
    'system_instructions_textarea': 'textarea[aria-label="System instructions"]',
    'user_prompt_textarea': 'div.text-input-wrapper textarea',
    'run_button': 'button[aria-label="Run"]',
    'close_button': 'button[aria-label="close"]',
    'insert_assets_button': 'button[aria-label="Insert assets such as images, videos, files, or audio"]',
    'file_input': 'input[type="file"]',
    'copyright_acknowledge_button': 'button[aria-label="Agree to the copyright acknowledgement"]',
    'code_blocks': 'code'
}

# File type to removal button mapping
FILE_TYPE_SELECTORS = {
    ".mp4": 'button[aria-label="Remove video"]',
    ".mov": 'button[aria-label="Remove video"]',
    ".avi": 'button[aria-label="Remove video"]',
    ".mkv": 'button[aria-label="Remove video"]',
    ".mp3": 'button[aria-label="Remove audio"]',
    ".wav": 'button[aria-label="Remove audio"]',
    ".flac": 'button[aria-label="Remove audio"]',
    ".aac": 'button[aria-label="Remove audio"]',
    ".jpg": 'button[aria-label="Remove image"]',
    ".jpeg": 'button[aria-label="Remove image"]',
    ".png": 'button[aria-label="Remove image"]',
    ".gif": 'button[aria-label="Remove image"]',
    ".webp": 'button[aria-label="Remove image"]',
    ".pdf": 'button[aria-label="Remove document"]',
    ".txt": 'button[aria-label="Remove document"]',
    ".doc": 'button[aria-label="Remove document"]',
    ".docx": 'button[aria-label="Remove document"]'
}

# --- Configuration ---
DEFAULT_WAIT_TIMEOUT = 2000
UPLOAD_TIMEOUT = 20000
RUN_TIMEOUT = 60 * 60 * 1000  # 1 hour

# Editable content
SYSTEM_INSTRUCTION = """Tell me about Goku and give me in json format

Provide your response in this exact JSON structure:

```json
{
  "data": "Your 1-minute recap content here, exactly 150-175 words that capture the essential story in an engaging, speech-optimized format."
}
```
"""

DEFAULT_USER_PROMPT = "Goku goal."

# --- Core Functions ---

def configure_system_instructions(page, instruction_content):
    """Set the system instruction in Google AI Studio."""
    print("[INFO] Setting system instruction...")
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    page.locator(SELECTORS['system_instructions_button']).click()
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    page.locator(SELECTORS['system_instructions_textarea']).fill(instruction_content)
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)

def configure_user_prompt(page, prompt_content):
    """Set the user prompt in Google AI Studio."""
    print("[INFO] Setting user prompt...")
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    prompt_textarea = page.locator(SELECTORS['user_prompt_textarea'])
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    prompt_textarea.fill(prompt_content)
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)

def execute_generation(page):
    """Click the run button and wait for completion."""
    from playwright.sync_api import expect
    print("[INFO] Executing generation...")
    run_button = page.locator(SELECTORS['run_button'])
    run_button.click()

    # Give it a moment to update
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)

    # Wait until the button text no longer says "Stop"
    print("[INFO] Waiting for generation to complete...")
    expect(run_button).not_to_have_text("Stop", timeout=RUN_TIMEOUT)

    print("[INFO] Generation complete.")

def dismiss_popup(page):
    """Close any popup that might appear."""
    try:
        page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
        close_button = page.locator(SELECTORS['close_button'])
        close_button.click()
        page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    except:
        pass

def extract_json_from_last_code_block(page):
    """Extract and parse JSON from the last code block on the page."""
    print("[INFO] Extracting result from last code block...")
    page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    code_blocks = page.eval_on_selector_all(
        SELECTORS['code_blocks'], 
        "elements => elements.map(e => e.innerText)"
    )
    if not code_blocks:
        raise Exception("No code blocks found.")
    
    last_code_content = code_blocks[-1]
    try:
        parsed_data = json_repair.loads(last_code_content)
        print(parsed_data)
        return parsed_data
    except:
        print("[WARN] Last code block is not valid JSON.")
        return last_code_content  # Return raw string if not JSON

def acknowledge_copyright(page):
    """Acknowledge copyright notice if it appears."""
    try:
        page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
        acknowledge_button = page.locator(SELECTORS['copyright_acknowledge_button'])
        acknowledge_button.click()
        page.wait_for_timeout(DEFAULT_WAIT_TIMEOUT)
    except:
        pass

def upload_media_file(page, file_path):
    """
    Upload a media file using the 'Insert assets' button in Google AI Studio,
    and wait for the corresponding asset type to load.

    Args:
        page: Playwright page object.
        file_path: Absolute or relative path to the file to upload.
    """
    print(f"[INFO] Uploading file: {file_path}")

    if not file_path or not os.path.exists(file_path):
        print("[WARN] File path is empty or file does not exist.")
        return

    file_extension = os.path.splitext(file_path)[-1].lower()

    # Step 1: Click the insert assets button
    page.wait_for_timeout(1000)
    page.locator(SELECTORS['insert_assets_button']).click()
    page.wait_for_timeout(1000)

    # Step 2: Wait for file input and upload
    page.wait_for_selector(SELECTORS['file_input'], state="attached", timeout=5000)
    page.wait_for_timeout(1000)

    # Step 3: Upload file
    page.locator(SELECTORS['file_input']).set_input_files(file_path)
    page.wait_for_timeout(1000)

    acknowledge_copyright(page)

    # Step 4: Wait for upload confirmation
    wait_for_upload_completion(page, file_extension)

    # Step 5: Dismiss upload dialog
    page.wait_for_timeout(1000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    print(f"[INFO] File uploaded successfully: {file_path}")

def wait_for_upload_completion(page, file_extension):
    """Wait for the appropriate upload confirmation element based on file type."""
    print(f"[INFO] Waiting for upload completion for file type: {file_extension}")

    removal_selector = FILE_TYPE_SELECTORS.get(file_extension)
    if not removal_selector:
        print(f"[WARN] Unknown file type: {file_extension}. Using fallback wait.")
        page.wait_for_timeout(3000)
        return

    try:
        page.wait_for_selector(removal_selector, timeout=UPLOAD_TIMEOUT)
        print(f"[INFO] Upload confirmed via element: {removal_selector}")
    except:
        print(f"[WARN] Could not detect confirmation for {file_extension}, continuing anyway.")

def process_gemini_session(page, system_instruction, user_prompt, file_path):
    """Execute the complete Gemini AI Studio workflow."""
    print("[INFO] Starting Gemini AI Studio session...")
    page.goto("https://aistudio.google.com/prompts/new_chat", wait_until="networkidle")
    dismiss_popup(page)
    configure_system_instructions(page, system_instruction)
    configure_user_prompt(page, user_prompt)
    
    if file_path:
        upload_media_file(page, file_path)
    
    execute_generation(page)
    result = extract_json_from_last_code_block(page)
    return result

# --- Main Interface ---

def run_gemini_generation(system_instruction, user_prompt, file_path=None, browser_manager=None, use_local_browser=False):
    """
    Execute a Gemini AI Studio generation with the provided parameters.
    
    Args:
        system_instruction (str): The system instruction to use
        user_prompt (str): The user prompt to send
        file_path (str, optional): Path to file to upload
        browser_manager (BrowserManager, optional): Existing browser manager instance
        use_local_browser (bool): Whether to use local browser instead of Docker
        
    Returns:
        dict or str: The generated response, parsed as JSON if possible
    """
    try:
        config = BrowserConfig()
        config.docker_name = "text_frame_aligner"
        
        if use_local_browser:
            config.use_neko = False
            config.browser_executable = '/usr/bin/brave-browser'
        
        config.headless = False
        config.user_data_dir = os.getenv("PROFILE_PATH", os.path.abspath("whoa/chatgpt_profile"))
        
        if not browser_manager:
            with BrowserManager(config) as page:
                result = process_gemini_session(page, system_instruction, user_prompt, file_path)
        else:
            page = browser_manager.new_page()
            result = process_gemini_session(page, system_instruction, user_prompt, file_path)
            page.close()

        return result
    except Exception as e:
        print(f"[ERROR] Generation failed: {str(e)}")
        return None

# --- Example Usage ---

if __name__ == "__main__":
    result = run_gemini_generation(
        system_instruction=SYSTEM_INSTRUCTION,
        user_prompt=DEFAULT_USER_PROMPT
    )
    print("[RESULT]")
    print(result)

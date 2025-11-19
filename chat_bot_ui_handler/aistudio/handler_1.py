"""
Google AI Studio Automation Module
Handles automated interactions with Google AI Studio for content generation
"""

import os
import time
import subprocess
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
from functools import partial

import json_repair
from dotenv import load_dotenv
from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig

# Load environment variables
if os.path.exists(".env"):
	load_dotenv()

class AIStudioLogger:
	"""Enhanced logging with step tracking"""
	
	@staticmethod
	def info(message: str, step: Optional[str] = None):
		prefix = f"[STEP {step}] " if step else "[INFO] "
		print(f"{prefix}{message}")
	
	@staticmethod
	def success(message: str, step: Optional[str] = None):
		prefix = f"[STEP {step}] ✓ " if step else "[SUCCESS] "
		print(f"{prefix}{message}")
	
	@staticmethod
	def warning(message: str, step: Optional[str] = None):
		prefix = f"[STEP {step}] ⚠️  " if step else "[WARNING] "
		print(f"{prefix}{message}")
	
	@staticmethod
	def error(message: str, step: Optional[str] = None):
		prefix = f"[STEP {step}] ❌ " if step else "[ERROR] "
		print(f"{prefix}{message}")
	
	@staticmethod
	def debug(message: str):
		print(f"[DEBUG] {message}")


class AIStudioSelectors:
	"""Centralized UI selectors for Google AI Studio"""
	
	# Main interface elements
	SYSTEM_INSTRUCTIONS_BUTTON = 'button[aria-label="System instructions"]'
	SYSTEM_INSTRUCTIONS_TEXTAREA = 'textarea[aria-label="System instructions"]'
	USER_PROMPT_TEXTAREA = 'div.text-input-wrapper textarea'
	GEMINI_USER_PROMPT_TEXTAREA = 'rich-textarea div.ql-editor[contenteditable="true"]'
	RUN_BUTTON = 'button[aria-label="Run"]'
	CLOSE_BUTTON = 'button[aria-label="close"]'
	
	# File upload elements
	INSERT_ASSETS_BUTTON = 'button[aria-label="Insert assets such as images, videos, files, or audio"]'
	FILE_INPUT = 'input[type="file"]'
	FILE_INPUT_MANUAL_UPLOAD = 'button[aria-label="Upload File"]'
	COPYRIGHT_ACKNOWLEDGE_BUTTON = 'button[aria-label="Agree to the copyright acknowledgement"]'
	
	# Content extraction
	CODE_BLOCKS = 'code'
	
	# File type removal buttons (for upload confirmation)
	FILE_TYPE_REMOVAL_SELECTORS = {
		# Video files
		".mp4": 'button[aria-label="Remove video"]',
		".mov": 'button[aria-label="Remove video"]',
		".avi": 'button[aria-label="Remove video"]',
		".mkv": 'button[aria-label="Remove video"]',
		
		# Audio files
		".mp3": 'button[aria-label="Remove audio"]',
		".wav": 'button[aria-label="Remove audio"]',
		".flac": 'button[aria-label="Remove audio"]',
		".aac": 'button[aria-label="Remove audio"]',
		
		# Image files
		".jpg": 'button[aria-label="Remove image"]',
		".jpeg": 'button[aria-label="Remove image"]',
		".png": 'button[aria-label="Remove image"]',
		".gif": 'button[aria-label="Remove image"]',
		".webp": 'button[aria-label="Remove image"]',
		
		# Document files
		".pdf": 'button[aria-label="Remove document"]',
		".txt": 'button[aria-label="Remove document"]',
		".doc": 'button[aria-label="Remove document"]',
		".docx": 'button[aria-label="Remove document"]'
	}


class AIStudioConfig:
	"""Configuration constants for AI Studio automation"""
	
	# Timeout settings
	DEFAULT_WAIT_TIMEOUT = 2000
	UPLOAD_TIMEOUT = 20000
	RUN_TIMEOUT = 60 * 60 * 1000  # 1 hour
	
	# URLs
	NEW_CHAT_URL = "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview"
	GEMINI_NEW_CHAT_URL = "https://gemini.google.com/app"
	
	# Default content
	DEFAULT_DOCKER_CONTAINER = "anime_shorts_aistudio_ui_handler"


class AIStudioAutomation:
	"""Main automation class for Google AI Studio interactions"""
	
	def __init__(self, config: Optional[BrowserConfig] = None, url: str = None, policies_path: str = None, folder_path: str = None, use_gemini: bool = False):
		self.policies_path = policies_path
		self.folder_path = folder_path
		self.config = config or self._create_default_config()
		self.logger = AIStudioLogger()
		self.selectors = AIStudioSelectors()
		self.settings = AIStudioConfig()
		self.settings.NEW_CHAT_URL = url or (AIStudioConfig.GEMINI_NEW_CHAT_URL if use_gemini else AIStudioConfig.NEW_CHAT_URL)
		self.use_gemini = use_gemini
	
	def _create_default_config(self) -> BrowserConfig:
		"""Create default browser configuration"""
		config = BrowserConfig()
		config.docker_name = AIStudioConfig.DEFAULT_DOCKER_CONTAINER
		config.headless = False
		config.user_data_dir = os.getenv("PROFILE_PATH", os.path.abspath("whoa/chatgpt_profile"))
	
		# Build additional docker flags dynamically
		additional_flags = []
		
		if self.folder_path:
			additional_flags.append(f'-v {self.folder_path}:/home/neko/Downloads')
		
		if self.policies_path:
			additional_flags.append(f'-v {self.policies_path}:/etc/opt/chrome/policies/managed/policies.json')
		
		# Join all flags with spaces
		config.additionl_docker_flag = ' '.join(additional_flags)
		return config
	
	def set_local_browser(self, executable_path: str = '/usr/bin/brave-browser', is_remote_debugging: bool = True, use_local_browser: bool = False):
		"""Configure to use local browser instead of Docker"""
		self.config.use_neko = not use_local_browser
		self.config.use_local_browser = use_local_browser
		if use_local_browser or not is_remote_debugging:
			self.config.browser_executable = executable_path
		self.config.is_remote_debugging = is_remote_debugging
	
	# --- Page Setup and Navigation ---

	def set_model(self, page):
		"""Set the Gemini model (2.5 Pro or fallback to 2.5 Flash)."""
		# Click the Bard mode menu button
		page.keyboard.press("Escape")
		page.wait_for_timeout(500)
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		page.wait_for_selector('div[data-test-id="bard-mode-menu-button"] button', state="visible")
		page.click('div[data-test-id="bard-mode-menu-button"] button')
		dropdown_panel = page.locator('#mat-menu-panel-0')
		if dropdown_panel.count() == 0:
			dropdown_panel = page.locator('.menu-inner-container')

		# Try selecting 2.5 Pro, fallback to 2.5 Flash if not found
		menu_clicked = False
		try:
			dropdown_panel.locator("text=2.5 Pro").wait_for(state="visible", timeout=3000)
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			dropdown_panel.locator("text=2.5 Pro").click()
			menu_clicked = True
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT*2)
			page.wait_for_selector(self.selectors.GEMINI_USER_PROMPT_TEXTAREA, state="visible", timeout=self.settings.DEFAULT_WAIT_TIMEOUT)
		except:
			if menu_clicked:
				page.click('div[data-test-id="bard-mode-menu-button"] button')
			dropdown_panel = page.locator('#mat-menu-panel-0')
			if dropdown_panel.count() == 0:
				dropdown_panel = page.locator('.menu-inner-container')
			dropdown_panel.locator("text=2.5 Flash").wait_for(state="visible")
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			dropdown_panel.locator("text=2.5 Flash").click()


	def navigate_to_new_chat(self, page) -> None:
		"""Navigate to AI Studio new chat page"""
		self.logger.info(f"Navigating to {self.settings.NEW_CHAT_URL}", "1")
		
		# Go to page, wait until no network connections for at least 500ms
		page.goto(
			self.settings.NEW_CHAT_URL,
			# wait_until="networkidle",
			timeout=600_000  # 10 minutes in milliseconds
		)
		
		# Keep your extra wait if needed
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT * 3)
		
		self._dismiss_popup(page)
		if self.use_gemini:
			self.set_model(page)
		self.logger.success("Navigation completed", "1")

	
	def _dismiss_popup(self, page) -> None:
		"""Dismiss any popup dialogs that might appear"""
		try:
			self.logger.debug("Attempting to dismiss popup...")
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			close_button = page.locator(self.selectors.CLOSE_BUTTON)
			if self.use_gemini:
				close_button = page.locator("button[data-test-id='close-button']")
			close_button.click(timeout=self.settings.DEFAULT_WAIT_TIMEOUT*2)
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			self.logger.debug("Popup dismissed successfully")
		except Exception as e:
			self.logger.debug(f"No popup to dismiss or dismissal failed: {e}")
	
	# --- Configuration Methods ---
	
	def configure_system_instructions(self, page, instruction_content: str) -> None:
		"""Set the system instruction in Google AI Studio"""
		self.logger.info("Configuring system instructions...", "2")
		
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
		page.locator(self.selectors.SYSTEM_INSTRUCTIONS_BUTTON).click()
		self.logger.debug("System instructions button clicked")
		
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
		page.locator(self.selectors.SYSTEM_INSTRUCTIONS_TEXTAREA).fill(instruction_content)
		self.logger.debug(f"System instructions filled ({len(instruction_content)} characters)")
		
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
		self.logger.success("System instructions configured", "2")
	
	def configure_user_prompt(self, page, prompt_content: str, system_instruction: str = None) -> None:
		"""Set the user prompt in Google AI Studio or Gemini."""
		self.logger.info("Configuring user prompt...", "3")
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)

		if self.use_gemini:
			# Fill in Gemini's rich-textarea
			prompt_textarea = page.locator(self.selectors.GEMINI_USER_PROMPT_TEXTAREA)

			prompt_textarea.fill(f"""System Instruction: {system_instruction}
User Prompt: {prompt_content}""")
		else:
			# AI Studio version
			prompt_textarea = page.locator(self.selectors.USER_PROMPT_TEXTAREA)
			prompt_textarea.fill(prompt_content)

		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
		self.logger.success("User prompt configured", "3")
	
	# --- File Upload Methods ---
	
	def upload_media_file(self, page, file_path: str, choose_file_via_xdotool) -> bool:
		"""Upload a media file using xdotool integration"""
		self.logger.info(f"Starting file upload: {file_path}", "4")
		
		if not self._validate_file_path(file_path):
			return False
		
		file_extension = Path(file_path).suffix.lower()
		
		# Step 4a: Click insert assets button
		self.logger.info("Clicking insert assets button...", "4a")
		page.locator(self.selectors.INSERT_ASSETS_BUTTON).click()
		page.wait_for_timeout(2000)
		self.logger.success("Insert assets button clicked", "4a")

		if self.is_remote_debugging:
			# Step 4b: Open file upload dialog
			self.logger.info("Opening file upload dialog...", "4b")
			page.locator(self.selectors.FILE_INPUT_MANUAL_UPLOAD).click()
			page.wait_for_timeout(3000)
			self.logger.success("File dialog opened", "4b")
		
		# Step 4c: Use xdotool to interact with dialog
		self.logger.info("Using xdotool to select file...", "4c")
		try:
			if not self.is_remote_debugging:
				file_input = page.locator("input[type='file']")
				file_input.set_input_files(file_path)
			else:
				choose_file_via_xdotool(file_path=file_path)
			self.logger.success("File selected via xdotool", "4c")
		except Exception as e:
			self.logger.error(f"xdotool file selection failed: {e}", "4c")
			return False
		
		# Step 4d: Handle copyright acknowledgment
		self.logger.info("Processing copyright acknowledgment...", "4d")
		self._acknowledge_copyright(page)
		self.logger.success("Copyright acknowledged", "4d")
		
		# Step 4e: Wait for upload completion
		self.logger.info("Waiting for upload completion...", "4e")
		self._wait_for_upload_completion(page, file_extension)
		self.logger.success("Upload completed", "4e")
		
		# Step 4f: Close dialogs
		self.logger.info("Closing upload dialogs...", "4f")
		page.keyboard.press("Escape")
		page.wait_for_timeout(500)
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		self.logger.success("Dialogs closed", "4f")
		
		self.logger.success(f"File uploaded successfully: {file_path}", "4")
		return True
	
	def _validate_file_path(self, file_path: str) -> bool:
		"""Validate that the file path is provided and accessible"""
		if not file_path:
			self.logger.error("File path is empty")
			return False
		
		# Note: We can't check if file exists since it's inside Docker container
		# Just validate the path format
		if not isinstance(file_path, str) or len(file_path.strip()) == 0:
			self.logger.error("Invalid file path format")
			return False
		
		return True
	
	def _acknowledge_copyright(self, page) -> None:
		"""Acknowledge copyright notice if it appears"""
		try:
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			acknowledge_button = page.locator(self.selectors.COPYRIGHT_ACKNOWLEDGE_BUTTON)
			acknowledge_button.click(timeout=self.settings.DEFAULT_WAIT_TIMEOUT * 2)
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			self.logger.debug("Copyright acknowledgment clicked")
		except Exception as e:
			self.logger.debug(f"No copyright dialog to acknowledge: {e}")
	
	def _wait_for_upload_completion(self, page, file_extension: str) -> None:
		"""Wait for upload completion based on file type"""
		self.logger.debug(f"Waiting for upload completion for file type: {file_extension}")
		
		removal_selector = self.selectors.FILE_TYPE_REMOVAL_SELECTORS.get(file_extension)
		if not removal_selector:
			self.logger.warning(f"Unknown file type: {file_extension}. Using fallback wait.")
			page.wait_for_timeout(3000)
			return
		
		try:
			page.wait_for_selector(removal_selector, timeout=self.settings.UPLOAD_TIMEOUT)
			self.logger.debug(f"Upload confirmed via element: {removal_selector}")
		except Exception as e:
			self.logger.warning(f"Could not detect confirmation for {file_extension}: {e}")

	def _get_url(self, page):
		if not self.use_gemini:
			self.configure_user_prompt(page, ".")
		return page.url

	# --- Generation and Execution ---
	
	def execute_generation(self, page) -> None:
		"""Execute the AI generation process."""
		from playwright.sync_api import expect

		self.logger.info("Starting AI generation...", "5")

		if self.use_gemini:
			# Gemini.com send workflow
			send_button = page.locator('button[aria-label="Send message"]')
			stop_button_selector = 'button[aria-label="Stop response"]'

			# Wait until send button is enabled
			self.logger.info("Waiting for send button to be enabled...", "5a")
			expect(send_button).to_be_enabled(timeout=self.settings.RUN_TIMEOUT)
			self.logger.success("Send button is enabled", "5a")

			# Click send
			self.logger.info("Clicking send button...", "5b")
			send_button.click()
			self.logger.success("Send button clicked", "5b")

			# Wait until stop button disappears (response finished)
			self.logger.info("Waiting for Gemini response to complete...", "5c")
			page.wait_for_selector(stop_button_selector, state="hidden", timeout=self.settings.RUN_TIMEOUT)
			self.logger.success("Gemini response completed", "5c")

		else:
			# AI Studio workflow
			run_button = page.locator(self.selectors.RUN_BUTTON)

			# Step 5a: Wait for run button to be enabled
			self.logger.info("Waiting for run button to be enabled...", "5a")
			expect(run_button).to_be_enabled(timeout=self.settings.RUN_TIMEOUT)
			self.logger.success("Run button is enabled", "5a")

			# Step 5b: Click run button
			self.logger.info("Clicking run button...", "5b")
			run_button.click()
			page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
			self.logger.success("Run button clicked", "5b")

			# Step 5c: Wait for generation to complete
			self.logger.info("Waiting for generation to complete...", "5c")
			expect(run_button).not_to_have_text("Stop", timeout=self.settings.RUN_TIMEOUT)
			self.logger.success("Generation completed", "5c")

		self.logger.success("AI generation finished", "5")

	
	# --- Result Extraction ---
	
	def extract_result(self, page) -> Union[Dict[str, Any], str]:
		"""Extract and parse the generated result"""
		self.logger.info("Extracting generation result...", "6")
		
		page.wait_for_timeout(self.settings.DEFAULT_WAIT_TIMEOUT)
		
		try:
			code_blocks = page.eval_on_selector_all(
				self.selectors.CODE_BLOCKS, 
				"elements => elements.map(e => e.innerText)"
			)
			
			if not code_blocks:
				self.logger.error("No code blocks found in response")
				raise Exception("No code blocks found.")
			
			last_code_content = code_blocks[-1]
			self.logger.debug(f"Found {len(code_blocks)} code blocks, using last one")
			
			# Try to parse as JSON
			try:
				parsed_data = json_repair.loads(last_code_content)
				self.logger.success(f"Successfully parsed JSON result", "6")
				self.logger.debug(f"Result preview: {str(parsed_data)}...")
				return parsed_data
			except Exception as json_error:
				self.logger.warning(f"Last code block is not valid JSON: {json_error}")
				self.logger.success(f"Returning raw text result", "6")
				return last_code_content
				
		except Exception as e:
			self.logger.error(f"Failed to extract result: {e}", "6")
			raise
	
	# --- Main Workflow ---
	
	def process_session(self, page, system_instruction: str, user_prompt: str, file_path: Optional[str] = None, choose_file_via_xdotool=None) -> Union[Dict[str, Any], str]:
		"""Execute the complete AI Studio workflow"""
		self.logger.info("=== Starting AI Studio Session ===")
		
		try:
			# Step 1: Navigate to new chat
			self.navigate_to_new_chat(page)
			if not self.use_gemini:
				# Step 2: Configure system instructions
				self.configure_system_instructions(page, system_instruction)
			
			# Step 3: Configure user prompt
			self.configure_user_prompt(page, user_prompt, system_instruction)
			
			# Step 4: Upload file if provided
			if not self.use_gemini:
				if file_path:
					if not self.upload_media_file(page, file_path, choose_file_via_xdotool):
						raise Exception("File upload failed")
			else: self.logger.warning("File path provided but no xdotool function available")
			
			# Step 5: Execute generation
			self.execute_generation(page)
			
			# Step 6: Extract result
			result = self.extract_result(page)

			url = self._get_url(page)
			
			self.logger.success("=== AI Studio Session Completed Successfully ===")
			return result, url
			
		except Exception as e:
			self.logger.error(f"Session failed: {str(e)}")
			raise
	
	# --- Public Interface ---
	
	def generate(self, system_instruction: str, user_prompt: str, file_path: Optional[str] = None, browser_manager: Optional[BrowserManager] = None, use_local_browser: bool = False, is_remote_debugging: bool = True) -> Optional[Union[Dict[str, Any], str]]:
		"""
		Execute a complete AI Studio generation workflow
		
		Args:
			system_instruction: The system instruction to use
			user_prompt: The user prompt to send
			file_path: Optional path to file to upload (must be accessible in container)
			browser_manager: Optional existing browser manager instance
			use_local_browser: Whether to use local browser instead of Docker
			
		Returns:
			The generated response, parsed as JSON if possible, None if failed
		"""
		try:
			self.use_local_browser = use_local_browser
			self.is_remote_debugging = is_remote_debugging
			self.set_local_browser(use_local_browser=use_local_browser, is_remote_debugging=is_remote_debugging)
			
			if not browser_manager:
				# Create new browser manager for this session
				browser_manager = BrowserManager(self.config)
				if use_local_browser or not is_remote_debugging:
					choose_file_via_xdotool = None
				else:
					choose_file_via_xdotool = partial(
						browser_manager.launcher.choose_file_via_xdotool, 
						config=self.config
					)
				
				with browser_manager as page:
					result, url = self.process_session(
						page, system_instruction, user_prompt, file_path, choose_file_via_xdotool
					)
			else:
				# Use existing browser manager
				page = browser_manager.new_page()
				if use_local_browser or not is_remote_debugging:
					choose_file_via_xdotool = None
				else:
					choose_file_via_xdotool = partial(
						browser_manager.launcher.choose_file_via_xdotool, 
						config=self.config
					)
				try:
					# Note: choose_file_via_xdotool needs to be provided externally in this case
					result, url = self.process_session(
						page, system_instruction, user_prompt, file_path, choose_file_via_xdotool
					)
				finally:
					page.close()
			
			return result, url
			
		except Exception as e:
			self.logger.error(f"Generation workflow failed: {str(e)}")
			return None, None


# --- Convenience Functions ---

def run_gemini_generation(system_instruction: str, user_prompt: str, url: str = None, file_path: Optional[str] = None, browser_manager: Optional[BrowserManager] = None, use_local_browser: bool = False, policies_path: str = None, folder_path: str = None, use_gemini: bool = False, is_remote_debugging: bool = True, config: BrowserConfig = None) -> Optional[Union[Dict[str, Any], str]]:
	"""
	Convenience function for running AI Studio generation
	
	Args:
		system_instruction: The system instruction to use
		user_prompt: The user prompt to send
		file_path: Optional path to file to upload
		browser_manager: Optional existing browser manager instance
		use_local_browser: Whether to use local browser instead of Docker
		
	Returns:
		The generated response, parsed as JSON if possible
	"""
	automation = AIStudioAutomation(config=config, url=url, policies_path=policies_path, folder_path=folder_path, use_gemini=use_gemini)
	return automation.generate(
		system_instruction=system_instruction,
		user_prompt=user_prompt,
		file_path=file_path,
		browser_manager=browser_manager,
		use_local_browser=use_local_browser,
		is_remote_debugging=is_remote_debugging
	)


# --- Example Usage ---

if __name__ == "__main__":
	# Example usage with detailed logging
	DEFAULT_SYSTEM_INSTRUCTION = """Tell me about Goku and give me in json format

Provide your response in this exact JSON structure:

```json
{
  "data": "Your 1-minute recap content here, exactly 150-175 words that capture the essential story in an engaging, speech-optimized format."
}
```
"""
	
	DEFAULT_USER_PROMPT = "Goku goal."
	
	result, url = run_gemini_generation(
		system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
		user_prompt=DEFAULT_USER_PROMPT,
		use_gemini=True
	)
	
	print("\n" + "="*50)
	print("FINAL RESULT:")
	print("="*50)
	print(result)
	print(url)
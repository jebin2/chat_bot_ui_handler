from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
from custom_logger import logger_config
from gemiwrap.utils import compress_image
import os
import traceback
from chat_bot_ui_handler import utils

def search_google_ai_mode(user_prompt, system_prompt=None, file_path=None, config=None):
	try:
		config = config or BrowserConfig()
		config.docker_name = "search_google_ai_mode"
		full_prompt = user_prompt
		if system_prompt:
			full_prompt = f"SYSTEM INSTRUCTIONS:: {system_prompt}\n\nUSER PROMPT{user_prompt}"

		with BrowserManager(config) as page:
			try:
				url = "https://www.google.com/"
				logger_config.info(f"Loading URL: {url}")
				page.goto(url, wait_until='domcontentloaded')
				logger_config.info("Page loaded successfully, waiting 5s for content...")
				page.wait_for_timeout(5000)
				utils.save_screenshot(page)

				logger_config.info("Locating 'AI Mode' button...")
				ai_button = page.locator("button:has-text('AI Mode')").first
				ai_button.click()
				logger_config.info("'AI Mode' button clicked")
				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				if file_path:
					file_path = os.path.abspath(compress_image(file_path))
					logger_config.info(f"Uploading file: {file_path}")
					file_input = page.locator('button[aria-label="Upload image"] input[type="file"]').first
					file_input.set_input_files(file_path)
					logger_config.info("File uploaded successfully")
					page.wait_for_timeout(5000)
					utils.save_screenshot(page)

				logger_config.info("Filling user prompt into textarea...")
				textarea = page.locator("textarea").first
				textarea.fill(full_prompt)
				logger_config.info("Prompt filled successfully")

				page.wait_for_timeout(2000)

				logger_config.info("Clicking 'Send' button...")
				send_button = page.locator('button[aria-label="Send"]').first
				send_button.click()
				logger_config.info("'Send' button clicked")

				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				logger_config.info("Waiting for results in 'main-col' container...")
				page.wait_for_selector('div[data-container-id="main-col"]', timeout=15000)
				page.wait_for_timeout(2000)

				result_text = page.locator('div[data-container-id="main-col"]').last.inner_text()
				result_text = result_text[:result_text.index("AI responses may include mistakes")]
				logger_config.info("Result fetched successfully")
				print("Result:", result_text)

				utils.save_screenshot(page)
				return result_text

			except Exception as e:
				logger_config.error(f"Error during search_google_ai_mode: {e} {traceback.format_exc()}")
				try:
					utils.save_screenshot(page)
				except:
					pass
	except: pass

	return None

if __name__ == "__main__":
	search_google_ai_mode(
		user_prompt = (
			"Describe what is happening in this video frame as if you're telling a story. "
			"Focus on the main subjects, their actions, the setting, and any important "
			"details that would help someone understand the scene's context. "
			"Max word: 100 ONLY"
		),
		file_path = "test.png"
	)

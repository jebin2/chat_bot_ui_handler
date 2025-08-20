from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
from custom_logger import logger_config
from gemiwrap.utils import compress_image
import os
import traceback
from chat_bot_ui_handler import utils

def set_model(page):
		"""Set the Gemini model (2.5 Pro or fallback to 2.5 Flash)."""
		# Click the Bard mode menu button
		page.keyboard.press("Escape")
		page.wait_for_timeout(500)
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		page.wait_for_selector('div[data-test-id="bard-mode-menu-button"] button', state="visible")
		page.click('div[data-test-id="bard-mode-menu-button"] button')
		dropdown_panel = page.locator('#mat-menu-panel-0')
		utils.save_screenshot(page)

		# Try selecting 2.5 Pro, fallback to 2.5 Flash if not found
		menu_clicked = False
		try:
			dropdown_panel.locator("text=2.5 Pro").wait_for(state="visible", timeout=3000)
			page.wait_for_timeout(2000)
			utils.save_screenshot(page)
			dropdown_panel.locator("text=2.5 Pro").click()
			menu_clicked = True
			utils.save_screenshot(page)
			page.wait_for_timeout(2000)
			page.wait_for_selector('rich-textarea div.ql-editor[contenteditable="true"]', state="visible", timeout=2000)
			utils.save_screenshot(page)
		except:
			if menu_clicked:
				page.click('div[data-test-id="bard-mode-menu-button"] button')
				utils.save_screenshot(page)
			dropdown_panel = page.locator('#mat-menu-panel-0')
			dropdown_panel.locator("text=2.5 Flash").wait_for(state="visible")
			page.wait_for_timeout(2000)
			utils.save_screenshot(page)
			dropdown_panel.locator("text=2.5 Flash").click()
			utils.save_screenshot(page)

def gemini_ui_chat(user_prompt, system_prompt=None, file_path=None, config=None):
	try:
		config = config or BrowserConfig()
		config.docker_name = "gemini_ui_chat"
		full_prompt = user_prompt
		if system_prompt:
			full_prompt = f"SYSTEM INSTRUCTIONS:: {system_prompt}\n\nUSER PROMPT{user_prompt}"

		with BrowserManager(config) as page:
			try:
				url = "https://gemini.google.com/"
				logger_config.info(f"Loading URL: {url}")
				page.goto(url, wait_until='domcontentloaded')
				logger_config.info("Page loaded successfully, waiting 5s for content...")
				page.wait_for_timeout(5000)
				utils.save_screenshot(page)
				set_model(page)

				if file_path:
					page.locator('button[aria-label="Open upload file menu"]').click()
					page.wait_for_timeout(1000)
					utils.save_screenshot(page)
					page.locator('[data-test-id="local-image-file-uploader-button"]').click()
					page.wait_for_timeout(1000)
					utils.save_screenshot(page)

					file_path = os.path.abspath(compress_image(file_path))
					logger_config.info(f"Uploading file: {file_path}")
					file_input = page.locator("input[type='file']").first
					file_input.wait_for(state="attached", timeout=5000)
					file_input.set_input_files(file_path)
					logger_config.info("File uploaded successfully")
					page.wait_for_timeout(5000)
					os.remove(file_path)
					utils.save_screenshot(page)

				logger_config.info("Filling user prompt into input...")
				input = page.locator('rich-textarea div.ql-editor[contenteditable="true"]').first
				input.fill(full_prompt)
				logger_config.info("Prompt filled successfully")
				page.wait_for_timeout(1000)
				utils.save_screenshot(page)

				logger_config.info("Clicking 'Send' button...")
				send_button = page.locator('button[aria-label="Send message"]')
				send_button.click()
				logger_config.info("'Send' button clicked")
				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				logger_config.info("Waiting for results in '#send-message-button' container...")
				page.wait_for_selector('button[aria-label="Stop response"]', state="hidden", timeout=20000)
				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				result_text = page.locator('message-content').last.inner_text()
				logger_config.info("Result fetched successfully")
				print("Result:", result_text)

				utils.save_screenshot(page)
				return result_text

			except Exception as e:
				logger_config.error(f"Error during gemini_ui_chat: {e} {traceback.format_exc()}")
				try:
					utils.save_screenshot(page)
				except:
					pass
	except: pass

	return None

if __name__ == "__main__":
	config = BrowserConfig()
	config.user_data_dir = os.getenv("PROFILE_PATH", None)
	gemini_ui_chat(
		user_prompt = (
			"Describe what is happening in this video frame as if you're telling a story. "
			"Focus on the main subjects, their actions, the setting, and any important "
			"details that would help someone understand the scene's context. "
			"Max word: 100 ONLY"
		),
		file_path = "test.png",
		config=config
	)
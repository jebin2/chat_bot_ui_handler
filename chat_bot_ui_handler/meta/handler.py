from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
from custom_logger import logger_config
from gemiwrap.utils import compress_image
import os
import traceback
from chat_bot_ui_handler import utils
from playwright.sync_api import expect
from functools import partial

def meta_ui_chat(user_prompt, system_prompt=None, file_path=None, config=None):
	try:
		config = config or BrowserConfig()
		config.docker_name = "meta_ui_chat"
		additional_flags = []
		
		additional_flags.append(f'-v {os.getcwd()}/{os.getenv("TEMP_OUTPUT", "chat_bot_ui_handler_logs")}:/home/neko/Downloads')
		
		additional_flags.append(f'-v /home/jebineinstein/git/browser_manager/policies.json:/etc/opt/chrome/policies/managed/policies.json')
		
		# Join all flags with spaces
		config.additionl_docker_flag = ' '.join(additional_flags)
		full_prompt = user_prompt
		if system_prompt:
			full_prompt = f"SYSTEM INSTRUCTIONS:: {system_prompt}\n\nUSER PROMPT{user_prompt}"

		browser_manager = BrowserManager(config)
		choose_file_via_xdotool = partial(
			browser_manager.launcher.choose_file_via_xdotool, 
			config=config
		)

		with browser_manager as page:
			try:
				url = "https://www.meta.ai"
				logger_config.info(f"Loading URL: {url}")
				page.goto(url, wait_until='domcontentloaded')
				# import time
				# time.sleep(1000000)
				logger_config.info("Page loaded successfully, waiting 5s for content...")
				page.wait_for_timeout(5000)
				utils.save_screenshot(page)

				if file_path:
					page.locator('div[aria-label="Attach a file or edit a video"]').click()
					page.wait_for_timeout(1000)
					utils.save_screenshot(page)
					page.locator('div[role="menuitem"]').last.click()
					page.wait_for_timeout(1000)
					utils.save_screenshot(page)
					page.locator('div[aria-label="Attach a file or edit a video"]').click()

					cur_path = compress_image(file_path)
					file_path = os.path.abspath(cur_path)
					logger_config.info(f"Uploading file: {f'/home/neko/Downloads/{os.path.basename(cur_path)}'}")
					choose_file_via_xdotool(file_path=f'/home/neko/Downloads/{os.path.basename(cur_path)}')

					logger_config.info("File uploaded successfully")
					page.wait_for_timeout(5000)
					utils.save_screenshot(page)

				logger_config.info("Filling user prompt into input...")
				input = page.locator('div[role="textbox"]').first
				input.clear()
				page.wait_for_timeout(2000)
				input.fill(full_prompt)
				logger_config.info("Prompt filled successfully")
				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				logger_config.info("Clicking 'Send' button...")
				send_button = page.locator('div[aria-label="Send message"]')
				expect(send_button).to_be_enabled(timeout=20000)
				send_button.click()
				logger_config.info("'Send' button clicked")
				page.wait_for_timeout(2000)
				utils.save_screenshot(page)

				logger_config.info("Waiting for results in 'div[aria-label=\"Send message\"]' container...")
				page.wait_for_selector('div[aria-label="Send message"]', timeout=15000)
				page.wait_for_timeout(2000)

				result_text = page.locator('div[dir="auto"]').last.inner_text()
				logger_config.info("Result fetched successfully")
				print("Result:", result_text)

				utils.save_screenshot(page)
				return result_text

			except Exception as e:
				logger_config.error(f"Error during meta_ui_chat: {e} {traceback.format_exc()}")
				try:
					utils.save_screenshot(page)
				except:
					pass
	except: pass

	return None

if __name__ == "__main__":
	config = BrowserConfig()
	config.user_data_dir = os.getenv("PROFILE_PATH", None)
	meta_ui_chat(
		user_prompt = (
			"Describe what is happening in this video frame as if you're telling a story. "
			"Focus on the main subjects, their actions, the setting, and any important "
			"details that would help someone understand the scene's context. "
			"Max word: 100 ONLY"
		),
		file_path = "test.png",
		config=config
	)
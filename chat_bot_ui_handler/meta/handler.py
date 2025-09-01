from functools import partial
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
import os

class MetaUIChat(BaseUIChat):
	def __init__(self, config=None):
		super().__init__(config)
		# Set up additional docker flags
		# additional_flags = []
		# additional_flags.append(f'-v {os.getcwd()}/{os.getenv("TEMP_OUTPUT", "chat_bot_ui_handler_logs")}:/home/neko/Downloads')
		# additional_flags.append(f'-v {os.getenv("POLICY_PATH", "POLICY_PATH")}:/etc/opt/chrome/policies/managed/policies.json')
		# self.config.additionl_docker_flag = ' '.join(additional_flags)

	def get_docker_name(self):
		return "meta_ui_chat"

	def get_url(self):
		return "https://www.meta.ai"

	def get_selectors(self):
		return {
			'input': 'div[role="textbox"]',
			'send_button': 'div[aria-label="Send message"]',
			'wait_selector': 'div[aria-label="Send message"]',
			'result': 'div[dir="auto"]'
		}

	def show_input_file_tag(self, page):
		"""Custom file upload for Meta AI using xdotool"""
		page.locator('div[aria-label="Attach a file or edit a video"]').click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('div[role="menuitem"]').last.click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('div[aria-label="Attach a file or edit a video"]').click()

	def upload_file(self, page, file_path):
		if file_path:
			self.show_input_file_tag(page)

			logger_config.info(f"Uploading file: {file_path}")
			
			# Use xdotool for file selection
			choose_file_via_xdotool = partial(
				self.get_browser_manager().launcher.choose_file_via_xdotool, 
				config=self.config
			)
			choose_file_via_xdotool(file_path=file_path)

			logger_config.info("File uploaded successfully")
			page.wait_for_timeout(5000)
			self.save_screenshot(page)
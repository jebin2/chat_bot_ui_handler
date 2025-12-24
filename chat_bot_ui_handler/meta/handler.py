from functools import partial
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
import os

class MetaUIChat(BaseUIChat):
	def __init__(self, config=None):
		super().__init__(config)

	def get_docker_name(self):
		return f"{self.config.docker_name}_meta_ui_chat"

	def get_url(self):
		return "https://www.meta.ai"

	def get_selectors(self):
		return {
			'input': 'div[role="textbox"]',
			'send_button': 'div[aria-label="Send"]',
			'wait_selector': 'div[aria-label="Add media and more"] [aria-disabled="true"]',
			'result': 'div[dir="auto"]'
		}

	def show_input_file_tag(self, page):
		"""Custom file upload for Meta AI using xdotool"""
		page.locator('div[aria-label="Add media and more"]').first.click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('div[role="menuitem"]:has-text("Add")').first.click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('div[aria-label="Add media and more"]').first.click()

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

	def wait_for_selector(self, page):
		page.wait_for_function('''
			() => {
				const element = document.querySelector("div[aria-label='Add media and more']");
				return element && (element.getAttribute('aria-disabled') === 'false' || !element.hasAttribute('aria-disabled'));
			}
		''', timeout=10000)

	def get_response_text(self, page):
		selectors = self.get_selectors()
		return page.locator(selectors['result']).first.inner_text()
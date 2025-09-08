from functools import partial
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
import os
from playwright.sync_api import expect

class AIStudioUIChat(BaseUIChat):
	def __init__(self, config=None):
		super().__init__(config)

	def get_docker_name(self):
		return f"{self.config.docker_name}_aistudio_ui_handler"

	def get_url(self):
		return "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-pro"

	def get_selectors(self):
		return {
			'input': 'div.text-input-wrapper textarea',
			'send_button': 'button[type="submit"]',
			'wait_selector': 'button[type="submit"]',
			'result': 'ms-chat-turn div[data-turn-role="Model"]'
		}

	def _dismiss_popup(self, page):
		"""Dismiss any popup dialogs that might appear"""
		try:
			self.save_screenshot(page)
			page.wait_for_timeout(2000)
			close_button = page.locator('button[aria-label="close"]')
			close_button.click(timeout=4000)
			page.wait_for_timeout(2000)
			self.save_screenshot(page)
		except:
			pass

	def _acknowledge_copyright(self, page) -> None:
		"""Acknowledge copyright notice if it appears"""
		try:
			self.save_screenshot(page)
			page.wait_for_timeout(2000)
			acknowledge_button = page.locator('button[aria-label="Agree to the copyright acknowledgement"]')
			acknowledge_button.click(timeout=2000)
			page.wait_for_timeout(2000)
			self.save_screenshot(page)
		except Exception as e:
			logger_config.debug(f"No copyright dialog to acknowledge: {e}")

	def login(self, page):
		"""Handle initial setup after page load"""
		self._dismiss_popup(page)

	def configure_system_instructions(self, page, system_prompt):
		"""Configure system instructions in AI Studio"""
		self.save_screenshot(page)
		page.wait_for_timeout(2000)
		page.locator('button[aria-label="System instructions"]').click()
		page.wait_for_timeout(2000)
		page.locator('textarea[aria-label="System instructions"]').fill(system_prompt)
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def upload_file(self, page, file_path):
		if file_path:
			logger_config.info(f"Uploading file: {file_path}")

			page.locator('button[aria-label="Insert assets such as images, videos, files, or audio"]').click()
			page.wait_for_timeout(2000)
			self.save_screenshot(page)

			page.locator('button[aria-label="Upload File"]').click()
			page.wait_for_timeout(3000)
			self.save_screenshot(page)

			# Use xdotool for file selection
			choose_file_via_xdotool = partial(
				self.get_browser_manager().launcher.choose_file_via_xdotool, 
				config=self.config
			)
			choose_file_via_xdotool(file_path=file_path)
			self.save_screenshot(page)
			self._acknowledge_copyright(page)
			self.save_screenshot(page)
			logger_config.info("File uploaded successfully")
			page.wait_for_timeout(5000)
			self.save_screenshot(page)
			# Wait for upload completion (look for remove buttons)
			file_extension = os.path.splitext(file_path)[1].lower()
			removal_selectors = {
				".mp4": 'button[aria-label="Remove video"]',
				".mov": 'button[aria-label="Remove video"]',
				".jpg": 'button[aria-label="Remove image"]',
				".jpeg": 'button[aria-label="Remove image"]',
				".png": 'button[aria-label="Remove image"]',
				".pdf": 'button[aria-label="Remove document"]',
			}

			removal_selector = removal_selectors.get(file_extension)
			if removal_selector:
				try:
					page.wait_for_selector(removal_selector, timeout=20000)
				except:
					pass

			# Close dialogs
			page.keyboard.press("Escape")
			page.wait_for_timeout(500)
			page.keyboard.press("Escape")
			page.wait_for_timeout(1000)

	def fill_prompt(self, page, user_prompt, system_prompt=None):
		if system_prompt:
			self.configure_system_instructions(page, system_prompt)

		selectors = self.get_selectors()
		logger_config.info("Filling user prompt into input...")
		input_field = page.locator(selectors['input']).first
		input_field.fill(user_prompt)
		logger_config.info("Prompt filled successfully")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

		for _ in range(20):
			try:
				page.wait_for_selector(selectors['wait_selector'], timeout=10000)
				break
			except: pass
		self.save_screenshot(page)

	def send(self, page):
		selectors = self.get_selectors()
		logger_config.info("Clicking 'Send' button...")
		send_button = page.locator(selectors['send_button']).first
		expect(send_button).to_be_enabled(timeout=10 * 60 * 1000)
		send_button.click(force=True)
		logger_config.info("'Send' button clicked")
		page.wait_for_timeout(2000)
		# send_button.click()
		self.save_screenshot(page)

	def add_wait_res(self, page):
		page.wait_for_timeout(180000)

	def get_response(self, page):
		self.save_screenshot(page)
		selectors = self.get_selectors()

		logger_config.info(f"Waiting for results in 'not_to_have_text text Stop' container...")
		for _ in range(20):
			try:
				page.wait_for_selector(selectors['wait_selector'], timeout=10000)
				break
			except: pass
		page.wait_for_timeout(20000) # wait for 20s
		self.save_screenshot(page)

		result_text = page.locator(selectors['result']).last.inner_text()
		result_text = self.post_process_response(result_text)
		logger_config.info("Result fetched successfully")
		print("Result:", result_text)
		self.save_screenshot(page)
		return result_text
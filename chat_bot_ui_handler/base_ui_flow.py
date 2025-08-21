from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
from custom_logger import logger_config
from gemiwrap.utils import compress_image
import os
import traceback
from abc import ABC, abstractmethod


class BaseUIChat(ABC):
	def __init__(self, config=None):
		self.config = config or BrowserConfig()
		self.config.docker_name = self.get_docker_name()
		self.compressed_path = None

	@abstractmethod
	def get_docker_name(self):
		"""Return the docker name for this chat handler"""
		pass

	@abstractmethod
	def get_url(self):
		"""Return the URL to navigate to"""
		pass

	@abstractmethod
	def get_selectors(self):
		"""Return a dict with required selectors"""
		pass

	def load_url(self, page):
		# Navigate to URL
		url = self.get_url()
		logger_config.info(f"Loading URL: {url}")
		page.goto(url, wait_until='domcontentloaded')
		logger_config.info("Page loaded successfully, waiting 5s for content...")
		page.wait_for_timeout(5000)
		self.save_screenshot(page)

	def login(self, page):
		"""Override this method if login is required"""
		pass

	def upload_file(self, page, file_path):
		if file_path:
			self.compressed_path = os.path.abspath(compress_image(file_path))
			logger_config.info(f"Uploading file: {self.compressed_path}")
			file_input = page.locator('input[type="file"]').first
			file_input.set_input_files(self.compressed_path)
			logger_config.info("File uploaded successfully")
			page.wait_for_timeout(5000)
			self.save_screenshot(page)

	def fill_prompt(self, page, user_prompt, system_prompt=None):
		full_prompt = user_prompt
		if system_prompt:
			full_prompt = f"SYSTEM INSTRUCTIONS:: {system_prompt}\n\nUSER PROMPT{user_prompt}"

		selectors = self.get_selectors()
		logger_config.info("Filling user prompt into input...")
		input_field = page.locator(selectors['input']).first
		input_field.fill(full_prompt)
		logger_config.info("Prompt filled successfully")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def send(self, page):
		selectors = self.get_selectors()
		logger_config.info("Clicking 'Send' button...")
		send_button = page.locator(selectors['send_button']).first
		send_button.click()
		logger_config.info("'Send' button clicked")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def get_response(self, page):
		selectors = self.get_selectors()
		logger_config.info(f"Waiting for results in '{selectors['wait_selector']}' container...")
		page.wait_for_selector(selectors['wait_selector'], timeout=15000)
		page.wait_for_timeout(2000)

		result_text = page.locator(selectors['result']).last.inner_text()
		logger_config.info("Result fetched successfully")
		print("Result:", result_text)
		self.save_screenshot(page)
		return result_text

	def save_screenshot(self, page):
		"""Override to customize screenshot naming"""
		folder = os.getenv("TEMP_OUTPUT", "chat_bot_ui_handler_logs")
		if not os.path.exists(folder):
			os.mkdir(folder)
		page.screenshot(path=f"chat_bot_ui_handler_logs/{self.get_docker_name()}.png")

	def chat(self, user_prompt, system_prompt=None, file_path=None):
		try:
			with BrowserManager(self.config) as page:
				try:
					self.load_url(page)

					self.login(page)

					self.upload_file(page, file_path)

					self.fill_prompt(page, user_prompt, system_prompt)

					self.send(page)

					return self.get_response(page)

				except Exception as e:
					logger_config.error(f"Error during {self.get_docker_name()}: {e} {traceback.format_exc()}")
					try:
						self.save_screenshot(page)
					except:
						pass
				finally:
					if self.compressed_path:
						os.remove(self.compressed_path)
		except:
			pass
		finally:
			if self.compressed_path:
				os.remove(self.compressed_path)

		return None
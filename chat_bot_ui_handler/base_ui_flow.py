from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig
from custom_logger import logger_config
import os
import traceback
from abc import ABC, abstractmethod
import json

class BaseUIChat(ABC):
	def __init__(self, config=None):
		self.config = config or BrowserConfig()
		self.config.docker_name = self.get_docker_name()
		if not self.config.user_data_dir:
			self.config.user_data_dir = os.path.expanduser(f'~/.{self.__class__.__name__.lower()}')
			os.makedirs(self.config.user_data_dir, exist_ok=True)

		self.browser_manager = None

	def get_browser_manager(self):
		if not self.browser_manager:
			self.browser_manager = BrowserManager(self.config)

		return self.browser_manager

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
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		self.save_screenshot(page)

	def force_click(self, page, selector: str):
		el = page.locator(selector)
		if el.count() == 0:
			raise Exception(f"Element not found: {selector}")

		pointer_events = el.evaluate("el => getComputedStyle(el).pointerEvents")
		print(pointer_events)
		if pointer_events == "none":
			el.evaluate("el => el.style.pointerEvents = 'auto'")

		el.click(force=True)

	def login(self, page):
		"""Override this method if login is required"""
		pass

	def show_input_file_tag(self, page):
		"""Override this method if show_input_file_tag is required"""
		pass

	def upload_file(self, page, file_path):
		if file_path:
			self.show_input_file_tag(page)

			selectors = self.get_selectors()
			logger_config.info(f"Uploading file: {file_path}")

			file_input = page.locator(selectors.get("input_file", 'input[type="file"]')).first
			file_input.wait_for(state="attached", timeout=5000)
			file_input.set_input_files(file_path)
			page.wait_for_timeout(5000)
			input_file_wait_selector = selectors.get("input_file_wait_selector", None)
			if input_file_wait_selector:
				page.wait_for_selector(input_file_wait_selector, timeout=15000)
				page.wait_for_timeout(1000)
			logger_config.info("File uploaded successfully")

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

	def post_process_response(self, result):
		return result

	def wait_for_generation(self, page):
		selectors = self.get_selectors()
		logger_config.info(f"Waiting for results in '{selectors['wait_selector']}' container...")
		for _ in range(20):
			try:
				page.wait_for_selector(selectors['wait_selector'], timeout=10000)
				break
			except: pass
		self.add_wait_res(page)

	def add_wait_res(self, page):
		page.wait_for_timeout(10000)

	def get_response(self, page):
		selectors = self.get_selectors()
		result_text = page.locator(selectors['result']).last.inner_text()
		result_text = self.post_process_response(result_text)
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

	def process(self, page, user_prompt, system_prompt, file_path):
		try:
			self.load_url(page)

			self.login(page)

			self.upload_file(page, file_path)

			self.fill_prompt(page, user_prompt, system_prompt)

			self.send(page)

			self.wait_for_generation(page)

			return self.get_response(page)

		except Exception as e:
			logger_config.error(f"Error during {self.get_docker_name()}: {e} {traceback.format_exc()}")
			try:
				self.save_screenshot(page)
			except:
				pass

	def quick_chat(self, user_prompt, system_prompt=None, file_path=None):
		try:
			with self.get_browser_manager() as page:
				return self.process(page, user_prompt, system_prompt, file_path)
		except:
			pass

		return None

	def chat(self, user_prompt, system_prompt=None, file_path=None):
		try:
			page = self.get_browser_manager().start()
			return self.process(page, user_prompt, system_prompt, file_path)
		except:
			pass

		return None

	def cleanup(self):
		if self.browser_manager:
			try:
				self.browser_manager.stop()
			except Exception as e:
				logger_config.error(f"Error while stopping browser manager: {e}")
			finally:
				self.browser_manager = None

	def __del__(self) -> None:
		"""Destructor cleanup."""
		try:
			self.cleanup()
		except: pass

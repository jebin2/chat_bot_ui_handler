from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
import os
import time

class GeminiUIChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_gemini_ui_chat"

	def need_google_login(self):
		return True

	def get_url(self):
		return "https://gemini.google.com/"

	def get_selectors(self):
		return {
			'input': 'rich-textarea div.ql-editor[contenteditable="true"]',
			'send_button': 'button[aria-label="Send message"]',
			'wait_selector': 'message-content',
			'result': 'message-content'
		}

	def login(self, page):
		"""No model to pick — the default one is used, so just wait for the input."""
		page.keyboard.press("Escape")
		page.wait_for_timeout(500)
		page.wait_for_selector(self.get_selectors()['input'], state="visible", timeout=30000)
		self.save_screenshot(page)

	def upload_file(self, page, file_path):
		"""The upload button opens a native file chooser instead of exposing an
		input[type=file], so the file has to be handed to the chooser event."""
		if not file_path:
			return

		self.logger.info(f"Uploading file: {file_path}")
		page.locator('button[aria-label="Upload & tools"]').click(force=True)
		page.wait_for_timeout(1000)
		self.save_screenshot(page)

		with page.expect_file_chooser() as fc_info:
			page.locator('button[data-test-id="local-images-files-uploader-button"]').click(force=True)
		fc_info.value.set_files(file_path)

		page.wait_for_timeout(5000)
		self.logger.info("File uploaded successfully")
		self.save_screenshot(page)

	def wait_for_generation(self, page):
		"""Gemini shows a stop button while streaming; it disappears when done.
		Wait for that, then for the text to stop growing."""
		try: timeout = int(os.getenv("GEMINI_GENERATION_TIMEOUT") or 300)
		except Exception: timeout = 300

		deadline = time.monotonic() + timeout
		last_len = -1
		stable_checks = 0
		while time.monotonic() < deadline:
			state = page.evaluate("""() => ({
				generating: !!document.querySelector('button[aria-label="Stop response"]'),
				length: (document.querySelector('model-response') || {innerText: ''}).innerText.length,
			})""")

			if not state['generating'] and state['length'] > 0 and state['length'] == last_len:
				stable_checks += 1
				if stable_checks >= 2:
					self.logger.info("Response generation complete")
					self.save_screenshot(page)
					return
			else:
				stable_checks = 0

			last_len = state['length']
			self.logger.info(f"Waiting for response... {last_len} chars", overwrite=True)
			page.wait_for_timeout(2000)

		self.logger.error(f"Response did not settle within {timeout}s; using what is on screen")
		self.save_screenshot(page)
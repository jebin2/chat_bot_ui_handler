from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config

class GeminiUIChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_gemini_ui_chat"

	def get_url(self):
		return "https://gemini.google.com/"

	def get_selectors(self):
		return {
			'input': 'rich-textarea div.ql-editor[contenteditable="true"]',
			'send_button': 'button[aria-label="Send message"]',
			'wait_selector': 'message-content',
			'result': 'message-content'
		}

	def set_model(self, page):
		"""Set the Gemini model (2.5 Pro or fallback to 2.5 Flash)."""
		# Click the Bard mode menu button
		page.keyboard.press("Escape")
		page.wait_for_timeout(500)
		page.keyboard.press("Escape")
		page.wait_for_timeout(1000)
		try:
			page.wait_for_selector('div[data-test-id="bard-mode-menu-button"] button', state="visible")
		except: pass
		self.force_click(page, 'div[data-test-id="bard-mode-menu-button"] button')
		dropdown_panel = page.locator('.menu-inner-container')
		self.save_screenshot(page)
		page.wait_for_timeout(2000)

		# Locate all enabled buttons inside the menu container
		enabled_buttons = dropdown_panel.locator('button[aria-disabled="false"]')

		# Click the last one
		last_button = enabled_buttons.nth(enabled_buttons.count() - 1)
		last_button.click(force=True)
		self.save_screenshot(page)

	def login(self, page):
		"""Custom setup after page load - set model"""
		self.set_model(page)

	def show_input_file_tag(self, page):
		page.locator('button[aria-label="Open upload file menu"]').click(force=True)
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('[data-test-id="local-images-files-uploader-button"]').click(force=True)
		page.wait_for_timeout(1000)
		self.save_screenshot(page)

	def wait_for_selector(self, page):
		page.wait_for_function("""
			() => {
				const el = document.querySelectorAll('.avatar_spinner_animation')[0];
				return el && el.style.visibility === 'hidden';
			}
		""", timeout=10000)
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config

class GoogleAISearchChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_search_google_ai_mode"

	def get_url(self):
		return "https://www.google.com/"

	def get_selectors(self):
		return {
			# The menu holds two file inputs; this one's accept list covers
			# documents and images, so it serves every supported file type.
			'input': 'textarea',
			'input_file': 'input[type="file"][accept*="application/pdf"]',
			'wait_selector': 'div[data-container-id="main-col"]',
			'result': 'div[data-container-id="main-col"]'
		}

	def send(self, page):
		# The search box has no usable send control — its Send button stays
		# display:none — so submit from the input itself.
		# fill() leaves the box focused; the autocomplete overlay makes
		# locator.press() fail its actionability check, so drive the keyboard.
		self.logger.info("Submitting prompt with Enter...")
		page.locator(self.get_selectors()['input']).first.focus()
		page.keyboard.press("Enter")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def login(self, page):
		"""Enable AI Mode after page load"""
		self.logger.info("Locating 'AI Mode' button...")
		ai_button = page.locator("button:has-text('AI Mode')").first
		ai_button.click()
		self.logger.info("'AI Mode' button clicked")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def post_process_response(self, result):
		# Remove disclaimer text if present; the wording varies by rollout
		disclaimers = (
			"AI can make mistakes",
			"AI responses may include mistakes",
		)
		for disclaimer in disclaimers:
			if disclaimer in result:
				result = result[:result.index(disclaimer)]

		return result.strip()
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config

class GoogleAISearchChat(BaseUIChat):
	def get_docker_name(self):
		return "search_google_ai_mode"

	def get_url(self):
		return "https://www.google.com/"

	def get_selectors(self):
		return {
			'input': 'textarea',
			'input_file': 'button[aria-label="Upload image"] input[type="file"]',
			'send_button': 'button[aria-label="Send"]',
			'wait_selector': 'div[data-container-id="main-col"]',
			'result': 'div[data-container-id="main-col"]'
		}

	def login(self, page):
		"""Enable AI Mode after page load"""
		logger_config.info("Locating 'AI Mode' button...")
		ai_button = page.locator("button:has-text('AI Mode')").first
		ai_button.click()
		logger_config.info("'AI Mode' button clicked")
		page.wait_for_timeout(2000)
		self.save_screenshot(page)

	def post_process_response(self, result):
		# Remove disclaimer text if present
		if "AI responses may include mistakes" in result:
			result = result[:result.index("AI responses may include mistakes")]

		return result
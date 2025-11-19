from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config

class MistralUIChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_mistral_ui_chat"

	def get_url(self):
		return "https://chat.mistral.ai/chat"

	def get_selectors(self):
		return {
			'input': 'div[contenteditable="true"]',
			'input_file': 'div[role="dialog"] input[type="file"]',
			'send_button': 'button[type="submit"]',
			'wait_selector': 'div[data-message-part-type="answer"]',
			'result': 'div[data-message-part-type="answer"]'
		}

	def wait_for_generation(self, page):
		selectors = self.get_selectors()
		logger_config.info(f"Waiting for results in '{selectors['wait_selector']}' chat specific container...")
		page.wait_for_timeout(5000)
		page.wait_for_selector('button[aria-label="Voice Mode"]', timeout=30000)
		page.wait_for_timeout(1000)

	def show_input_file_tag(self, page):
		page.locator('button[aria-label="Add files"]').click()
		page.wait_for_timeout(5000)
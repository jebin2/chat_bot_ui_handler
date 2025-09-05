from chat_bot_ui_handler.base_ui_flow import BaseUIChat

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

	def add_wait_res(self, page):
		page.wait_for_timeout(1000)
		page.wait_for_selector('button[aria-label="Voice Mode"]', timeout=10000)

	def show_input_file_tag(self, page):
		page.locator('button[aria-label="Add files"]').click()
		page.wait_for_timeout(5000)
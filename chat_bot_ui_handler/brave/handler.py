from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class BraveAISearch(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_brave_ai_search"

	def get_url(self):
		return "https://search.brave.com/ask"

	def get_selectors(self):
		return {
			'input': '#tap-input-field',
			'input_file': 'input[type="file"]',
			'send_button': 'button[aria-label="Ask"]',
			'wait_selector': '.answering-label',
			'result': ".llm-output"
		}

	def wait_for_selector(self, page):
		page.wait_for_function("""
			() => {
				const el = document.querySelectorAll('.answering-label')[0];
				return el && el.innerText === 'Finished';
			}
		""", timeout=10000)
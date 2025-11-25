from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class DuckDuckGoAISearch(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_duck_duck_go_ai_search"

	def get_url(self):
		return "https://duckduckgo.com/?q=DuckDuckGo+AI+Chat&ia=chat&duckai=1"

	def login(self, page):
		page.wait_for_function("""
			() => {
				const el = document.querySelectorAll('div[role="presentation"] button')[0];
				if (el) {
					el.click();
					return false;
				} else {
					return true;
				}
			}
		""", timeout=10000)
		page.wait_for_timeout(2000)

	def get_selectors(self):
		return {
			'input': 'textarea[name="user-prompt"]',
			'input_file': 'input[type="file"]',
			'send_button': 'main button[type="submit"]',
			'result': 'main div[data-activeresponse="true"] p'
		}

	def wait_for_selector(self, page):
		page.wait_for_function("""
			() => {
				const el = document.querySelectorAll('main div[data-activeresponse="false"] span')[0];
				return !el;
			}
		""", timeout=10000)
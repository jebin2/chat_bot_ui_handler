from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class BingUIChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_bing_ui_chat"

	def get_url(self):
		return "https://www.bing.com/images"

	def get_selectors(self):
		return {
			'input': '#sb_form_q',
			'send_button': '#sb_form_go',
			'wait_selector': '.semi-ew-wrapper',
			'result': '.semi-ew-wrapper'
		}
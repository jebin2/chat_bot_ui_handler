from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class QwenUIChat(BaseUIChat):
	def get_docker_name(self):
		return "qwen_ui_chat"

	def get_url(self):
		return "https://chat.qwen.ai/"

	def get_selectors(self):
		return {
			'input': 'textarea[id="chat-input"]',
			'send_button': 'button[type="submit"]',
			'wait_selector': '#send-message-button',
			'result': '#response-message-body'
		}

	def login(self, page):
		try:
			# Wait for login button to appear (5 seconds timeout)
			try:
				login = page.get_by_role("button", name="Log in")
				login.wait_for(timeout=5000)  # Wait up to 5 seconds
				login.click()
				page.wait_for_timeout(2000)
				self.save_screenshot(page)

				button = page.get_by_role("button", name="Continue with Google")
				button.wait_for(timeout=5000)  # Wait up to 5 seconds
				button.click()
				page.wait_for_timeout(5000)
				
			except:
				pass

			page.wait_for_timeout(2000)
			self.save_screenshot(page)
		except: 
			pass
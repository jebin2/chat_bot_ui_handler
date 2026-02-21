from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
from functools import partial

class QwenUIChat(BaseUIChat):
	def get_docker_name(self):
		return f"{self.config.docker_name}_qwen_ui_chat"

	def get_url(self):
		return "https://chat.qwen.ai/"

	def get_selectors(self):
		return {
			'input': '.message-input-container textarea',
			'send_button': '.send-button',
			'wait_selector': '.send-button[disabled]',
			'result': '.response-message-content'
		}

	def show_input_file_tag(self, page):
		# Click the "Upload image" button to reveal the file input
		page.locator('.message-input-container .mode-select-open').first.click()
		page.wait_for_timeout(1000)  # Wait for the file input to become visible

	def upload_file(self, page, file_path):
		if file_path:
			self.show_input_file_tag(page)

			page.locator('[role="menuitem"]').first.click()
			page.wait_for_timeout(1000)

			logger_config.info(f"Uploading file: {file_path}")
			
			# Use xdotool for file selection
			choose_file_via_xdotool = partial(
				self.get_browser_manager().launcher.choose_file_via_xdotool, 
				config=self.config
			)
			choose_file_via_xdotool(file_path=file_path)

			logger_config.info("File uploaded successfully")
			page.wait_for_timeout(5000)
			self.save_screenshot(page)

	# def login(self, page):
	# 	try:
	# 		# Wait for login button to appear (5 seconds timeout)
	# 		try:
	# 			login = page.get_by_role("button", name="Log in")
	# 			login.wait_for(timeout=5000)  # Wait up to 5 seconds
	# 			login.click()
	# 			page.wait_for_timeout(2000)
	# 			self.save_screenshot(page)

	# 			button = page.get_by_role("button", name="Continue with Google")
	# 			button.wait_for(timeout=5000)  # Wait up to 5 seconds
	# 			button.click()
	# 			page.wait_for_timeout(5000)
				
	# 		except:
	# 			pass

	# 		page.wait_for_timeout(2000)
	# 		self.save_screenshot(page)
	# 	except: 
	# 		pass
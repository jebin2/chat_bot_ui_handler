from chat_bot_ui_handler.base_ui_flow import BaseUIChat

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
		page.wait_for_selector('div[data-test-id="bard-mode-menu-button"] button', state="visible")
		page.click('div[data-test-id="bard-mode-menu-button"] button')
		dropdown_panel = page.locator('#mat-menu-panel-0')
		if not dropdown_panel:
			dropdown_panel = page.locator('.menu-inner-container')
		self.save_screenshot(page)

		# Try selecting 2.5 Pro, fallback to 2.5 Flash if not found
		menu_clicked = False
		try:
			dropdown_panel.locator("text=2.5 Pro").wait_for(state="visible", timeout=3000)
			page.wait_for_timeout(2000)
			self.save_screenshot(page)
			dropdown_panel.locator("text=2.5 Pro").click()
			menu_clicked = True
			self.save_screenshot(page)
			page.wait_for_timeout(2000)
			page.wait_for_selector('rich-textarea div.ql-editor[contenteditable="true"]', state="visible", timeout=2000)
			self.save_screenshot(page)
		except:
			if menu_clicked:
				page.click('div[data-test-id="bard-mode-menu-button"] button')
				self.save_screenshot(page)
			dropdown_panel = page.locator('#mat-menu-panel-0')
			if not dropdown_panel:
				dropdown_panel = page.locator('.menu-inner-container')
			dropdown_panel.locator("text=2.5 Flash").wait_for(state="visible")
			page.wait_for_timeout(2000)
			self.save_screenshot(page)
			dropdown_panel.locator("text=2.5 Flash").click()
			self.save_screenshot(page)

	def login(self, page):
		"""Custom setup after page load - set model"""
		self.set_model(page)

	def show_input_file_tag(self, page):
		page.locator('button[aria-label="Open upload file menu"]').click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)
		page.locator('[data-test-id="local-image-file-uploader-button"]').click()
		page.wait_for_timeout(1000)
		self.save_screenshot(page)

	def add_wait_res(self, page):
		page.wait_for_timeout(2000)
		page.wait_for_function(
			"""() => {
				const el = document.querySelectorAll('.avatar_spinner_animation')[0];
				return el && el.style.visibility === 'hidden';
			}"""
		)
		page.wait_for_timeout(2000)
		# page.wait_for_timeout(180000)
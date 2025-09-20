from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class MoonDream(BaseUIChat):
    def get_docker_name(self):
        return f"{self.config.docker_name}_MoonDream_caption"

    def get_url(self):
        return "https://moondream.ai/c/playground"

    def get_selectors(self):
        return {
            'input': 'button[type="button"]:has-text("Caption")',
            'input_file_wait_selector': '#image-container button[type="button"]',
            'send_button': '#playground-form button[data-slot="button"] svg',
            'wait_selector': 'button[data-slot="button"]:has-text("Show Code")',
            'result': 'main div.break-words'
        }

    def fill_prompt(self, page, user_prompt, system_prompt=None):
        input_field = page.locator(self.get_selectors()['input']).first
        input_field.click()
        self.save_screenshot(page)
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
from custom_logger import logger_config
import os

class PerplexityUIChat(BaseUIChat):
    def get_docker_name(self):
        return f"{self.config.docker_name}_perplexity_ui_chat"

    def get_url(self):
        return "https://perplexity.ai"

    def get_selectors(self):
        return {
            'input': '#ask-input',
            'send_button': 'button[data-testid="submit-button"]',
            'wait_selector': 'button[data-testid="submit-button"]',
            'result': 'div[id*="markdown-content"]'
        }

    def get_cookie_path(self):
        return os.getenv("COOKIE_2")

    def upload_file(self, page, file_path):
        """Custom file upload for Perplexity which requires clicking an upload button first"""
        upload_button_selector = "button[aria-label='Attach files']"
        logger_config.info("Waiting for upload button to appear...")
        page.wait_for_selector(upload_button_selector, state='visible', timeout=10000)
        logger_config.info("Clicking upload button...")
        page.click(upload_button_selector)

        logger_config.info(f"Uploading file: {file_path}")
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(file_path)

        logger_config.info("Waiting for upload preview or cancel button (max 20s)...")
        page.wait_for_timeout(2000)
        page.wait_for_selector("button[aria-label='Cancel upload'], img", timeout=20000)

        logger_config.info("File uploaded successfully")
        page.wait_for_timeout(5000)
        self.save_screenshot(page)
from chat_bot_ui_handler.base_ui_flow import BaseUIChat
import os

class GrokUIChat(BaseUIChat):
    def get_docker_name(self):
        return f"{self.config.docker_name}_grok_ui_chat"

    def get_url(self):
        return "https://grok.com/"

    def get_selectors(self):
        return {
            'input': 'textarea[aria-label="Ask Grok anything"]',
            'send_button': 'button[type="submit"]',
            'wait_selector': 'button[aria-label="Enter voice mode"]',
            'result': '#last-reply-container .message-bubble'
        }

    def get_cookie_path(self):
        return os.getenv("COOKIE_2")
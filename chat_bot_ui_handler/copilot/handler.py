from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class CopilotUIChat(BaseUIChat):
    def get_docker_name(self):
        return "copilot_ui_chat"

    def get_url(self):
        return "https://copilot.microsoft.com"

    def get_selectors(self):
        return {
            'input': 'textarea[id="userInput"]',
            'send_button': 'button[aria-label="Submit message"]',
            'wait_selector': 'button[aria-label="Talk to Copilot"]',
            'result': 'div[data-content="ai-message"] p'
        }
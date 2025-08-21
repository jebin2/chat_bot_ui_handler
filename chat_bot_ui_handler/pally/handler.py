from chat_bot_ui_handler.base_ui_flow import BaseUIChat

class PallyUIChat(BaseUIChat):
    def get_docker_name(self):
        return "pally_search_caption"

    def get_url(self):
        return "https://pallyy.com/tools/image-description-generator"

    def get_selectors(self):
        return {
            'input': 'input[name="description"]',
            'input_file_wait_selector': 'a[href="#remove"]',
            'send_button': 'button[type="submit"]',
            'wait_selector': 'button[type="button"]:has-text("Copy")',
            'result': 'button[type="button"]:has-text("Copy") >> xpath=preceding-sibling::p[1]'
        }
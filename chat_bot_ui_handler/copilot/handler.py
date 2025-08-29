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

    def login(self, page):
        try:
            # Wait for login button to appear (5 seconds timeout)
            try:
                login = page.locator('button[title="Sign in"]').first
                print(login)
                login.wait_for(timeout=5000)  # Wait up to 5 seconds
                login.click()
                page.wait_for_timeout(2000)
                self.save_screenshot(page)

                login = page.locator('button[title="Sign in"]').last
                login.wait_for(timeout=5000)  # Wait up to 5 seconds
                login.click()
                page.wait_for_timeout(2000)
                self.save_screenshot(page)

                login = page.locator('button[title="Continue with Google"]').last
                login.wait_for(timeout=5000)  # Wait up to 5 seconds
                login.click()
                page.wait_for_timeout(5000)
                self.save_screenshot(page)

                button = page.get_by_text("Jebin Einstein", exact=False).first
                button.wait_for(timeout=5000)  # Wait up to 5 seconds
                button.click()
                page.wait_for_timeout(8000)
                self.save_screenshot(page)
                
            except Exception as e:
                print(str(e))
                pass

            page.wait_for_timeout(2000)
            self.save_screenshot(page)
        except: 
            pass
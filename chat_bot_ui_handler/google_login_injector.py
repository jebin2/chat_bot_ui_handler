import os
from custom_logger import logger_config

class GoogleLoginInjector:
    def __init__(self):
        self.email = os.getenv('GOOGLE_EMAIL') or os.getenv('OAUTH_EMAIL')
        self.password = os.getenv('GOOGLE_PASSWORD') or os.getenv('OAUTH_PASSWORD')

    def login(self, page):
        page.wait_for_timeout(2000)
        page.goto("https://accounts.google.com", wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        if page.url.startswith("https://accounts.google.com"):
            # Wait for email input and enter email
            logger_config.info("Looking for email input...")
            email_selector = '#identifierId'
            page.wait_for_selector(email_selector)
            page.wait_for_timeout(2000)
            page.fill(email_selector, self.email)
            
            # Click next button
            next_button = '#identifierNext'
            page.wait_for_selector(next_button)
            page.wait_for_timeout(2000)
            page.click(next_button)
            
            # Wait for password input and enter password
            logger_config.info("Looking for password input...")
            password_selector = 'input[type="password"]'
            page.wait_for_selector(password_selector)
            page.wait_for_timeout(2000)
            page.fill(password_selector, self.password)
            
            # Click next/sign in button
            signin_button = '#passwordNext'
            page.wait_for_selector(signin_button)
            page.wait_for_timeout(2000)
            page.click(signin_button)

            while True:
                try:
                    logger_config.info("Wait until 2-Step Verification", seconds=5)
                    if page.query_selector("#headingText").text_content() == "2-Step Verification":
                        page.query_selector('input[type="checkbox"]').uncheck()
                        logger_config.info("Wait after found 2-Step Verification", seconds=5)
                        break
                except: pass
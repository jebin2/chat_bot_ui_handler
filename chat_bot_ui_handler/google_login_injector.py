import os
import tempfile
from custom_logger import logger_config

def _upload_screenshot_to_hf(page):
    try:
        from jebin_lib.hf_dataset_client import HFDatasetClient
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        page.screenshot(path=tmp_path)
        repo_path = f"screenshots/2fa.png"
        HFDatasetClient(repo_id="jebin2/google").upload(tmp_path, repo_path)
        os.unlink(tmp_path)
    except Exception as e:
        logger_config.info(f"Failed to upload screenshot to HF: {e}")

class GoogleLoginInjector:
    def __init__(self):
        self.email = os.getenv('GOOGLE_EMAIL') or os.getenv('OAUTH_EMAIL')
        self.password = os.getenv('GOOGLE_PASSWORD') or os.getenv('OAUTH_PASSWORD')

    def login(self, page):
        logger_config.info(f"Current URL: {page.url}")
        page.wait_for_timeout(2000)
        page.goto("https://accounts.google.com", wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        logger_config.info(f"Current URL after goto: {page.url}")
        if "accountchooser" in page.url or page.url.startswith("https://accounts.google.com"):
            # Handle potential Account Chooser
            try:
                page.wait_for_timeout(2000) # Give it time to load dynamic content
                
                use_another_account = page.get_by_text("Use another account", exact=True)
                saved_account = page.locator(f'[data-identifier="{self.email}"]')
                saved_account_alt = page.locator(f'[data-email="{self.email}"]')
                
                if saved_account.is_visible():
                    logger_config.info("Account chooser detected. Clicking existing account...")
                    saved_account.first.click()
                    page.wait_for_timeout(2000)
                elif saved_account_alt.is_visible():
                    logger_config.info("Account chooser detected. Clicking existing account...")
                    saved_account_alt.first.click()
                    page.wait_for_timeout(2000)
                elif use_another_account.is_visible():
                    logger_config.info("Account chooser detected. Clicking 'Use another account'...")
                    use_another_account.first.click()
                    page.wait_for_timeout(2000)
            except Exception as e:
                logger_config.info(f"Error handling account chooser: {e}")

            # Wait for email input and enter email (if NOT already prepopulated/skipped)
            logger_config.info("Looking for email input...")
            email_selector = '#identifierId'
            if page.locator(email_selector).is_visible():
                page.wait_for_selector(email_selector)
                page.wait_for_timeout(2000)
                page.fill(email_selector, self.email)
                
                # Click next button
                next_button = '#identifierNext'
                page.wait_for_selector(next_button)
                page.wait_for_timeout(2000)
                page.click(next_button)
            else:
                logger_config.info("Email input not found (likely already on password page or prepopulated)")
            
            # Wait for password input and enter password
            logger_config.info("Looking for password input...")
            password_selector = 'input[type="password"]'
            if page.locator(password_selector).is_visible():
                page.wait_for_timeout(2000)
                page.fill(password_selector, self.password)

                # Click next/sign in button
                signin_button = '#passwordNext'
                page.wait_for_selector(signin_button)
                page.wait_for_timeout(2000)
                page.click(signin_button)
            else:
                logger_config.info("Password input not found (likely already authenticated via existing account)")

            page.wait_for_timeout(5000)
            _upload_screenshot_to_hf(page)
            while True:
                try:
                    logger_config.info("Wait until 2-Step Verification", seconds=5)
                    if page.query_selector("#headingText").text_content() == "2-Step Verification":
                        page.query_selector('input[type="checkbox"]').uncheck()
                        logger_config.info("Wait after found 2-Step Verification", seconds=5)
                        break
                except: pass
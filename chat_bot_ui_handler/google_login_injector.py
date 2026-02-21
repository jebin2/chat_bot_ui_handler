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
        logger_config.info(f"[GoogleLogin] Step 1: Starting login process. Current URL: {page.url}")
        page.wait_for_timeout(2000)
        logger_config.info("[GoogleLogin] Step 2: Navigating to https://accounts.google.com")
        page.goto("https://accounts.google.com", wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        logger_config.info(f"[GoogleLogin] Step 3: Current URL after navigation: {page.url}")
        if "accountchooser" in page.url or page.url.startswith("https://accounts.google.com"):
            # Handle potential Account Chooser
            try:
                logger_config.info("[GoogleLogin] Step 4: Checking for Account Chooser...")
                page.wait_for_timeout(2000) # Give it time to load dynamic content
                
                use_another_account = page.get_by_text("Use another account", exact=True)
                saved_account = page.locator(f'[data-identifier="{self.email}"]')
                saved_account_alt = page.locator(f'[data-email="{self.email}"]')
                
                if saved_account.is_visible():
                    logger_config.info("[GoogleLogin] Step 4a: Account chooser detected. Clicking existing account...")
                    saved_account.first.click()
                    page.wait_for_timeout(2000)
                elif saved_account_alt.is_visible():
                    logger_config.info("[GoogleLogin] Step 4b: Account chooser detected. Clicking existing account (alt)...")
                    saved_account_alt.first.click()
                    page.wait_for_timeout(2000)
                elif use_another_account.is_visible():
                    logger_config.info("[GoogleLogin] Step 4c: Account chooser detected. Clicking 'Use another account'...")
                    use_another_account.first.click()
                    page.wait_for_timeout(2000)
                else:
                    logger_config.info("[GoogleLogin] Step 4d: No known account options visible in Account Chooser.")
            except Exception as e:
                logger_config.error(f"[GoogleLogin] Error handling account chooser: {e}")

            # Wait for email input and enter email (if NOT already prepopulated/skipped)
            logger_config.info("[GoogleLogin] Step 5: Looking for email input...")
            email_selector = '#identifierId'
            if page.locator(email_selector).is_visible():
                logger_config.info("[GoogleLogin] Step 5a: Email input found. Entering email...")
                page.wait_for_selector(email_selector)
                page.wait_for_timeout(2000)
                page.fill(email_selector, self.email)
                
                # Click next button
                logger_config.info("[GoogleLogin] Step 5b: Clicking next button after email input...")
                next_button = '#identifierNext'
                page.wait_for_selector(next_button)
                page.wait_for_timeout(2000)
                page.click(next_button)
            else:
                logger_config.info("[GoogleLogin] Step 5c: Email input not found (likely already on password page or prepopulated).")
            
            # Wait for password input and enter password
            logger_config.info("[GoogleLogin] Step 6: Looking for password input...")
            password_selector = 'input[type="password"]'
            if page.locator(password_selector).is_visible():
                logger_config.info("[GoogleLogin] Step 6a: Password input found. Entering password...")
                page.wait_for_timeout(2000)
                page.fill(password_selector, self.password)

                # Click next/sign in button
                logger_config.info("[GoogleLogin] Step 6b: Clicking sign-in button after password input...")
                signin_button = '#passwordNext'
                page.wait_for_selector(signin_button)
                page.wait_for_timeout(2000)
                page.click(signin_button)
            else:
                logger_config.info("[GoogleLogin] Step 6c: Password input not found (likely already authenticated via existing account).")

            logger_config.info("[GoogleLogin] Step 7: Waiting for post-login actions (5 seconds) before checking 2FA...")
            page.wait_for_timeout(5000)
            logger_config.info("[GoogleLogin] Step 8: Uploading 2FA screenshot to HF...")
            _upload_screenshot_to_hf(page)
            
            logger_config.info("[GoogleLogin] Step 9: Starting 2FA verification check loop...")
            while True:
                try:
                    logger_config.info("[GoogleLogin] Step 9a: Waiting 5 seconds before checking for '2-Step Verification' header.")
                    page.wait_for_timeout(5000)
                    if page.query_selector("#headingText") and page.query_selector("#headingText").text_content() == "2-Step Verification":
                        logger_config.info("[GoogleLogin] Step 9b: '2-Step Verification' detected. Unchecking 'Don't ask again on this device'...")
                        if page.query_selector('input[type="checkbox"]'):
                            page.query_selector('input[type="checkbox"]').uncheck()
                        logger_config.info("[GoogleLogin] Step 9c: '2-Step Verification' handled. Breaking loop.")
                        break
                    else:
                        break # Added break to not loop infinitely if 2FA is not there or we pass it
                except Exception as e:
                    logger_config.error(f"[GoogleLogin] Error in 2FA check loop: {e}")
                    break
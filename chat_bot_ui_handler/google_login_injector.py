"""Sign a browser session into Google.

The flow is deliberately state-driven rather than a fixed sequence of steps:
Google varies which screens appear (account chooser, password, 2FA, consent
interstitials) depending on the account and how much it trusts the session, so
each iteration looks at what is on screen and handles that.

Environment variables:
    GOOGLE_EMAIL / OAUTH_EMAIL       - account to sign in as
    GOOGLE_PASSWORD / OAUTH_PASSWORD - its password
    GOOGLE_LOGIN_TIMEOUT             - seconds for the whole flow (default 300)
    GOOGLE_2FA_TIMEOUT               - seconds to wait for a phone tap (default 180)
    GOOGLE_CAPTCHA_TIMEOUT           - seconds to wait for a CAPTCHA reply (default 300)

Challenges are relayed to a human rather than defeated: a 2FA prompt pushes the
on-screen number to your phone via ntfy so you know which number to tap, and a
CAPTCHA pushes the image so you can read it and publish the text back.
"""

import os
import re
import tempfile
import time

from custom_logger import logger_config

from chat_bot_ui_handler import notifier as notifier_mod
from chat_bot_ui_handler.notifier import Notifier

SIGNED_IN_URL_MARKERS = ("myaccount.google.com", "accounts.google.com/b/0", "/ManageAccount")

# Google's login CAPTCHA. It is a human check by design, so it is never solved
# here: the image is pushed to the phone and a human sends the text back.
CAPTCHA_IMAGE_SELECTORS = ('img#captchaimg', 'img[alt*="captcha" i]', 'img[src*="captcha" i]')
CAPTCHA_INPUT_SELECTORS = ('input[name="ca"]', '#ca', 'input[aria-label*="captcha" i]')

# Interstitials Google shows after a successful sign-in ("Save a passkey?",
# "Add a recovery phone"). None of them block the session, so dismiss and move on.
_SKIP_BUTTON_TEXTS = ("Not now", "Not Now", "Skip", "Cancel", "Later")


def _upload_screenshot_to_hf(page):
	try:
		from jebin_lib.hf_dataset_client import HFDatasetClient
		with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
			tmp_path = tmp.name
		page.screenshot(path=tmp_path)
		HFDatasetClient(repo_id="jebin2/google").upload(tmp_path, "screenshots/2fa.png")
		os.unlink(tmp_path)
	except Exception as e:
		logger_config.info(f"Failed to upload screenshot to HF: {e}")


class GoogleLoginInjector:
	def __init__(self):
		self.email = os.getenv('GOOGLE_EMAIL') or os.getenv('OAUTH_EMAIL')
		self.password = os.getenv('GOOGLE_PASSWORD') or os.getenv('OAUTH_PASSWORD')
		self.notifier = Notifier()
		self._notified_challenge = None

	# ------------------------------------------------------------------ #
	# helpers
	# ------------------------------------------------------------------ #

	def _wait_visible(self, page, selector, timeout=15000):
		# is_visible() does not auto-wait, so a field that is still rendering
		# after a navigation reads as absent. Wait for it before deciding.
		try:
			page.wait_for_selector(selector, state="visible", timeout=timeout)
			return True
		except Exception:
			return False

	def _wait_gone(self, page, selector, timeout=15000):
		"""Wait for a submitted field to leave the screen.

		Without this the next iteration can still see the old field and submit
		it a second time, against an element that is on its way out.
		"""
		try:
			page.wait_for_selector(selector, state="hidden", timeout=timeout)
		except Exception:
			pass
		page.wait_for_timeout(2000)

	def _read_state(self, page):
		"""Snapshot the page. Returns None while a navigation is in flight."""
		try:
			# Fields linger in the DOM (hidden) while Google transitions between
			# steps, so presence is not enough — only count what is visible.
			return page.evaluate("""() => {
				const visible = el => !!el && !!(
					el.offsetWidth || el.offsetHeight || el.getClientRects().length
				);
				return {
					url: location.href,
					heading: (document.querySelector('#headingText') || {innerText: ''}).innerText.trim(),
					body: document.body ? document.body.innerText : '',
					hasEmail: visible(document.querySelector('#identifierId')),
					hasPassword: visible(document.querySelector('input[type="password"]')),
				};
			}""")
		except Exception:
			# Execution context destroyed mid-navigation; the caller retries.
			return None

	def _is_signed_in(self, page, state):
		if any(marker in state['url'] for marker in SIGNED_IN_URL_MARKERS):
			return True
		# Signed in but parked on some other Google property.
		return "accounts.google.com" not in state['url'] and "gemini.google.com" in state['url']

	def _click_if_present(self, page, selector, description):
		try:
			locator = page.locator(selector).first
			if locator.is_visible(timeout=2000):
				locator.click()
				logger_config.info(f"[GoogleLogin] Clicked {description}")
				page.wait_for_timeout(2000)
				return True
		except Exception:
			pass
		return False

	# ------------------------------------------------------------------ #
	# CAPTCHA
	# ------------------------------------------------------------------ #

	def _find_first(self, page, selectors):
		for selector in selectors:
			try:
				locator = page.locator(selector).first
				if locator.is_visible(timeout=1000):
					return locator
			except Exception:
				continue
		return None

	def _is_captcha(self, page):
		return (
			self._find_first(page, CAPTCHA_IMAGE_SELECTORS) is not None
			and self._find_first(page, CAPTCHA_INPUT_SELECTORS) is not None
		)

	def _handle_captcha(self, page, state):
		"""Send the CAPTCHA image to a human and type back what they reply.

		The challenge exists to prove a human is present, so it is deliberately
		relayed rather than solved: a person reads the image and answers.
		"""
		image = self._find_first(page, CAPTCHA_IMAGE_SELECTORS)
		text_input = self._find_first(page, CAPTCHA_INPUT_SELECTORS)
		if image is None or text_input is None:
			return False

		with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
			shot_path = tmp.name
		try:
			try:
				# Just the image: easier to read on a phone than the whole page.
				image.screenshot(path=shot_path)
			except Exception:
				page.screenshot(path=shot_path)

			reply_topic = notifier_mod._ntfy_reply_topic()
			title = "Google CAPTCHA: reply with the text"
			message = (
				f"Sign-in as {self.email} hit a CAPTCHA. Read the image and publish "
				f"the characters to the '{reply_topic}' ntfy topic."
			)
			logger_config.info(f"[GoogleLogin] CAPTCHA detected. Asking a human via '{reply_topic}'")
			if not self.notifier.notify_with_screenshot(title, message, shot_path, priority="urgent"):
				self.notifier.notify(title, message, priority="urgent")
			_upload_screenshot_to_hf(page)
		finally:
			try: os.unlink(shot_path)
			except Exception: pass

		try: timeout = int(os.getenv("GOOGLE_CAPTCHA_TIMEOUT") or 300)
		except Exception: timeout = 300

		answer = self.notifier.wait_for_reply(timeout=timeout)
		if not answer:
			raise TimeoutError(f"No CAPTCHA answer received within {timeout}s")

		# The answer arrives with whatever whitespace/case the human typed.
		answer = answer.strip()
		logger_config.info(f"[GoogleLogin] Submitting CAPTCHA answer ({len(answer)} chars)")
		text_input.fill(answer)

		# The CAPTCHA shares a page with the email or password field, so fill
		# whatever else is on screen before submitting.
		if state['hasEmail']:
			page.fill('#identifierId', self.email)
			page.click('#identifierNext')
		elif state['hasPassword']:
			page.fill('input[type="password"]', self.password)
			page.click('#passwordNext')
		else:
			text_input.press("Enter")
		page.wait_for_timeout(4000)
		return True

	# ------------------------------------------------------------------ #
	# 2FA
	# ------------------------------------------------------------------ #

	def _extract_challenge_number(self, page, state):
		"""Pull the number to tap off the challenge screen.

		Google renders it in a <samp> on the number-match screen, but the markup
		shifts between variants, so fall back to reading the prompt text.
		"""
		try:
			samp = page.locator("samp").first
			if samp.is_visible(timeout=2000):
				digits = re.sub(r"\D", "", samp.inner_text())
				if digits:
					return digits
		except Exception:
			pass

		patterns = (
			r"[Tt]ap\s+(\d{1,3})\b",
			r"\b[Nn]umber\s+(\d{1,3})\b",
			r"\b(\d{1,3})\s+on your phone\b",
		)
		for pattern in patterns:
			match = re.search(pattern, state['body'])
			if match:
				return match.group(1)

		# Last resort: a short number alone on its own line is the big digit block.
		for line in state['body'].splitlines():
			line = line.strip()
			if re.fullmatch(r"\d{1,3}", line):
				return line
		return None

	def _is_challenge(self, state):
		heading = state['heading'].lower()
		body = state['body'].lower()
		return (
			"2-step verification" in heading
			or "check your phone" in heading
			or "verify it" in heading
			or "tap yes on your phone" in body
			or "open the gmail app" in body
		)

	def _handle_challenge(self, page, state):
		"""Notify the phone, then wait for the tap. Returns when the screen changes."""
		# Some interstitials ("verifying it's you") look like a challenge but
		# resolve themselves. Give them a moment rather than buzzing the phone.
		try: grace = int(os.getenv("GOOGLE_2FA_GRACE") or 15)
		except Exception: grace = 15
		grace_deadline = time.monotonic() + grace
		while time.monotonic() < grace_deadline:
			page.wait_for_timeout(3000)
			current = self._read_state(page)
			if current is None:
				continue
			if not self._is_challenge(current):
				logger_config.info("[GoogleLogin] Challenge screen cleared on its own")
				return True
			state = current

		number = self._extract_challenge_number(page, state)

		# Don't re-notify while polling the same challenge.
		key = f"{state['heading']}|{number}"
		if key != self._notified_challenge:
			self._notified_challenge = key
			_upload_screenshot_to_hf(page)

			if number:
				title = f"Google 2FA: tap {number}"
				message = f"Tap {number} on your phone to finish signing in as {self.email}."
			else:
				title = "Google 2FA required"
				message = (
					f"A 2FA challenge is blocking sign-in as {self.email}, but the "
					f"number could not be read. Screen says: {state['heading'] or 'unknown'}"
				)
			logger_config.info(f"[GoogleLogin] 2FA challenge detected. {title}")

			with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
				shot_path = tmp.name
			try:
				page.screenshot(path=shot_path)
				# The screenshot makes the challenge readable even if scraping missed.
				if not self.notifier.notify_with_screenshot(title, message, shot_path, priority="urgent"):
					self.notifier.notify(title, message, priority="urgent")
			finally:
				try: os.unlink(shot_path)
				except Exception: pass

		# Leave "Don't ask again on this device" unticked, as the previous flow did.
		try:
			checkbox = page.locator('input[type="checkbox"]').first
			if checkbox.is_visible(timeout=2000) and checkbox.is_checked():
				checkbox.uncheck()
		except Exception:
			pass

		try: timeout = int(os.getenv("GOOGLE_2FA_TIMEOUT") or 180)
		except Exception: timeout = 180

		logger_config.info(f"[GoogleLogin] Waiting up to {timeout}s for the phone tap...")
		deadline = time.monotonic() + timeout
		while time.monotonic() < deadline:
			page.wait_for_timeout(3000)
			current = self._read_state(page)
			if current is None:
				continue
			if not self._is_challenge(current):
				logger_config.info("[GoogleLogin] 2FA challenge cleared")
				return True

		self.notifier.notify(
			"Google 2FA timed out",
			f"No tap received within {timeout}s while signing in as {self.email}.",
			priority="high",
		)
		raise TimeoutError(f"2FA was not confirmed within {timeout}s")

	# ------------------------------------------------------------------ #
	# main flow
	# ------------------------------------------------------------------ #

	def login(self, page):
		if not self.email or not self.password:
			raise ValueError(
				"GOOGLE_EMAIL/GOOGLE_PASSWORD (or OAUTH_EMAIL/OAUTH_PASSWORD) must be set"
			)

		# A JS dialog can appear and vanish during navigation; accepting a dialog
		# that is already gone raises, so swallow that race.
		def _safe_dialog_handler(dialog):
			try:
				dialog.accept()
			except Exception:
				pass

		page.on("dialog", _safe_dialog_handler)

		logger_config.info(f"[GoogleLogin] Starting login. Current URL: {page.url}")
		page.goto("https://accounts.google.com", wait_until='domcontentloaded')
		page.wait_for_timeout(2000)

		try: timeout = int(os.getenv("GOOGLE_LOGIN_TIMEOUT") or 300)
		except Exception: timeout = 300
		deadline = time.monotonic() + timeout

		email_submitted = False
		password_submitted = False

		while time.monotonic() < deadline:
			state = self._read_state(page)
			if state is None:
				page.wait_for_timeout(1000)
				continue

			if self._is_signed_in(page, state):
				logger_config.info(f"[GoogleLogin] Signed in successfully ({state['url']})")
				return True

			if self._is_challenge(state):
				self._handle_challenge(page, state)
				continue

			# Before the email/password branches: the CAPTCHA is rendered on the
			# same page as those fields, and submitting without it just fails.
			if self._is_captcha(page):
				self._handle_captcha(page, state)
				continue

			if state['hasEmail']:
				logger_config.info("[GoogleLogin] Entering email...")
				page.fill('#identifierId', self.email)
				page.click('#identifierNext')
				email_submitted = True
				self._wait_gone(page, '#identifierId')
				continue

			if state['hasPassword']:
				logger_config.info("[GoogleLogin] Entering password...")
				page.fill('input[type="password"]', self.password)
				page.click('#passwordNext')
				password_submitted = True
				self._wait_gone(page, 'input[type="password"]')
				continue

			# Account chooser: pick the saved account, else add a new one.
			if self._click_if_present(page, f'[data-identifier="{self.email}"]', "saved account"):
				continue
			if self._click_if_present(page, f'[data-email="{self.email}"]', "saved account (alt)"):
				continue
			if self._click_if_present(page, 'text="Use another account"', "'Use another account'"):
				continue

			# Post-login interstitials.
			dismissed = False
			for label in _SKIP_BUTTON_TEXTS:
				if self._click_if_present(page, f'button:has-text("{label}")', f"'{label}'"):
					dismissed = True
					break
			if dismissed:
				continue

			logger_config.info(
				f"[GoogleLogin] Waiting... url={state['url'][:80]} heading={state['heading']!r}"
			)
			page.wait_for_timeout(3000)

		_upload_screenshot_to_hf(page)
		self.notifier.notify(
			"Google login failed",
			f"Could not sign in as {self.email} within {timeout}s. Last URL: {page.url}",
			priority="high",
		)
		raise TimeoutError(
			f"Google login did not complete within {timeout}s "
			f"(email_submitted={email_submitted}, password_submitted={password_submitted}, "
			f"url={page.url})"
		)

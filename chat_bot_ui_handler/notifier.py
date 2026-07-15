"""
Notifier for out-of-band alerts, configured entirely via environment variables.

Sends through every channel that is configured. If none is configured (or all
fail) the message is still logged so it shows up in the run output. Duplicate
messages are suppressed within a window so a retry loop does not spam the phone.

    ntfy.sh (zero-signup push to phone):
        CHAT_BOT_NTFY_TOPIC       - topic to publish to (default: DEFAULT_NTFY_TOPIC)
        CHAT_BOT_NTFY_REPLY_TOPIC - topic polled for your answers
                                    (default: <topic>-reply)
        NTFY_SERVER               - server base URL (default: https://ntfy.sh)
        NTFY_TOKEN                - optional access token for protected topics

    Email via SMTP (works with a Gmail app password):
        GOOGLE_EMAIL / NOTIFY_SMTP_USER            - SMTP username (sender)
        GOOGLE_APP_PASSWORD / NOTIFY_SMTP_PASSWORD - SMTP password
        NOTIFY_EMAIL_TO     - recipient (default: same as sender)
        NOTIFY_SMTP_HOST    - SMTP host (default: smtp.gmail.com)
        NOTIFY_SMTP_PORT    - SMTP SSL port (default: 465)

    Behaviour tuning:
        NOTIFY_DEDUPE_SECONDS - suppress an identical dedupe_key within this
                                many seconds (default: 300)
"""

import json
import os
import smtplib
import time
from email.message import EmailMessage
from typing import Dict, Optional

import requests

from custom_logger import logger_config

# Subscribe to this topic in the ntfy app to receive 2FA prompts. Anyone who
# knows a topic name can read it, so this is deliberately unguessable.
DEFAULT_NTFY_TOPIC = "jebin-chatbot-ui-2fa-k7m2xq"

_STATE_PATH = os.path.expanduser("~/.chat_bot_ui_handler_notifier.json")


def _ntfy_topic() -> str:
	# Deliberately not the shared NTFY_TOPIC: other projects export that, and
	# inheriting it would send 2FA prompts to whichever topic they picked.
	return os.getenv("CHAT_BOT_NTFY_TOPIC") or DEFAULT_NTFY_TOPIC


def _ntfy_reply_topic() -> str:
	"""Topic polled for answers sent back from the phone."""
	return os.getenv("CHAT_BOT_NTFY_REPLY_TOPIC") or f"{_ntfy_topic()}-reply"


# A human can also drop the answer here, for when the phone is not to hand.
def _reply_file() -> str:
	return os.getenv("CHAT_BOT_REPLY_FILE") or os.path.expanduser("~/.chat_bot_ui_reply.txt")


def reply_web_url() -> str:
	"""Page where an answer can be typed and published.

	The iOS ntfy app has no reply action, so a notification that only says
	"reply to this topic" is a dead end on an iPhone. This URL opens the topic
	in a browser, where there is a send box.
	"""
	server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
	return f"{server}/{_ntfy_reply_topic()}"


def build_reply_instructions(preamble: str, timeout: int) -> str:
	"""Spell out every way to send an answer back."""
	minutes = max(1, timeout // 60)
	return "\n".join([
		preamble,
		"",
		"Send it back (any option works):",
		f"  - tap this notification, or open {reply_web_url()}, then type the",
		"    text in the send box at the bottom and publish it",
		f"  - in the ntfy app, publish to the topic '{_ntfy_reply_topic()}'",
		f"  - on the server, save it to: {_reply_file()}",
		"",
		f"Waiting {minutes} min for an answer.",
	])


def _header_safe(value: str) -> str:
	"""Make a string usable as an HTTP header value.

	ntfy carries the title/message in headers when a file is attached, and a
	raw newline there makes the request invalid — ntfy renders a literal \\n
	escape as a line break instead. Non-ASCII would also be rejected.
	"""
	value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
	return value.encode("ascii", "ignore").decode()


def _ntfy_headers(title: str, priority: str) -> Dict[str, str]:
	headers = {"Title": _header_safe(title), "Priority": priority}
	token = os.getenv("NTFY_TOKEN")
	if token:
		headers["Authorization"] = f"Bearer {token}"
	return headers


def _send_via_ntfy(title: str, message: str, priority: str) -> bool:
	server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
	resp = requests.post(
		f"{server}/{_ntfy_topic()}",
		data=message.encode("utf-8"),
		headers=_ntfy_headers(title, priority),
		timeout=15,
	)
	resp.raise_for_status()
	return True


def _send_via_email(title: str, message: str, priority: str) -> bool:
	user = os.getenv("NOTIFY_SMTP_USER") or os.getenv("GOOGLE_EMAIL")
	password = os.getenv("NOTIFY_SMTP_PASSWORD") or os.getenv("GOOGLE_APP_PASSWORD")
	if not user or not password:
		return False
	to_addr = os.getenv("NOTIFY_EMAIL_TO", user)
	host = os.getenv("NOTIFY_SMTP_HOST", "smtp.gmail.com")
	port = int(os.getenv("NOTIFY_SMTP_PORT", "465"))

	msg = EmailMessage()
	msg["Subject"] = title
	msg["From"] = user
	msg["To"] = to_addr
	msg.set_content(message)

	with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
		smtp.login(user, password)
		smtp.send_message(msg)
	return True


_CHANNELS = (
	("ntfy", _send_via_ntfy),
	("email", _send_via_email),
)


class _DedupeStore:
	"""Persists when each dedupe key was last sent."""

	def __init__(self, path: str):
		self._path = path

	def recently_sent(self, key: str) -> bool:
		try: window = int(os.getenv("NOTIFY_DEDUPE_SECONDS") or 300)
		except Exception: window = 300
		return (time.time() - self._load().get(key, 0)) < window

	def mark_sent(self, key: str) -> None:
		state = self._load()
		state[key] = time.time()
		# Drop stale entries so the file does not grow forever.
		cutoff = time.time() - 7 * 24 * 3600
		state = {k: v for k, v in state.items() if v > cutoff}
		try:
			with open(self._path, "w") as f:
				json.dump(state, f)
		except Exception as e:
			logger_config.info(f"[Notifier] Could not persist dedupe state: {e}")

	def _load(self) -> Dict[str, float]:
		try:
			with open(self._path, "r") as f:
				return json.load(f)
		except Exception:
			return {}


class Notifier:
	"""Send notifications through any channel configured via env vars."""

	def __init__(self, state_path: str = _STATE_PATH):
		self._dedupe = _DedupeStore(state_path)

	def notify(
		self,
		title: str,
		message: str,
		priority: str = "default",
		dedupe_key: Optional[str] = None,
	) -> bool:
		"""Send through every configured channel.

		Returns True if at least one channel delivered the message.
		"""
		# Always mirror to the log so the message survives a delivery failure.
		logger_config.info(f"[Notifier] {title}\n{message}")

		if dedupe_key and self._dedupe.recently_sent(dedupe_key):
			logger_config.info(f"[Notifier] Skipping duplicate notification: {dedupe_key}")
			return False

		delivered = False
		for name, send in _CHANNELS:
			try:
				if send(title, message, priority):
					logger_config.info(f"[Notifier] Sent via {name}")
					delivered = True
			except Exception as e:
				logger_config.error(f"[Notifier] {name} failed: {e}")

		if not delivered:
			logger_config.error(
				"[Notifier] No channel delivered. Set NTFY_TOPIC (and subscribe on "
				"your phone) and/or GOOGLE_APP_PASSWORD to enable alerts."
			)

		if delivered and dedupe_key:
			self._dedupe.mark_sent(dedupe_key)
		return delivered

	def notify_with_screenshot(
		self,
		title: str,
		message: str,
		image_path: str,
		priority: str = "default",
		click: Optional[str] = None,
		actions: Optional[str] = None,
	) -> bool:
		"""Push the screenshot itself, so the challenge is readable on the phone
		even when the on-screen number could not be scraped.

		`click` opens a URL when the notification is tapped and `actions` adds
		buttons to it — the only way to get an answer back from iOS, which has
		no reply action.
		"""
		try:
			server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
			headers = _ntfy_headers(title, priority)
			headers["Filename"] = "2fa.png"
			headers["Message"] = _header_safe(message)
			if click:
				headers["Click"] = click
			if actions:
				headers["Actions"] = actions
			with open(image_path, "rb") as f:
				resp = requests.put(
					f"{server}/{_ntfy_topic()}",
					data=f,
					headers=headers,
					timeout=30,
				)
			resp.raise_for_status()
			logger_config.info("[Notifier] Sent screenshot via ntfy")
			return True
		except Exception as e:
			logger_config.error(f"[Notifier] ntfy screenshot failed: {e}")
			return False


	def wait_for_reply(self, timeout: int = 300, poll_interval: int = 5) -> Optional[str]:
		"""Block until a human sends an answer back, or the window closes.

		Polls the ntfy reply topic and a local file. Only messages published
		after this call are considered, so an answer to an earlier prompt is
		never replayed into this one.
		"""
		started_at = int(time.time())
		reply_file = _reply_file()
		# A leftover file would otherwise be read as an answer to this prompt.
		self._clear_reply_file()

		logger_config.info(
			f"[Notifier] Waiting up to {timeout}s for a reply "
			f"(ntfy topic: {_ntfy_reply_topic()}, or write to {reply_file})"
		)
		deadline = time.time() + timeout
		while time.time() < deadline:
			reply = self._check_reply_file() or self._check_ntfy_reply(started_at)
			if reply:
				return reply
			time.sleep(poll_interval)

		logger_config.error(f"[Notifier] No reply received within {timeout}s")
		return None

	def _clear_reply_file(self) -> None:
		try:
			if os.path.exists(_reply_file()):
				os.remove(_reply_file())
		except Exception:
			pass

	def _check_reply_file(self) -> Optional[str]:
		try:
			path = _reply_file()
			if os.path.exists(path):
				with open(path, "r") as f:
					content = f.read().strip()
				if content:
					logger_config.info("[Notifier] Received reply via local file")
					# Consume it so it cannot answer a later prompt too.
					self._clear_reply_file()
					return content
		except Exception as e:
			logger_config.info(f"[Notifier] Could not read reply file: {e}")
		return None

	def _check_ntfy_reply(self, since_ts: int) -> Optional[str]:
		server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
		headers = {}
		token = os.getenv("NTFY_TOKEN")
		if token:
			headers["Authorization"] = f"Bearer {token}"
		try:
			resp = requests.get(
				f"{server}/{_ntfy_reply_topic()}/json",
				params={"poll": "1", "since": str(since_ts)},
				headers=headers,
				timeout=30,
			)
			resp.raise_for_status()
		except Exception as e:
			logger_config.info(f"[Notifier] ntfy reply poll failed: {e}")
			return None

		latest = None
		for line in resp.text.splitlines():
			try:
				event = json.loads(line)
			except Exception:
				continue
			if event.get("event") != "message":
				continue
			message = (event.get("message") or "").strip()
			if message:
				latest = message
		if latest:
			logger_config.info("[Notifier] Received reply via ntfy")
		return latest


if __name__ == "__main__":
	import sys

	title = sys.argv[1] if len(sys.argv) > 1 else "Test notification"
	body = sys.argv[2] if len(sys.argv) > 2 else f"Notifier is working. Topic: {_ntfy_topic()}"
	sys.exit(0 if Notifier().notify(title, body) else 1)

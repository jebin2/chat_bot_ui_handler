import os

def save_screenshot(page, name="page"):
	folder = os.getenv("TEMP_OUTPUT", "chat_bot_ui_handler_logs")
	if not os.path.exists(folder):
		os.mkdir(folder)
	page.screenshot(path=f"chat_bot_ui_handler_logs/{name}.png")
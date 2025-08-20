from chat_bot_ui_handler import perplexity_ui_chat, search_google_ai_mode, gemini_ui_chat, meta_ui_chat, grok_ui_chat
from browser_manager.browser_manager import BrowserConfig
import os

config = BrowserConfig()
config.user_data_dir = os.getenv("PROFILE_PATH_1", None)
grok_ui_chat(
	user_prompt = (
		"Describe what is happening in this video frame as if you're telling a story. "
		"Focus on the main subjects, their actions, the setting, and any important "
		"details that would help someone understand the scene's context. "
		"Max word: 100 ONLY"
	),
	file_path = "test.png",
	config=config
)
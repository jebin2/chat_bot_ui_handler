from chat_bot_ui_handler import PerplexityUIChat, GoogleAISearchChat, GeminiUIChat, MetaUIChat, GrokUIChat, CopilotUIChat, QwenUIChat, PallyUIChat, AIStudioUIChat, BingUIChat, MistralUIChat
from browser_manager.browser_manager import BrowserConfig
import os

source = MetaUIChat
config = BrowserConfig()

baseUIChat = source(config)
result = baseUIChat.chat(
	user_prompt=(
		"Describe what is happening in this video frame as if you're telling a story. "
		"Focus on the main subjects, their actions, the setting, and any important "
		"details that would help someone understand the scene's context. "
		"Keep your description to exactly 100 words or fewer."
	),
	file_path="test.png"
)
result = baseUIChat.chat(
	user_prompt=(
		"Describe what is happening in this video frame as if you're telling a story. "
		"Focus on the main subjects, their actions, the setting, and any important "
		"details that would help someone understand the scene's context. "
		"Keep your description to exactly 100 words or fewer."
	),
	file_path="test.png"
)
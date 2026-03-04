from chat_bot_ui_handler import PerplexityUIChat, GoogleAISearchChat, GeminiUIChat, MetaUIChat, GrokUIChat, CopilotUIChat, QwenUIChat, PallyUIChat, AIStudioUIChat, BingUIChat, MistralUIChat, MoonDream, BraveAISearch, DuckDuckGoAISearch
from browser_manager.browser_manager import BrowserConfig
import os

source = AIStudioUIChat
config = BrowserConfig()
# search works without login : GoogleAISearchChat, QwenUIChat, BingUIChat, BraveAISearch, DuckDuckGoAISearch
# config.use_neko = False
# config.browser_executable = "/usr/bin/brave"
# config.headless = True
# BraveAISearch - works in headless browser

if source.__name__ == "MetaUIChat" or source.__name__ == "AIStudioUIChat" or source.__name__ == "QwenUIChat":
	# Set up additional docker flags
	policy_path = os.path.join(os.getcwd(), 'policies.json')
	additional_flags = []
	additional_flags.append(f'-v {os.getcwd()}:{config.neko_attach_folder}')
	additional_flags.append(config.policy_volume_mount(policy_path))
	config.additionl_docker_flag = ' '.join(additional_flags)

baseUIChat = source(config)
result = baseUIChat.chat(
	user_prompt=(
		"Describe what is happening in this video frame as if you're telling a story. "
		"Focus on the main subjects, their actions, the setting, and any important "
		"details that would help someone understand the scene's context. "
		"Keep your description to exactly 100 words or fewer."
	),
    system_prompt="follow user prompt",
	file_path="test.png"
)
# result = baseUIChat.chat(
# 	user_prompt=(
# 		"Describe what is happening in this video frame as if you're telling a story. "
# 		"Focus on the main subjects, their actions, the setting, and any important "
# 		"details that would help someone understand the scene's context. "
# 		"Keep your description to exactly 100 words or fewer."
# 	),
# 	file_path="test.png"
# )
from chat_bot_ui_handler import PerplexityUIChat, GoogleAISearchChat, GeminiUIChat, MetaUIChat, GrokUIChat, CopilotUIChat, QwenUIChat, PallyUIChat, AIStudioUIChat, BingUIChat, MistralUIChat, MoonDream, BraveAISearch, DuckDuckGoAISearch
from browser_manager.browser_manager import BrowserConfig
import os

source = QwenUIChat
config = BrowserConfig()
# search works without login : GoogleAISearchChat, QwenUIChat
# config.use_neko = False
# config.browser_executable = "/usr/bin/brave"
# config.headless = True
# BraveAISearch - works in headless browser

if source.__name__ == "MetaUIChat" or source.__name__ == "AIStudioUIChat" or source.__name__ == "QwenUIChat":
	# Set up additional docker flags
	additional_flags = []
	additional_flags.append(f'-v /home/jebin/git/chat_bot_ui_handler:{config.neko_attach_folder}')
	additional_flags.append(f'-v /home/jebin/git/chat_bot_ui_handler/policies.json:/etc/opt/chrome/policies/managed/policies.json')
	config.additionl_docker_flag = ' '.join(additional_flags)

baseUIChat = source(config)

print("--- First Chat (Fresh) ---")
try:
    result1 = baseUIChat.chat_fresh(
        user_prompt=(
            "Describe what is happening in this video frame as if you're telling a story. "
            "Focus on the main subjects, their actions, the setting, and any important "
            "details that would help someone understand the scene's context. "
            "Keep your description to exactly 100 words or fewer."
        ),
        system_prompt="follow user prompt",
        file_path="test.png"
    )
    print(f"Result 1: {result1}")
except Exception as e:
    print(f"Error in First Chat: {e}")

print("--- Second Chat (Fresh - should reuse browser) ---")
try:
    result2 = baseUIChat.chat_fresh(
        user_prompt=(
            "Describe what is happening in this video frame as if you're telling a story. "
            "Focus on the main subjects, their actions, the setting, and any important "
            "details that would help someone understand the scene's context. "
            "Keep your description to exactly 100 words or fewer."
        ),
        system_prompt="follow user prompt",
        file_path="test.png"
    )
    print(f"Result 2: {result2}")
except Exception as e:
    print(f"Error in Second Chat: {e}")

print("--- Cleanup ---")
baseUIChat.cleanup()
print("Done.")

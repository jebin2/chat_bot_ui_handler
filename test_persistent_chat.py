from chat_bot_ui_handler import GeminiUIChat, BraveAISearch
from browser_manager.browser_config import BrowserConfig
import time
import os

source = GeminiUIChat # or BraveAISearch
config = BrowserConfig()
# config.headless = False # Set to False to see what's happening

print("Initializing Chat...")
baseUIChat = source(config)

print("--- First Chat (Fresh) ---")
try:
    result1 = baseUIChat.chat_fresh(
        user_prompt="Say 'First' and nothing else.",
        system_prompt="You are a test bot."
    )
    print(f"Result 1: {result1}")
except Exception as e:
    print(f"Error in First Chat: {e}")

print("--- Second Chat (Fresh - should reuse browser) ---")
try:
    result2 = baseUIChat.chat_fresh(
        user_prompt="Say 'Second' and nothing else.",
        system_prompt="You are a test bot."
    )
    print(f"Result 2: {result2}")
except Exception as e:
    print(f"Error in Second Chat: {e}")

print("--- Cleanup ---")
baseUIChat.cleanup()
print("Done.")

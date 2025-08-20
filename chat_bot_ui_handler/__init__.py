# chat_bot_ui_handler/__init__.py
"""
Chat Bot UI Handler - A package for automating various chatbot UI interactions
"""

__version__ = "0.1.0"

# Import main functions for easy access
from .aistudio.handler import run_gemini_generation
from .search_google.ai_mode import search_google_ai_mode
from .pally.handler import get_caption_from_pally
from .qwen.handler import qwen_ui_chat
from .perplexity.handler import perplexity_ui_chat

from dotenv import load_dotenv
import os
if os.path.exists(".env"):
    print("Loaded load_dotenv")
    load_dotenv()

__all__ = [
    "run_gemini_generation",
    "search_google_ai_mode",
    "get_caption_from_pally",
    "qwen_ui_chat",
    "perplexity_ui_chat",
]
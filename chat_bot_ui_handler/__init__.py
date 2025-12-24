# chat_bot_ui_handler/__init__.py
"""
Chat Bot UI Handler - A package for automating various chatbot UI interactions
"""

__version__ = "0.1.0"

# Import main functions for easy access
from .base_ui_flow import BaseUIChat
from .aistudio.handler import AIStudioUIChat
from .search_google.ai_mode import GoogleAISearchChat
from .pally.handler import PallyUIChat
from .qwen.handler import QwenUIChat
from .perplexity.handler import PerplexityUIChat
from .gemini.handler import GeminiUIChat
from .meta.handler import MetaUIChat
from .grok.handler import GrokUIChat
from .copilot.handler import CopilotUIChat
from .bing.handler import BingUIChat
from .mistral.handler import MistralUIChat
from .moondream.handler import MoonDream
from .brave.handler import BraveAISearch
from .duckduckgo.handler import DuckDuckGoAISearch

from jebin_lib import load_env
load_env()

__all__ = [
    "BaseUIChat",
    "AIStudioUIChat",
    "GoogleAISearchChat",
    "PallyUIChat",
    "QwenUIChat",
    "PerplexityUIChat",
    "GeminiUIChat",
    "MetaUIChat",
    "GrokUIChat",
    "CopilotUIChat",
    "BingUIChat",
    "MistralUIChat",
    "MoonDream",
    "BraveAISearch",
    "DuckDuckGoAISearch"
]
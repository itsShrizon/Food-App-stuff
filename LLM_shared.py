"""
LLM Shared Module - Backward Compatible Facade.

This module re-exports from the core package for backward compatibility.
Actual implementation is in core/llm.py.
"""

from app.core.llm import chatbot, ChatOpenAI

__all__ = ['chatbot']

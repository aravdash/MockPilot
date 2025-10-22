"""
Backend Services

External integrations and services for the Notes Summarizer
"""

from .pinecone_integration import NotesToPinecone

__all__ = ['NotesToPinecone']
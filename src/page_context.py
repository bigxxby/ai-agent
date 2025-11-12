"""
BrowserContext - Manages textual representation of the webpage for AI.

Handles token limits and context formatting.
"""

from typing import Dict, Any
from browser.interface import BrowserInterface
from browser.page_vision import PageVision


class BrowserContext:
    """
    Manages the textual context that AI sees.
    Implements token limits and smart truncation.
    """

    # Estimate: ~4 characters per token
    CHARS_PER_TOKEN = 4

    def __init__(self, browser: BrowserInterface, token_limit: int = 3000):
        """
        Initialize context manager.
        
        Args:
            browser: Browser interface instance
            token_limit: Maximum tokens for context
        """
        self.browser = browser
        self.token_limit = token_limit
        # Don't store vision - create it on demand to always use current page
        
    @property
    def vision(self) -> PageVision:
        """Get PageVision for current page."""
        return PageVision(self.browser.page)

    def capture_current_state(self) -> Dict[str, Any]:
        """
        Capture current page state as text.
        
        Returns:
            Dict with url, title, snapshot, tokens_used, truncated
        """
        snapshot = self.vision.get_text_snapshot()
        
        # Estimate tokens
        estimated_tokens = len(snapshot) // self.CHARS_PER_TOKEN
        truncated = False
        
        # Truncate if needed
        if estimated_tokens > self.token_limit:
            snapshot, truncated = self._truncate_snapshot(snapshot)
            estimated_tokens = len(snapshot) // self.CHARS_PER_TOKEN
        
        return {
            "url": self.browser.get_url(),
            "title": self.browser.get_title(),
            "snapshot": snapshot,
            "tokens_used": estimated_tokens,
            "truncated": truncated
        }

    def _truncate_snapshot(self, snapshot: str) -> tuple[str, bool]:
        """
        Intelligently truncate snapshot to fit token limit.
        
        Args:
            snapshot: Original snapshot
            
        Returns:
            (truncated_snapshot, was_truncated)
        """
        max_chars = self.token_limit * self.CHARS_PER_TOKEN
        
        if len(snapshot) <= max_chars:
            return snapshot, False
        
        # Keep header and truncate elements
        lines = snapshot.split('\n')
        truncated_lines = []
        current_chars = 0
        
        for line in lines:
            if current_chars + len(line) > max_chars:
                truncated_lines.append(
                    f"\n... [TRUNCATED: {len(lines) - len(truncated_lines)} lines omitted]"
                )
                break
            truncated_lines.append(line)
            current_chars += len(line) + 1  # +1 for newline
        
        return '\n'.join(truncated_lines), True

    def discover_elements(self, search_text: str, element_type: str = None) -> list:
        """
        Find elements by text (TWO-STEP discovery process).
        
        Args:
            search_text: Text to search for
            element_type: Optional element type filter
            
        Returns:
            List of discovered elements with selectors
        """
        return self.vision.find_elements(search_text, element_type)

    def get_element_details(self, selector: str) -> str:
        """
        Get detailed information about specific element.
        
        Args:
            selector: CSS selector
            
        Returns:
            Element context
        """
        return self.vision.get_element_context(selector)

"""
BrowserInterface - Synchronous Playwright wrapper for browser automation.

Provides clean API for browser control with focus on reliability.
"""

import os
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright


class BrowserInterface:
    """
    Manages browser lifecycle and provides interaction methods.
    Uses synchronous Playwright for simplicity.
    """

    def __init__(
        self, 
        browser_type: str = "chromium",
        headless: bool = False,
        user_data_dir: Optional[str] = None
    ):
        """
        Initialize browser interface.
        
        Args:
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Run in headless mode
            user_data_dir: Path for persistent browser data (cookies, sessions)
        """
        self.browser_type = browser_type
        self.headless = headless
        self.user_data_dir = user_data_dir or "./user-data"
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def launch(self) -> Page:
        """
        Launch browser and return the page.
        
        Returns:
            Active Playwright page
        """
        self._playwright = sync_playwright().start()
        
        # Get browser launcher
        if self.browser_type == "chromium":
            launcher = self._playwright.chromium
        elif self.browser_type == "firefox":
            launcher = self._playwright.firefox
        elif self.browser_type == "webkit":
            launcher = self._playwright.webkit
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
        
        # Ensure user data directory exists
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # Launch with persistent context (saves cookies, sessions)
        self._context = launcher.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # Get or create page
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()
        
        return self._page

    def shutdown(self):
        """Close browser and cleanup resources."""
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()

    @property
    def page(self) -> Page:
        """Get current page."""
        if not self._page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._page

    # Navigation methods
    
    def navigate(self, url: str, timeout: int = 15000) -> None:
        """
        Navigate to URL.
        
        Args:
            url: URL to navigate to
            timeout: Timeout in milliseconds
        """
        self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    def get_url(self) -> str:
        """Get current URL."""
        return self.page.url

    def get_title(self) -> str:
        """Get page title."""
        return self.page.title()

    def go_back(self) -> None:
        """Navigate back."""
        self.page.go_back(wait_until="domcontentloaded")

    # Tab management methods
    
    def list_tabs(self) -> list:
        """
        List all open tabs.
        
        Returns:
            List of dicts with tab information
        """
        tabs = []
        for i, page in enumerate(self._context.pages):
            tabs.append({
                "index": i,
                "title": page.title(),
                "url": page.url,
                "is_active": page == self._page
            })
        return tabs

    def switch_to_tab(self, tab_index: int) -> None:
        """
        Switch to different tab.
        
        Args:
            tab_index: Zero-based tab index
            
        Raises:
            Exception: If invalid tab index
        """
        pages = self._context.pages
        
        if tab_index < 0 or tab_index >= len(pages):
            raise Exception(f"Invalid tab index: {tab_index}. Available: 0-{len(pages)-1}")
        
        self._page = pages[tab_index]
        try:
            self._page.bring_to_front()
        except Exception:
            pass

    def close_tab(self, tab_index: int) -> None:
        """
        Close a tab by index.
        
        Args:
            tab_index: Zero-based tab index
            
        Raises:
            Exception: If invalid index or trying to close only tab
        """
        pages = self._context.pages
        
        if len(pages) == 1:
            raise Exception("Cannot close the only tab")
        
        if tab_index < 0 or tab_index >= len(pages):
            raise Exception(f"Invalid tab index: {tab_index}")
        
        page_to_close = pages[tab_index]
        
        # If closing active tab, switch to another
        if page_to_close == self._page:
            new_index = tab_index + 1 if tab_index < len(pages) - 1 else tab_index - 1
            self._page = pages[new_index]
            try:
                self._page.bring_to_front()
            except Exception:
                pass
        
        page_to_close.close()

    def get_active_tab_index(self) -> int:
        """
        Get index of active tab.
        
        Returns:
            Zero-based index or -1 if not found
        """
        for i, page in enumerate(self._context.pages):
            if page == self._page:
                return i
        return -1

    # Frame/iframe support
    
    def get_frames(self) -> list:
        """
        Get all frames on current page.
        
        Returns:
            List of frame information
        """
        frames = []
        for i, frame in enumerate(self.page.frames):
            frames.append({
                "index": i,
                "name": frame.name,
                "url": frame.url
            })
        return frames

    # Interaction methods
    
    def click(self, selector: str, timeout: int = 5000) -> None:
        """
        Click element with fallback strategies.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
        """
        try:
            # Try normal click
            self.page.click(selector, timeout=timeout)
        except Exception as e:
            # Try force click as fallback
            try:
                self.page.click(selector, force=True, timeout=timeout)
            except Exception:
                raise Exception(f"Failed to click {selector}: {str(e)}")

    def type_text(self, selector: str, text: str, timeout: int = 5000) -> None:
        """
        Type text into input field.
        
        Args:
            selector: CSS selector for input
            text: Text to type
            timeout: Timeout in milliseconds
        """
        self.page.fill(selector, text, timeout=timeout)

    def press_key(self, key: str) -> None:
        """
        Press keyboard key.
        
        Args:
            key: Key to press (Enter, Escape, etc.)
        """
        self.page.keyboard.press(key)

    def scroll(self, direction: str = "down", pixels: int = 500) -> None:
        """
        Scroll the page.
        
        Args:
            direction: Direction (down, up, top, bottom)
            pixels: Amount to scroll (for down/up)
        """
        if direction == "down":
            self.page.evaluate(f"window.scrollBy(0, {pixels})")
        elif direction == "up":
            self.page.evaluate(f"window.scrollBy(0, -{pixels})")
        elif direction == "top":
            self.page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def hover(self, selector: str, timeout: int = 10000) -> None:
        """
        Hover over element.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
        """
        self.page.hover(selector, timeout=timeout)

    def wait_for_selector(
        self, 
        selector: str, 
        timeout: int = 5000, 
        state: str = "visible"
    ) -> bool:
        """
        Wait for element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            state: Element state (visible, hidden, attached)
            
        Returns:
            True if element appeared, False on timeout
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception:
            return False

    # Utility methods
    
    def screenshot(self, path: str, full_page: bool = False) -> None:
        """
        Take screenshot.
        
        Args:
            path: File path to save
            full_page: Capture full page or viewport only
        """
        self.page.screenshot(path=path, full_page=full_page)

    def evaluate_js(self, script: str) -> any:
        """
        Execute JavaScript on page.
        
        Args:
            script: JavaScript code
            
        Returns:
            Result of execution
        """
        return self.page.evaluate(script)

    def wait(self, seconds: float) -> None:
        """
        Wait for specified seconds.
        
        Args:
            seconds: Time to wait
        """
        self.page.wait_for_timeout(int(seconds * 1000))

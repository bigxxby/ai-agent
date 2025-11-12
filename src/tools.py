"""
BrowserActions - Tools available to the AI agent.

Implements the TWO-STEP interaction pattern:
1. Discover elements by text
2. Interact using discovered selectors
"""

from typing import Dict, Any, List, Callable
from web.interface import BrowserInterface
from src.context import BrowserContext


class BrowserActions:
    """
    Provides action tools for the AI agent.
    All tools return string results for LLM consumption.
    """

    def __init__(self, browser: BrowserInterface, context: BrowserContext):
        """
        Initialize browser actions.
        
        Args:
            browser: Browser interface
            context: Browser context manager
        """
        self.browser = browser
        self.context = context
        
        # Map tool names to handlers
        self._tools: Dict[str, Callable] = {
            "observe_page": self.observe_page,
            "discover_element": self.discover_element,
            "extract_links": self.extract_links,
            "click_element": self.click_element,
            "type_text": self.type_text,
            "hover_element": self.hover_element,
            "press_key": self.press_key,
            "navigate_url": self.navigate_url,
            "navigate_back": self.navigate_back,
            "scroll_page": self.scroll_page,
            "wait_for_element": self.wait_for_element,
            "wait_seconds": self.wait_seconds,
            "check_modals": self.check_modals,
            "get_page_html": self.get_page_html,
            "wait_for_page_load": self.wait_for_page_load,
            "list_tabs": self.list_tabs,
            "switch_tab": self.switch_tab,
            "close_tab": self.close_tab,
            "request_human_help": self.request_human_help,
            "request_confirmation": self.request_confirmation,
            "task_complete": self.task_complete,
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get Anthropic Claude tool calling definitions.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "observe_page",
                "description": "Get text-based snapshot of current page. Use this FIRST to understand page structure before taking actions.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "discover_element",
                "description": "Find elements by visible text (STEP 1 of interaction). Returns selectors for found elements. ALWAYS use this before clicking or typing!",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_text": {
                            "type": "string",
                            "description": "Visible text to search for (e.g., 'Login', 'Submit', 'Search')"
                        },
                        "element_type": {
                            "type": "string",
                            "enum": ["button", "link", "input", "any"],
                            "description": "Type of element to find. Use 'any' if unsure."
                        }
                    },
                    "required": ["search_text"]
                }
            },
            {
                "name": "extract_links",
                "description": "Extract all links with their text and URLs. Useful to find specific links without discover_element errors.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter_text": {
                            "type": "string",
                            "description": "Optional: filter links containing this text (case-insensitive)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "click_element",
                "description": "Click an element (STEP 2 of interaction). Use selector from discover_element. NEVER guess selectors!",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector from discover_element result"
                        },
                        "description": {
                            "type": "string",
                            "description": "What you're clicking (for logging)"
                        }
                    },
                    "required": ["selector", "description"]
                }
            },
            {
                "name": "type_text",
                "description": "Type text into an input field. Use selector from discover_element.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector from discover_element"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "Press Enter after typing (for search boxes)",
                            "default": False
                        }
                    },
                    "required": ["selector", "text"]
                }
            },
            {
                "name": "hover_element",
                "description": "Hover over an element to reveal dropdown menus, tooltips, or hidden content. Use selector from discover_element.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector from discover_element"
                        },
                        "description": {
                            "type": "string",
                            "description": "What you're hovering over (for logging)"
                        }
                    },
                    "required": ["selector", "description"]
                }
            },
            {
                "name": "press_key",
                "description": "Press a keyboard key. Useful for Enter, Escape, Tab, arrows, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key to press: Enter, Escape, Tab, Space, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Backspace, Delete, PageUp, PageDown, Home, End"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "navigate_url",
                "description": "Navigate to a specific URL.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Full URL to navigate to"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "navigate_back",
                "description": "Navigate back to the previous page in browser history.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "scroll_page",
                "description": "Scroll the page to load more content or navigate.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["down", "up", "top", "bottom"],
                            "description": "Scroll direction"
                        },
                        "pixels": {
                            "type": "integer",
                            "description": "Amount to scroll (for down/up)",
                            "default": 500
                        }
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "wait_for_element",
                "description": "Wait for a specific element to appear on the page. Use selector from discover_element or a known selector.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to wait for"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in milliseconds (default 5000)",
                            "default": 5000
                        }
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "wait_seconds",
                "description": "Wait for page to load. Use SHORT waits (1-2 sec). Only use longer waits for slow pages.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "description": "Seconds to wait (1-5 recommended)",
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["seconds"]
                }
            },
            {
                "name": "check_modals",
                "description": "Check for modal windows, popups, or overlays on the page. Use this after clicking buttons or navigating to detect any modals that may have appeared. Returns information about visible modals and their content.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "list_tabs",
                "description": "List all open browser tabs with their titles, URLs, and active status. Use before switching or closing tabs.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "switch_tab",
                "description": "Switch to a different browser tab by index. Use list_tabs first to see available tabs.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tab_index": {
                            "type": "integer",
                            "description": "Zero-based tab index (0 = first tab, 1 = second, etc.)"
                        }
                    },
                    "required": ["tab_index"]
                }
            },
            {
                "name": "close_tab",
                "description": "Close a browser tab by index. Cannot close the only remaining tab. Use list_tabs first.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tab_index": {
                            "type": "integer",
                            "description": "Zero-based tab index to close"
                        }
                    },
                    "required": ["tab_index"]
                }
            },
            {
                "name": "wait_for_page_load",
                "description": "Wait for page to fully load including dynamic content. Use when page seems empty or elements are missing after navigation. Better than wait_seconds for dynamic pages.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Maximum seconds to wait (default: 5)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_page_html",
                "description": "Get raw HTML of the page body (truncated to 5000 chars). Use when observe_page doesn't show expected elements and you need to debug page structure. ONLY use when stuck.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "request_human_help",
                "description": "Request human intervention for tasks requiring manual action (CAPTCHA, 2FA, login, etc.). Use when you detect security barriers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Clear instructions for what the user needs to do manually"
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "request_confirmation",
                "description": "Request user confirmation before destructive/financial/communication actions. ALWAYS use before: purchasing, deleting, payment, canceling subscriptions, sending messages/emails, job applications, posting content.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action_description": {
                            "type": "string",
                            "description": "Clear description of the action (e.g., 'Send job application with cover letter', 'Complete purchase for $99', 'Delete account')"
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["financial", "deletion", "irreversible"],
                            "description": "Risk category"
                        }
                    },
                    "required": ["action_description", "risk_level"]
                }
            },
            {
                "name": "task_complete",
                "description": "Mark the task as FULLY COMPLETE with a summary. Use ONLY when task is accomplished and verified. DO NOT use to ask for information - just continue working with available tools.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Detailed summary of what was accomplished"
                        }
                    },
                    "required": ["summary"]
                }
            },
        ]

    def execute(self, tool_name: str, **kwargs) -> str:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool arguments
            
        Returns:
            Result string for LLM
        """
        handler = self._tools.get(tool_name)
        if not handler:
            return f"❌ Unknown tool: {tool_name}"
        
        try:
            return handler(**kwargs)
        except Exception as e:
            return f"❌ Error executing {tool_name}: {str(e)}"

    # Tool implementations

    def observe_page(self) -> str:
        """Get current page snapshot."""
        # Give page a moment to render dynamic content
        import time
        time.sleep(0.2)
        
        state = self.context.capture_current_state()
        
        result = f"📄 Current Page State:\n\n{state['snapshot']}"
        
        if state['truncated']:
            result += f"\n\n⚠️ Note: Snapshot truncated (using {state['tokens_used']} tokens)"
        
        # Add tabs information automatically
        tabs = self.browser.list_tabs()
        if len(tabs) > 1:
            result += f"\n\n📑 Open Tabs ({len(tabs)} total):\n"
            
            # Find current tab index
            current_url = self.browser.get_url()
            current_idx = 0
            for idx, tab in enumerate(tabs):
                if tab['url'] == current_url:
                    current_idx = idx
                    break
            
            for idx, tab in enumerate(tabs):
                marker = "→ " if idx == current_idx else "  "
                title = tab['title'][:60]
                result += f"{marker}{idx}. {title}\n"
            result += "\n💡 Use switch_tab(index) to switch between tabs"
        
        return result

    def discover_element(self, search_text: str, element_type: str = "any") -> str:
        """
        Discover elements by text (STEP 1).
        
        Args:
            search_text: Text to search for
            element_type: Element type filter
            
        Returns:
            Formatted result with selectors
        """
        type_filter = None if element_type == "any" else element_type
        
        found = self.context.discover_elements(search_text, type_filter)
        
        if not found:
            return f"❌ No elements found with text '{search_text}'"
        
        if len(found) == 1:
            elem = found[0]
            return f"✅ Found 1 element:\n" \
                   f"  Selector: {elem['selector']}\n" \
                   f"  Text: {elem['text'][:80]}\n" \
                   f"  Tag: <{elem['tag']}>"
        
        # Multiple results
        lines = [f"✅ Found {len(found)} elements:"]
        for idx, elem in enumerate(found, 1):
            lines.append(
                f"\n{idx}. Selector: {elem['selector']}\n" \
                f"   Text: {elem['text'][:60]}\n" \
                f"   Tag: <{elem['tag']}>"
            )
        
        lines.append("\n💡 Use the selector from the list above for interact_click or interact_type")
        
        return "\n".join(lines)

    def extract_links(self, filter_text: str = None) -> str:
        """
        Extract all links from the page.
        
        Args:
            filter_text: Optional text filter (case-insensitive)
            
        Returns:
            Formatted list of links with URLs
        """
        try:
            script = """
            () => {
                const links = [];
                const elements = document.querySelectorAll('a[href]');
                
                elements.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    // Check visibility
                    if (style.display === 'none' || 
                        style.visibility === 'hidden' ||
                        rect.width === 0 || 
                        rect.height === 0) return;
                    
                    const text = (el.innerText || el.textContent || '').trim();
                    const href = el.getAttribute('href');
                    
                    if (text && href) {
                        links.push({
                            text: text.substring(0, 100),
                            href: href,
                            index: idx
                        });
                    }
                });
                
                return links;
            }
            """
            
            links = self.browser.page.evaluate(script)
            
            if not links:
                return "❌ No links found on page"
            
            # Filter if requested
            if filter_text:
                filter_lower = filter_text.lower()
                links = [l for l in links if filter_lower in l['text'].lower()]
            
            if not links:
                return f"❌ No links found containing '{filter_text}'"
            
            # Format output
            lines = [f"🔗 Found {len(links)} link(s):\n"]
            
            for idx, link in enumerate(links[:20], 1):  # Limit to 20
                text_preview = link['text'][:60]
                href_preview = link['href'][:80]
                lines.append(f"{idx}. {text_preview}")
                lines.append(f"   URL: {href_preview}\n")
            
            if len(links) > 20:
                lines.append(f"\n... and {len(links) - 20} more links")
            
            lines.append("\n💡 Use navigate_url with the URL to open the link")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ Failed to extract links: {str(e)}"

    def click_element(self, selector: str, description: str) -> str:
        """
        Click element (STEP 2).
        
        Args:
            selector: CSS selector from discover_element
            description: What you're clicking
            
        Returns:
            Result message
        """
        try:
            # Check if element is a link with href
            # Escape single quotes in selector
            escaped_selector = selector.replace("'", "\\'")
            check_link_script = f"""
            () => {{
                const element = document.querySelector('{escaped_selector}');
                if (!element) return null;
                
                // Check if element is a link or contains a link
                if (element.tagName.toLowerCase() === 'a' && element.href) {{
                    return {{
                        isLink: true,
                        href: element.href,
                        target: element.target || '_self'
                    }};
                }}
                
                // Check if element contains a link
                const link = element.querySelector('a[href]');
                if (link) {{
                    return {{
                        isLink: true,
                        href: link.href,
                        target: link.target || '_self'
                    }};
                }}
                
                return {{ isLink: false }};
            }}
            """
            
            link_info = self.browser.evaluate_js(check_link_script)
            
            # If it's a link and opens in same tab, use navigate_url instead
            if link_info and link_info.get('isLink') and link_info.get('target') == '_self':
                href = link_info.get('href')
                if href and not href.startswith('javascript:'):
                    # Use direct navigation for links
                    self.browser.navigate(href)
                    self.browser.wait(0.5)
                    
                    current_url = self.browser.get_url()
                    result = f"✅ Navigated via link: {description}\n"
                    result += f"Current URL: {current_url}"
                    
                    # Check for modals after navigation
                    modal_check = self.check_modals()
                    if not modal_check.startswith("✅ No modal"):
                        result += f"\n\n{modal_check}"
                    
                    return result
            
            # Remember current tabs count and active tab
            tabs_before = self.browser.list_tabs()
            initial_tab_count = len(tabs_before) if tabs_before else 1
            initial_url = self.browser.get_url()
            
            # Perform the click
            self.browser.click(selector)
            
            # Wait a bit for any modals or new tabs to appear
            self.browser.wait(0.5)
            
            # Check if new tabs were opened
            tabs_after = self.browser.list_tabs()
            current_tab_count = len(tabs_after) if tabs_after else 1
            new_tabs_opened = current_tab_count - initial_tab_count
            
            # Build result message
            result = f"✅ Clicked: {description}\n"
            
            # Check if we're still on the same tab or navigated
            current_url = self.browser.get_url()
            
            if new_tabs_opened > 0:
                result += f"🆕 {new_tabs_opened} new tab(s) opened!\n"
                result += f"Current tab URL: {current_url}\n\n"
                
                # Show info about new tabs
                result += "New tabs:\n"
                for tab in tabs_after[-new_tabs_opened:]:
                    result += f"  - Tab {tab['index']}: {tab['title'][:50]}\n"
                    result += f"    URL: {tab['url'][:70]}\n"
                
                result += f"\n💡 Use switch_tab({tabs_after[-1]['index']}) to switch to the newest tab"
            else:
                result += f"Current URL: {current_url}"
                
                # Check if URL changed (navigation on same tab)
                if current_url != initial_url:
                    result += " (navigated)"
            
            # Check for modals after click
            modal_check = self.check_modals()
            
            # Append modal info if any found
            if not modal_check.startswith("✅ No modal"):
                result += f"\n\n{modal_check}"
            
            return result
        except Exception as e:
            return f"❌ Failed to click '{description}': {str(e)}"

    def type_text(self, selector: str, text: str, press_enter: bool = False) -> str:
        """
        Type into input field.
        
        Args:
            selector: CSS selector
            text: Text to type
            press_enter: Whether to press Enter
            
        Returns:
            Result message
        """
        try:
            self.browser.type_text(selector, text)
            
            if press_enter:
                self.browser.press_key("Enter")
                return f"✅ Typed '{text}' and pressed Enter"
            
            return f"✅ Typed into field: {text}"
        except Exception as e:
            return f"❌ Failed to type: {str(e)}"

    def hover_element(self, selector: str, description: str) -> str:
        """
        Hover over element to reveal dropdowns/tooltips.
        
        Args:
            selector: CSS selector
            description: What you're hovering over
            
        """
        try:
            self.browser.hover(selector)
            return f"✅ Hovered over: {description}"
        except Exception as e:
            return f"❌ Failed to hover: {str(e)}"

    def press_key(self, key: str) -> str:
        """
        Press keyboard key.
        
        Args:
            key: Key name
            
        Returns:
            Result message
        """
        try:
            self.browser.press_key(key)
            return f"✅ Pressed key: {key}"
        except Exception as e:
            return f"❌ Failed to press key: {str(e)}"

    def navigate_url(self, url: str) -> str:
        """
        Navigate to URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Result message
        """
        try:
            self.browser.navigate(url)
            title = self.browser.get_title()
            return f"✅ Navigated to: {url}\n" \
                   f"Page title: {title}"
        except Exception as e:
            return f"❌ Failed to navigate: {str(e)}"

    def navigate_back(self) -> str:
        """
        Navigate back to previous page.
        
        Returns:
            Result message
        """
        try:
            self.browser.go_back()
            new_url = self.browser.get_url()
            return f"✅ Navigated back to: {new_url}"
        except Exception as e:
            return f"❌ Failed to go back: {str(e)}"

    def scroll_page(self, direction: str, pixels: int = 500) -> str:
        """
        Scroll page.
        
        Args:
            direction: Scroll direction
            pixels: Amount to scroll
            
        Returns:
            Result message
        """
        try:
            self.browser.scroll(direction, pixels)
            return f"✅ Scrolled {direction}"
        except Exception as e:
            return f"❌ Failed to scroll: {str(e)}"

    def wait_for_element(self, selector: str, timeout: int = 5000) -> str:
        """
        Wait for element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            Result message
        """
        try:
            success = self.browser.wait_for_selector(selector, timeout)
            if success:
                return f"✅ Element appeared: {selector}"
            else:
                return f"⚠️ Element did not appear within timeout: {selector}"
        except Exception as e:
            return f"❌ Wait failed: {str(e)}"

    def wait_seconds(self, seconds: float) -> str:
        """
        Wait for specified time.
        
        Args:
            seconds: Time to wait
            
        Returns:
            Result message
        """
        try:
            self.browser.wait(seconds)
            return f"⏱️ Waited {seconds} seconds"
        except Exception as e:
            return f"❌ Wait failed: {str(e)}"

    def check_modals(self) -> str:
        """
        Check for modal windows, popups, or overlays on the page.
        
        Returns:
            Information about visible modals
        """
        try:
            # JavaScript to detect modals, overlays, and popups
            script = """
            () => {
                const modals = [];
                
                // Common modal selectors
                const modalSelectors = [
                    '[role="dialog"]',
                    '[role="alertdialog"]',
                    '.modal',
                    '.popup',
                    '.overlay',
                    '.dialog',
                    '[class*="modal"]',
                    '[class*="popup"]',
                    '[class*="dialog"]',
                    '[class*="overlay"]',
                    '[id*="modal"]',
                    '[id*="popup"]',
                    '[id*="dialog"]'
                ];
                
                // Check each selector
                modalSelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((el, idx) => {
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            
                            // Check if element is actually visible
                            if (style.display !== 'none' && 
                                style.visibility !== 'hidden' &&
                                style.opacity !== '0' &&
                                rect.width > 0 && 
                                rect.height > 0) {
                                
                                // Get text content
                                const text = (el.innerText || el.textContent || '').trim();
                                
                                // Find buttons in modal
                                const buttons = [];
                                const buttonElements = el.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]');
                                buttonElements.forEach(btn => {
                                    const btnStyle = window.getComputedStyle(btn);
                                    if (btnStyle.display !== 'none' && btnStyle.visibility !== 'hidden') {
                                        const btnText = (btn.innerText || btn.textContent || btn.value || '').trim();
                                        if (btnText) {
                                            buttons.push({
                                                text: btnText,
                                                id: btn.id,
                                                class: btn.className
                                            });
                                        }
                                    }
                                });
                                
                                // Find close buttons
                                const closeButtons = [];
                                const closeBtnElements = el.querySelectorAll('[aria-label*="close" i], [title*="close" i], .close, .modal-close, button[aria-label*="закрыть" i]');
                                closeBtnElements.forEach(btn => {
                                    const btnStyle = window.getComputedStyle(btn);
                                    if (btnStyle.display !== 'none' && btnStyle.visibility !== 'hidden') {
                                        closeButtons.push({
                                            selector: btn.id ? `#${btn.id}` : btn.className.split(' ')[0] ? `.${btn.className.split(' ')[0]}` : 'button',
                                            text: (btn.innerText || btn.textContent || btn.getAttribute('aria-label') || '').trim()
                                        });
                                    }
                                });
                                
                                modals.push({
                                    selector: el.id ? `#${el.id}` : el.className.split(' ')[0] ? `.${el.className.split(' ')[0]}` : selector,
                                    text: text.substring(0, 300),
                                    buttons: buttons,
                                    closeButtons: closeButtons,
                                    dimensions: {
                                        width: rect.width,
                                        height: rect.height,
                                        top: rect.top,
                                        left: rect.left
                                    }
                                });
                            }
                        });
                    } catch (e) {
                        // Skip selector if it fails
                    }
                });
                
                // Remove duplicates based on position
                const unique = [];
                const seen = new Set();
                modals.forEach(modal => {
                    const key = `${modal.dimensions.top}-${modal.dimensions.left}-${modal.dimensions.width}-${modal.dimensions.height}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        unique.push(modal);
                    }
                });
                
                return unique;
            }
            """
            
            modals = self.browser.evaluate_js(script)
            
            if not modals or len(modals) == 0:
                return "✅ No modal windows detected"
            
            # Format response
            lines = [f"🪟 Detected {len(modals)} modal window(s):\n"]
            
            for idx, modal in enumerate(modals, 1):
                lines.append(f"\n--- Modal {idx} ---")
                lines.append(f"Selector: {modal['selector']}")
                
                if modal['text']:
                    preview = modal['text'][:200]
                    if len(modal['text']) > 200:
                        preview += "..."
                    lines.append(f"Content preview: {preview}")
                
                if modal['buttons']:
                    lines.append(f"\nButtons found ({len(modal['buttons'])}):")
                    for btn in modal['buttons'][:5]:  # Limit to 5 buttons
                        btn_id = f" (id='{btn['id']}')" if btn['id'] else ""
                        btn_class = f" (class='{btn['class']}')" if btn['class'] and not btn['id'] else ""
                        lines.append(f"  - {btn['text']}{btn_id}{btn_class}")
                
                if modal['closeButtons']:
                    lines.append(f"\nClose buttons:")
                    for btn in modal['closeButtons'][:3]:
                        lines.append(f"  - Selector: {btn['selector']}")
                        if btn['text']:
                            lines.append(f"    Text: {btn['text']}")
            
            lines.append("\n💡 Use discover_element to find specific buttons in the modal, then interact_click to click them.")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ Failed to check modals: {str(e)}"

    def get_page_html(self) -> str:
        """
        Get raw HTML of page body for debugging.
        Use when observe_page doesn't show expected elements.
        
        Returns:
            Truncated HTML content
        """
        try:
            html = self.browser.page.content()
            
            # Remove scripts and styles to reduce size
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            cleaned = str(soup.body) if soup.body else str(soup)
            
            # Truncate to 5000 chars
            if len(cleaned) > 5000:
                cleaned = cleaned[:5000] + "\n\n... [TRUNCATED - showing first 5000 chars]"
            
            return f"📄 Page HTML:\n\n{cleaned}"
            
        except Exception as e:
            return f"❌ Failed to get HTML: {str(e)}"

    def wait_for_page_load(self, timeout: int = 5) -> str:
        """
        Wait for page to fully load including dynamic content.
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            Status message
        """
        try:
            # Wait for network to be idle (no requests for 500ms)
            self.browser.page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            
            # Also wait for any load event
            self.browser.page.wait_for_load_state("load", timeout=timeout * 1000)
            
            # Give extra time for JavaScript to render
            import time
            time.sleep(0.3)
            
            return f"✅ Page fully loaded (waited up to {timeout}s)"
            
        except Exception as e:
            return f"⚠️ Page load timeout or error: {str(e)}"

    def list_tabs(self) -> str:
        """
        List all open tabs.
        
        Returns:
            Formatted list of tabs
        """
        try:
            tabs = self.browser.list_tabs()
            if not tabs:
                return "❌ No tabs found"
            
            lines = [f"📑 Found {len(tabs)} open tab(s):\n"]
            for tab in tabs:
                active = " [ACTIVE]" if tab["is_active"] else ""
                lines.append(
                    f"{tab['index']}. {tab['title'][:50]}\n"
                    f"   URL: {tab['url'][:60]}{active}"
                )
            
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Failed to list tabs: {str(e)}"

    def switch_tab(self, tab_index: int) -> str:
        """
        Switch to different tab.
        
        Args:
            tab_index: Tab index
            
        Returns:
            Result message
        """
        try:
            self.browser.switch_to_tab(tab_index)
            tabs = self.browser.list_tabs()
            active = tabs[tab_index]
            return f"✅ Switched to tab {tab_index}:\n" \
                   f"   {active['title'][:50]}\n" \
                   f"   URL: {active['url'][:60]}"
        except Exception as e:
            return f"❌ Failed to switch tab: {str(e)}"

    def close_tab(self, tab_index: int) -> str:
        """
        Close a tab.
        
        Args:
            tab_index: Tab index to close
            
        Returns:
            Result message
        """
        try:
            tabs = self.browser.list_tabs()
            if tab_index < len(tabs):
                tab_info = tabs[tab_index]
                self.browser.close_tab(tab_index)
                return f"✅ Closed tab {tab_index}: {tab_info['title'][:50]}"
            return f"❌ Invalid tab index: {tab_index}"
        except Exception as e:
            return f"❌ Failed to close tab: {str(e)}"

    def request_human_help(self, description: str) -> str:
        """
        Request human intervention.
        
        Args:
            description: What the user needs to do
            
        Returns:
            Special signal for agent core to handle
        """
        return f"🚨 HUMAN_HELP_NEEDED: {description}"

    def request_confirmation(self, action_description: str, risk_level: str) -> str:
        """
        Request user confirmation for risky action.
        
        Args:
            action_description: Description of action
            risk_level: Risk category
            
        Returns:
            Special signal for agent core to handle
        """
        return f"⚠️ CONFIRMATION_REQUIRED:{risk_level}:{action_description}"

    def task_complete(self, summary: str) -> str:
        """
        Mark task as complete.
        
        Args:
            summary: Summary of accomplishments
            
        Returns:
            Special signal for agent core
        """
        return f"✅ TASK_COMPLETE: {summary}"

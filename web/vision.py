"""
PageVision - Transform visual DOM into text representation.

This module implements the "text-based vision" concept where AI agent
"sees" the webpage through structured text rather than screenshots.
"""

from typing import List, Dict, Any, Optional
from playwright.sync_api import Page


class PageVision:
    """
    Converts DOM structure into AI-readable text representation.
    Uses accessibility tree + JavaScript to extract semantic structure.
    """

    def __init__(self, page: Page):
        self.page = page

    def get_text_snapshot(self) -> str:
        """
        Create text-based snapshot of the current page.
        This is what the AI "sees".
        
        Returns:
            Formatted text representation with URL, title, and interactive elements
        """
        # Give JavaScript a moment to execute and render
        import time
        time.sleep(0.15)
        
        url = self.page.url
        title = self.page.title()
        
        elements = self._extract_interactive_elements()
        
        # Format as readable text
        lines = [
            f"=== PAGE SNAPSHOT ===",
            f"URL: {url}",
            f"Title: {title}",
            f"",
            f"=== INTERACTIVE ELEMENTS ===",
        ]
        
        # Group by type
        grouped = self._group_by_type(elements)
        
        for element_type, items in grouped.items():
            if not items:
                continue
                
            lines.append(f"\n[{element_type.upper()}]")
            
            # Show more items for important types
            if element_type in ['product-card', 'order-item', 'heading', 'navigation', 
                               'price', 'badge', 'cart-item']:
                limit = 30
            else:
                limit = 15
            
            for idx, item in enumerate(items[:limit], 1):
                name = item.get('text', '')[:150]
                selector_hint = self._build_selector_hint(item)
                lines.append(f"  {idx}. {name} {selector_hint}")
            
            if len(items) > limit:
                lines.append(f"  ... (+{len(items) - limit} more)")
        
        return "\n".join(lines)

    def _extract_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Extract interactive elements using JavaScript execution.
        Returns list of elements with their properties.
        """
        script = """
        () => {
            const elements = [];
            
            // Define what we're looking for
            const selectors = [
                'button', 
                'a[href]', 
                'input', 
                'select', 
                'textarea',
                '[role="button"]', 
                '[role="link"]',
                '[role="tab"]',
                '[role="menuitem"]',
                '[role="option"]',
                '[onclick]',
                '[contenteditable="true"]',
                'form',
                'label',
                '[data-product-id]',
                'article',
                '[class*="card"]',
                '[class*="item"]',
                '[class*="product"]',
                '[class*="order"]',
                '[class*="cart"]',
                '[class*="checkout"]',
                'h1', 'h2', 'h3', 'h4',
                'p[class*="price"]',
                'span[class*="price"]',
                'div[class*="price"]',
                '[class*="badge"]',
                '[class*="tag"]',
                '[class*="label"]',
                'img[alt]',
                'nav',
                'menu',
                'ul[class]',
                'li[class*="item"]',
                'section[class]',
                'aside',
                '[data-testid]',
                '[data-qa]',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '[class*="dropdown"]'
            ];
            
            // Find all matching elements
            const found = document.querySelectorAll(selectors.join(', '));
            
            found.forEach((el, index) => {
                // Check visibility - but be more lenient for form elements
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                const isHidden = (
                    style.display === 'none' ||
                    style.visibility === 'hidden' ||
                    style.opacity === '0'
                );
                
                const isFormElement = ['input', 'textarea', 'select', 'form'].includes(el.tagName.toLowerCase());
                const hasSize = rect.width > 0 && rect.height > 0;
                
                // For form elements, check if they or their parent is visible
                if (isHidden) return;
                if (!isFormElement && !hasSize) return;
                
                // Determine element type
                let type = el.tagName.toLowerCase();
                // Safely get className as string
                const className = (typeof el.className === 'string' 
                    ? el.className 
                    : (el.className.baseVal || el.className.animVal || '')).toLowerCase();
                const role = el.getAttribute('role');
                
                // Links
                if (type === 'a') type = 'link';
                
                // Buttons and inputs
                if (type === 'input') {
                    const inputType = el.getAttribute('type') || 'text';
                    type = inputType === 'submit' || inputType === 'button' 
                        ? 'button' 
                        : 'input';
                }
                if (el.hasAttribute('contenteditable')) type = 'input';
                
                // Images with alt text
                if (type === 'img' && el.getAttribute('alt')) {
                    type = 'image';
                }
                
                // Navigation and menus
                if (type === 'nav' || role === 'navigation') type = 'navigation';
                if (type === 'menu' || role === 'menu') type = 'menu';
                if (role === 'menuitem') type = 'menu-item';
                if (role === 'tab') type = 'tab';
                
                // Lists and list items
                if (type === 'ul' && el.hasAttribute('class')) type = 'list';
                if (type === 'li' && className.includes('item')) type = 'list-item';
                
                // Sections and containers
                if (type === 'section' && el.hasAttribute('class')) type = 'section';
                if (type === 'aside') type = 'sidebar';
                
                // Product cards
                if (type === 'article' || 
                    className.includes('card') ||
                    className.includes('product') ||
                    el.hasAttribute('data-product-id')) {
                    type = 'product-card';
                }
                
                // Order/cart related
                if (className.includes('order') && !className.includes('button')) {
                    type = 'order-item';
                }
                if (className.includes('cart') && !className.includes('button')) {
                    type = 'cart-item';
                }
                
                // Modals and popups
                if (className.includes('modal') || className.includes('popup') || 
                    className.includes('dialog') || role === 'dialog') {
                    type = 'modal';
                }
                
                // Badges, tags, labels
                if (className.includes('badge') || className.includes('tag')) {
                    type = 'badge';
                }
                if (className.includes('label') && type !== 'label') {
                    type = 'tag';
                }
                
                // Prices
                if (className.includes('price') || el.hasAttribute('data-price')) {
                    type = 'price';
                }
                
                // Dropdowns
                if (className.includes('dropdown') || role === 'listbox') {
                    type = 'dropdown';
                }
                
                // Get text content with better fallbacks
                let text = el.innerText || 
                          el.textContent || 
                          el.value || 
                          el.placeholder || 
                          el.getAttribute('aria-label') || 
                          el.getAttribute('title') || 
                          el.getAttribute('alt') ||
                          el.getAttribute('name') ||
                          '';
                
                text = text.trim();
                
                // For product cards, try to extract name and price
                if (type === 'product-card') {
                    const nameEl = el.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                    const priceEl = el.querySelector('[class*="price"]');
                    
                    if (nameEl) {
                        text = nameEl.innerText || nameEl.textContent;
                        if (priceEl) {
                            const price = priceEl.innerText || priceEl.textContent;
                            text += ' | ' + price;
                        }
                    }
                }
                
                // For order items, extract order details
                if (type === 'order-item') {
                    const nameEl = el.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                    const statusEl = el.querySelector('[class*="status"]');
                    const priceEl = el.querySelector('[class*="price"], [class*="total"]');
                    
                    if (nameEl) {
                        text = nameEl.innerText || nameEl.textContent;
                        if (priceEl) {
                            text += ' | ' + (priceEl.innerText || priceEl.textContent);
                        }
                        if (statusEl) {
                            text += ' | ' + (statusEl.innerText || statusEl.textContent);
                        }
                    }
                }
                
                // For images, use alt text
                if (type === 'image') {
                    text = el.getAttribute('alt') || text;
                }
                
                // For form elements, include even if no text
                // Also include labels, headings, and special elements
                const importantTypes = ['form', 'label', 'h1', 'h2', 'h3', 'h4', 'heading', 
                                       'navigation', 'section', 'modal', 'price', 'badge'];
                if (!text && !isFormElement && !importantTypes.includes(type)) return;
                
                // For empty textareas, add a hint
                if (type === 'textarea' && !text) {
                    text = '<empty textarea>';
                }
                
                // For headings, mark them
                if (['h1', 'h2', 'h3', 'h4'].includes(type)) {
                    text = `[${type.toUpperCase()}] ` + text;
                    type = 'heading';
                }
                
                // Collect attributes for selector generation
                // Safely get className as string or array
                const classNameStr = typeof el.className === 'string' 
                    ? el.className 
                    : (el.className.baseVal || el.className.animVal || '');
                
                elements.push({
                    type: type,
                    text: text.substring(0, 200),
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    classes: classNameStr ? classNameStr.split(' ').slice(0, 3) : [],
                    name: el.getAttribute('name'),
                    href: el.getAttribute('href'),
                    role: el.getAttribute('role'),
                    placeholder: el.getAttribute('placeholder'),
                    index: index
                });
            });
            
            return elements;
        }
        """
        
        try:
            return self.page.evaluate(script) or []
        except Exception as e:
            print(f"Warning: Failed to extract elements: {e}")
            return []

    def find_elements(self, search_text: str, element_type: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Find elements by text content (TWO-STEP INTERACTION).
        Temporarily marks elements and returns selectors.
        
        Args:
            search_text: Text to search for
            element_type: Optional filter by type (button, link, input)
            
        Returns:
            List of found elements with temporary selectors
        """
        escaped_text = search_text.replace("'", "\\'").replace('"', '\\"')
        
        # Build type filter check - будет использоваться как отдельное условие
        if element_type and element_type != 'any':
            type_check = f"""
                // Check element type
                let tagName = node.tagName.toLowerCase();
                let matchesType = false;
                
                if ('{element_type}' === 'button') {{
                    matchesType = (tagName === 'button' || 
                                 (tagName === 'input' && (node.type === 'button' || node.type === 'submit')) ||
                                 node.getAttribute('role') === 'button');
                }} else if ('{element_type}' === 'link') {{
                    matchesType = (tagName === 'a' || node.getAttribute('role') === 'link');
                }} else if ('{element_type}' === 'input') {{
                    matchesType = (tagName === 'input' || tagName === 'textarea' || tagName === 'select' || 
                                 node.hasAttribute('contenteditable'));
                }} else {{
                    matchesType = (tagName === '{element_type}');
                }}
                
                if (!matchesType) continue;
            """
        else:
            type_check = "// No type filter"
        
        script = f"""
        () => {{
            const searchText = '{escaped_text}'.toLowerCase();
            const interactiveTags = ['button', 'a', 'input', 'select', 'textarea'];
            
            // Helper: Calculate element priority (higher = better match)
            const getPriority = (node) => {{
                let priority = 0;
                const tag = node.tagName.toLowerCase();
                
                // Prefer interactive elements
                if (interactiveTags.includes(tag)) priority += 100;
                if (node.getAttribute('role') === 'button' || node.getAttribute('role') === 'link') {{
                    priority += 80;
                }}
                
                // Check if text is directly in this element (not just in children)
                const ownText = Array.from(node.childNodes)
                    .filter(n => n.nodeType === Node.TEXT_NODE)
                    .map(n => n.textContent.trim())
                    .join(' ');
                
                if (ownText.toLowerCase().includes(searchText)) {{
                    priority += 50; // Direct text match is better
                }}
                
                // CRITICAL: Penalize text-only elements inside interactive elements
                // If this is a span/div inside a button/link, heavily penalize it
                if (['span', 'div', 'p'].includes(tag)) {{
                    let parent = node.parentElement;
                    if (parent && interactiveTags.includes(parent.tagName.toLowerCase())) {{
                        priority -= 200; // Heavy penalty - prefer the parent instead
                    }}
                }}
                
                // Penalize generic containers
                if (['div', 'span', 'body', 'html'].includes(tag)) priority -= 20;
                
                // Prefer elements with shorter text (more specific)
                const textLength = node.textContent.length;
                priority -= Math.min(textLength / 100, 30);
                
                return priority;
            }};
            
            // Walk through all elements
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                null
            );
            
            let node;
            const candidates = [];
            
            while (node = walker.nextNode()) {{
                // Get all possible text sources
                const innerText = (node.innerText || '').toLowerCase();
                const textContent = (node.textContent || '').toLowerCase();
                const placeholder = (node.getAttribute('placeholder') || '').toLowerCase();
                const ariaLabel = (node.getAttribute('aria-label') || '').toLowerCase();
                const title = (node.getAttribute('title') || '').toLowerCase();
                const alt = (node.getAttribute('alt') || '').toLowerCase();
                const name = (node.getAttribute('name') || '').toLowerCase();
                
                // Check if any text matches
                const hasMatch = innerText.includes(searchText) || 
                               textContent.includes(searchText) ||
                               placeholder.includes(searchText) ||
                               ariaLabel.includes(searchText) ||
                               title.includes(searchText) ||
                               alt.includes(searchText) ||
                               name.includes(searchText);
                
                if (!hasMatch) continue;
                
                {type_check}
                
                // Check visibility
                const rect = node.getBoundingClientRect();
                const style = window.getComputedStyle(node);
                
                if (style.display === 'none' || 
                    style.visibility === 'hidden' ||
                    rect.width === 0 || 
                    rect.height === 0) continue;
                
                // Collect display text
                let displayText = node.innerText || node.textContent || 
                                node.getAttribute('placeholder') || 
                                node.getAttribute('aria-label') || 
                                node.getAttribute('title') || '';
                
                // Safely get className
                const nodeClassName = typeof node.className === 'string' 
                    ? node.className 
                    : (node.className.baseVal || node.className.animVal || null);
                
                candidates.push({{
                    node: node,
                    priority: getPriority(node),
                    text: displayText.substring(0, 100),
                    tag: node.tagName.toLowerCase(),
                    id: node.id || null,
                    classes: nodeClassName
                }});
            }}
            
            // Sort by priority (best matches first)
            candidates.sort((a, b) => b.priority - a.priority);
            
            // Take top 10 matches and assign selectors
            const results = [];
            const topMatches = candidates.slice(0, 10);
            
            topMatches.forEach((item, idx) => {{
                item.node.setAttribute('data-vision-discover', idx);
                results.push({{
                    selector: '[data-vision-discover="' + idx + '"]',
                    text: item.text,
                    tag: item.tag,
                    id: item.id,
                    classes: item.classes,
                    priority: item.priority
                }});
            }});
            
            return results;
        }}
        """
        
        try:
            results = self.page.evaluate(script)
            return results or []
        except Exception as e:
            print(f"Error in discover_by_text: {e}")
            return []

    def _group_by_type(self, elements: List[Dict]) -> Dict[str, List[Dict]]:
        """Group elements by their type."""
        grouped = {}
        for elem in elements:
            elem_type = elem.get('type', 'other')
            if elem_type not in grouped:
                grouped[elem_type] = []
            grouped[elem_type].append(elem)
        return grouped

    def _build_selector_hint(self, element: Dict) -> str:
        """Build a selector hint for display."""
        parts = [f"<{element.get('tag', 'unknown')}>"]
        
        if element.get('id'):
            parts.append(f"#{element['id']}")
        elif element.get('classes') and len(element['classes']) > 0:
            parts.append(f".{element['classes'][0]}")
        
        return "".join(parts)

    def get_accessibility_tree(self) -> Optional[Dict]:
        """
        Get the accessibility tree snapshot.
        This is a semantic representation used by screen readers.
        """
        try:
            return self.page.accessibility.snapshot()
        except Exception as e:
            print(f"Warning: Could not get accessibility tree: {e}")
            return None

    def extract_visible_text(self) -> str:
        """Extract all visible text from the page."""
        try:
            return self.page.inner_text("body")
        except Exception:
            return ""

    def get_element_context(self, selector: str, max_length: int = 1000) -> str:
        """
        Get detailed context for a specific element.
        
        Args:
            selector: CSS selector
            max_length: Maximum characters to return
            
        Returns:
            HTML content or error message
        """
        try:
            element = self.page.query_selector(selector)
            if not element:
                return "Element not found"
            
            html = element.inner_html()
            
            if len(html) > max_length:
                html = html[:max_length] + "... [TRUNCATED]"
            
            return html
        except Exception as e:
            return f"Error: {str(e)}"

"""Инструменты для работы с браузером через Playwright."""

import asyncio
import os
from typing import Optional, Dict, Any
from playwright.async_api import Page, Browser
from utils import Logger, create_screenshots_dir, generate_screenshot_filename


class BrowserTools:
    """Набор инструментов для управления браузером."""
    
    def __init__(self, page: Page, browser: Browser):
        """
        Инициализация инструментов браузера.
        
        Args:
            page: Playwright Page объект
            browser: Playwright Browser объект
        """
        self.page = page
        self.browser = browser
        self.screenshots_dir = create_screenshots_dir()
    
    async def navigate_to_url(self, url: str) -> str:
        """
        Навигация по URL.
        
        Args:
            url: URL для перехода
            
        Returns:
            Результат навигации
        """
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(0.5)  # Короткая пауза для стабильности
            current_url = self.page.url
            return f"Successfully navigated to {current_url}"
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"
    
    async def take_screenshot(self, full_page: bool = False) -> str:
        """
        Делает скриншот текущей страницы.
        
        Args:
            full_page: Сделать скриншот всей страницы или только видимой части
            
        Returns:
            Путь к сохраненному скриншоту
        """
        try:
            filename = generate_screenshot_filename()
            filepath = os.path.join(self.screenshots_dir, filename)
            await self.page.screenshot(path=filepath, full_page=full_page)
            return f"Screenshot saved as {filepath}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    async def click_element(self, selector: str) -> str:
        """
        Кликает по элементу на странице.
        
        Args:
            selector: CSS селектор элемента
            
        Returns:
            Результат клика
        """
        try:
            # Ждем, пока элемент появится
            await self.page.wait_for_selector(selector, timeout=10000, state="visible")
            await self.page.click(selector)
            await asyncio.sleep(0.5)  # Короткая пауза после клика
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Error clicking element {selector}: {str(e)}"
    
    async def type_text(self, selector: str, text: str, press_enter: bool = False) -> str:
        """
        Вводит текст в элемент.
        
        Args:
            selector: CSS селектор элемента
            text: Текст для ввода
            press_enter: Нажать Enter после ввода
            
        Returns:
            Результат ввода
        """
        try:
            await self.page.wait_for_selector(selector, timeout=10000, state="visible")
            await self.page.fill(selector, text)
            
            if press_enter:
                await self.page.press(selector, "Enter")
            
            await asyncio.sleep(0.5)  # Короткая пауза после ввода
            return f"Typed text into {selector}"
        except Exception as e:
            return f"Error typing into {selector}: {str(e)}"
    
    async def wait(self, seconds: int) -> str:
        """
        Ожидание указанное количество секунд.
        
        Args:
            seconds: Количество секунд для ожидания
            
        Returns:
            Результат ожидания
        """
        try:
            await asyncio.sleep(seconds)
            return f"Waited for {seconds} seconds"
        except Exception as e:
            return f"Error during wait: {str(e)}"
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> str:
        """
        Прокручивает страницу.
        
        Args:
            direction: Направление прокрутки ("down", "up", "top", "bottom")
            amount: Количество пикселей для прокрутки
            
        Returns:
            Результат прокрутки
        """
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "top":
                await self.page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            await asyncio.sleep(0.5)
            return f"Scrolled {direction}"
        except Exception as e:
            return f"Error scrolling: {str(e)}"
    
    async def get_page_content(self) -> str:
        """
        Получает HTML содержимое страницы.
        
        Returns:
            HTML содержимое
        """
        try:
            content = await self.page.content()
            return content
        except Exception as e:
            return f"Error getting page content: {str(e)}"
    
    async def get_current_url(self) -> str:
        """
        Получает текущий URL страницы.
        
        Returns:
            Текущий URL
        """
        return self.page.url
    
    async def get_page_title(self) -> str:
        """
        Получает заголовок страницы.
        
        Returns:
            Заголовок страницы
        """
        try:
            title = await self.page.title()
            return title
        except Exception as e:
            return f"Error getting page title: {str(e)}"
    
    async def go_back(self) -> str:
        """
        Возвращается на предыдущую страницу.
        
        Returns:
            Результат операции
        """
        try:
            await self.page.go_back(wait_until="domcontentloaded")
            await asyncio.sleep(1)
            return f"Navigated back to {self.page.url}"
        except Exception as e:
            return f"Error going back: {str(e)}"
    
    async def evaluate_js(self, js_code: str) -> str:
        """
        Выполняет JavaScript код на странице.
        
        Args:
            js_code: JavaScript код для выполнения
            
        Returns:
            Результат выполнения
        """
        try:
            result = await self.page.evaluate(js_code)
            return str(result)
        except Exception as e:
            return f"Error evaluating JavaScript: {str(e)}"
    
    async def get_element_text(self, selector: str) -> str:
        """
        Получает текст элемента.
        
        Args:
            selector: CSS селектор элемента
            
        Returns:
            Текст элемента
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                text = await element.text_content()
                return text or ""
            return ""
        except Exception as e:
            return f"Error getting element text: {str(e)}"
    
    async def check_element_exists(self, selector: str) -> bool:
        """
        Проверяет существование элемента на странице.
        
        Args:
            selector: CSS селектор элемента
            
        Returns:
            True если элемент существует
        """
        try:
            element = await self.page.query_selector(selector)
            return element is not None
        except:
            return False


# Определения инструментов для OpenAI function calling
BROWSER_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to_url",
            "description": "Navigate to a specific URL in the browser. Use this when you need to go to a different page or website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to (e.g., 'https://example.com')"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current page. Useful for debugging or saving the current state. Use full_page=false for faster screenshots of visible area only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "full_page": {
                        "type": "boolean",
                        "description": "Whether to capture the full page or just the visible viewport. Default is false for speed.",
                        "default": False
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Click on an element on the page using a CSS selector. The selector should be specific and unique to avoid clicking the wrong element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click (e.g., 'button#submit', '.login-button', 'a[href=\"/profile\"]')"
                    }
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into an input field or textarea. First clears the field, then types the new text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input element (e.g., 'input[name=\"username\"]', '#search-box')"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type into the element"
                    },
                    "press_enter": {
                        "type": "boolean",
                        "description": "Whether to press Enter after typing (useful for search boxes or forms)",
                        "default": False
                    }
                },
                "required": ["selector", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_dom",
            "description": "Query the DOM to find elements, extract information, or analyze page structure. This uses a specialized sub-agent to intelligently search the page and return relevant selectors and information. Use this instead of getting full page HTML to save tokens.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing what you're looking for on the page (e.g., 'Find the search input field', 'Get all product names and prices', 'Find the button to add items to cart')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait for a specified number of seconds. Use sparingly - modern pages load quickly. Prefer 1-2 seconds for most cases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "integer",
                        "description": "Number of seconds to wait. Use 1-2 for most pages, max 5 for slow pages. Default should be 2.",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 2
                    }
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page in a specific direction. Useful for loading more content or navigating long pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["down", "up", "top", "bottom"],
                        "description": "Direction to scroll: 'down' (scroll down), 'up' (scroll up), 'top' (scroll to top), 'bottom' (scroll to bottom)"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Number of pixels to scroll (only used for 'down' and 'up' directions)",
                        "default": 500
                    }
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigate back to the previous page in browser history.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

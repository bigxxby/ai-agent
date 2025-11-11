"""DOM Sub-Agent для интеллектуального анализа и запроса DOM элементов."""

import json
from typing import Dict, Any, List
from openai import OpenAI
from bs4 import BeautifulSoup
from utils import Logger, truncate_html


class DOMAgent:
    """
    Специализированный sub-agent для работы с DOM.
    Анализирует структуру страницы и находит нужные элементы без загрузки всего HTML в контекст.
    """
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        """
        Инициализация DOM агента.
        
        Args:
            client: OpenAI клиент
            model: Модель для использования (по умолчанию gpt-4o-mini для скорости)
        """
        self.client = client
        self.model = model
    
    def _extract_interactive_elements(self, html: str) -> str:
        """
        Извлекает только интерактивные и важные элементы из HTML.
        
        Args:
            html: Полный HTML страницы
            
        Returns:
            Упрощенная структура с важными элементами
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Удаляем скрипты, стили, и другой ненужный контент
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()
        
        important_elements = []
        
        # Собираем интерактивные элементы
        selectors = {
            'buttons': soup.find_all(['button', 'input[type="submit"]', 'input[type="button"]']),
            'links': soup.find_all('a', href=True),
            'inputs': soup.find_all(['input', 'textarea', 'select']),
            'forms': soup.find_all('form'),
            'clickable': soup.find_all(attrs={'onclick': True}),
            'interactive': soup.find_all(attrs={'role': ['button', 'link', 'tab', 'menuitem']})
        }
        
        for category, elements in selectors.items():
            for elem in elements[:20]:  # Уменьшаем до 20 элементов для скорости
                element_info = self._describe_element(elem, category)
                if element_info:
                    important_elements.append(element_info)
        
        # Добавляем структуру навигации и главные разделы
        nav_elements = soup.find_all(['nav', 'header', 'footer', 'main'])
        for elem in nav_elements:
            element_info = self._describe_element(elem, 'structure')
            if element_info:
                important_elements.append(element_info)
        
        return json.dumps(important_elements, ensure_ascii=False, indent=2)
    
    def _describe_element(self, element, category: str) -> Dict[str, Any]:
        """
        Создает описание элемента с его селектором и свойствами.
        
        Args:
            element: BeautifulSoup элемент
            category: Категория элемента
            
        Returns:
            Словарь с описанием элемента
        """
        try:
            # Генерируем уникальный селектор
            selector = self._generate_selector(element)
            if not selector:
                return None
            
            # Извлекаем текст (ограничиваем длину)
            text = element.get_text(strip=True)[:200] if element.get_text(strip=True) else ""
            
            # Собираем информацию
            info = {
                'category': category,
                'tag': element.name,
                'selector': selector,
                'text': text,
            }
            
            # Добавляем важные атрибуты
            important_attrs = ['id', 'class', 'name', 'type', 'placeholder', 'href', 'role', 'aria-label', 'title', 'value']
            for attr in important_attrs:
                if element.get(attr):
                    info[attr] = element.get(attr)
            
            return info
        except:
            return None
    
    def _generate_selector(self, element) -> str:
        """
        Генерирует CSS селектор для элемента.
        
        Args:
            element: BeautifulSoup элемент
            
        Returns:
            CSS селектор
        """
        try:
            # Приоритет: id > уникальный атрибут > class + tag > позиция
            
            # ID - самый надежный
            if element.get('id'):
                return f"#{element.get('id')}"
            
            # Уникальные атрибуты
            if element.get('name'):
                selector = f"{element.name}[name='{element.get('name')}']"
                return selector
            
            if element.get('data-testid'):
                return f"{element.name}[data-testid='{element.get('data-testid')}']"
            
            # Комбинация класса и тега
            if element.get('class'):
                classes = element.get('class')
                if isinstance(classes, list):
                    # Используем первый класс
                    class_name = classes[0]
                    selector = f"{element.name}.{class_name}"
                    return selector
            
            # Для ссылок - используем href
            if element.name == 'a' and element.get('href'):
                href = element.get('href')
                return f"a[href='{href}']"
            
            # Для input - используем type
            if element.name == 'input' and element.get('type'):
                input_type = element.get('type')
                return f"input[type='{input_type}']"
            
            # Последний вариант - просто тег
            return element.name
            
        except:
            return ""
    
    async def query(self, html: str, query: str, current_url: str) -> str:
        """
        Обрабатывает запрос к DOM и возвращает релевантную информацию.
        
        Args:
            html: HTML содержимое страницы
            query: Запрос пользователя на естественном языке
            current_url: Текущий URL страницы
            
        Returns:
            Ответ на запрос с найденными элементами и селекторами
        """
        Logger.sub_agent("DOM Sub-agent", f"Processing query: {query}")
        Logger.debug(f"HTML length: {len(html)} chars, URL: {current_url}")
        
        # Извлекаем интерактивные элементы
        Logger.debug("Extracting interactive elements from HTML...")
        extracted_elements = self._extract_interactive_elements(html)
        Logger.debug(f"Extracted elements length: {len(extracted_elements)} chars")
        
        # Получаем заголовок страницы
        soup = BeautifulSoup(html, 'lxml')
        page_title = soup.title.string if soup.title else "Unknown"
        Logger.debug(f"Page title: {page_title}")
        
        # Создаем prompt для sub-агента
        system_prompt = """You are a specialized DOM analysis agent. Your job is to analyze web page structure and find specific elements based on user queries.

You will receive:
1. A structured list of interactive elements from the page (buttons, links, inputs, etc.)
2. A user query about what they're looking for

Your task:
- Analyze the elements and find those that match the user's query
- Return relevant CSS selectors that can be used to interact with these elements
- Provide clear descriptions of what each element does
- If multiple elements match, return all of them with explanations

Response format (JSON):
{
  "elements": [
    {
      "selector": "CSS selector here",
      "description": "What this element does",
      "text": "Visible text on element",
      "confidence": "high/medium/low"
    }
  ],
  "summary": "Brief summary of findings",
  "suggestions": "Any suggestions for the main agent on how to proceed"
}

Be precise with selectors. Prefer IDs and unique attributes over generic class names."""

        user_prompt = f"""Page: {page_title}
URL: {current_url}

Available elements on the page:
{extracted_elements}

User query: {query}

Analyze the elements and find those that match the query. Return your response as JSON."""

        Logger.debug(f"Sending query to OpenAI model: {self.model}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=30.0  # Таймаут 30 секунд
            )
            
            Logger.debug(f"OpenAI response received. Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            
            result = response.choices[0].message.content
            Logger.sub_agent("DOM Sub-agent", f"Found elements matching the query")
            
            # Парсим и форматируем результат для удобного отображения
            try:
                parsed_result = json.loads(result)
                formatted_output = f"**DOM Query Result:**\n\n"
                formatted_output += f"Summary: {parsed_result.get('summary', 'No summary')}\n\n"
                
                if 'elements' in parsed_result and parsed_result['elements']:
                    formatted_output += f"Found {len(parsed_result['elements'])} element(s):\n\n"
                    for idx, elem in enumerate(parsed_result['elements'], 1):
                        formatted_output += f"{idx}. Selector: `{elem.get('selector', 'N/A')}`\n"
                        formatted_output += f"   Description: {elem.get('description', 'N/A')}\n"
                        formatted_output += f"   Text: {elem.get('text', 'N/A')}\n"
                        formatted_output += f"   Confidence: {elem.get('confidence', 'N/A')}\n\n"
                
                if 'suggestions' in parsed_result:
                    formatted_output += f"Suggestions: {parsed_result['suggestions']}\n"
                
                return formatted_output
            except:
                return result
            
        except Exception as e:
            Logger.error(f"DOM agent error: {str(e)}")
            return f"Error analyzing DOM: {str(e)}"

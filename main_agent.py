"""Главный AI-агент для управления браузером."""

import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from browser_tools import BrowserTools, BROWSER_TOOL_DEFINITIONS
from dom_agent import DOMAgent
from utils import Logger, parse_security_action, ask_user_confirmation


class MainAgent:
    """
    Основной агент для автономного управления браузером.
    Использует OpenAI function calling для принятия решений и вызова инструментов.
    """
    
    def __init__(self, api_key: str, browser_tools: BrowserTools, model: str = "gpt-4o-mini"):
        """
        Инициализация главного агента.
        
        Args:
            api_key: OpenAI API ключ
            browser_tools: Экземпляр BrowserTools
            model: Модель для использования (gpt-4o-mini быстрее и дешевле)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.browser_tools = browser_tools
        self.dom_agent = DOMAgent(self.client, model="gpt-4o-mini")  # Используем быструю модель для DOM
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 30  # Максимум итераций для одной задачи
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_api_calls = os.getenv("LOG_API_CALLS", "false").lower() == "true"
        
        # Системный промпт для агента
        self.system_prompt = """You are an advanced AI agent that autonomously controls a web browser to complete complex tasks.

Your capabilities:
- Navigate websites and interact with web pages
- Click buttons, fill forms, search for information
- Analyze page content and make decisions
- Handle multi-step tasks that require navigation across multiple pages
- Adapt to errors and find alternative solutions

Key principles:
1. **Think step-by-step**: Break down complex tasks into smaller actions
2. **Explore intelligently**: Use query_dom to understand page structure before acting
3. **Be adaptive**: If something doesn't work, try a different approach
4. **Be thorough**: Don't assume - verify by checking the page
5. **Be efficient**: Minimize unnecessary actions and token usage
6. **VERIFY COMPLETION**: Before finishing, ALWAYS verify that the task was actually completed successfully

Tool usage guidelines:
- **query_dom**: Use this FIRST to understand the page before taking actions. It's much more efficient than getting full HTML.
- **navigate_to_url**: Use when you need to go to a specific URL
- **click_element**: Use to click buttons, links, or other interactive elements
- **type_text**: Use to fill input fields, search boxes, forms
- **take_screenshot**: Use sparingly for debugging or when you need to see the visual state
- **wait**: Use SHORT waits (1-2 seconds). Only use longer waits (3-5 sec) for very slow pages. Modern pages load quickly!
- **scroll**: Use to load more content or navigate long pages

Important:
- You MUST find selectors yourself using query_dom - no hardcoded selectors are provided
- You MUST determine page structure and navigation yourself
- Always explain your reasoning before taking actions
- If you encounter an error, analyze it and try a different approach
- Ask the user for clarification ONLY when truly necessary

Response format:
- Start with your reasoning/thoughts
- Then call the appropriate tools
- After getting results, decide next steps or provide final answer

CRITICAL - Task Completion Verification:
Before you declare a task complete, you MUST:
1. **Verify each step**: Check that every action in the task was completed
2. **Confirm results**: Use query_dom or take_screenshot to verify the outcome
3. **Check for errors**: Look for error messages, failed submissions, or unexpected states
4. **Final validation**: Re-read the original task and confirm ALL requirements are met

Examples of proper verification:
- If asked to "find vacancies", verify you actually found and can list them
- If asked to "apply for a job", verify the application was submitted (check for confirmation message)
- If asked to "add to cart", verify the item is in the cart (check cart count or contents)
- If asked to "send a message", verify it was sent (check for success message)

DO NOT complete the task until you have VERIFIED that:
✓ All required actions were performed
✓ The final state matches what was requested
✓ No errors occurred during the process
✓ You can provide concrete evidence of completion (URLs, messages, data found, etc.)

When task is truly complete:
- Summarize EXACTLY what you accomplished with specific details
- Provide concrete evidence (URLs visited, data found, confirmations received)
- List any relevant information or results
- Wait for the next user instruction"""

    async def run(self, user_task: str) -> str:
        """
        Выполняет задачу пользователя автономно.
        
        Args:
            user_task: Задача от пользователя
            
        Returns:
            Результат выполнения задачи
        """
        Logger.user_message(user_task)
        Logger.debug(f"Starting task execution. Max iterations: {self.max_iterations}")
        
        # Инициализируем историю разговора с системным промптом
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_task}
        ]
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            Logger.debug(f"--- Iteration {iteration}/{self.max_iterations} ---")
            
            try:
                # Получаем ответ от модели
                Logger.debug(f"Sending request to OpenAI model: {self.model}")
                Logger.debug(f"Conversation history length: {len(self.conversation_history)} messages")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=BROWSER_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.1,
                    timeout=60.0  # Таймаут 60 секунд
                )
                
                Logger.debug(f"Received response. Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
                
                assistant_message = response.choices[0].message
                Logger.debug(f"Assistant message has content: {bool(assistant_message.content)}, tool_calls: {bool(assistant_message.tool_calls)}")
                
                # Если есть текстовое сообщение от ассистента
                if assistant_message.content:
                    Logger.assistant_message(assistant_message.content)
                
                # Проверяем, есть ли вызовы инструментов
                if not assistant_message.tool_calls:
                    # Агент завершил задачу
                    Logger.debug("No tool calls - task completed")
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })
                    return assistant_message.content
                
                Logger.debug(f"Processing {len(assistant_message.tool_calls)} tool call(s)")
                
                # Обрабатываем вызовы инструментов
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in assistant_message.tool_calls
                    ]
                })
                
                # Выполняем каждый вызов инструмента
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    Logger.debug(f"Tool call ID: {tool_call.id}")
                    
                    # Проверка безопасности для потенциально опасных действий
                    if function_name == "click_element":
                        action_desc = f"Click on element: {function_args.get('selector', 'unknown')}"
                        if parse_security_action(action_desc):
                            if not ask_user_confirmation(action_desc):
                                result = "Action cancelled by user for security reasons."
                                self.conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": result
                                })
                                continue
                    
                    Logger.tool_call(function_name, function_args)
                    
                    # Выполняем инструмент
                    result = await self._execute_tool(function_name, function_args)
                    
                    Logger.tool_result(result)
                    
                    # Добавляем результат в историю
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
            except Exception as e:
                error_msg = f"Error in agent loop: {str(e)}"
                Logger.error(error_msg)
                
                # Добавляем ошибку в контекст, чтобы агент мог адаптироваться
                self.conversation_history.append({
                    "role": "user",
                    "content": f"An error occurred: {error_msg}. Please try a different approach."
                })
                
                # Продолжаем выполнение
                continue
        
        # Достигнут лимит итераций
        final_message = f"Reached maximum iterations ({self.max_iterations}). Task may be incomplete."
        Logger.error(final_message)
        return final_message
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Выполняет указанный инструмент с заданными аргументами.
        
        Args:
            tool_name: Название инструмента
            args: Аргументы для инструмента
            
        Returns:
            Результат выполнения инструмента
        """
        Logger.debug(f"Executing tool: {tool_name}")
        
        try:
            if tool_name == "navigate_to_url":
                return await self.browser_tools.navigate_to_url(args["url"])
            
            elif tool_name == "take_screenshot":
                full_page = args.get("full_page", False)
                return await self.browser_tools.take_screenshot(full_page)
            
            elif tool_name == "click_element":
                return await self.browser_tools.click_element(args["selector"])
            
            elif tool_name == "type_text":
                selector = args["selector"]
                text = args["text"]
                press_enter = args.get("press_enter", False)
                return await self.browser_tools.type_text(selector, text, press_enter)
            
            elif tool_name == "query_dom":
                # Используем DOM sub-агента
                Logger.debug("Getting page content for DOM query...")
                html = await self.browser_tools.get_page_content()
                current_url = await self.browser_tools.get_current_url()
                query = args["query"]
                Logger.debug(f"Calling DOM agent with query: {query}")
                return await self.dom_agent.query(html, query, current_url)
            
            elif tool_name == "wait":
                seconds = args["seconds"]
                return await self.browser_tools.wait(seconds)
            
            elif tool_name == "scroll":
                direction = args["direction"]
                amount = args.get("amount", 500)
                return await self.browser_tools.scroll(direction, amount)
            
            elif tool_name == "go_back":
                return await self.browser_tools.go_back()
            
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def reset_conversation(self):
        """Сбрасывает историю разговора."""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

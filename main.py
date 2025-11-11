"""Точка входа в AI-агент для автоматизации браузера."""

import asyncio
import os
import sys
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from browser_tools import BrowserTools
from main_agent import MainAgent
from utils import Logger
from colorama import Fore, Style


async def main():
    """Главная функция запуска агента."""
    
    # Загружаем переменные окружения
    load_dotenv()
    api_key = os.getenv("OPEN_AI")
    
    if not api_key:
        Logger.error("OPEN_AI key not found in .env file")
        return
    
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'AI Browser Automation Agent':^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    Logger.info("Starting browser...")
    
    # Запускаем браузер
    async with async_playwright() as p:
        # Используем persistent context для сохранения сессий
        user_data_dir = "./user-data"
        
        browser = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,  # Браузер видимый
            viewport={"width": 1280, "height": 720},
            args=[
                "--disable-blink-features=AutomationControlled",  # Скрываем признаки автоматизации
            ],
            # Убрали slow_mo для максимальной скорости
            slow_mo=0
        )
        
        # Получаем первую страницу или создаем новую
        if len(browser.pages) > 0:
            page = browser.pages[0]
        else:
            page = await browser.new_page()
        
        # Инициализируем инструменты и агента
        browser_tools = BrowserTools(page, browser)
        agent = MainAgent(api_key, browser_tools)
        
        Logger.success("Browser started successfully!")
        Logger.info("Agent is ready to accept tasks.\n")
        
        print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Instructions:{Style.RESET_ALL}")
        print(f"  • Type your task and press Enter")
        print(f"  • The agent will work autonomously to complete it")
        print(f"  • Watch the browser and terminal to see the agent in action")
        print(f"  • Type 'exit' or 'quit' to stop")
        print(f"  • Type 'reset' to clear conversation history")
        print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.GREEN}Example tasks:{Style.RESET_ALL}")
        print(f"  • Go to hh.ru and find 3 AI engineer vacancies")
        print(f"  • Search for 'hot dog' on Yandex Lavka and add one to cart")
        print(f"  • Find the latest news about AI on any news website")
        print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}\n")
        
        # Интерактивный цикл
        while True:
            try:
                # Получаем задачу от пользователя
                user_input = input(f"{Fore.BLUE}👤 Enter your task: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    Logger.info("Shutting down agent...")
                    break
                
                if user_input.lower() == 'reset':
                    agent.reset_conversation()
                    Logger.success("Conversation history reset!")
                    continue
                
                # Выполняем задачу
                print(f"\n{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
                Logger.info("Agent is working on your task...\n")
                
                result = await agent.run(user_input)
                
                print(f"\n{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
                Logger.success("Task completed!")
                print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}\n")
                
            except KeyboardInterrupt:
                Logger.info("\nInterrupted by user. Shutting down...")
                break
            except Exception as e:
                Logger.error(f"Unexpected error: {str(e)}")
                Logger.info("You can continue with a new task or type 'exit' to quit.\n")
        
        # Закрываем браузер
        Logger.info("Closing browser...")
        await browser.close()
        Logger.success("Agent shut down successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nAgent terminated by user.")
        sys.exit(0)

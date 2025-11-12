"""Вспомогательные функции для AI-агента."""

import os
import json
from datetime import datetime
from colorama import Fore, Style, init

# Инициализация colorama для цветного вывода
init(autoreset=True)

# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

class Logger:
    """Логгер для красивого вывода информации о работе агента."""
    
    @staticmethod
    def debug(message: str):
        """Debug логирование (только если DEBUG_MODE=true)."""
        if DEBUG_MODE:
            print(f"{Fore.LIGHTBLACK_EX}[DEBUG] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def tool_call(tool_name: str, inputs: dict):
        """Логирование вызова инструмента."""
        print(f"\n{Fore.CYAN}{'┌' + '─' * 78 + '┐'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ ▶ Tool: {Fore.WHITE}{Style.BRIGHT}{tool_name}{Style.RESET_ALL}")
        
        # Форматируем inputs с отступами
        if inputs:
            inputs_str = json.dumps(inputs, ensure_ascii=False, indent=2)
            for line in inputs_str.split('\n'):
                print(f"{Fore.CYAN}│ {Fore.LIGHTBLACK_EX}{line}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'└' + '─' * 78 + '┘'}{Style.RESET_ALL}")
        Logger.debug(f"Tool {tool_name} called at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    @staticmethod
    def tool_result(result: str):
        """Логирование результата инструмента."""
        # Обрезаем длинные результаты
        display_result = result if len(result) < 500 else result[:500] + "..."
        
        # Определяем цвет по типу результата
        if result.startswith("✅"):
            color = Fore.GREEN
        elif result.startswith("❌"):
            color = Fore.RED
        elif result.startswith("⚠️"):
            color = Fore.YELLOW
        else:
            color = Fore.LIGHTWHITE_EX
            
        print(f"{color}  ↳ {display_result}{Style.RESET_ALL}")
        
        if DEBUG_MODE and len(result) > 500:
            Logger.debug(f"Full result length: {len(result)} chars")
    
    @staticmethod
    def assistant_message(message: str):
        """Логирование сообщения ассистента."""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}🤖 Assistant:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def user_message(message: str):
        """Логирование сообщения пользователя."""
        print(f"\n{Fore.BLUE}{Style.BRIGHT}👤 You:{Style.RESET_ALL} {Fore.LIGHTBLUE_EX}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def sub_agent(agent_name: str, message: str):
        """Логирование работы sub-агента."""
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}🔍 {agent_name}:{Style.RESET_ALL} {Fore.LIGHTMAGENTA_EX}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        """Логирование ошибки."""
        print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error:{Style.RESET_ALL} {Fore.LIGHTRED_EX}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def success(message: str):
        """Логирование успешного завершения."""
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def info(message: str):
        """Информационное сообщение."""
        print(f"{Fore.LIGHTWHITE_EX}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str):
        """Предупреждающее сообщение."""
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️  {message}{Style.RESET_ALL}")
    
    @staticmethod
    def separator():
        """Печатает разделитель."""
        print(f"\n{Fore.LIGHTBLACK_EX}{'═' * 80}{Style.RESET_ALL}")
    
    @staticmethod
    def header(text: str):
        """Печатает заголовок."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'╔' + '═' * 78 + '╗'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}║{text.center(78)}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'╚' + '═' * 78 + '╝'}{Style.RESET_ALL}")
    
    @staticmethod
    def step(step_num: int, total_steps: int, description: str):
        """Печатает шаг выполнения задачи."""
        bar = f"[{step_num}/{total_steps}]"
        print(f"{Fore.LIGHTCYAN_EX}{bar} {Fore.WHITE}{description}{Style.RESET_ALL}")
    
    @staticmethod
    def page_info(url: str, title: str):
        """Печатает информацию о странице."""
        print(f"\n{Fore.LIGHTBLUE_EX}┌{'─' * 78}┐{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}│ 🌐 URL:   {Fore.WHITE}{url[:70]}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}│ 📄 Title: {Fore.WHITE}{title[:70]}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}└{'─' * 78}┘{Style.RESET_ALL}")


def truncate_html(html: str, max_length: int = 50000) -> str:
    """
    Обрезает HTML до заданной длины, сохраняя структуру.
    
    Args:
        html: HTML строка
        max_length: Максимальная длина
        
    Returns:
        Обрезанный HTML
    """
    if len(html) <= max_length:
        return html
    
    return html[:max_length] + "\n\n[... HTML truncated to fit context ...]"


def extract_visible_text(html: str, max_length: int = 30000) -> str:
    """
    Извлекает видимый текст из HTML.
    
    Args:
        html: HTML строка
        max_length: Максимальная длина
        
    Returns:
        Видимый текст
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Удаляем скрипты и стили
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Получаем текст
    text = soup.get_text()
    
    # Убираем лишние пробелы
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[... Text truncated to fit context ...]"
    
    return text


def create_screenshots_dir():
    """Создает директорию для скриншотов если её нет."""
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    return screenshots_dir


def generate_screenshot_filename() -> str:
    """Генерирует уникальное имя файла для скриншота."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"screenshot-{timestamp}.png"


def format_tool_description(name: str, description: str, parameters: dict) -> dict:
    """
    Форматирует описание инструмента для OpenAI function calling.
    
    Args:
        name: Название инструмента
        description: Описание инструмента
        parameters: Схема параметров
        
    Returns:
        Отформатированное описание
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    }


def parse_security_action(action: str) -> bool:
    """
    Определяет, является ли действие потенциально деструктивным.
    
    Args:
        action: Описание действия
        
    Returns:
        True если действие требует подтверждения
    """
    dangerous_keywords = [
        "delete", "удалить", "remove", "убрать",
        "pay", "оплатить", "buy", "купить", "purchase",
        "submit", "отправить", "confirm", "подтвердить",
        "checkout", "оформить"
    ]
    
    action_lower = action.lower()
    return any(keyword in action_lower for keyword in dangerous_keywords)


def ask_user_confirmation(action: str) -> bool:
    """
    Запрашивает подтверждение у пользователя для деструктивных действий.
    
    Args:
        action: Описание действия
        
    Returns:
        True если пользователь подтвердил
    """
    print(f"\n{Fore.YELLOW}⚠️  Security check: The agent wants to perform a potentially destructive action:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   {action}{Style.RESET_ALL}")
    
    while True:
        response = input(f"{Fore.YELLOW}   Do you want to proceed? (yes/no): {Style.RESET_ALL}").strip().lower()
        if response in ['yes', 'y', 'да']:
            return True
        elif response in ['no', 'n', 'нет']:
            return False
        else:
            print(f"{Fore.RED}   Please answer 'yes' or 'no'{Style.RESET_ALL}")

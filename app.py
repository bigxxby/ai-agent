"""
Main entry point for Text-Vision AI Browser Agent.

This agent "sees" webpages through structured text representation
and interacts using a two-step discovery pattern.
"""

import time
from contextlib import contextmanager

from anthropic import Anthropic

from src.core import AgentCore
from web.interface import BrowserInterface
from config import AppSettings
from utils import Logger


@contextmanager
def browser_session(settings: AppSettings):
    """
    Manage browser lifecycle with automatic cleanup.
    
    Args:
        settings: Application settings
        
    Yields:
        BrowserInterface instance
    """
    browser = BrowserInterface(
        browser_type=settings.browser.browser_type,
        headless=settings.browser.headless,
        user_data_dir=settings.browser.user_data_dir
    )
    
    try:
        Logger.info(f"🌐 Launching {settings.browser.browser_type} browser...")
        browser.launch()
        Logger.success(f"✅ Browser ready! (Data: {settings.browser.user_data_dir})")
        yield browser
    finally:
        Logger.info("🔒 Shutting down browser...")
        try:
            browser.shutdown()
        except Exception:
            pass


def get_user_task(is_first: bool = True) -> str:
    """
    Prompt user for task input.
    
    Args:
        is_first: Whether this is the first task
        
    Returns:
        User's task description, or empty string if quit
    """
    from colorama import Fore, Style
    
    Logger.separator()
    if is_first:
        print(f"{Fore.LIGHTCYAN_EX}💬 What would you like me to do? {Fore.LIGHTBLACK_EX}(or 'quit' to exit){Style.RESET_ALL}\n")
    else:
        print(f"{Fore.LIGHTCYAN_EX}💬 Next task? {Fore.LIGHTBLACK_EX}(or 'quit' to exit){Style.RESET_ALL}\n")
    
    user_input = input(f"{Fore.CYAN}Your task: {Style.RESET_ALL}").strip()
    return user_input


def main() -> None:
    """Main entry point for Text-Vision AI Browser Agent."""
    
    Logger.header("🤖 Text-Vision AI Browser Agent")
    Logger.info("Agent sees webpages through structured text, not pixels\n")

    try:
        # Load configuration
        Logger.info("📋 Loading configuration...")
        settings = AppSettings.from_env()
        Logger.info(f"🤖 Using model: {settings.agent.model}")
        Logger.info(f"🔄 Max iterations: {settings.agent.max_iterations}")
        Logger.info(f"📊 Context limit: {settings.agent.context_token_limit} tokens\n")

        # Launch browser
        with browser_session(settings) as browser:
            
            # Initialize Anthropic client
            anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            
            # Initialize agent core
            Logger.info("🧠 Initializing AI agent core...")
            agent = AgentCore(
                anthropic_client=anthropic_client,
                browser=browser,
                model=settings.agent.model,
                max_iterations=settings.agent.max_iterations,
                context_token_limit=settings.agent.context_token_limit
            )
            Logger.success("✅ Agent ready!\n")

            # Task execution loop
            is_first_task = True
            while True:
                # Reload configuration for dynamic model changes
                settings = AppSettings.from_env()
                agent.model = settings.agent.model
                agent.max_iterations = settings.agent.max_iterations
                
                # Get task from user
                task = get_user_task(is_first=is_first_task)
                is_first_task = False

                if not task or task.lower() == "quit":
                    Logger.info("Exiting... Goodbye! 👋")
                    break
                
                # Show current model
                Logger.info(f"🤖 Using model: {agent.model}")

                # Execute task
                Logger.separator()
                Logger.header("🚀 Starting Task Execution")
                
                try:
                    result = agent.execute_task(task)

                    # Display final result
                    Logger.separator()
                    Logger.header("📊 Task Complete")
                    print(f"\n{result}\n")
                    
                    # Small delay before next task prompt
                    time.sleep(0.5)
                    
                except Exception as task_error:
                    Logger.error(f"Task failed: {str(task_error)}")
                    print("\n")
                    # Continue to next task even if this one failed
                    time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n")
        Logger.info("⚠️  Interrupted by user. Shutting down...")
        
    except Exception as e:
        from anthropic import (
            AuthenticationError,
            RateLimitError,
            APITimeoutError,
            APIConnectionError
        )
        
        # Handle specific Anthropic errors
        if isinstance(e, AuthenticationError):
            Logger.error("Authentication failed. Check your ANTHROPIC_API_KEY in .env file.")
        elif isinstance(e, RateLimitError):
            Logger.error("Rate limit exceeded. Please wait and try again.")
        elif isinstance(e, APITimeoutError):
            Logger.error("API timeout. Check your internet connection.")
        elif isinstance(e, APIConnectionError):
            Logger.error("Failed to connect to Anthropic API. Check internet connection.")
        else:
            Logger.error(f"Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
            
    finally:
        Logger.separator()
        Logger.info("👋 Goodbye!\n")


if __name__ == "__main__":
    main()

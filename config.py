"""
Application settings and configuration.

Uses dataclasses for type safety and clarity.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BrowserSettings:
    """Browser configuration."""
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False
    user_data_dir: str = "./user-data"


@dataclass
class AgentSettings:
    """AI agent configuration."""
    model: str = "claude-3-5-sonnet-20241022"
    max_iterations: int = 50  # Увеличено с 25 до 50 для сложных задач
    context_token_limit: int = 3000


@dataclass
class AppSettings:
    """Main application settings."""
    anthropic_api_key: str
    browser: BrowserSettings
    agent: AgentSettings
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        Load settings from environment variables.
        
        Returns:
            AppSettings instance
            
        Raises:
            ValueError: If required env vars are missing
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please create .env file with ANTHROPIC_API_KEY=your_key"
            )
        
        # Browser settings
        browser = BrowserSettings(
            browser_type=os.getenv("BROWSER_TYPE", "chromium"),
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            user_data_dir=os.getenv("USER_DATA_DIR", "./user-data")
        )
        
        # Agent settings
        agent = AgentSettings(
            model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20240620"),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "50")),
            context_token_limit=int(os.getenv("CONTEXT_TOKEN_LIMIT", "3000"))
        )
        
        return cls(
            anthropic_api_key=api_key,
            browser=browser,
            agent=agent
        )


# Example .env file:
"""
# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-...

# Browser settings (optional)
BROWSER_TYPE=chromium
HEADLESS=false
USER_DATA_DIR=./user-data

# Agent settings (optional)
AI_MODEL=claude-3-5-sonnet-20241022
MAX_ITERATIONS=50
CONTEXT_TOKEN_LIMIT=3000
"""

"""
AgentCore - Main agent loop with Anthropic Claude integration.

Implements the autonomous decision-making loop.
"""

from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from src.context import BrowserContext
from src.tools import BrowserActions
from web.interface import BrowserInterface
from ai.prompts import get_agent_system_prompt
from utils import Logger


class AgentCore:
    """
    Core agent that autonomously completes web tasks.
    Uses Anthropic Claude's tool calling to make decisions.
    """

    def __init__(
        self,
        anthropic_client: Anthropic,
        browser: BrowserInterface,
        model: str = "claude-3-5-sonnet-20241022",
        max_iterations: int = 25,
        context_token_limit: int = 3000
    ):
        """
        Initialize agent core.
        
        Args:
            anthropic_client: Anthropic client instance
            browser: Browser interface
            model: Claude model to use
            max_iterations: Maximum decision loops
            context_token_limit: Token limit for page context
        """
        self.client = anthropic_client
        self.browser = browser
        self.model = model
        self.max_iterations = max_iterations
        
        # Initialize components
        self.context = BrowserContext(browser, context_token_limit)
        self.actions = BrowserActions(browser, self.context)
        
        # Conversation state
        self.messages: List[Dict[str, Any]] = []
        self.system_prompt = get_agent_system_prompt()

    def execute_task(self, user_task: str) -> str:
        """
        Execute user task autonomously.
        
        Args:
            user_task: Natural language task description
            
        Returns:
            Final result or summary
        """
        Logger.user_message(user_task)
        
        # Initialize conversation (Claude doesn't include system in messages)
        self.messages = [
            {"role": "user", "content": user_task}
        ]
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            Logger.step(iteration, self.max_iterations, "Processing...")
            
            try:
                # Get agent's decision using Claude
                response = self.client.messages.create(
                    model=self.model,
                    system=self.system_prompt,
                    messages=self.messages,
                    tools=self.actions.get_tool_definitions(),
                    max_tokens=4096
                )
                
                # Log agent's reasoning
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                
                if text_content:
                    Logger.assistant_message(text_content)
                
                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent has completed or given final answer
                    self.messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    Logger.success("Task Complete")
                    return text_content
                
                # Add assistant message
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Check for tool use
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_args = block.input
                        tool_id = block.id
                        
                        Logger.tool_call(tool_name, tool_args)
                        
                        # Execute
                        result = self.actions.execute(tool_name, **tool_args)
                        
                        # Handle special signals
                        if result.startswith("🚨 HUMAN_HELP_NEEDED:"):
                            result = self._handle_human_help(result)
                        elif result.startswith("⚠️ CONFIRMATION_REQUIRED:"):
                            result = self._handle_confirmation(result)
                        elif result.startswith("✅ TASK_COMPLETE:"):
                            summary = result.replace("✅ TASK_COMPLETE:", "").strip()
                            Logger.info(f"📊 Agent thinks task is complete: {summary}\n")
                            
                            # Ask user if they agree
                            Logger.separator()
                            Logger.warning("Is the task actually complete?")
                            Logger.separator()
                            print("\nOptions:")
                            print("  'yes' or 'y' - Task is complete, exit")
                            print("  'no' or 'n' - Task is NOT complete, continue working")
                            print("  Or type additional instructions to continue\n")
                            
                            try:
                                user_response = input("Your response: ").strip()
                                
                                if user_response.lower() in ["yes", "y", ""]:
                                    Logger.success(f"Task Complete: {summary}")
                                    return summary
                                elif user_response.lower() in ["no", "n"]:
                                    result = "🚫 User says task is NOT complete yet. Continue working on the task."
                                else:
                                    # User provided additional instructions
                                    result = f"📝 User provided additional instructions: {user_response}\nContinue working with this new information."
                            except KeyboardInterrupt:
                                print("\n")
                                return "Task cancelled by user"
                            
                            Logger.separator()
                        
                        Logger.tool_result(result)
                        
                        # Add to tool results
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })
                        
                        # Auto-refresh context after navigation actions
                        if tool_name in ["interact_click", "navigate_url", "scroll_page", "switch_tab"]:
                            # Give page time to load dynamic content
                            import time
                            time.sleep(0.4)
                            
                            context_update = self.context.capture_current_state()
                            context_msg = f"🔄 Page Updated:\nURL: {context_update['url']}\nTitle: {context_update['title']}"
                            
                            # Append to last tool result
                            tool_results[-1]["content"] += f"\n{context_msg}"
                            Logger.page_info(context_update['url'], context_update['title'])
                
                # Add tool results to conversation
                if tool_results:
                    self.messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                Logger.error(error_msg)
                
                # Add error to conversation so agent can adapt
                self.messages.append({
                    "role": "user",
                    "content": f"An error occurred: {error_msg}. Please try a different approach."
                })
                
                continue
        
        # Max iterations reached
        final_msg = f"Reached maximum iterations ({self.max_iterations}). Task may be incomplete."
        Logger.warning(final_msg)
        return final_msg

    def reset(self):
        """Reset conversation state."""
        self.messages = []

    def _handle_human_help(self, signal: str) -> str:
        """
        Handle human intervention request.
        
        Args:
            signal: Signal from action toolkit
            
        Returns:
            Result after human intervention
        """
        description = signal.replace("🚨 HUMAN_HELP_NEEDED:", "").strip()
        
        Logger.separator()
        Logger.warning("PAUSED - Human Action Required")
        Logger.separator()
        Logger.info(f"📋 {description}\n")
        print("👉 Please complete this action in the browser, then press Enter to continue...\n")
        
        try:
            input("Press Enter when ready: ")
        except KeyboardInterrupt:
            print("\n")
            raise Exception("Task cancelled by user during human intervention")
        
        Logger.separator()
        Logger.info("▶️  Resuming agent execution...")
        Logger.separator()
        
        # Refresh context
        context_update = self.context.capture_current_state()
        
        return f"✅ Human intervention completed.\n" \
               f"Current URL: {context_update['url']}\n" \
               f"Page Title: {context_update['title']}\n" \
               f"Agent can now continue."

    def _handle_confirmation(self, signal: str) -> str:
        """
        Handle confirmation request for risky actions.
        
        Args:
            signal: Signal from action toolkit
            
        Returns:
            Confirmation result
        """
        parts = signal.replace("⚠️ CONFIRMATION_REQUIRED:", "").split(":", 2)
        risk_level = parts[0] if len(parts) > 0 else "unknown"
        action_description = parts[1] if len(parts) > 1 else "Unknown action"
        
        risk_emojis = {
            "financial": "💰",
            "deletion": "🗑️",
            "irreversible": "⚠️"
        }
        emoji = risk_emojis.get(risk_level, "⚠️")
        
        Logger.separator()
        Logger.warning(f"{emoji}  CONFIRMATION REQUIRED - {risk_level.upper()} ACTION")
        Logger.separator()
        Logger.info(f"➡️  {action_description}\n")
        Logger.warning("This action may be irreversible!\n")
        
        while True:
            try:
                response = input("Do you want to proceed? (yes/no): ").strip().lower()
                if response in ["yes", "y"]:
                    Logger.success("User confirmed action\n")
                    Logger.separator()
                    return f"✅ User CONFIRMED the action. You may proceed with: {action_description}"
                elif response in ["no", "n"]:
                    Logger.warning("User declined action\n")
                    Logger.separator()
                    return f"🚫 User DECLINED the action. Do NOT proceed. Find an alternative approach or complete the task differently."
                else:
                    print("Please enter 'yes' or 'no'")
            except KeyboardInterrupt:
                print("\n")
                return "🚫 User cancelled. Do NOT proceed with this action."

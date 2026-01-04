"""
BMO Assistant - Main Entry Point and CLI Interface.

This module provides the main command-line interface for interacting with
the BMO AI assistant. It handles session management, user input processing,
and response streaming with comprehensive error handling and user experience
considerations.
"""

import argparse
import uuid
import sys
import signal
import logging
from typing import Optional, List, Dict, Any, Set
from langchain_core.messages import HumanMessage, BaseMessage

import asyncio
from src.BMO.orchestrator.supervisor import Supervisor
from src.BMO.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)

class BMOSession:
    """
    Represents a single user session with BMO assistant.
    
    Handles session state, conversation history, and provides methods
    for interacting with the A2A Supervisor.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new BMO session.
        """
        self.session_id: str = session_id or str(uuid.uuid4())
        
        # Explicitly load skill registry manifest
        from src.BMO.skills.registry import load_manifest
        load_manifest()
        
        self.supervisor = Supervisor()
        self.message_history: List[BaseMessage] = []
        
        # Ensure we have an event loop for this session
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        logger.info(f"Initialized BMO session: {self.session_id}")

    def send_message(self, user_input: str) -> str:
        """
        Send a message to BMO and get the response.
        """
        try:
            # Create human message
            human_message: HumanMessage = HumanMessage(content=user_input)
            self.message_history.append(human_message)
            
            # Execute async supervisor
            response_text = self.loop.run_until_complete(self._process_message(user_input))
            
            # Append AI response
            ai_message = BaseMessage(content=response_text, type="ai")
            self.message_history.append(ai_message)
            
            return response_text
            
        except Exception as e:
            error_msg: str = f"Failed to process message: {str(e)}"
            logger.error(f"Session {self.session_id}: {error_msg}", exc_info=True)
            raise RuntimeError(error_msg) from e

    async def _process_message(self, user_input: str) -> str:
        final_state = await self.supervisor.ainvoke(user_input)
        
        # Formulate final response from step results
        steps = final_state.get("plan", {}).steps
        step_results = final_state.get("step_results", {})
        
        summary = ["Task Completed via A2A Orchestration:\n"]
        for step in steps:
             s_id = getattr(step, 'step_id', None)
             # step_results keys might be step_id or something else?
             # In supervisor.py, I used `step_id = step.step_id ...`.
             # ExecutionStep schema has step_id (Step 17).
             result = step_results.get(s_id)
             if result:
                 summary.append(f"Step '{step.intent}': {result.output.get('summary', result.output)}")
        
        return "\n".join(summary)

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        """
        return {
            "session_id": self.session_id,
            "message_count": len(self.message_history),
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
        }

    def clear_history(self) -> None:
        """Clear the conversation history for this session."""
        previous_count: int = len(self.message_history)
        self.message_history.clear()
        logger.info(f"Session {self.session_id}: Cleared {previous_count} messages from history")


class BMOCLI:
    """
    Command Line Interface for BMO Assistant.
    
    Provides an interactive chat interface with features like session
    management, command processing, and graceful shutdown handling.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the CLI interface.
        
        Args:
            session_id: Optional fixed session ID to use for persistence.
        """
        self.initial_session_id: Optional[str] = session_id
        self.session: Optional[BMOSession] = None
        self.running: bool = False
        self._setup_signal_handlers()
        
        # Supported exit commands
        self.exit_commands: Set[str] = {"exit", "quit", "sair", "bye", "goodbye", "q"}
        
        # Special commands and their handlers
        self.special_commands: Dict[str, Callable[[], str]] = {
            "help": self._show_help,
            "clear": self._clear_history,
            "info": self._show_session_info,
            "version": self._show_version,
        }

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.
        
        Handles Ctrl+C (SIGINT) and other termination signals
        to ensure clean shutdown.
        """
        def signal_handler(signum, frame):
            print(f"\n\nReceived signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self) -> None:
        """
        Start the BMO CLI interface.
        
        Initializes a new session and enters the main interaction loop.
        """
        print("🚀 Initializing BMO Assistant...")
        
        try:
            self.session: Optional[BMOSession] = BMOSession(session_id=self.initial_session_id)
            self.running: bool = True
            
            self._show_welcome_message()
            self._main_loop()
            
        except Exception as e:
            logger.error(f"Failed to start BMO CLI: {e}", exc_info=True)
            print(f"❌ Error starting BMO Assistant: {e}")
            sys.exit(1)

    def stop(self) -> None:
        """Stop the CLI interface and cleanup resources."""
        self.running: bool = False
        if self.session:
            logger.info(f"Ending BMO session: {self.session.session_id}")
        print("\nThank you for using BMO Assistant! 👋")

    def _show_welcome_message(self) -> None:
        """Display welcome message and usage instructions."""
        print(f"\n🤖 BMO Assistant Ready! (Session: {self.session.session_id})")
        print("=" * 50)
        print(f"Model: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")
        print(f"Streaming: {'Enabled' if settings.ENABLE_STREAMING else 'Disabled'}")
        print("=" * 50)
        print("Type your messages below. Special commands:")
        print("  • /help - Show this help message")
        print("  • /clear - Clear conversation history")
        print("  • /info - Show session information")
        print("  • /version - Show version information")
        print("  • /exit, /quit, /sair - Exit the program")
        print("=" * 50)

    def _show_help(self) -> str:
        """Display help information."""
        help_text = """
Available Commands:
  /help     - Show this help message
  /clear    - Clear conversation history
  /info     - Show session information  
  /version  - Show version information
  /exit     - Exit the program (also: /quit, /sair, /bye)

Just type normally to chat with BMO!
        """
        return help_text.strip()

    def _clear_history(self) -> str:
        """Clear conversation history."""
        if self.session:
            self.session.clear_history()
            return "Conversation history cleared! 🧹"
        return "No active session to clear."

    def _show_session_info(self) -> str:
        """Display session information."""
        if self.session:
            info: Dict[str, Any] = self.session.get_session_info()
            return (
                f"Session Info:\n"
                f"• ID: {info['session_id']}\n"
                f"• Messages: {info['message_count']}\n"
                f"• Provider: {info['llm_provider']}\n"
                f"• Model: {info['llm_model']}"
            )
        return "No active session."

    def _show_version(self) -> str:
        """Display version information."""
        return f"BMO Assistant\n• Model: {settings.FULL_LLM_MODEL_NAME}\n• Provider: {settings.LLM_PROVIDER}"

    def _process_special_command(self, command: str) -> Optional[str]:
        """
        Process special commands starting with '/'.
        
        Args:
            command: The command string (without leading slash).
            
        Returns:
            Command response or None if not a special command.
        """
        command: str = command.lower().lstrip('/')
        
        if command in self.exit_commands:
            self.stop()
            return None
            
        if command in self.special_commands:
            return self.special_commands[command]()
            
        return f"Unknown command: /{command}. Type /help for available commands."

    def _process_user_input(self, user_input: str) -> Optional[str]:
        """
        Process user input and return BMO's response.
        
        Args:
            user_input: Raw input from the user.
            
        Returns:
            BMO's response or None if the session should end.
        """
        # Check for empty input
        if not user_input.strip():
            return "Please enter a message to continue our conversation! 💬"

        # Check for special commands
        if user_input.startswith('/'):
            return self._process_special_command(user_input)

        # Process regular message
        try:
            if not self.session:
                return "Session not available. Please restart BMO Assistant."
                
            response: str = self.session.send_message(user_input)
            return response
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}", exc_info=True)
            return f"I encountered an error while processing your message: {str(e)}"

    def _main_loop(self) -> None:
        """Main interaction loop."""
        while self.running:
            try:
                # Get user input
                user_input: str = input("\n👤 User: ").strip()
                
                # Process input and get response
                response: Optional[str] = self._process_user_input(user_input)
                
                # Handle None response (usually for exit commands)
                if response is None:
                    break
                    
                # Display BMO's response
                if response:
                    print(f"🤖 BMO: {response}")
                    
            except EOFError:
                # Handle Ctrl+D gracefully
                print("\n\nReceived EOF, closing session...")
                break
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully (though signals should catch this)
                print("\n\nInterrupted by user, closing session...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                print(f"\n❌ Unexpected error: {e}")


def main() -> None:
    """
    Main entry point for BMO Assistant CLI.
    """
    parser = argparse.ArgumentParser(description="BMO Assistant CLI")
    parser.add_argument(
        "--session", 
        type=str, 
        help="Custom session ID for persistence. Use the same name to continue a conversation."
    )
    args = parser.parse_args()

    try:
        # Configure logging based on settings
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info(f"Starting BMO Assistant CLI (Session: {args.session or 'New'})")
        
        # Create and start CLI
        cli: BMOCLI = BMOCLI(session_id=args.session)
        cli.start()
        
    except Exception as e:
        logger.critical(f"BMO Assistant failed to start: {e}", exc_info=True)
        print(f"💥 Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
BMO Assistant - Main Entry Point and CLI Interface.

This module provides the main command-line interface for interacting with
the BMO AI assistant. It handles session management, user input processing,
and response streaming with comprehensive error handling and user experience
considerations.
"""

import uuid
import sys
import signal
import logging
from typing import Optional, List, Dict, Any, Set
from langchain_core.messages import HumanMessage, BaseMessage

from src.BMO.core.orchestrator import build_graph
from src.BMO.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)


class BMOSession:
    """
    Represents a single user session with BMO assistant.
    
    Handles session state, conversation history, and provides methods
    for interacting with the LangGraph workflow.
    
    Attributes:
        session_id: Unique identifier for the session.
        graph: Compiled LangGraph workflow instance.
        config: Runtime configuration for graph execution.
        message_history: List of messages in the current session.
        
    Example:
        >>> session = BMOSession()
        >>> response = session.send_message("Hello, BMO!")
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new BMO session.
        
        Args:
            session_id: Optional custom session ID. If not provided,
                       a UUID4 will be generated automatically.
        """
        self.session_id: str = session_id or str(uuid.uuid4())
        self.graph: LangGraph = build_graph()
        self.config: Dict[str, Any] = {"configurable": {"thread_id": self.session_id}}
        self.message_history: List[BaseMessage] = []
        
        logger.info(f"Initialized BMO session: {self.session_id}")

    def send_message(self, user_input: str) -> str:
        """
        Send a message to BMO and get the response.
        
        Args:
            user_input: The user's message text.
            
        Returns:
            BMO's response as a string.
            
        Raises:
            RuntimeError: If the graph fails to process the message.
        """
        try:
            # Create human message
            human_message: HumanMessage = HumanMessage(content=user_input)
            self.message_history.append(human_message)
            
            # Prepare inputs for graph
            inputs: Dict[str, Any] = {"messages": [human_message]}
            
            # Stream the response
            response_parts: List[str] = []
            for event in self.graph.stream(inputs, config=self.config, stream_mode="values"):
                message: BaseMessage = event["messages"][-1]
                if message.type == "ai" and message.content:
                    response_parts.append(message.content)
                    # Update message history with AI response
                    if message not in self.message_history:
                        self.message_history.append(message)
            
            full_response: str = "".join(response_parts)
            logger.debug(f"Session {self.session_id}: Processed user message, response length: {len(full_response)}")
            
            return full_response
            
        except Exception as e:
            error_msg: str = f"Failed to process message: {str(e)}"
            logger.error(f"Session {self.session_id}: {error_msg}", exc_info=True)
            raise RuntimeError(error_msg) from e

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary containing session metadata.
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
    
    def __init__(self):
        """Initialize the CLI interface."""
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
            self.session: Optional[BMOSession] = BMOSession()
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
    
    This function initializes and starts the BMO CLI interface with
    proper error handling and resource management.
    
    Example:
        $ python -m src.BMO.main
        🚀 Initializing BMO Assistant...
        🤖 BMO Assistant Ready! (Session: abc123...)
    """
    try:
        # Configure logging based on settings
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Starting BMO Assistant CLI")
        
        # Create and start CLI
        cli: BMOCLI = BMOCLI()
        cli.start()
        
    except Exception as e:
        logger.critical(f"BMO Assistant failed to start: {e}", exc_info=True)
        print(f"💥 Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
import argparse
import asyncio
import os
import sys
from typing import Dict, Any, Optional

# Import the tool
from tools.commands import run_shell_command

# Import ADK components
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# --- A Callback for Logging ---
def log_tool_calls(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    This is a `before_tool_callback`. It runs before any tool is executed.
    Here, we use it to log the command that is about to be run.
    """
    print(
        f"--- Callback: Agent '{tool_context.agent_name}' is about to run tool "
        f"'{tool.name}' with arguments: {args} ---"
    )
    # Returning None allows the tool execution to proceed
    return None

async def interact_with_agent(runner: Runner, user_id: str, session_id: str, initial_query: str):
    """Handles the asynchronous interaction loop with the agent."""
    content = types.Content(role='user', parts=[types.Part(text=initial_query)])
    print(f"\n>>> Kicking off agent with query: '{initial_query}'")

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        author = event.author or "system"
        if event.error_message:
            print(f"[{author}] Error: {event.error_message}")
        for part in event.content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"[{author}] Says: {part.text}")
            if hasattr(part, 'function_response') and part.function_response:
                response = part.function_response.response
                print(f"--- Tool Response ---\nSTDOUT:\n{response.get('stdout')}\nSTDERR:\n{response.get('stderr')}\n--------------------")
        if event.is_final_response():
            print("--- Agent has finished this turn. ---")
            break

def main():
    """Main function to set up and run the agent."""
    parser = argparse.ArgumentParser(description="Kubernetes AI Conformance Testing Agent")
    parser.add_argument(
        "--prompt-file",
        default="prompts/ai_conformance_prompt.txt",
        help="Path to the file containing the agent's instructions."
    )
    args = parser.parse_args()

    try:
        with open(args.prompt_file, "r") as f:
            prompt_instructions = f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at '{args.prompt_file}'", file=sys.stderr)
        sys.exit(1)

    # --- Agent Definition ---
    k8s_agent = Agent(
        name="ai_conformance_tester",
        model=os.environ.get("MODEL", "gemini-2.5-flash"),
        description="An agent that uses kubectl to test for Kubernetes AI conformance.",
        instruction=prompt_instructions,
        tools=[run_shell_command],
        # Here we add the callback
        before_tool_callback=log_tool_calls,
    )

    # --- Runner and Session Setup ---
    APP_NAME = "ai-conformance"
    USER_ID = "test-user"
    SESSION_ID = "session-1"

    session_service = InMemorySessionService()
    asyncio.run(session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID))

    runner = Runner(
        agent=k8s_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    # --- Start the conversation ---
    asyncio.run(interact_with_agent(runner, USER_ID, SESSION_ID, "Begin the AI conformance test."))

if __name__ == "__main__":
    main()
import os
import time
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load .env from workspace root or lemonade_stand directory
_env_root = Path(__file__).resolve().parent.parent.parent / ".env"
_env_local = Path(__file__).resolve().parent.parent / ".env"
if _env_local.exists():
    load_dotenv(dotenv_path=_env_local)
elif _env_root.exists():
    load_dotenv(dotenv_path=_env_root)
else:
    load_dotenv()



DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


class BaseAgent:
    def __init__(
        self,
        name: str,
        system_instruction: str,
        tools: List[Callable],
        model: Optional[str] = None,
    ):
        self.name = name
        self.system_instruction = system_instruction
        self.tools = tools
        self.tool_map: Dict[str, Callable] = {fn.__name__: fn for fn in tools}
        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(http_options=types.HttpOptions(timeout=30000))
        self.history: List[types.Content] = []

    def reset(self) -> None:
        """Clears working memory for a new customer or task."""
        self.history = []

    def chat(self, user_message: str, max_turns: int = 6) -> str:
        """
        Processes a single conversational turn within an ongoing dialogue,
        preserving history across calls until reset() is invoked.
        """
        # Append the new incoming user utterance to ongoing history
        self.history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        for turn in range(1, max_turns + 1):
            print(f"[{self.name} Internal Turn {turn}] Thinking...", flush=True)

            response = None
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=self.history,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_instruction,
                            tools=self.tools,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                                disable=True
                            ),
                            temperature=0.2,
                        ),
                    )
                    break
                except Exception as e:
                    err_msg = str(e)
                    is_transient = any(
                        code in err_msg
                        for code in ["429", "503", "500", "504", "UNAVAILABLE", "ResourceExhausted"]
                    )
                    if is_transient and attempt < max_retries - 1:
                        delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE)
                        if not delay_match:
                            delay_match = re.search(r"retry after (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE)

                        if delay_match:
                            wait_time = float(delay_match.group(1)) + 1.5
                        else:
                            # If 429 without explicit retry time, wait 15-20s for the rolling window
                            wait_time = 20.0 if ("429" in err_msg or "ResourceExhausted" in err_msg) else (attempt + 1) * 5.0

                        status_label = "Rate limit (429)" if ("429" in err_msg or "ResourceExhausted" in err_msg) else "High server demand / temporary glitch (503)"
                        print(
                            f"[{self.name}] {status_label} hit on '{self.model}'. Backing off for {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})...\n"
                            f"  -> API Details: {err_msg.strip()}",
                            flush=True,
                        )
                        time.sleep(wait_time)
                    else:
                        print(f"[{self.name}] Unrecoverable error on '{self.model}':\n  -> {err_msg.strip()}", flush=True)
                        raise e

            candidate = response.candidates[0]
            model_content = candidate.content
            self.history.append(model_content)

            function_calls = [
                part.function_call
                for part in model_content.parts
                if part.function_call
            ]

            # If no tools were called, the agent generated its response to the customer
            if not function_calls:
                return response.text or ""

            # Execute tool calls and feed results into the ongoing history
            tool_response_parts = []
            for call in function_calls:
                tool_name = call.name
                tool_args = dict(call.args) if call.args else {}

                print(f"  -> Executing Tool: {tool_name}({tool_args})", flush=True)
                if tool_name not in self.tool_map:
                    output = {"error": f"Tool '{tool_name}' is not registered."}
                else:
                    try:
                        output = self.tool_map[tool_name](**tool_args)
                    except Exception as e:
                        output = {"error": f"Tool execution failed: {str(e)}"}

                print(f"     Tool Output: {output}", flush=True)

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": output},
                    )
                )

            self.history.append(types.Content(role="user", parts=tool_response_parts))


        return "I apologize, but I encountered an internal delay processing that request."

    def run(self, single_prompt: str, max_turns: int = 6) -> str:
        """One-shot executor: resets state, executes prompt, returns response."""
        self.reset()
        return self.chat(single_prompt, max_turns=max_turns)
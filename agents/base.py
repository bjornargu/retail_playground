import os
import time
from typing import Any, Callable, Dict, List
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
import re

load_dotenv()


class BaseAgent:
    def __init__(
        self,
        name: str,
        system_instruction: str,
        tools: List[Callable],
        model: str = "gemini-3.5-flash-lite",
    ):
        self.name = name
        self.system_instruction = system_instruction
        self.tools = tools
        self.tool_map: Dict[str, Callable] = {fn.__name__: fn for fn in tools}
        self.model = model
        self.client = genai.Client()
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
            print(f"[{self.name} Internal Turn {turn}] Thinking...")

            response = None
            max_retries = 4
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
                    if "429" in err_msg and attempt < max_retries - 1:
                        # Extract suggested wait time from error if available (e.g. "retry in 20.11s")
                        delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_msg)
                        if delay_match:
                            wait_time = float(delay_match.group(1)) + 1.5
                        else:
                            wait_time = (attempt + 1) * 10.0

                        print(f"[{self.name}] Rate limit (429) hit. Backing off for {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
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

                print(f"  -> Executing Tool: {tool_name}({tool_args})")
                if tool_name not in self.tool_map:
                    output = {"error": f"Tool '{tool_name}' is not registered."}
                else:
                    try:
                        output = self.tool_map[tool_name](**tool_args)
                    except Exception as e:
                        output = {"error": f"Tool execution failed: {str(e)}"}

                print(f"     Tool Output: {output}")

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
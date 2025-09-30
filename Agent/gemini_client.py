import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging
from Agent.Helpers.auto_tool_creator import identify_tools
from Agent.Helpers.tool_runtime import call_function

log = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client for generating code modifications and ability creation."""

    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-flash-latest"
        self.history = []
        self.tools = identify_tools("Agent/Tools")

    def switch_model(self, model: str):
        """Switch to a different Gemini model."""
        self.model = model
        log.info(f"Switched to model: {model}")

    def ask(self, prompt: str, system_prompt: str = None, use_history: bool = False,
            save_in_history: bool = True, thinking_budget: int = -1) -> str:
        """
        Ask Gemini a question and get a response.

        Args:
            prompt: The user's question or request
            system_prompt: System instructions for the model (optional)
            use_history: Whether to include conversation history
            save_in_history: Whether to save this exchange in history
            thinking_budget: Budget for thinking (-1 for unlimited, 0 to disable)

        Returns:
            The model's text response
        """
        if use_history:
            self.history.append({
                "role": "user",
                "parts": [types.Part.from_text(text=prompt)]
            })
            response_text = self._get_response(
                messages=self.history,
                system_prompt=system_prompt,
                thinking_budget=thinking_budget
            )
            self.history.append({
                "role": "model",
                "parts": [types.Part.from_text(text=response_text)]
            })
        else:
            response_text = self._get_response(
                messages=[{"role": "user", "parts": [types.Part.from_text(text=prompt)]}],
                system_prompt=system_prompt,
                thinking_budget=thinking_budget
            )
            if save_in_history:
                self.history.append({
                    "role": "user",
                    "parts": [types.Part.from_text(text=prompt)]
                })
                self.history.append({
                    "role": "model",
                    "parts": [types.Part.from_text(text=response_text)]
                })

        return response_text

    def _get_response(self, messages: list, system_prompt: str = None,
                     thinking_budget: int = -1) -> str:
        """
        Internal method to get a response from Gemini.

        Args:
            messages: List of message objects
            system_prompt: System instructions
            thinking_budget: Thinking budget for the model

        Returns:
            The complete response text
        """
        # Convert messages to Content objects
        contents = []
        for msg in messages:
            if isinstance(msg, dict):
                contents.append(types.Content(
                    role=msg.get("role", "user"),
                    parts=msg.get("parts", [])
                ))
            else:
                contents.append(msg)

        # Build config
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=thinking_budget,
            ),
            system_instruction=system_prompt if system_prompt else None
        )

        # Stream the response and collect text
        response_text = ""
        try:
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text
        except Exception as e:
            log.error(f"Error generating content: {e}")
            raise

        return response_text

    def ask_with_streaming(self, prompt: str, system_prompt: str = None,
                          thinking_budget: int = -1):
        """
        Ask Gemini and get a streaming response generator.

        Args:
            prompt: The user's question
            system_prompt: System instructions
            thinking_budget: Thinking budget

        Yields:
            Text chunks as they arrive
        """
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]

        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=thinking_budget,
            ),
            system_instruction=system_prompt if system_prompt else None
        )

        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text

    def ask_with_tools(self, prompt: str, system_prompt: str = None,
                      use_history: bool = False, save_in_history: bool = True,
                      tools: list = None, max_iterations: int = 10) -> str:
        """
        Ask Gemini with tool calling support using the correct Google Gemini API format.

        Args:
            prompt: The user's question or request
            system_prompt: System instructions for the model
            use_history: Whether to include conversation history
            save_in_history: Whether to save this exchange in history
            tools: List of tool definitions (uses all available tools if None)
            max_iterations: Maximum number of tool call iterations

        Returns:
            The model's final text response after all tool calls
        """
        # Use all tools if none specified
        if tools is None:
            tools = self.tools

        # Convert tool definitions to proper Gemini format
        gemini_tools = []
        for tool_def in tools:
            # Extract function name and parameters
            func_name = tool_def.get("name", "")
            func_desc = tool_def.get("description", "")
            params = tool_def.get("parameters", {}).get("properties", {})

            # Create function declaration
            func_decl = types.FunctionDeclaration(
                name=func_name,
                description=func_desc,
                parameters={
                    "type": "object",
                    "properties": params,
                    "required": tool_def.get("parameters", {}).get("required", [])
                }
            )

            # Create tool object
            tool = types.Tool(
                function_declarations=[func_decl]
            )

            gemini_tools.append(tool)

        # Initialize messages
        if use_history:
            contents = list(self.history)
        else:
            contents = []

        # Add the user's prompt
        contents.append({
            "role": "user",
            "parts": [types.Part.from_text(text=prompt)]
        })

        # Tool calling loop
        iteration = 0
        final_response = None

        while iteration < max_iterations:
            iteration += 1

            # Build config with tools
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=gemini_tools,
            )

            # Convert contents to proper format
            formatted_contents = []
            for msg in contents:
                if isinstance(msg, dict):
                    formatted_contents.append(types.Content(
                        role=msg.get("role", "user"),
                        parts=msg.get("parts", [])
                    ))
                else:
                    formatted_contents.append(msg)

            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=formatted_contents,
                config=config,
            )

            # Check if there are function calls
            has_function_calls = False
            function_responses = []

            # Parse function calls from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        func_call = part.function_call
                        func_name = func_call.name
                        func_args = dict(func_call.args) if func_call.args else {}

                        log.debug(f"Calling function: {func_name} with args: {func_args}")

                        try:
                            # Call the function
                            result = call_function(func_name, func_args)
                            log.debug(f"Function result: {result}")

                            # Store the function response
                            function_responses.append(
                                types.Part.from_function_response(
                                    name=func_name,
                                    response={"result": str(result)}
                                )
                            )
                        except Exception as e:
                            log.error(f"Error calling function {func_name}: {e}")
                            function_responses.append(
                                types.Part.from_function_response(
                                    name=func_name,
                                    response={"error": str(e)}
                                )
                            )

            # Add model's response to contents
            contents.append({
                "role": "model",
                "parts": response.candidates[0].content.parts
            })

            # If there were function calls, add function responses and continue
            if has_function_calls and function_responses:
                contents.append({
                    "role": "user",
                    "parts": function_responses
                })
            else:
                # No more function calls, extract final text response
                final_response = response.text if hasattr(response, 'text') else ""
                break

        # Save to history if requested
        if save_in_history:
            if not use_history:
                self.history.append({
                    "role": "user",
                    "parts": [types.Part.from_text(text=prompt)]
                })
            if final_response:
                self.history.append({
                    "role": "model",
                    "parts": [types.Part.from_text(text=final_response)]
                })

        return final_response if final_response else "Max iterations reached without completion."

    def clear_history(self):
        """Clear the conversation history."""
        self.history = []
        log.info("Conversation history cleared")
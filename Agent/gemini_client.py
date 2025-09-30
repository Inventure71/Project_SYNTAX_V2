import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

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
    
    def clear_history(self):
        """Clear the conversation history."""
        self.history = []
        log.info("Conversation history cleared")

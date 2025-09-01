import os
from openai import OpenAI
from Agent.Helpers.auto_tool_creator import identify_tools
from Agent.Helpers.tool_runtime import call_function
import json
from dotenv import load_dotenv

import logging
log = logging.getLogger(__name__)

class ChatGPT:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.history = []
        self.active_model = "gpt-5-mini"
        self.gpt_5_settings = True

        self.tools = identify_tools("Agent/Tools")

    def switch_model(self, model: str, gpt_5_settings: bool):
        self.active_model = model
        self.gpt_5_settings = gpt_5_settings

    def ask(self, prompt: str, system_prompt: str, use_history: bool = False, save_in_history: bool = True, tools: list[str] = None) -> str:
        if use_history:
            self.history.append({"role": "user", "content": prompt})

            response = self.get_response(input=self.history, system_prompt=system_prompt, tools=tools)
            
            self.history.append({"role": "assistant", "content": response})

        else: 
            response = self.get_response(input=prompt, system_prompt=system_prompt, tools=tools)

            if save_in_history:
                self.history.append({"role": "user", "content": prompt})
                self.history.append({"role": "assistant", "content": response})
        
        return response

    def get_response(self, input: str, system_prompt: str, tools: list[str] = None) -> str:
        if self.gpt_5_settings:
            reasoning = {
                "effort": "minimal"
            }
            verbosity = {
                "verbosity": "low"
            }
        else:
            reasoning = None
            verbosity = None

        response = self.client.responses.create(
            model=self.active_model,
            input=input,
            system=system_prompt,
            reasoning=reasoning,
            text=verbosity,
            tools=tools
        )
        return response.output_text

    def get_response_with_tools(self, input: str, system_prompt: str, tools: list[str] = None) -> str:
        if tools is None:
            log.debug("# No tools provided, using default tools %s", self.tools)
            tools = self.tools

        if self.gpt_5_settings:
            reasoning = {
                "effort": "minimal"
            }
            verbosity = {
                "verbosity": "low"
            }
        else:
            reasoning = None
            verbosity = None

        # Create a running input list we will add to over time
        input_list = [
            {"role": "user", "content": input}
        ]

        while True:
            # 2. Prompt the model with tools defined
            response = self.client.responses.create(
                model=self.active_model,
                tools=tools,
                input=input_list,
                instructions=system_prompt,
                reasoning=reasoning,
                text=verbosity,
            )

            # Save function call outputs for subsequent requests
            input_list += response.output

            log.debug("## Partial Response to see function calls:")
            log.debug(response.model_dump_json(indent=2))

            at_least_one_function_call = False

            for item in response.output:
                if item.type == "function_call":
                    at_least_one_function_call = True
                    log.debug("## Identified function call:")
                    log.debug(item, "\n", item.model_dump_json(indent=2))
                    name = item.name
                    args = json.loads(item.arguments)

                    log.debug(f"Calling function: {name} with args: {args}")

                    result = call_function(name, args)
                    input_list.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result)
                    })

            if not at_least_one_function_call:
                break

        log.debug("# Final input:")
        log.debug(input_list)
        log.debug("# Final output:")
        log.debug(response.output_text)

        return response.output_text

    
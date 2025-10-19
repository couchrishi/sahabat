from google.adk.agents import LlmAgent
from . import prompt
from ... import config

specialist_text_agent = LlmAgent(
    model=config.TEXT_FLASH_MODEL, # This will be dynamically overridden by the router
    name="specialist_text",
    description="Handles all text generation tasks.",
    instruction=prompt.TEXT_INSTR,
    # The final answer will be saved to state['final_response']
    output_key="final_response"
)

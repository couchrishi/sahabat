from google.adk.agents import LlmAgent
from ... import config
from . import prompt

specialist_image_agent = LlmAgent(
    model=config.IMAGE_MODEL,
    name="specialist_image",
    description="Handles all image generation tasks. Use this agent if the user wants to create, generate, draw, or design an image, picture, or graphic.",
    instruction=prompt.IMAGE_PROMPT,
    output_key="final_response"
)

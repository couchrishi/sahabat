from google.adk.agents import LlmAgent
from ... import config
from . import prompt

specialist_video_agent = LlmAgent(
    model=config.VIDEO_MODEL,
    name="specialist_video",
    description="Handles all video generation tasks. Use this agent if the user wants to create, generate, or make a video, animation, or motion picture.",
    instruction=prompt.VIDEO_PROMPT,
    output_key="final_response"
)

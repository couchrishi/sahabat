import json
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from . import config
from .prompt import ORCHESTRATOR_PROMPT
from .sub_agents.specialist_text.agent import specialist_text_agent
from .sub_agents.specialist_image.agent import specialist_image_agent
from .sub_agents.specialist_video.agent import specialist_video_agent

def save_query_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
):
    """Saves the user's query to the session state before the model is called."""
    print("--- BEFORE_MODEL_CALLBACK TRIGGERED ---")
    # The user's message is typically the last one in the request contents
    last_message = llm_request.contents[-1]
    if last_message and last_message.role == "user":
        # Assuming the user message has one text part
        if last_message.parts:
            callback_context.state["user_query"] = last_message.parts[0].text

def save_analysis_after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
):
    """Parses the orchestrator's JSON output and saves it to the state."""
    json_string = None
    try:
        # The LLM response for an orchestrator might have multiple parts
        # (e.g., a function call part and a text part with the JSON).
        # We need to find the text part.
        if llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                if part.text:
                    json_string = part.text
                    break
        
        if json_string:
            # The response is often wrapped in markdown ```json ... ```
            cleaned_json_string = json_string.strip().replace("```json", "").replace("```", "").strip()
            analysis = json.loads(cleaned_json_string)
            callback_context.state["orchestrator_analysis"] = analysis
        else:
            # This can happen if the model only returns a tool call without any text
            callback_context.state["orchestrator_analysis"] = {"error": "No JSON analysis found in LLM response"}

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing orchestrator analysis: {e}")
        callback_context.state["orchestrator_analysis"] = {"error": "Failed to parse analysis"}

root_agent = LlmAgent(
    name="sahabat_orchestrator",
    model=config.ORCHESTRATOR_MODEL,
    instruction=ORCHESTRATOR_PROMPT,
    before_model_callback=save_query_before_model_callback,
    after_model_callback=save_analysis_after_model_callback,
    sub_agents=[
        specialist_text_agent,
        specialist_image_agent,
        specialist_video_agent
    ],
)
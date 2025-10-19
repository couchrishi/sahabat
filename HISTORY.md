# Project Sahabat - Development History & Status

This document tracks the development, debugging, and architectural decisions made for the Sahabat AI project.

## Initial Goal

The objective is to build a multi-agent AI system with a dedicated frontend for user interaction. The system consists of three main components:
1.  **Agent Server:** A Google ADK-based application responsible for AI logic, including an orchestrator agent that routes tasks to specialist agents (e.g., for text generation).
2.  **Backend API (BFF):** A FastAPI server intended to act as a Backend-for-Frontend, proxying requests from the UI to the agent server.
3.  **Frontend:** A modern React application (using Vite, TypeScript, and shadcn/ui) for users to interact with the agent in a chat interface.

## Work Done & Debugging Journey

### 1. Agent Server (`/agents`)

- **Initial Setup:** An orchestrator agent (`root_agent`) was created to route to a `specialist_text` agent.
- **Problem:** The agent server was consistently crashing with various errors.
- **Debugging Steps & Solutions:**
    - **`ModuleNotFoundError: No module named 'google.adk.server'`:** Fixed by changing the import in `serve.py` to `from google.adk.cli.fast_api import start_server`.
    - **`ValueError: No root_agent found`:** Fixed by running the `adk api_server` from the `agents/src` directory, which is the correct location for agent discovery.
    - **`KeyError: Context variable not found`:** This was a recurring issue.
        - Initially fixed by correcting template syntax from `{{var}}` to `{var}`.
        - The root cause was identified as trying to access state variables before they were set.
        - **Solution:** We implemented a robust, two-part callback system in `agent.py`:
            1.  A `before_model_callback` (`save_query_before_model_callback`) now reliably saves the user's query to the state as `user_query`.
            2.  An `after_model_callback` (`save_analysis_after_model_callback`) now saves the orchestrator's JSON analysis to the state as `orchestrator_analysis`.
    - **`TypeError: unexpected keyword argument 'callback_context'`:** Fixed by renaming the callback function's parameter to `callback_context` to match what the ADK framework provides.
    - **`AttributeError: 'CallbackContext' object has no attribute 'new_message'`:** Fixed by moving the state-saving logic from a `before_agent_callback` to the `before_model_callback`, which correctly provides access to the `LlmRequest` containing the user's message.
    - **Model `404 Not Found` Error:** The `specialist_text` agent was using a hardcoded, incorrect model name. This was fixed by updating it to use the correct model name from `config.py`.

### 2. End-to-End Streaming Integration

- **Goal:** Implement a real-time, token-by-token streaming experience, similar to ChatGPT or Perplexity.
- **Initial Architecture Attempted:** `Frontend -> Backend API (BFF) -> Agent Server`
- **What Worked:**
    - A direct `curl` test against the **ADK Agent Server's `/run_sse` endpoint** was **100% successful**. This proved that the agent server itself is streaming correctly and producing a valid Server-Sent Event (SSE) stream.
- **What Didn't Work (The Core Problem):**
    - The **Backend API (BFF)**, acting as a streaming proxy, has consistently failed.
    - We tried multiple implementations in `apis/routers/chat.py`:
        1.  **Translating the stream:** Attempting to parse the agent's JSON events and forward only the text. This led to `httpx.ResponseNotRead` errors because the logic for handling the stream's lifecycle was incorrect.
        2.  **Pure byte-level proxy:** Attempting to pass the raw bytes from the agent server directly to the client. This resulted in `curl: (18) transfer closed with outstanding read data remaining` errors, indicating a failure to correctly manage the two streaming connections.
    - **Conclusion:** The FastAPI proxy is the single point of failure. It is a complex component to implement correctly for this specific type of stream-to-stream proxying.

## Current Status

- **Agent Server:** **Fully functional and stable.** It correctly processes requests and provides a valid, streaming SSE response via the `/run_sse` endpoint on port `8001`.
- **Frontend:** **Fully implemented.** It has a modern UI, a `useChat` hook for state management, and is ready to consume a streaming SSE response. It is currently pointing at the non-functional BFF.
- **Backend API (BFF):** **Non-functional and buggy.** It is the source of all current streaming errors.

## Recommended Next Step

The most logical and robust path forward is to **eliminate the failing component (the BFF)** and adopt a simpler, more direct architecture.

1.  **Enable CORS on the ADK Agent Server:** Modify the `agents/serve.py` script to add the FastAPI `CORSMiddleware`. This will allow the frontend (on `localhost:8080`) to make requests directly to the agent server (on `localhost:8001`).
2.  **Update the Frontend's Target URL:** Change the `fetch` request in `frontend/src/hooks/useChat.ts` to point directly to the ADK server's working endpoint: `http://localhost:8001/run_sse`.
3.  **Update Frontend Request Payload:** The request body in the frontend hook must be updated to match the full format expected by the ADK's `/run_sse` endpoint (including `app_name`, `session_id`, etc.).

This plan leverages the components that we have proven to be working and removes the one that is broken, representing the most direct path to a fully functional application.

---

## How to Test the ADK API Server Directly

After extensive debugging, the correct procedure for testing the agent server via `curl` has been identified. The process is sensitive to the server's working directory and requires a specific two-step sequence.

### 1. Start the Server from the Correct Directory

The `adk api_server` command **must** be run from the `agents/src` directory. This is critical for the server to correctly discover and load the `sahabat` agent module.

```bash
# Navigate to the correct directory
cd /path/to/your/project/sahabat/agents/src

# Run the server
adk api_server --port 8001
```

### 2. The Two-Step Testing Process

Interacting with the agent requires two separate API calls: the first creates a session, and the second executes the agent within that session.

#### Step 1: Create a New Session

First, send a `POST` request to the session management endpoint to create a new, empty session. The `app_name` in the URL must be the name of the agent module (`sahabat`).

**Example `curl` command:**
```bash
curl -X POST -H "Content-Type: application/json" \
--data '{}' \
http://localhost:8001/apps/sahabat/users/test-user/sessions/test-session-1
```
This will return a JSON object confirming the session was created.

#### Step 2: Run the Agent and Stream the Response

Next, send a `POST` request to the `/run_sse` endpoint. This request must reference the `app_name` and the `session_id` from Step 1. The user's message is included in this request. To enable token-level streaming, the body must include `"streaming": true`.

**Example `curl` command:**
```bash
curl -X POST -N -H "Content-Type: application/json" \
--data '{
  "app_name": "sahabat",
  "user_id": "test-user",
  "session_id": "test-session-1",
  "new_message": {
    "parts": [
      {
        "text": "What is the capital of Indonesia?"
      }
    ]
  },
  "streaming": true
}' \
http://localhost:8001/run_sse
```
This command will now correctly execute the agent and return the token-by-token stream of Server-Sent Events.

---

## 3. Multi-Modal Agent Implementation (Image Generation)

The next major goal was to add image generation capabilities, making the system truly multi-modal. This involved a significant debugging effort that revealed the correct architectural patterns for integrating specialized, non-conversational models with the ADK.

### The Goal

-   The orchestrator should be able to route image-related queries to a new `specialist_image` agent.
-   This specialist agent should call a dedicated image generation model (e.g., Google's Imagen).
-   The frontend should be able to receive and display the generated image.

### The Debugging Journey & Key Learnings

1.  **Initial Failure (`LlmAgent` + `ValueError`):**
    -   **Attempt:** The `specialist_image` agent was initially created as a standard `LlmAgent`, similar to the text specialist. We configured it to use an Imagen model identifier.
    -   **Problem:** This failed immediately with a `ValueError: Model ... not found`.
    -   **Reason:** We discovered that the ADK's `LlmAgent` has an internal model registry that, in the installed version, only recognizes `gemini-...` model patterns. It cannot be used with non-Gemini models like Imagen.

2.  **Incorrect Path (`BaseAgent` + `ImportError`):**
    -   **Attempt:** To bypass the model registry, we re-implemented the image specialist as a custom `BaseAgent`. This involved writing manual code to call the Vertex AI API.
    -   **Problem:** This led to a cascade of `ImportError`s and other crashes. We were trying to manually construct `Event` objects and use internal ADK classes (`RunContext`, `AgentEvent`) that were not part of the public API, leading to constant failures. This approach was fundamentally incorrect.

3.  **The Breakthrough (MCP Server Architecture):**
    -   **Discovery:** By analyzing official Google documentation and sample repositories, we discovered the correct architectural pattern: **Model Context Protocol (MCP)**.
    -   **The Correct Pattern:** The ADK is not intended to call specialized services like Imagen directly. Instead, you run a separate, pre-built **MCP Server** (e.g., the `mcp-imagen-go` server) which acts as a bridge to the media API. The ADK agent is then given a simple `MCPToolset` which automatically discovers and connects to this external server.
    -   **Validation:** We successfully ran the external MCP server and used `curl` to verify that our ADK agent could communicate with it, generate an image, and get a URL back. This proved the backend architecture was sound.

4.  **Final Frontend Integration Failure & Solution (Structured Data):**
    -   **Problem:** When connecting the frontend, we encountered numerous bugs related to parsing the agent's final response. The agent was returning a natural language sentence that also contained the image URL (e.g., "Here is your image: [URL]"). The frontend's string parsing and regex logic was fragile and kept breaking.
    -   **The Definitive Solution:** We adopted a proper API contract. The `specialist_image` agent's prompt was updated to instruct it to **always return a single, valid JSON object**.
        ```json
        {
          "text": "Here is the image of a butterfly you requested!",
          "imageUrl": "https://..."
        }
        ```
    -   The frontend's `useChat` hook was then simplified to parse this clean, predictable JSON. It uses the `author` field of the event to know whether to expect plain text (from `specialist_text`) or JSON (from `specialist_image`).

### Final, Working Architecture

-   **Orchestrator (`LlmAgent`):** Routes to the correct specialist based on user intent.
-   **Text Specialist (`LlmAgent`):** A standard agent that streams back plain text.
-   **Image Specialist (`LlmAgent`):** A standard agent whose only job is to use an `MCPToolset`. Its prompt instructs it to return a structured JSON object containing the final text and image URL.
-   **MCP Server:** A separate, running process that handles all communication with the Google Imagen API.
-   **Frontend:** Parses the event stream, checks the `author`, and renders either plain text or the text/image pair from the parsed JSON. This is the final, robust, and correct implementation.

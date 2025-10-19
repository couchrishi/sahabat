from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx
import os
import json

router = APIRouter()

AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "http://localhost:8001")

# Create a reusable httpx client
client = httpx.AsyncClient(timeout=60)

async def stream_proxy(payload: dict):
    """
    Proxies a streaming request to the agent server's /run_sse endpoint.
    """
    try:
        async with client.stream("POST", f"{AGENT_SERVER_URL}/run_sse", json=payload) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
    except httpx.RequestError as e:
        error_event = {"error": f"Agent service connection error: {e}"}
        yield f"data: {json.dumps(error_event)}\n\n"
    except httpx.HTTPStatusError as e:
        error_event = {"error": f"Agent service error: {e.response.status_code} - {e.response.text}"}
        yield f"data: {json.dumps(error_event)}\n\n"


@router.post("/chat")
async def handle_chat(request: Request):
    """
    This endpoint acts as a simple streaming proxy. It takes the request body
    from the client and forwards it directly to the ADK agent's /run_sse endpoint.
    
    The client is responsible for session creation and management.
    """
    if not AGENT_SERVER_URL:
        raise HTTPException(status_code=500, detail="AGENT_SERVER_URL is not configured.")

    # Get the raw JSON body from the incoming request
    payload = await request.json()

    return StreamingResponse(
        stream_proxy(payload),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

@router.post("/session/{app_name}/users/{user_id}/sessions/{session_id}")
async def create_session_proxy(app_name: str, user_id: str, session_id: str):
    """
    Proxies the request to create a new session on the ADK agent server.
    """
    session_url = f"{AGENT_SERVER_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
    try:
        response = await client.post(session_url, json={})
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Agent service connection error: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
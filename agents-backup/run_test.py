import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from src.sahabat.agent import root_agent
import threading
from typing import AsyncGenerator, Generator, Any
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def to_async_generator(gen: Generator[Any, None, None]) -> AsyncGenerator[Any, None]:
    """Wraps a synchronous generator to be used in an async for loop."""
    loop = asyncio.get_event_loop()
    q = asyncio.Queue()
    stop_event = threading.Event()

    def producer():
        try:
            for item in gen:
                if stop_event.is_set():
                    break
                loop.call_soon_threadsafe(q.put_nowait, item)
        finally:
            loop.call_soon_threadsafe(q.put_nowait, StopAsyncIteration)

    threading.Thread(target=producer).start()

    async def consumer():
        while True:
            item = await q.get()
            if item is StopAsyncIteration:
                break
            yield item

    return consumer()

async def main():
    """
    An asynchronous function to set up and run the agent test.
    """
    print("--- Starting Agent Test ---")

    # 1. Set up the necessary components
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("The GOOGLE_API_KEY environment variable is not set.")

    session_service = InMemorySessionService()
    app_name = "sahabat_test"
    user_id = "test_user"

    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service,
        config={"api_key": google_api_key}
    )

    # 3. Define the user's query and initial state
    user_query = "Write a short story about a friendly robot."
    initial_state = {
        "user_tier": "Paid",
        "query": user_query
    }
    user_message = Content(parts=[Part(text=user_query)])
    print(f"User query: {user_query}")

    # 2. Create a new session with the desired initial state
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        state=initial_state
    )

    # 4. Run the agent and process the events
    event_generator = to_async_generator(runner.run(
        user_id=user_id,
        session_id=session.id,
        new_message=user_message
    ))

    async for event in event_generator:
        # We are just consuming the events here. The final result is in the state.
        pass

    # 5. Retrieve the final state to verify the changes
    final_session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session.id
    )
    
    final_response = final_session.state.get("final_response")
    print(f"\nAgent's Final Response:\n---")
    print(final_response)
    print("---")

    print(f"\nFinal session state: {final_session.state}")
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())

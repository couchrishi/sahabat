import os
from google.adk.cli.fast_api import start_server
from google.adk.sessions import ThreadSafeInMemorySessionService
from src.sahabat.agent import root_agent
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Starts the ADK server to expose the root_agent as an HTTP service.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("The GOOGLE_API_KEY environment variable is not set.")

    print("--- Starting ADK Agent Server ---")
    
    # The SessionService must be thread-safe when used with the server.
    session_service = ThreadSafeInMemorySessionService()
    
    app = start_server(
        agent=root_agent,
        session_service=session_service,
        config={"api_key": google_api_key}
    )

    # Add CORS middleware to allow requests from the frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()

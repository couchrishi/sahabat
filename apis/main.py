from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sahabat AI Gateway",
    version="1.1.0",
    description="The central gateway for the Sahabat AI Aggregator Platform.",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    return {"message": "Sahabat AI Gateway is running."}

# Placeholder for including API routes
from routers import chat
app.include_router(chat.router)

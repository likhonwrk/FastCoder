import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
import requests
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    # Add your Vercel deployment URL here after deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hugging Face client
client = OpenAI(
    base_url="https://api-inference.huggingface.co/v1",
    api_key=os.environ.get("HF_TOKEN"),
)

# MCP Server configuration
HF_MCP_HEADERS = {"Authorization": f"Bearer {os.environ.get('HF_TOKEN')}"}
HF_MCP_SERVER = "https://huggingface.co/mcp"

@app.get("/api/chat")
async def chat(prompt: str):
    # Basic logic to decide if we need to use a tool
    if "search for model" in prompt.lower():
        query = prompt.lower().replace("search for model", "").strip()
        response = requests.get(
            f"{HF_MCP_SERVER}/search/models",
            headers=HF_MCP_HEADERS,
            params={"q": query}
        )
        return response.json()

    # Default to chat completion
    stream = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8b-chat-hf",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    def event_stream():
        for chunk in stream:
            delta = chunk.choices[0].delta.get("content")
            if delta:
                yield delta

    return StreamingResponse(event_stream(), media_type="text/plain")

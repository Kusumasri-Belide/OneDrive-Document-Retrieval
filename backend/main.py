from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.llm_answer import generate_answer
from backend.mcp_server import mcp

app = FastAPI(title="Document Agent API", version="1.0.0")

# CORS (tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # required by browser MCP clients
)

# Expose MCP over HTTP at /mcp
app.mount("/mcp", mcp.streamable_http_app())


class Query(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
async def ask_question(q: Query):
    try:
        answer = generate_answer(q.question)
        return {"answer": answer}
    except FileNotFoundError as e:
        # Vector store not built yet
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Bubble other errors with message
        raise HTTPException(status_code=500, detail=str(e))

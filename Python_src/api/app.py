from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from models.dispatcher import handle_recommendation


app = FastAPI()

# CORS (allow from env ALLOWED_ORIGINS="http://a.com,https://b.com"; default: *)
_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
if _origins_raw.strip():
    _allowed_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
else:
    _allowed_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend")
async def recommend(req: Request):
    payload = await req.json()
    result = handle_recommendation(payload)
    return result



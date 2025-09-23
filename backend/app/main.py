from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_asr import router as asr_router
from app.core.logger import setup_logging

app = FastAPI(title="VnPost ASR API")

# Logging
setup_logging()

# CORS (tùy chỉnh theo môi trường của bạn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asr_router, prefix="/api/v1")

@app.get("/")
async def hello():
    return {"message": "Welcome to VnPost ASR API!"}
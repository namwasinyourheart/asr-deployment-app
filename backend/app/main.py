from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_asr import router as asr_router
from app.api.routes_language import router as language_router

app = FastAPI(title="VnPost ASR API")

# CORS (tùy chỉnh theo môi trường của bạn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(asr_router, prefix="/asr/v1")
app.include_router(language_router, prefix="/apr/v1")

@app.get("/")
async def hello():
    return {"message": "Welcome to VnPost ASR API!"}
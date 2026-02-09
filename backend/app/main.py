from fastapi import FastAPI
from api.routes import router as api_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agentic Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
load_dotenv()


@app.get("/")
async def root():
    return {"message": "Agentic Backend is running"}

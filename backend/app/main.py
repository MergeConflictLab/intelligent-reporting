from fastapi import FastAPI
from api.routes import router as api_router
from dotenv import load_dotenv

app = FastAPI(title="Agentic Backend")

app.include_router(api_router)
load_dotenv()

@app.get("/")
async def root():
    return {"message": "Agentic Backend is running"}

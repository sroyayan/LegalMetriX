import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.api.scan import router as scan_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LegalMetriX API",
    version="1.0.0",
)

app.include_router(
    scan_router,
    prefix="/scan",
    tags=["Scan"]
)

@app.get("/")
def root():
    return {
        "status": "running",
        "project": "LegalMetriX"
    }
import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import db
from dotenv import load_dotenv
from routes import teacher

load_dotenv('app/.env')
engine = db.engine

app = FastAPI()
app.include_router(teacher.router, prefix="/api/v1")
logger = logging.getLogger(__name__)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(status_code=exc.status_code, content={"message": message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else {}
    message = first_error.get("msg", "Validation error")
    return JSONResponse(status_code=400, content={"message": message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.on_event("startup")
def startup_event():
    db.seed_default_admin()


@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_frontend():
    if frontend_dir.exists():
        return FileResponse(frontend_dir / "index.html")
    return JSONResponse(status_code=404, content={"message": "Frontend not found"})


if __name__ == "__main__":
    server_address = os.getenv("SERVER_ADDRESS", "0.0.0.0:8080")
    host, port = server_address.split(":")
    uvicorn.run(app=app, host=host, port=int(port))

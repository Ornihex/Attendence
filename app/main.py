import os
from fastapi import FastAPI
import uvicorn
import db
from dotenv import load_dotenv
from routes import teacher

load_dotenv('app/.env')
engine = db.engine

app = FastAPI()
app.include_router(teacher.router)

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    server_address = os.getenv("SERVER_ADDRESS", "0.0.0.0:8080")
    host, port = server_address.split(":")
    uvicorn.run(app=app, host=host, port=int(port))
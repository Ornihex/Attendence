import os
from fastapi import FastAPI
import uvicorn
import db

engine = db.engine

app = FastAPI()

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    server_address = os.getenv("SERVER_ADDRESS", "0.0.0.0:8080")
    host, port = server_address.split(":")
    uvicorn.run(app=app, host=host, port=int(port))
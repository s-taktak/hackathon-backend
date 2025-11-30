from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import input


app = FastAPI()


@app.get("/hello")
async def hello():
    return {"message": "hello world!"}

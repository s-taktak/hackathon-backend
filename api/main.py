from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import api.models
import api.core as core
from api.utils.searcher import VectorSearchEngine
from api.routers import auth, item, me, search, comment, users, recommend,category,aiSearch, brand

MODEL_PATH = "/code/api/data/mercari_twotower_model.pth"
ENCODERS_PATH = "/code/api/data/encoders.pkl"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        engine = VectorSearchEngine(MODEL_PATH, ENCODERS_PATH)
        core.search_engine = engine
        print("✅ Search engine initialized")
    except Exception:
        core.search_engine = None
        print("❌ Search engine initialization failed")
    
    yield
    
    core.search_engine = None

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(item.router)
app.include_router(search.router)
app.include_router(me.router)
app.include_router(comment.router)
app.include_router(users.router)
app.include_router(recommend.router)
app.include_router(category.router)
app.include_router(aiSearch.router)
app.include_router(brand.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://hackathon-frontend-o4tcag5i3-s-taktaks-projects.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
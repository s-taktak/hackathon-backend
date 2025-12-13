from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import api.models
import api.core as core  # coreをインポート
from api.utils.searcher import VectorSearchEngine

# --- ルーターのインポート ---
# 循環参照を避けるため、ここでは関数内でインポートするか、
# coreの初期化が済んだ後に router を include する構成にします。
from api.routers import auth, item, me, search,comment,users


# モデルのパス設定
MODEL_PATH = "/code/api/data/mercari_twotower_model.pth"
ENCODERS_PATH = "/code/api/data/encoders.pkl"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🌟 Lifespan started! Initializing search engine...")
    try:
        # インスタンス生成
        engine = VectorSearchEngine(MODEL_PATH, ENCODERS_PATH)
        # ★ coreにセットする (これで他のファイルから core.search_engine で使える)
        core.search_engine = engine
        print("✅ Search Engine successfully loaded into api.core")
    except Exception as e:
        print(f"❌ Failed to load Search Engine: {e}")
        core.search_engine = None
    
    yield
    
    print("👋 Lifespan ending...")
    core.search_engine = None

app = FastAPI(lifespan=lifespan) # ★ここ忘れずに！
app.include_router(auth.router)
app.include_router(item.router)
app.include_router(search.router)
app.include_router(me.router)
app.include_router(comment.router)
app.include_router(users.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
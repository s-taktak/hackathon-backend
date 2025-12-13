import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# 環境変数の読み込み
# --------------------------------------------------------------------------
DB_USER = os.getenv("MYSQL_USER", "uttc")
DB_PASSWORD = os.getenv("MYSQL_PWD", "password")
DB_NAME = os.getenv("MYSQL_DATABASE", "hackathon")
DB_HOST = os.getenv("MYSQL_HOST", "34.xxx.xxx.xxx")

# Cloud Runでのみ設定する変数（例: project-id:region:instance-name）
# ※ ローカルの .env には書かないでください（または空にしておく）
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

# --------------------------------------------------------------------------
# 接続URLと設定の自動切り替え
# --------------------------------------------------------------------------
if INSTANCE_CONNECTION_NAME:
    # 【Cloud Run用】 Unixソケット接続 (SSL設定不要)
    # Cloud Runでは自動的に /cloudsql/接続名 というパスでSocketが作られます
    socket_path = f"/cloudsql/{INSTANCE_CONNECTION_NAME}"
    ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?unix_socket={socket_path}&charset=utf8mb4"
    connect_args = {}  # Cloud Run上のUnixソケットは安全なのでSSL設定オブジェクトは不要
    print(f"🚀 [Cloud Run Mode] Connecting via Unix Socket: {socket_path}")

else:
    # 【ローカル開発用】 TCP接続 + SSL (さっき直したやつ)
    # 鍵ファイルのパス
    SSL_CA = "server-ca.pem"
    SSL_CERT = "client-cert.pem"
    SSL_KEY = "client-key.pem"

    ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    
    # SSLコンテキストの作成
    ssl_context = ssl.create_default_context(cafile=SSL_CA)
    ssl_context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    connect_args = {"ssl": ssl_context}
    print(f"💻 [Local Mode] Connecting via TCP: {DB_HOST}")


# --------------------------------------------------------------------------
# エンジンの作成
# --------------------------------------------------------------------------
async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=True,
    connect_args=connect_args
)

async_session = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
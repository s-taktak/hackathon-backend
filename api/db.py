import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("MYSQL_USER", "uttc")
DB_PASSWORD = os.getenv("MYSQL_PWD", "password")
DB_NAME = os.getenv("MYSQL_DATABASE", "hackathon")
DB_HOST = os.getenv("MYSQL_HOST", "34.xxx.xxx.xxx")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

if INSTANCE_CONNECTION_NAME: # CloudRun
    socket_path = f"/cloudsql/{INSTANCE_CONNECTION_NAME}"
    ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?unix_socket={socket_path}&charset=utf8mb4"
    connect_args = {}

else:# local
    SSL_CA = "server-ca.pem"
    SSL_CERT = "client-cert.pem"
    SSL_KEY = "client-key.pem"

    ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    
    ssl_context = ssl.create_default_context(cafile=SSL_CA)
    ssl_context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    connect_args = {"ssl": ssl_context}

async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    connect_args=connect_args
)

async_session = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
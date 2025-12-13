from sqlalchemy import create_engine
from api.models.users import Base  # ← 作成したuserモデルを読み込む
import os

# ---------------------------------------------------------
# 環境変数から設定を取得 (api/db.py と同じロジック)
# ---------------------------------------------------------
DB_USER = os.getenv("MYSQL_USER", "uttc")
DB_PASSWORD = os.getenv("MYSQL_PWD", "password")
DB_HOST = os.getenv("MYSQL_HOST", "34.xxx.xxx.xxx")
DB_NAME = os.getenv("MYSQL_DATABASE", "hackathon")

# SSL証明書のパス
SSL_CA = "server-ca.pem"
SSL_CERT = "client-cert.pem"
SSL_KEY = "client-key.pem"

# ---------------------------------------------------------
# 同期接続用のURL作成 (mysql+pymysql を使用)
# ---------------------------------------------------------
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

# エンジン作成時にSSL設定を渡す
engine = create_engine(
    DB_URL, 
    echo=True,
    connect_args={
        "ssl": {
            "ca": SSL_CA,
            "cert": SSL_CERT,
            "key": SSL_KEY
        }
    }
)

def reset_database():
    # 注意: これを実行すると既存のデータが全て消えます！
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ テーブルを再作成しました！")

if __name__ == "__main__":
    reset_database()
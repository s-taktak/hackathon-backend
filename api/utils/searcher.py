import torch
import numpy as np
import pickle
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn
from api.utils.two_tower_model import TwoTowerModel

# --- 設定 ---
QDRANT_HOST = "qdrant" 
COLLECTION_NAME = "mercari_items"
EMBEDDING_DIM = 128
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_NAME = 'prajjwal1/bert-tiny'

class SafeLabelEncoder:
    def __init__(self):
        self.vocab = {}
        self.unknown_idx = 0 # 0番を「未知/その他」にする

    def fit(self, values):
        # ユニークな値を取得し、文字列としてソート
        unique_values = np.unique(values.astype(str))
        # 1番から連番を振る (0番はUnknown用に空ける)
        self.vocab = {val: i + 1 for i, val in enumerate(unique_values)}
        # 次元数 = ユニーク数 + 1 (Unknown分)
        self.num_classes = len(self.vocab) + 1

    def transform(self, values):
        # 辞書にないものは 0 (Unknown) に変換する
        return np.array([self.vocab.get(str(v), self.unknown_idx) for v in values])
    
try:
    import uvicorn.__main__
    setattr(uvicorn.__main__, 'SafeLabelEncoder', SafeLabelEncoder)
except (ImportError, AttributeError):
    pass # uvicorn以外で動いているときは無視

# --- 3. カスタムUnpickler (念のための保険) ---
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # デバッグ用ログ
        # print(f"🔍 Unpickling: {module}.{name}") 
        if name == 'SafeLabelEncoder':
            return SafeLabelEncoder
        return super().find_class(module, name)
    

# --- 検索エンジンクラス ---
class VectorSearchEngine:
    def __init__(self, model_path: str, encoders_path: str):
        try:
            self.client = QdrantClient(host=QDRANT_HOST, port=6333)
        except:
            self.client = None
            print("⚠️ Qdrant connection failed.")

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = None
        self.encoders = None
        
        # モデル読み込み
        try:
            self._load_resources(model_path, encoders_path)
        except Exception as e:
            print(f"⚠️ Model load failed detail: {e}")
            raise e 
        
        if self.client:
            try:
                self._init_collection()
            except Exception as e:
                print(f"⚠️ Qdrant init failed: {e}")

    def _load_resources(self, model_path, encoders_path):
        print(f"📂 Loading model from {model_path}...")
        
        with open(encoders_path, 'rb') as f:
            data_pack = CustomUnpickler(f).load()
            self.encoders = data_pack['encoders']
            dims = data_pack['dims']

        self.model = TwoTowerModel(dims).to(DEVICE)
        self.model.load_state_dict(torch.load(model_path, map_location=DEVICE))
        self.model.eval()
        print("✅ Model loaded successfully.")

    def _init_collection(self):
        try:
            collections = self.client.get_collections()
            exists = any(c.name == COLLECTION_NAME for c in collections.collections)
            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=EMBEDDING_DIM,
                        distance=qmodels.Distance.COSINE
                    )
                )
                print(f"✅ Collection '{COLLECTION_NAME}' created.")
        except Exception as e:
            print(f"⚠️ Failed to init collection: {e}")

    def encode_single_item(self, item_dict: dict) -> list:
        if not self.model:
            print("⚠️ Model is not loaded.")
            return []
        
        self.model.eval()
        with torch.no_grad():
            try:
                # IDを文字列に変換 (Noneは '0' に)
                def safe_str_id(val):
                    if val is None: return '0'
                    return str(val)

                b_id = safe_str_id(item_dict.get('brand_id'))
                c_id = safe_str_id(item_dict.get('category_id'))
                cond_id = safe_str_id(item_dict.get('condition_id'))

                # SafeLabelEncoderなら未知の値でもエラーにならず 0 が返る
                # リスト形式で渡して [0] を取り出す
                brand_val = self.encoders['brand_id'].transform([b_id])[0]
                cat_val = self.encoders['c2_id'].transform([c_id])[0]
                cond_val = self.encoders['item_condition_id'].transform([cond_id])[0]

                price_val = float(item_dict.get('price', 0))
                price = torch.tensor([np.log1p(price_val)], dtype=torch.float).to(DEVICE)
                brand = torch.tensor([brand_val], dtype=torch.long).to(DEVICE)
                cat = torch.tensor([cat_val], dtype=torch.long).to(DEVICE)
                cond = torch.tensor([cond_val], dtype=torch.long).to(DEVICE)

                inputs = self.tokenizer(
                    item_dict.get('title', ''), 
                    padding='max_length', truncation=True, max_length=32, return_tensors='pt'
                ).to(DEVICE)

                vector = self.model.forward_one_tower(
                    inputs['input_ids'], inputs['attention_mask'],
                    price, brand, cat, cond
                )
                
                print(f"✅ Vector created for: {item_dict.get('title')[:10]}...")
                return vector.cpu().numpy()[0].tolist()

            except Exception as e:
                import traceback
                print(f"❌ Vector encoding failed: {e}")
                print(traceback.format_exc())
                return []

    def encode_query(self, query_text: str) -> list:
        if not self.model: return []

        self.model.eval()
        with torch.no_grad():
            try:
                inputs = self.tokenizer(
                    query_text, 
                    padding='max_length', truncation=True, max_length=32, return_tensors='pt'
                ).to(DEVICE)

                dummy_price = torch.tensor([np.log1p(3000.0)], dtype=torch.float).to(DEVICE)
                dummy_id = torch.tensor([0], dtype=torch.long).to(DEVICE)

                vector = self.model.forward_one_tower(
                    inputs['input_ids'], 
                    inputs['attention_mask'],
                    dummy_price, dummy_id, dummy_id, dummy_id
                )
                
                return vector.cpu().numpy()[0].tolist()

            except Exception as e:
                print(f"❌ Query encoding failed: {e}")
                return []
        
    def encode_query(self, query_text: str) -> list[float]:
        """
        検索キーワードをベクトルに変換して返す
        （カテゴリや価格は不明なので、ダミー値を入れて推論する）
        """
        self.model.eval()
        with torch.no_grad():
            try:
                # テキストのトークナイズ
                inputs = self.tokenizer(
                    query_text, 
                    padding='max_length', truncation=True, max_length=32, return_tensors='pt'
                ).to(DEVICE)

                # ダミーデータの作成
                # 検索クエリには「価格」や「ブランド」の概念がないため、
                # モデルが混乱しないよう「0 (Unknown)」や「平均的な値」を入れます
                dummy_price = torch.tensor([np.log1p(3000.0)], dtype=torch.float).to(DEVICE) # 仮の価格
                dummy_id = torch.tensor([0], dtype=torch.long).to(DEVICE) # Unknown ID

                # 推論 (forward_one_tower)
                vector = self.model.forward_one_tower(
                    inputs['input_ids'], 
                    inputs['attention_mask'],
                    dummy_price, # price
                    dummy_id,    # brand
                    dummy_id,    # category
                    dummy_id     # condition
                )
                
                # Pythonのリストに変換して返す ([0.123, ...])
                return vector.cpu().numpy()[0].tolist()

            except Exception as e:
                print(f"❌ Query encoding failed: {e}")
                return []
        
    def create_index(self, items: list[dict]):
        """
        全商品をベクトル化して保存する
        items: [{"id": "uuid", "title": "name", "price": 1000, ...}, ...] のリスト
        """
        print(f"🔄 {len(items)}件のインデックスを作成中...")
        vectors = []
        ids = []
        
        with torch.no_grad():
            for item in items:
                try:
                    # ID変換 (未知の値は0番=Unknownに変換)
                    # DBから来る値は文字列やIntが混ざる可能性があるので str() で統一
                    b_id = str(item.get('brand_id', '0'))
                    c_id = str(item.get('category_id', '0')) # DBのカラム名に合わせて調整
                    cond_id = str(item.get('condition_id', '0'))

                    brand_val = self.encoders['brand_id'].transform([b_id])[0]
                    cat_val = self.encoders['c2_id'].transform([c_id])[0] # 学習時のキー名 'c2_id' に合わせる
                    cond_val = self.encoders['item_condition_id'].transform([cond_id])[0]

                    # Tensor化
                    price = torch.tensor([np.log1p(float(item.get('price', 0)))], dtype=torch.float).to(DEVICE)
                    brand = torch.tensor([brand_val], dtype=torch.long).to(DEVICE)
                    cat = torch.tensor([cat_val], dtype=torch.long).to(DEVICE)
                    cond = torch.tensor([cond_val], dtype=torch.long).to(DEVICE)

                    # テキスト処理
                    inputs = self.tokenizer(
                        item.get('title', ''), 
                        padding='max_length', truncation=True, max_length=32, return_tensors='pt'
                    ).to(DEVICE)

                    # ベクトル生成
                    vec = self.model.forward_one_tower(
                        inputs['input_ids'], inputs['attention_mask'],
                        price, brand, cat, cond
                    )
                    vectors.append(vec.cpu())
                    ids.append(str(item['id']))
                    
                except Exception as e:
                    print(f"Skipping item {item.get('id')}: {e}")
                    continue

        if not vectors:
            print("⚠️ ベクトル化できるアイテムがありませんでした")
            return

        # 結合して保存
        self.index_vectors = torch.cat(vectors)
        self.index_ids = ids
        
        with open(self.index_path, 'wb') as f:
            pickle.dump({'vectors': self.index_vectors, 'ids': self.index_ids}, f)
        print("✅ インデックス作成完了")

    def load_index(self):
        """保存されたインデックスをメモリに読み込む"""
        if not self.index_path.exists():
            return
        
        with open(self.index_path, 'rb') as f:
            data = pickle.load(f)
            self.index_vectors = data['vectors'].to(DEVICE)
            self.index_ids = data['ids']
        print(f"✅ インデックス読込完了: {len(self.index_ids)}件")

    def search(self, query: str, top_k: int = 10):
        """検索を実行する"""
        if self.index_vectors is None:
            return []

        # クエリのベクトル化 (価格などはダミー値を入れる)
        with torch.no_grad():
            inputs = self.tokenizer(
                query, padding='max_length', truncation=True, max_length=32, return_tensors='pt'
            ).to(DEVICE)
            
            # 検索クエリには「条件」がないので全て0(Unknown)や平均値を入れる
            dummy_price = torch.tensor([np.log1p(3000.0)], dtype=torch.float).to(DEVICE) # 仮の平均価格
            dummy_id = torch.tensor([0], dtype=torch.long).to(DEVICE)

            query_vec = self.model.forward_one_tower(
                inputs['input_ids'], inputs['attention_mask'],
                dummy_price, dummy_id, dummy_id, dummy_id
            )

        # 類似度計算 (コサイン類似度)
        scores = torch.matmul(query_vec, self.index_vectors.T).squeeze(0)
        
        # 上位取得
        k = min(top_k, len(self.index_ids))
        top_scores, top_indices = torch.topk(scores, k=k)
        
        # IDリストを返す
        results = [self.index_ids[i] for i in top_indices.cpu().numpy()]
        return results
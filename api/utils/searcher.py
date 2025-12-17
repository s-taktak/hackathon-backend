import torch
import numpy as np
import pickle
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn
from api.utils.two_tower_model import TwoTowerModel
import json

# --- 設定 ---
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
        self.client = None # Qdrantは使わないのでNone
        self.model = None
        self.encoders = None
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        try:
            self._load_resources(model_path, encoders_path)
        except Exception as e:
            print(f"⚠️ Model load failed detail: {e}")
            raise e 

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

    # _init_collection は削除

    def encode_single_item(self, item_dict: dict) -> list:
        # ベクトル生成ロジックはそのまま
        if not self.model: return []
        self.model.eval()
        with torch.no_grad():
            try:
                def safe_str_id(val): return '0' if val is None else str(val)
                b_id = safe_str_id(item_dict.get('brand_id'))
                c_id = safe_str_id(item_dict.get('category_id'))
                cond_id = safe_str_id(item_dict.get('condition_id'))

                brand_val = self.encoders['brand_id'].transform([b_id])[0]
                cat_val = self.encoders['c2_id'].transform([c_id])[0]
                cond_val = self.encoders['item_condition_id'].transform([cond_id])[0]

                price_val = float(item_dict.get('price', 0))
                price = torch.tensor([np.log1p(price_val)], dtype=torch.float).to(DEVICE)
                brand = torch.tensor([brand_val], dtype=torch.long).to(DEVICE)
                cat = torch.tensor([cat_val], dtype=torch.long).to(DEVICE)
                cond = torch.tensor([cond_val], dtype=torch.long).to(DEVICE)

                inputs = self.tokenizer(item_dict.get('title', ''), padding='max_length', truncation=True, max_length=32, return_tensors='pt').to(DEVICE)

                vector = self.model.forward_one_tower(
                    inputs['input_ids'], inputs['attention_mask'],
                    price, brand, cat, cond
                )
                return vector.cpu().numpy()[0].tolist()
            except Exception as e:
                print(f"❌ Vector encoding failed: {e}")
                return []

    def encode_query(self, query_text: str) -> list:
        if not self.model: return []
        self.model.eval()
        with torch.no_grad():
            try:
                inputs = self.tokenizer(query_text, padding='max_length', truncation=True, max_length=32, return_tensors='pt').to(DEVICE)
                dummy_price = torch.tensor([np.log1p(3000.0)], dtype=torch.float).to(DEVICE)
                dummy_id = torch.tensor([0], dtype=torch.long).to(DEVICE)
                vector = self.model.forward_one_tower(
                    inputs['input_ids'], inputs['attention_mask'],
                    dummy_price, dummy_id, dummy_id, dummy_id
                )
                return vector.cpu().numpy()[0].tolist()
            except Exception as e:
                print(f"❌ Query encoding failed: {e}")
                return []
            
    def sort_by_similarity(self, vector: list, all_vectors_data: list, top_k: int = 20) -> list:
        """
        全ベクトルデータを受け取り、類似度が高い順にIDのリストを返す
        vector: 検索したいベクトル (list of float)
        all_vectors_data: ItemVectorモデルのリスト
        """
        if not all_vectors_data:
            return []

        scores = []
        query_vec_np = np.array(vector)
        query_norm = np.linalg.norm(query_vec_np)

        for v_obj in all_vectors_data:
            try:
                # DBの文字列型ベクトルをリストに戻す
                if isinstance(v_obj.embedding, str):
                    vec = np.array(json.loads(v_obj.embedding))
                else:
                    vec = np.array(v_obj.embedding)
                
                vec_norm = np.linalg.norm(vec)
                
                if query_norm == 0 or vec_norm == 0:
                    score = 0
                else:
                    # コサイン類似度計算
                    score = np.dot(query_vec_np, vec) / (query_norm * vec_norm)
                
                scores.append((v_obj.item_id, score))
            except Exception as e:
                continue

        # スコア順にソート
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 上位K件のIDだけを返す
        return [item_id for item_id, score in scores[:top_k]]
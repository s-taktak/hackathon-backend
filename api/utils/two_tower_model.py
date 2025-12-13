import torch
import numpy as np
import pickle
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn

MODEL_NAME = 'prajjwal1/bert-tiny'

# --- モデル定義 (学習時と同じ構造にする必要があります) ---
class TwoTowerModel(nn.Module):
    def __init__(self, embedding_dims):
        super().__init__()
        self.bert = AutoModel.from_pretrained(MODEL_NAME)
        bert_out_dim = self.bert.config.hidden_size
        
        # 学習時と同じ次元数で定義
        self.brand_emb = nn.Embedding(embedding_dims['brand_id'], 16)
        self.cat_emb = nn.Embedding(embedding_dims['c2_id'], 16)
        self.cond_emb = nn.Embedding(embedding_dims['item_condition_id'], 8)
        
        self.projection = nn.Sequential(
            nn.Linear(bert_out_dim + 16 + 16 + 8 + 1, 256),
            nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(256, 128) # EMBEDDING_DIM
        )

    def forward_one_tower(self, input_ids, mask, price, brand, category, condition):
        bert_out = self.bert(input_ids=input_ids, attention_mask=mask).pooler_output
        combined = torch.cat([
            bert_out, self.brand_emb(brand), self.cat_emb(category),
            self.cond_emb(condition), price.unsqueeze(1)
        ], dim=1)
        return torch.nn.functional.normalize(self.projection(combined), p=2, dim=1)
import os
from rank_bm25 import BM25Okapi
from pathlib import Path

class SimpleBM25Retriever:
    def __init__(self, docs_dir="docs"):
        self.docs_dir = Path(docs_dir)
        self.chunks = []
        self.bm25 = None
        self._load_and_chunk()

    def _load_and_chunk(self):
        chunk_id = 0
        for file_path in self.docs_dir.rglob("*.md"):
            text = file_path.read_text(encoding="utf-8")
            lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#")]
            for i, line in enumerate(lines):
                if len(line) > 20:  # skip very short lines
                    self.chunks.append({
                        "id": f"{file_path.name}::chunk{chunk_id}",
                        "content": line,
                        "source": str(file_path)
                    })
                    chunk_id += 1
        tokenized_corpus = [doc["content"].lower().split() for doc in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, k: int = 4):
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = scores.argsort()[::-1][:k]
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            chunk["score"] = float(scores[idx])
            results.append(chunk)
        return results
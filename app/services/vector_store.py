from typing import List, Dict, Tuple
from collections import defaultdict

# Very simple TF-IDF-ish stub: store document texts and return when query tokens overlap.
class InMemoryVectorStore:
    def __init__(self):
        self.docs: Dict[int, str] = {}

    def add_document(self, doc_id: int, text: str) -> str:
        self.docs[doc_id] = text
        return str(doc_id)

    def query(self, query: str, top_k: int = 5) -> List[Dict]:
        qtokens = set(query.lower().split())
        results = []
        for doc_id, text in self.docs.items():
            tset = set(text.lower().split())
            score = len(qtokens & tset)
            if score > 0:
                snippet = text[:200]
                results.append({"doc_id": doc_id, "score": float(score), "snippet": snippet})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]


# singleton instance
vector_store = InMemoryVectorStore()


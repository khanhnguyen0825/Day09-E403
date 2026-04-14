"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - (optional) retrieved_chunks nếu đã có từ trước

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames
    - worker_io_log: log input/output của worker này

Gọi độc lập để test:
    python workers/retrieval.py
"""

import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Đường dẫn đến database từ Day 08
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../day08/lab/chroma_db"))
WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3

def _get_embedding_fn():
    """Sử dụng OpenAI embedding như Day 08."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    def embed(text: str) -> list:
        resp = client.embeddings.create(input=text, model="text-embedding-3-small")
        return resp.data[0].embedding
    return embed

def _get_collection():
    import chromadb
    # Debug: In ra đường dẫn thực tế để kiểm tra
    print(f"DEBUG: Connecting to ChromaDB at: {CHROMA_DB_PATH}")
    if not os.path.exists(CHROMA_DB_PATH):
        print(f"ERROR: Path does not exist: {CHROMA_DB_PATH}")
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    # Tên collection ở Day 08 là "rag_lab"
    return client.get_collection("rag_lab")

def retrieve_dense(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    embed_fn = _get_embedding_fn()
    query_embedding = embed_fn(query)
    collection = _get_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    chunks = []
    if results["documents"]:
        for i in range(len(results["documents"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]
            })
    return chunks

def retrieve_sparse(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    from rank_bm25 import BM25Okapi
    collection = _get_collection()
    results = collection.get(include=["documents", "metadatas"])
    
    if not results["documents"]:
        return []

    corpus = results["documents"]
    metadatas = results["metadatas"]
    
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    chunks = []
    for i in top_indices:
        if scores[i] > 0:
            chunks.append({
                "text": corpus[i],
                "metadata": metadatas[i],
                "score": scores[i]
            })
    return chunks

def retrieve_hybrid(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """Kết hợp Dense và Sparse bằng RRF (giống Day 08)."""
    dense_results = retrieve_dense(query, top_k * 2)
    sparse_results = retrieve_sparse(query, top_k * 2)
    
    rrf_scores = {}
    chunk_map = {}
    
    for rank, chunk in enumerate(dense_results):
        text = chunk["text"]
        if text not in rrf_scores:
            rrf_scores[text] = 0
            chunk_map[text] = chunk
        rrf_scores[text] += 0.6 * (1 / (60 + rank))
        
    for rank, chunk in enumerate(sparse_results):
        text = chunk["text"]
        if text not in rrf_scores:
            rrf_scores[text] = 0
            chunk_map[text] = chunk
        rrf_scores[text] += 0.4 * (1 / (60 + rank))
        
    sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for text, score in sorted_chunks[:top_k]:
        chunk = chunk_map[text]
        chunk["score"] = round(score, 4)
        results.append(chunk)
    return results

def run(state: dict) -> dict:
    task = state.get("task", "")
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)
    
    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)
    
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }
    
    try:
        # Sử dụng Hybrid Retrieval làm mặc định vì nó mạnh nhất
        chunks = retrieve_hybrid(task, top_k=top_k)
        sources = list({c["metadata"].get("source", "unknown") for c in chunks})
        
        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources
        worker_io["output"] = {"chunks_count": len(chunks), "sources": sources}
        state["history"].append(f"[{WORKER_NAME}] retrieved {len(chunks)} chunks using Hybrid Search")
        
    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")
        
    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query})
        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved: {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")
        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")

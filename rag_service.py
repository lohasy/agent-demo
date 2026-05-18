from pathlib import Path
import hashlib
import chromadb
from chromadb.utils import embedding_functions

KNOWLEDGE_DIR = Path("D:/agent-demo/knowledge")

_cache_file = KNOWLEDGE_DIR / ".cache_checksum"
_collection = None


def _get_embedding_fn():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5",
        device="cpu",
    )


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(
            path=str(KNOWLEDGE_DIR / ".chromadb")
        )
        _collection = client.get_or_create_collection(
            name="knowledge",
            embedding_function=_get_embedding_fn(),
        )
    return _collection


def _compute_checksum() -> str:
    hasher = hashlib.md5()
    for txt in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        hasher.update(txt.read_bytes())
    return hasher.hexdigest()


def _load_documents():
    docs = []
    for txt in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        raw = txt.read_text(encoding="utf-8")
        chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": f"{txt.stem}_{i}",
                "content": chunk,
                "source": txt.name,
            })
    return docs


def index_documents(force: bool = False):
    checksum = _compute_checksum()
    cached = _cache_file.read_text().strip() if _cache_file.exists() else ""

    if not force and checksum == cached:
        return

    docs = _load_documents()
    if not docs:
        return

    col = _get_collection()
    existing = col.get()["ids"]
    if existing:
        col.delete(ids=existing)
    col.add(
        ids=[d["id"] for d in docs],
        documents=[d["content"] for d in docs],
        metadatas=[{"source": d["source"]} for d in docs],
    )

    _cache_file.write_text(checksum)


def search(query: str, top_k: int = 3) -> str:
    col = _get_collection()
    results = col.query(query_texts=[query], n_results=top_k)
    docs = results["documents"][0]

    if not docs or all(not d for d in docs):
        return "未在知识库中找到相关内容。"

    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"【相关文档{i}】{doc}")
    return "\n\n".join(parts)

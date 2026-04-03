import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from langchain.schema import Document

try:
    # Pinecone SDK
    from pinecone import Pinecone  # type: ignore
except Exception:  # pragma: no cover
    Pinecone = None  # type: ignore


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    # Small, allocation-light cosine similarity for MMR re-ranking.
    dot = 0.0
    a_norm = 0.0
    b_norm = 0.0
    for x, y in zip(a, b):
        dot += x * y
        a_norm += x * x
        b_norm += y * y
    if a_norm <= 0.0 or b_norm <= 0.0:
        return 0.0
    return dot / (math.sqrt(a_norm) * math.sqrt(b_norm))


def _allowed_tenant_ids_from_filter(filter_dict: Optional[Dict[str, Any]]) -> Optional[Set[str]]:
    """
    Your current code passes Chroma-style filters like:
      {"$or": [{"tenant_id": "A"}, {"tenant_id": "tenant_all"}]}
    We map that to a set of allowed tenant ids for post-filtering.
    """
    if not filter_dict:
        return None

    if "$or" in filter_dict and isinstance(filter_dict["$or"], list):
        out: Set[str] = set()
        for item in filter_dict["$or"]:
            if isinstance(item, dict) and "tenant_id" in item:
                val = item.get("tenant_id")
                if val is not None:
                    out.add(str(val))
        return out or None

    # Fallback: handle {"tenant_id": "..."}
    if "tenant_id" in filter_dict:
        val = filter_dict.get("tenant_id")
        if val is not None:
            return {str(val)}

    return None


@dataclass(frozen=True)
class _Candidate:
    id: str
    score: float
    values: Optional[List[float]]
    metadata: Dict[str, Any]


class PineconeVectorStore:
    """
    Minimal Pinecone-backed vector store that exposes a Chroma-like interface
    for `RetrievalServiceV2`:
      - add_documents(docs)
      - get(where={"tenant_id": ...})
      - delete(ids=[...])
      - as_retriever(search_type=..., search_kwargs=...).invoke(query)

    NOTE: Pinecone does not provide a "get all vectors by metadata" API.
    To keep your current suggestion/count logic working, we persist chunk
    text + metadata in a local JSON file per tenant under `meta_path`.
    """

    def __init__(
        self,
        *,
        embeddings: Any,
        pinecone_api_key: str,
        index_name: str,
        meta_path: str,
        host: Optional[str] = None,
        environment: Optional[str] = None,
        embedding_batch_size: int = 100,
    ):
        if Pinecone is None:
            raise ImportError(
                "Pinecone SDK is not installed. Add `pinecone` to requirements.txt and reinstall."
            )
        if not pinecone_api_key or not index_name:
            raise ValueError("pinecone_api_key and index_name are required")

        self.embeddings = embeddings
        self.pinecone_api_key = pinecone_api_key
        self.index_name = index_name
        # Make the cache path absolute so it doesn't depend on where `python main.py`
        # is launched from.
        self.meta_path = os.path.abspath(meta_path)
        self.host = host
        self.environment = environment
        self.embedding_batch_size = max(1, int(embedding_batch_size))

        os.makedirs(self.meta_path, exist_ok=True)
        self._index = self._init_index()

        # Simple in-process cache to avoid re-reading the same tenant file repeatedly.
        # Key: tenant_id -> {"ids": [...], "documents": [...], "metadatas": [...]}
        self._tenant_meta_cache: Dict[str, Dict[str, Any]] = {}

    def _init_index(self) -> Any:
        # Pinecone SDK has evolved; we support both "host" targeting and older "environment".
        if self.host:
            pc = Pinecone(api_key=self.pinecone_api_key)
            # `host` here should be the index's data-plane host from your Pinecone console.
            index = pc.Index(self.index_name, host=self.host)
            return index
        if self.environment:
            pc = Pinecone(api_key=self.pinecone_api_key, environment=self.environment)
            index = pc.Index(self.index_name)
            return index

        pc = Pinecone(api_key=self.pinecone_api_key)
        # Prefer direct name targeting; SDK will validate/route internally.
        return pc.Index(self.index_name)

    def _meta_file(self, tenant_id: str) -> str:
        # Tenant ids are usually safe strings (UUIDs). If yours contain slashes, we hash them.
        safe_name = tenant_id if "/" not in tenant_id else _sha256_hex(tenant_id)
        return os.path.join(self.meta_path, f"{safe_name}.json")

    def _load_tenant_meta(self, tenant_id: str) -> Dict[str, Any]:
        if tenant_id in self._tenant_meta_cache:
            return self._tenant_meta_cache[tenant_id]

        path = self._meta_file(tenant_id)
        if not os.path.exists(path):
            meta = {"ids": [], "documents": [], "metadatas": []}
            self._tenant_meta_cache[tenant_id] = meta
            return meta

        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        # Normalize expected shape.
        meta.setdefault("ids", [])
        meta.setdefault("documents", [])
        meta.setdefault("metadatas", [])

        self._tenant_meta_cache[tenant_id] = meta
        return meta

    def _save_tenant_meta(self, tenant_id: str, meta: Dict[str, Any]) -> None:
        path = self._meta_file(tenant_id)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
        os.replace(tmp_path, path)
        self._tenant_meta_cache[tenant_id] = meta

    @staticmethod
    def _make_chunk_id(tenant_id: str, source: str, content: str) -> str:
        # Deterministic id so rebuilding/upserts overwrite the same vectors.
        source_hash = _sha256_hex(source)[:10]
        content_hash = _sha256_hex(content.strip())[:16]
        return f"{tenant_id}:::{source_hash}:{content_hash}"

    @staticmethod
    def _tenant_id_from_chunk_id(chunk_id: str) -> str:
        # Our id format is: "{tenant_id}:::<source_hash>:<content_hash>"
        return chunk_id.split(":::", 1)[0]

    def persist(self) -> None:
        # Chroma persists to disk; Pinecone persists remotely.
        # Our local meta store is persisted as part of add/delete.
        return

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        # Embed and upsert in batches to reduce API pressure.
        # We still need per-document ids and metadata.
        all_docs = list(documents)
        to_upsert: List[Dict[str, Any]] = []

        # Track meta store updates per tenant.
        new_records_by_tenant: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}

        for doc in all_docs:
            tenant_id = str((doc.metadata or {}).get("tenant_id", ""))
            source = str((doc.metadata or {}).get("source", "unknown"))
            content = (doc.page_content or "").strip()

            chunk_id = self._make_chunk_id(tenant_id=tenant_id, source=source, content=content)
            meta = {"tenant_id": tenant_id, "source": source}

            new_records_by_tenant.setdefault(tenant_id, []).append((chunk_id, content, meta))
            to_upsert.append({"id": chunk_id, "metadata": meta, "content": content})

        # Embed in batches; keep ordering aligned with `to_upsert`.
        texts = [item["content"] for item in to_upsert]
        vectors: List[List[float]] = []
        for i in range(0, len(texts), self.embedding_batch_size):
            batch = texts[i : i + self.embedding_batch_size]
            batch_vectors = self.embeddings.embed_documents(batch)
            vectors.extend(batch_vectors)

        for i, item in enumerate(to_upsert):
            item["values"] = vectors[i]

        # Upsert to Pinecone.
        pinecone_vectors = [
            {"id": item["id"], "values": item["values"], "metadata": item["metadata"]}
            for item in to_upsert
        ]
        self._index.upsert(vectors=pinecone_vectors)

        # Update local meta store.
        for tenant_id, records in new_records_by_tenant.items():
            meta = self._load_tenant_meta(tenant_id)
            existing_ids = set(meta.get("ids") or [])
            for chunk_id, content, md in records:
                if chunk_id in existing_ids:
                    continue
                meta["ids"].append(chunk_id)
                meta["documents"].append(content)
                meta["metadatas"].append(md)
                existing_ids.add(chunk_id)
            self._save_tenant_meta(tenant_id, meta)

    def delete(self, ids: List[str]) -> None:
        if not ids:
            return

        # Delete from Pinecone first.
        self._index.delete(ids=ids)

        # Delete from local meta store by tenant file.
        ids_set = set(ids)
        tenants = {self._tenant_id_from_chunk_id(cid) for cid in ids}
        for tenant_id in tenants:
            meta = self._load_tenant_meta(tenant_id)
            keep_indices: List[int] = []
            for idx, cid in enumerate(meta.get("ids") or []):
                if cid not in ids_set:
                    keep_indices.append(idx)

            if len(keep_indices) == len(meta.get("ids") or []):
                continue

            meta["ids"] = [meta["ids"][i] for i in keep_indices]
            meta["documents"] = [meta["documents"][i] for i in keep_indices]
            meta["metadatas"] = [meta["metadatas"][i] for i in keep_indices]
            self._save_tenant_meta(tenant_id, meta)

    def get(self, *, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tenant_id = None
        if where and isinstance(where, dict):
            tenant_id = where.get("tenant_id")
        tenant_id_str = str(tenant_id) if tenant_id is not None else ""
        meta = self._load_tenant_meta(tenant_id_str) if tenant_id_str else {"ids": [], "documents": [], "metadatas": []}
        return {
            "ids": meta.get("ids") or [],
            "documents": meta.get("documents") or [],
            "metadatas": meta.get("metadatas") or [],
        }

    def _get_docs_for_ids(self, ids: List[str]) -> Dict[str, Tuple[str, Dict[str, Any]]]:
        # Returns chunk_id -> (page_content, metadata)
        by_tenant: Dict[str, List[str]] = {}
        for cid in ids:
            tenant_id = self._tenant_id_from_chunk_id(cid)
            by_tenant.setdefault(tenant_id, []).append(cid)

        out: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        for tenant_id, tenant_ids in by_tenant.items():
            meta = self._load_tenant_meta(tenant_id)
            id_to_doc: Dict[str, int] = {}
            for idx, cid in enumerate(meta.get("ids") or []):
                if cid in tenant_ids:
                    id_to_doc[cid] = idx

            for cid in tenant_ids:
                if cid not in id_to_doc:
                    continue
                idx = id_to_doc[cid]
                out[cid] = (meta["documents"][idx], meta["metadatas"][idx])

        return out

    def as_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        search_kwargs = search_kwargs or {}
        return _PineconeRetriever(store=self, search_type=search_type, search_kwargs=search_kwargs)


class _PineconeRetriever:
    def __init__(self, *, store: PineconeVectorStore, search_type: str, search_kwargs: Dict[str, Any]):
        self.store = store
        self.search_type = search_type
        self.search_kwargs = search_kwargs

    def invoke(self, query: str) -> List[Document]:
        k = int(self.search_kwargs.get("k", 4))
        fetch_k = int(self.search_kwargs.get("fetch_k", k))
        lambda_mult = float(self.search_kwargs.get("lambda_mult", 0.5))
        filt = self.search_kwargs.get("filter")
        allowed_tenants = _allowed_tenant_ids_from_filter(filt)  # can be None

        # Use a larger pool so post-filtering still leaves enough items.
        pool_k = min(200, max(fetch_k, k) * 4)

        query_vec = self.store.embeddings.embed_query(query)
        include_values = True

        resp = self.store._index.query(
            vector=query_vec,
            top_k=pool_k,
            include_metadata=True,
            include_values=include_values,
        )
        matches = getattr(resp, "matches", None) or resp.get("matches") or []

        candidates: List[_Candidate] = []
        candidate_ids: List[str] = []
        for m in matches:
            md = getattr(m, "metadata", None) or m.get("metadata") or {}
            tenant_id = md.get("tenant_id")
            if allowed_tenants is not None and tenant_id not in allowed_tenants:
                continue

            cid = getattr(m, "id", None) or m.get("id")
            if not cid:
                continue

            values = getattr(m, "values", None) or m.get("values")  # list[float] or None
            score = float(getattr(m, "score", None) or m.get("score", 0.0))
            candidates.append(_Candidate(id=str(cid), score=score, values=values, metadata=md))
            candidate_ids.append(str(cid))

        # Map chunk ids -> (page_content, metadata)
        id_to_payload = self.store._get_docs_for_ids(candidate_ids)

        # If we don't have values/embeddings, degrade gracefully to similarity ranking.
        if not candidates:
            return []

        if self.search_type != "mmr":
            selected = sorted(candidates, key=lambda c: c.score, reverse=True)[:k]
        else:
            # If values are missing, we can't compute doc-doc similarity; fallback.
            if any(c.values is None for c in candidates):
                selected = sorted(candidates, key=lambda c: c.score, reverse=True)[:k]
            else:
                selected = self._mmr_select(
                    query_vec=query_vec,
                    candidates=candidates,
                    k=k,
                    lambda_mult=lambda_mult,
                )

        out_docs: List[Document] = []
        for c in selected:
            payload = id_to_payload.get(c.id)
            if not payload:
                continue
            content, md = payload
            # Ensure tenant_id/source are present in metadata.
            md2 = dict(md or {})
            md2.setdefault("tenant_id", c.metadata.get("tenant_id"))
            md2.setdefault("source", c.metadata.get("source"))
            out_docs.append(Document(page_content=content, metadata=md2))
        return out_docs

    def _mmr_select(
        self,
        *,
        query_vec: List[float],
        candidates: List[_Candidate],
        k: int,
        lambda_mult: float,
    ) -> List[_Candidate]:
        # MMR selection over candidate set using cosine similarity.
        # Formula:
        #   MMR = lambda * sim(query, doc) - (1 - lambda) * max_{sel in selected} sim(doc, sel)

        # Precompute candidate vectors once.
        cand_vectors = [c.values or [] for c in candidates]
        if any(len(v) == 0 for v in cand_vectors):
            return sorted(candidates, key=lambda c: c.score, reverse=True)[:k]

        n = len(candidates)
        remaining_indices: List[int] = list(range(n))
        selected_indices: List[int] = []

        # Similarity between query and each candidate
        query_sims: List[float] = [_cosine_similarity(query_vec, v) for v in cand_vectors]

        # Memo for doc-doc cosine similarities.
        sim_cache: Dict[Tuple[int, int], float] = {}

        def doc_doc_sim(i: int, j: int) -> float:
            key = (i, j) if i <= j else (j, i)
            if key in sim_cache:
                return sim_cache[key]
            sim = _cosine_similarity(cand_vectors[i], cand_vectors[j])
            sim_cache[key] = sim
            return sim

        while remaining_indices and len(selected_indices) < k:
            if not selected_indices:
                # Choose best candidate by query relevance.
                best_i = max(remaining_indices, key=lambda i: query_sims[i])
            else:
                best_i = None
                best_mmr = float("-inf")
                for i in remaining_indices:
                    relevance = query_sims[i]
                    diversity_penalty = 0.0
                    for sj in selected_indices:
                        diversity_penalty = max(diversity_penalty, doc_doc_sim(i, sj))
                    mmr = lambda_mult * relevance - (1.0 - lambda_mult) * diversity_penalty
                    if mmr > best_mmr:
                        best_mmr = mmr
                        best_i = i
                if best_i is None:
                    break

            selected_indices.append(best_i)
            remaining_indices = [i for i in remaining_indices if i != best_i]

        return [candidates[i] for i in selected_indices]


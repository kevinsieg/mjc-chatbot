from pathlib import Path

import psycopg
from pgvector.psycopg import Vector

from app.db_util import ensure_document_chunks_table, get_connection
from app.mistral_service import chat_complete, embed_texts
from app.schemas.chat import ChatRequest
from app.settings import get_mistral_api_key, get_rag_top_k

SYSTEM_PROMPT = """Tu es l'assistant de la MJC de Fécamp.
Tu réponds en français, de façon claire et concise, en texte brut uniquement (pas de Markdown : pas de **, pas de #, pas de tirets de liste).
Tu t'appuies uniquement sur les extraits fournis dans la section « Contextes internes ».
Si les extraits ne contiennent pas l'information, dis-le honnêtement et propose une orientation générale (par exemple contacter la MJC) sans inventer de faits."""

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split long text into overlapping windows for embedding."""
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    step = max(1, size - overlap)
    for start in range(0, len(cleaned), step):
        piece = cleaned[start : start + size].strip()
        if piece:
            chunks.append(piece)
    return chunks


def _retrieve_context(conn: psycopg.Connection, query_vec: list[float], k: int) -> str:
    """Build a single context string from the closest chunks (cosine distance)."""
    sql = """
    SELECT source_path, content
    FROM document_chunks
    ORDER BY embedding <=> %(q)s
    LIMIT %(k)s
    """
    max_chars = 14_000
    parts: list[str] = []
    total = 0
    with conn.cursor() as cur:
        cur.execute(sql, {"q": Vector(query_vec), "k": k})
        rows = cur.fetchall()
    for source_path, content in rows:
        block = f"### {source_path}\n{content}\n\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    body = "".join(parts).strip()
    if not body:
        return "(Aucun document indexé pour le moment. Lance `make dev-data` après avoir défini MISTRAL_API_KEY.)"
    return body


def _messages_for_mistral(body: ChatRequest, context_block: str) -> list[dict[str, str]]:
    """Build chat messages with a single system block that carries RAG context."""
    system_content = f"{SYSTEM_PROMPT}\n\n--- Contextes internes ---\n{context_block}"
    out: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    for m in body.messages:
        if m.role not in ("user", "assistant"):
            continue
        out.append({"role": m.role, "content": m.content})
    return out


def answer_chat_turn(body: ChatRequest) -> str:
    """Embed last user turn, retrieve chunks, call Mistral chat."""
    if not get_mistral_api_key():
        raise ValueError("MISTRAL_API_KEY is not set")
    last = body.messages[-1]
    if last.role != "user":
        raise ValueError("Last message must be from the user")
    query = last.content.strip()
    if not query:
        raise ValueError("User message is empty")
    qvec = embed_texts([query])[0]
    k = get_rag_top_k()
    with get_connection() as conn:
        context_block = _retrieve_context(conn, qvec, k)
        conn.commit()
    messages = _messages_for_mistral(body, context_block)
    return chat_complete(messages)


def ingest_markdown_dir(root: Path) -> int:
    """Chunk all *.md under root, embed with Mistral, upsert into document_chunks."""
    if not get_mistral_api_key():
        raise RuntimeError("MISTRAL_API_KEY is not set")
    if not root.is_dir():
        raise FileNotFoundError(f"DATA_DIR is not a directory: {root}")
    files = sorted(root.rglob("*.md"))
    if not files:
        raise RuntimeError(f"No .md files found under {root}")
    total_rows = 0
    batch_embed = 16
    with get_connection() as conn:
        ensure_document_chunks_table(conn)
        conn.commit()
        for path in files:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
            raw = path.read_text(encoding="utf-8")
            chunks = chunk_text(raw)
            if not chunks:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM document_chunks WHERE source_path = %s", (rel,)
                    )
                conn.commit()
                continue
            all_vectors: list[list[float]] = []
            for i in range(0, len(chunks), batch_embed):
                batch = chunks[i : i + batch_embed]
                all_vectors.extend(embed_texts(batch))
            if len(all_vectors) != len(chunks):
                raise RuntimeError("Embedding batch length mismatch during ingest")
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM document_chunks WHERE source_path = %s", (rel,)
                )
                for idx, (content, vec) in enumerate(zip(chunks, all_vectors, strict=True)):
                    cur.execute(
                        """
                        INSERT INTO document_chunks (source_path, chunk_index, content, embedding)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (rel, idx, content, vec),
                    )
            total_rows += len(chunks)
            conn.commit()
    return total_rows

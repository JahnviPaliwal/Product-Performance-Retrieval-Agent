"""
rag/chunker.py
Pure-Python recursive text chunker — no langchain dependency.
"""


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks using recursive separators."""
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks = _split(text, separators, chunk_size)
    # Apply overlap by including a tail of the previous chunk
    if chunk_overlap <= 0 or len(chunks) < 2:
        return chunks
    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-chunk_overlap:]
        overlapped.append(prev_tail + chunks[i])
    return overlapped


def _split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    sep = ""
    for s in separators:
        if s and s in text:
            sep = s
            break

    if not sep:
        # Hard split
        return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size) if text[i:i + chunk_size].strip()]

    parts = text.split(sep)
    chunks, current = [], ""
    for part in parts:
        candidate = (current + sep + part).lstrip(sep) if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(part) > chunk_size:
                chunks.extend(_split(part, separators[separators.index(sep) + 1:], chunk_size))
                current = ""
            else:
                current = part
    if current.strip():
        chunks.append(current.strip())
    return chunks

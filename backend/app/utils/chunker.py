"""文本切块：段落优先 + 超长硬切（带 overlap）。"""
from app.core.config import settings


def _split_long_paragraph(para: str, size: int, overlap: int) -> list[str]:
    """超长段落按定长窗口硬切，相邻窗口保留 overlap 重叠。"""
    step = max(1, size - overlap)
    pieces: list[str] = []
    for i in range(0, len(para), step):
        piece = para[i : i + size]
        if not piece.strip():
            continue
        # 尾部已被前一窗口的 overlap 覆盖时跳过，避免碎块
        if i > 0 and len(piece) <= overlap:
            continue
        pieces.append(piece.strip())
    return pieces


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """把纯文本切成适合 embedding 的块。

    规则：
    1. 先按换行切段落，段落累积到 chunk_size 上限即成块（保持语义边界）；
    2. 单段超过 chunk_size 时硬切成定长窗口，相邻窗口重叠 overlap；
    3. 丢弃过短（<20 字）的碎块，除非它是唯一内容。
    """
    size = chunk_size if chunk_size is not None else settings.chunk_size
    ovl = overlap if overlap is not None else settings.chunk_overlap

    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

    # 先把超长段落硬切成不超过 size 的片段
    pieces: list[str] = []
    for para in paragraphs:
        if len(para) <= size:
            pieces.append(para)
        else:
            pieces.extend(_split_long_paragraph(para, size, ovl))

    # 片段按段落边界累积成块
    chunks: list[str] = []
    buffer = ""
    for piece in pieces:
        candidate = f"{buffer}\n{piece}" if buffer else piece
        if len(candidate) <= size or not buffer:
            buffer = candidate
        else:
            chunks.append(buffer)
            buffer = piece
    if buffer:
        chunks.append(buffer)

    # 过滤碎块
    filtered = [c for c in chunks if len(c) >= 20]
    return filtered if filtered else ([chunks[0]] if chunks else [])

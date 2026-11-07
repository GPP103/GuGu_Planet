"""切块工具测试。"""
from app.utils.chunker import chunk_text


def test_empty_text():
    assert chunk_text("") == []
    assert chunk_text("   \n  \n") == []


def test_short_text_single_chunk():
    text = "RAG 是检索增强生成。它先检索再生成。"
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert "RAG" in chunks[0]


def test_paragraphs_accumulate_within_size():
    paras = [f"第{i}段：" + "内容" * 20 for i in range(10)]
    text = "\n".join(paras)
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 120


def test_long_paragraph_hard_split_with_overlap():
    para = "甲" * 300
    chunks = chunk_text(para, chunk_size=100, overlap=20)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) <= 100
    # 相邻块之间有 overlap：后块开头内容出现在前块结尾
    assert chunks[1][:10] in chunks[0]


def test_tiny_fragments_filtered():
    text = "正文内容" * 30 + "\n短"
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert all(len(c) >= 20 for c in chunks)


def test_default_params_use_settings():
    text = "\n".join(["这是一个关于量子计算的段落，讲述了量子比特的原理与应用。"] * 40)
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)

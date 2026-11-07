"""文档解析测试。"""
import io

import pytest

from app.core.exceptions import DocumentParseError
from app.services.document_parser import parse_file


def test_parse_txt_utf8():
    text = parse_file("note.txt", "你好，RAG。".encode("utf-8"))
    assert "RAG" in text


def test_parse_txt_gbk():
    text = parse_file("note.txt", "中文笔记内容".encode("gbk"))
    assert "中文笔记" in text


def test_parse_md():
    text = parse_file("doc.md", "# 标题\n\n正文内容".encode("utf-8"))
    assert "正文内容" in text


def test_parse_docx_roundtrip():
    import docx

    buffer = io.BytesIO()
    d = docx.Document()
    d.add_paragraph("量子计算入门")
    d.add_paragraph("量子比特是基本单元")
    d.save(buffer)
    text = parse_file("doc.docx", buffer.getvalue())
    assert "量子比特" in text


def test_unsupported_ext():
    with pytest.raises(DocumentParseError) as e:
        parse_file("evil.exe", b"binary")
    assert "仅支持" in e.value.message


def test_empty_text_rejected():
    with pytest.raises(DocumentParseError):
        parse_file("empty.txt", b"   \n")


def test_broken_pdf_rejected():
    with pytest.raises(DocumentParseError):
        parse_file("bad.pdf", b"not a pdf at all")

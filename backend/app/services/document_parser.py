"""文档解析：PDF / docx / txt / md → 纯文本。"""
import io

from app.core.exceptions import DocumentParseError

ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".md"}


def parse_file(filename: str, data: bytes) -> str:
    """按扩展名解析上传文件为纯文本，失败抛 DocumentParseError。"""
    name = (filename or "").lower()
    ext = None
    for e in ALLOWED_EXTS:
        if name.endswith(e):
            ext = e
            break
    if ext is None:
        raise DocumentParseError("仅支持 PDF / docx / txt / md 文档")

    if ext == ".pdf":
        return _parse_pdf(data)
    if ext == ".docx":
        return _parse_docx(data)
    return _parse_text(data)


def _parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    except DocumentParseError:
        raise
    except Exception as e:
        raise DocumentParseError("PDF 解析失败，请确认文件未加密损坏") from e
    if not text.strip():
        raise DocumentParseError("未解析到有效文本（纯图片/扫描版 PDF 暂不支持）")
    return text


def _parse_docx(data: bytes) -> str:
    try:
        import docx

        document = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
    except Exception as e:
        raise DocumentParseError("Word 解析失败，请确认文件为 .docx 格式") from e
    if not text.strip():
        raise DocumentParseError("未解析到有效文本")
    return text


def _parse_text(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = data.decode("gbk")
        except UnicodeDecodeError as e:
            raise DocumentParseError("文本编码不支持，请使用 UTF-8 编码") from e
    if not text.strip():
        raise DocumentParseError("未解析到有效文本")
    return text

"""题目库缓存键生成。"""
import hashlib
import re


def normalize_cache_input(text: str) -> str:
    """归一化输入以提高缓存命中率：小写、去空白与标点。"""
    return re.sub(r"[\W_]+", "", (text or "").strip().lower())


def cache_key(text: str, question_count: int) -> str:
    raw = f"{normalize_cache_input(text)}|{question_count}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

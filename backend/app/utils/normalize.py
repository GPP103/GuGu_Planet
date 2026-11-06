"""题目字段归一化工具。"""

_TYPE_MAP = {
    "single": "single",
    "单选": "single",
    "single_choice": "single",
    "choice": "single",
    "multiple": "multiple",
    "多选": "multiple",
    "multi": "multiple",
    "multiple_choice": "multiple",
    "judge": "judge",
    "判断": "judge",
    "truefalse": "judge",
    "true_false": "judge",
    "tf": "judge",
}

_DIFFICULTY_MAP = {
    "easy": "easy",
    "简单": "easy",
    "medium": "medium",
    "中等": "medium",
    "hard": "hard",
    "困难": "hard",
}


def normalize_type(value: str) -> str:
    return _TYPE_MAP.get((value or "").strip().lower(), "single")


def normalize_difficulty(value: str) -> str:
    return _DIFFICULTY_MAP.get((value or "").strip().lower(), "medium")

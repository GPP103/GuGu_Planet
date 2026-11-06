"""ID 生成。"""
import secrets


def gen_quiz_id() -> str:
    return "quiz_" + secrets.token_hex(8)

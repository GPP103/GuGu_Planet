"""输入校验测试。"""
import pytest

from app.utils.content_filter import validate_input


def test_validate_empty_string():
    with pytest.raises(ValueError):
        validate_input("")


def test_validate_none():
    with pytest.raises(ValueError):
        validate_input(None)


def test_validate_whitespace_only():
    with pytest.raises(ValueError):
        validate_input("   \n  ")


def test_validate_too_long():
    with pytest.raises(ValueError):
        validate_input("a" * 2001)


def test_validate_ok_strips():
    assert validate_input("  hello world  ") == "hello world"

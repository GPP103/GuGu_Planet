"""FastAPI 公共依赖：当前登录用户。"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.db import get_db
from app.models.user import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError()
    token = authorization[len("Bearer "):]
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise AuthError() from None
    user = db.get(User, user_id)
    if user is None:
        raise AuthError()
    return user

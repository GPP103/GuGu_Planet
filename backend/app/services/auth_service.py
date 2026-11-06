"""登录服务。"""
from sqlalchemy.orm import Session

from app.core.exceptions import LoginCodeInvalidError
from app.core.security import create_access_token
from app.models.user import User
from app.models.user_schemas import LoginResponse
from app.services import wechat
from app.services.user_service import to_user_out


class AuthService:
    def __init__(self, db: Session, session_fetcher=None):
        self.db = db
        self.session_fetcher = session_fetcher or wechat.code2session

    def login(self, code: str) -> LoginResponse:
        data = self.session_fetcher(code)
        openid = data.get("openid")
        if not openid:
            raise LoginCodeInvalidError()

        user = self.db.query(User).filter(User.openid == openid).first()
        if user is None:
            user = User(openid=openid, unionid=data.get("unionid"))
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        token = create_access_token(user.id)
        return LoginResponse(token=token, user=to_user_out(user))

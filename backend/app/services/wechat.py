"""微信登录凭证校验（code2session）。"""
import httpx

from app.core.config import settings
from app.core.exceptions import WechatLoginError


def code2session(code: str) -> dict:
    """调用微信 jscode2session，返回 {openid, session_key, unionid}。"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10.0)
    except Exception as e:
        raise WechatLoginError() from e

    try:
        data = resp.json()
    except Exception as e:
        raise WechatLoginError() from e

    if data.get("errcode"):
        raise WechatLoginError(f"微信登录失败（errcode={data['errcode']}）")
    return data

"""图片存储抽象：默认存本地并由 FastAPI 静态目录提供访问；后续可换 COS。

换存储只需实现 save()，image_service 不感知具体实现。
"""
import os

from app.core.config import settings

# 对外访问前缀（FastAPI 挂载点）
STATIC_PREFIX = "/static/images"


class LocalImageStorage:
    def __init__(self, root: str | None = None):
        self.root = root if root is not None else settings.image_dir
        os.makedirs(self.root, exist_ok=True)

    def exists(self, name: str) -> bool:
        return os.path.isfile(os.path.join(self.root, name))

    def save(self, name: str, data: bytes) -> str:
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return f"{STATIC_PREFIX}/{name}"


def get_image_storage() -> LocalImageStorage:
    """存储工厂（测试注入临时目录；换 COS 时改这里）。"""
    return LocalImageStorage()

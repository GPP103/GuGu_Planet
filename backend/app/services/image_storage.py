"""图片存储：默认腾讯云 COS（公有读），未配置凭证时退回本地静态目录。

换/加存储只需实现 exists(name) 与 save(name, data) -> 可访问 URL，
image_service 不感知具体实现。
"""
import os

from app.core.config import settings

# 本地静态目录的对外访问前缀（FastAPI 挂载点）
STATIC_PREFIX = "/static/images"


class LocalImageStorage:
    def __init__(self, root: str | None = None, url_prefix: str | None = None):
        self.root = root if root is not None else settings.image_dir
        self.url_prefix = url_prefix if url_prefix is not None else STATIC_PREFIX
        os.makedirs(self.root, exist_ok=True)

    def exists(self, name: str) -> bool:
        return os.path.isfile(os.path.join(self.root, name))

    def url_for(self, name: str) -> str:
        return f"{self.url_prefix}/{name}"

    def save(self, name: str, data: bytes) -> str:
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return self.url_for(name)


class CosImageStorage:
    """腾讯云 COS 存储。凭证仅从 .env 读取（SecretStr，不会进日志）。"""

    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
        secret_id: str | None = None,
        secret_key: str | None = None,
        prefix: str | None = None,
        client=None,
    ):
        self.bucket = bucket if bucket is not None else settings.cos_bucket
        self.region = region if region is not None else settings.cos_region
        self.prefix = prefix if prefix is not None else settings.cos_prefix
        if client is not None:
            self.client = client
        else:
            from qcloud_cos import CosConfig, CosS3Client

            sid = secret_id if secret_id is not None else settings.cos_secret_id.get_secret_value()
            skey = secret_key if secret_key is not None else settings.cos_secret_key.get_secret_value()
            self.client = CosS3Client(
                CosConfig(Region=self.region, SecretId=sid, SecretKey=skey, Scheme="https")
            )

    def _key(self, name: str) -> str:
        return f"{self.prefix}/{name}"

    def url_for(self, name: str) -> str:
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{self._key(name)}"

    def exists(self, name: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(name))
            return True
        except Exception:  # noqa: BLE001 不存在/网络异常都当作未命中，交给生成流程
            return False

    def save(self, name: str, data: bytes) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(name),
            Body=data,
            ContentType="image/png",
        )
        return self.url_for(name)


def get_image_storage():
    """存储工厂：配了 COS 凭证用 COS，否则本地（测试可注入）。"""
    if settings.image_backend == "cos" and settings.cos_bucket and settings.cos_secret_id.get_secret_value():
        try:
            return CosImageStorage()
        except Exception:  # noqa: BLE001 SDK 缺失/初始化失败 → 退回本地
            pass
    return LocalImageStorage()


def get_question_image_storage():
    """题目配图存储：与海报插画分开前缀/目录，便于统计与清理。"""
    if settings.image_backend == "cos" and settings.cos_bucket and settings.cos_secret_id.get_secret_value():
        try:
            return CosImageStorage(prefix=settings.question_image_prefix)
        except Exception:  # noqa: BLE001
            pass
    return LocalImageStorage(
        root=os.path.join(settings.image_dir, "questions"),
        url_prefix=f"{STATIC_PREFIX}/questions",
    )

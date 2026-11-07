"""应用配置。"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend 项目根目录（config.py 位于 app/core/ 下，往上三层）
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "咕咕星球 GuGu API"
    app_version: str = "0.1.0"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    # LLM 调用参数
    llm_timeout: int = 30
    llm_max_retries: int = 2
    llm_max_tokens: int = 1500
    quiz_temperature: float = 0.4
    report_temperature: float = 0.5

    # 出题约束
    default_question_count: int = 3
    max_input_chars: int = 2000

    # 微信小程序
    wechat_appid: str = ""
    wechat_secret: str = ""

    # MySQL
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "gugu_star"

    # JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # Tavily 联网搜索
    tavily_api_key: str = ""
    tavily_search_depth: str = "advanced"
    tavily_max_results: int = 5
    tavily_timeout: int = 15

    # 千问AI（阿里百炼）embedding（RAG 知识库）
    embedding_api_key: str = ""
    embedding_base_url: str = "https://maas.qianwenaiapi.com/compatible-mode/v1"
    embedding_model: str = "qwen3.7-text-embedding-flash"
    embedding_dimensions: int = 1024
    embedding_timeout: int = 30

    # 知识库（RAG）
    vector_backend: str = "chroma"  # chroma | sqlite
    chroma_dir: str = str(BASE_DIR / "data" / "chroma")
    vector_dir: str = str(BASE_DIR / "data" / "vectors")
    chunk_size: int = 500
    chunk_overlap: int = 50
    kb_top_k: int = 5
    kb_max_file_size: int = 5 * 1024 * 1024

    # AI 生图（分享海报插画）
    image_api_key: str = ""
    image_base_url: str = "https://maas.qianwenaiapi.com/compatible-mode/v1"
    image_model: str = "qwen-image-3.0"
    image_size: str = "1024x1024"
    image_timeout: int = 180
    image_dir: str = str(BASE_DIR / "data" / "images")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


settings = Settings()

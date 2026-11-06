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
    quiz_temperature: float = 0.4
    report_temperature: float = 0.5

    # 出题约束
    default_question_count: int = 5
    max_input_chars: int = 2000


settings = Settings()

"""
Central config: env vars for OpenAI, Neo4j, etc.
Use .env file or export in shell.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (OpenAI)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_output_tokens: int = 16384
    # 单次调用时发给 API 的合同文本最大字符数；snippet-only clause text 下用全文可跑完并得到约 40 clauses
    openai_max_input_chars: int = 120000

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # App
    debug: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

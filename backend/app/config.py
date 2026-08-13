from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central place for every environment-driven setting. Import `settings`
    from this module rather than reading os.environ directly, so the whole
    app has one source of truth.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    openai_api_key: str = "sk-placeholder"
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    embedding_mode: str = "local"  # "local" | "openai"
    openai_embedding_model: str = "text-embedding-3-small"

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    database_url: str = "sqlite:///./dar_global.db"
    vector_db_dir: str = "./chroma_store"

    # Guardrails
    max_turns_before_human_handoff: int = 12
    allowed_topic_label: str = "dar_global_real_estate"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

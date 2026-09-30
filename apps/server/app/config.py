from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    projects_dir: str = "./projects"
    default_voice: str = "zh-TW-YunJheNeural"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def projects_path(self) -> Path:
        path = Path(self.projects_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()

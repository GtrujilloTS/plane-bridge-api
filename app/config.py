from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    plane_base_url: str = "https://plane.takumi-dev.com"
    plane_api_token: str = ""
    default_workspace_slug: str = "citelis"
    bridge_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

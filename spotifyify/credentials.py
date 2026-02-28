from pydantic_settings import BaseSettings


class SpotifyCredentials(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8888/callback"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

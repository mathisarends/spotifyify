from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SpotifyCredentials(BaseSettings):
    """Environment-backed credentials used by the async Spotify client."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    client_id: str | None = Field(default=None, validation_alias="SPOTIFY_CLIENT_ID")
    client_secret: SecretStr | None = Field(
        default=None, validation_alias="SPOTIFY_CLIENT_SECRET"
    )
    redirect_uri: str | None = Field(
        default=None, validation_alias="SPOTIFY_REDIRECT_URI"
    )
    access_token: SecretStr | None = Field(
        default=None, validation_alias="SPOTIFY_ACCESS_TOKEN"
    )
    refresh_token: SecretStr | None = Field(
        default=None, validation_alias="SPOTIFY_REFRESH_TOKEN"
    )
    token_expires_at: int | None = Field(
        default=None, validation_alias="SPOTIFY_TOKEN_EXPIRES_AT"
    )

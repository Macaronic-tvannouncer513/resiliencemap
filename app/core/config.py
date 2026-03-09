from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://resiliencemap:resiliencemap@localhost:5432/resiliencemap"

    # External APIs
    noaa_api_base: str = "https://api.weather.gov"
    usgs_earthquake_api: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    fema_nfhl_wfs: str = (
        "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    )
    census_api_key: str = ""

    # Alerting
    alert_webhook_url: str = ""
    alert_email: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

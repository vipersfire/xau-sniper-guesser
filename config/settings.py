from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field("postgresql+asyncpg://postgres:postgres@localhost:5432/xauusd_sniper")

    # MT5
    mt5_login: int = Field(0)
    mt5_password: str = Field("")
    mt5_server: str = Field("MIFX-Demo")
    mt5_path: str = Field("")  # path to MT5 terminal if needed

    # FRED API
    fred_api_key: str = Field("")

    # Nasdaq Data Link (COT)
    nasdaq_api_key: str = Field("")

    # OANDA
    oanda_api_key: str = Field("")
    oanda_account_id: str = Field("")
    oanda_environment: str = Field("practice")  # practice | live

    # Telegram
    telegram_bot_token: str = Field("")
    telegram_chat_id: str = Field("")

    # Trading
    account_balance_override: float = Field(0.0)  # 0 = use live MT5 balance
    max_concurrent_positions: int = Field(3)
    paper_trading: bool = Field(True)

    # OTA
    ota_watch_dir: str = Field(str(BASE_DIR / "config"))
    ota_strategy_params_path: str = Field(str(BASE_DIR / "config" / "strategy_params.json"))

    # Logging
    log_level: str = Field("INFO")
    log_dir: str = Field(str(BASE_DIR / "logs"))

    # Model artifacts
    artifacts_dir: str = Field(str(BASE_DIR / "models" / "artifacts"))


settings = Settings()

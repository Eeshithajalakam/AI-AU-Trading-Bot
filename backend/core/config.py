from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "AI AU Trading Backend"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    PUBLIC_API_URL: str = ""
    PUBLIC_FRONTEND_URL: str = ""

    SECRET_KEY: str = "super-secret-jwt-key-replace-in-production"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    RATE_LIMIT_PER_MINUTE: int = 120
    API_TIMEOUT_SECONDS: int = 30

    MARKET_SYMBOL: str = "GC=F"
    MARKET_INTERVAL: str = "1m"
    MODEL_DIR: str = str(BASE_DIR / "models")
    MODEL_PATH: str = ""
    AUTO_TRAIN_ON_STARTUP: bool = True
    PREDICTION_INTERVAL_SECONDS: int = 10
    RETRAIN_INTERVAL_HOURS: int = 168

    AUTO_TRADE_ENABLED: bool = True
    PAPER_TRADING_MODE: bool = True
    MT5_SYMBOL: str = "XAUUSD"

    MT5_LOGIN: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = ""

    MT5_DEMO_LOGIN: int = 0
    MT5_DEMO_PASSWORD: str = ""
    MT5_DEMO_SERVER: str = ""
    MT5_LIVE_LOGIN: int = 0
    MT5_LIVE_PASSWORD: str = ""
    MT5_LIVE_SERVER: str = ""

    # Risk — institutional defaults
    MAX_SPREAD_POINTS: float = 45.0
    MAX_SLIPPAGE_POINTS: float = 30.0
    TRADE_COOLDOWN_SECONDS: int = 90
    MAX_OPEN_TRADES: int = 2
    MAX_DAILY_LOSS_USD: float = 300.0
    MAX_DRAWDOWN_PCT: float = 0.08
    MAX_CONSECUTIVE_LOSSES: int = 4
    MIN_RISK_REWARD: float = 1.5
    KELLY_FRACTION: float = 0.25
    CAPITAL_PRESERVATION_MODE: bool = False
    TRADING_HOURS_UTC_START: int = 0
    TRADING_HOURS_UTC_END: int = 24
    USE_KELLY_SIZING: bool = True

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def resolved_model_path(self) -> str:
        if self.MODEL_PATH:
            return self.MODEL_PATH
        return str(Path(self.MODEL_DIR) / "xau_lstm.pt")

    @property
    def scaler_path(self) -> str:
        return str(Path(self.MODEL_DIR) / "xau_scaler.pkl")

    @property
    def mt5_login(self) -> int:
        return self.MT5_LOGIN or self.MT5_DEMO_LOGIN or self.MT5_LIVE_LOGIN

    @property
    def mt5_password(self) -> str:
        return self.MT5_PASSWORD or self.MT5_DEMO_PASSWORD or self.MT5_LIVE_PASSWORD

    @property
    def mt5_server(self) -> str:
        return self.MT5_SERVER or self.MT5_DEMO_SERVER or self.MT5_LIVE_SERVER

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = list(self.BACKEND_CORS_ORIGINS)
        if self.PUBLIC_FRONTEND_URL and self.PUBLIC_FRONTEND_URL not in origins:
            origins.append(self.PUBLIC_FRONTEND_URL.rstrip("/"))
        return origins


settings = Settings()

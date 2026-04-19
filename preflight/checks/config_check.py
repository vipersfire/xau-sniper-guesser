from preflight.checks.base_check import BaseCheck, CheckResult
from config.settings import settings

REQUIRED_ENV_VARS = [
    ("mt5_login", "MT5_LOGIN"),
    ("mt5_password", "MT5_PASSWORD"),
    ("mt5_server", "MT5_SERVER"),
    ("fred_api_key", "FRED_API_KEY"),
    ("nasdaq_api_key", "NASDAQ_API_KEY"),
    ("oanda_api_key", "OANDA_API_KEY"),
    ("database_url", "DATABASE_URL"),
]


class ConfigCheck(BaseCheck):
    name = "Config"
    fix_command = "Edit .env"

    async def run(self) -> CheckResult:
        missing = []
        for attr, env_name in REQUIRED_ENV_VARS:
            val = getattr(settings, attr, None)
            if not val or (isinstance(val, int) and val == 0 and attr == "mt5_login"):
                missing.append(env_name)
        if missing:
            return self._fail(f"Missing env vars: {', '.join(missing)}")
        return self._pass("all required env vars present")

from preflight.checks.base_check import BaseCheck, CheckResult


class BrokerCheck(BaseCheck):
    name = "MT5 connection"
    fix_command = None  # must be done manually

    async def run(self) -> CheckResult:
        try:
            from mt5.adapter import MT5Adapter
            adapter = MT5Adapter()
            if not adapter.connect():
                return self._fail("MT5 connection failed — check terminal is open and logged in")
            info = adapter.account_info()
            broker = info.get("company", "unknown")
            account = info.get("login", "?")
            at_enabled = info.get("trade_allowed", False)
            adapter.disconnect()
            if not at_enabled:
                return self._fail("AutoTrading is DISABLED in MT5 — enable it first")
            return self._pass(f"{broker} | account {account} | connected")
        except Exception as e:
            return self._fail(f"MT5 error: {e}")

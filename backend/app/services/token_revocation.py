from time import time


class InMemoryTokenDenylist:
    def __init__(self) -> None:
        self._revoked_until: dict[str, int] = {}

    def revoke(self, jti: str, expires_at: int) -> None:
        self._purge_expired()
        self._revoked_until[jti] = expires_at

    def is_revoked(self, jti: str) -> bool:
        self._purge_expired()
        expires_at = self._revoked_until.get(jti)
        if expires_at is None:
            return False
        if expires_at <= int(time()):
            self._revoked_until.pop(jti, None)
            return False
        return True

    def _purge_expired(self) -> None:
        now = int(time())
        expired = [jti for jti, expires_at in self._revoked_until.items() if expires_at <= now]
        for jti in expired:
            self._revoked_until.pop(jti, None)


token_denylist = InMemoryTokenDenylist()

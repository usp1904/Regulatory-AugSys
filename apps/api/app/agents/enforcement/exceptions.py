"""Enforcement failures. Not regulatory decisions."""


class AgentEnforcementError(Exception):
    def __init__(self, message: str, *, http_status: int = 400) -> None:
        super().__init__(message)
        self.http_status = http_status


class UnauthorizedAgentAccess(AgentEnforcementError):
    def __init__(self, message: str = "Unauthorized agent access blocked") -> None:
        super().__init__(message, http_status=403)


class SchemaGuardrailError(AgentEnforcementError):
    def __init__(self, message: str) -> None:
        super().__init__(message, http_status=422)


class DataGovernanceError(AgentEnforcementError):
    def __init__(self, message: str) -> None:
        super().__init__(message, http_status=403)

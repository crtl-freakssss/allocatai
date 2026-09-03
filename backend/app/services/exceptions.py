from typing import Any, Optional


class AllocateAIServiceError(Exception):
    """Base exception for all domain and service-layer failures."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(AllocateAIServiceError):
    """Raised when a requested resource does not exist in the database."""

    def __init__(
        self,
        entity_type: str,
        identifier: Any,
        message: Optional[str] = None,
    ) -> None:
        msg = message or f"{entity_type} with identifier '{identifier}' was not found"
        super().__init__(msg, details={"entity_type": entity_type, "identifier": str(identifier)})
        self.entity_type = entity_type
        self.identifier = identifier


class ResourceAlreadyExistsError(AllocateAIServiceError):
    """Raised when an entity with a unique key or reference already exists."""

    def __init__(
        self,
        entity_type: str,
        key: str,
        value: Any,
        message: Optional[str] = None,
    ) -> None:
        msg = message or f"{entity_type} with {key}='{value}' already exists"
        super().__init__(msg, details={"entity_type": entity_type, "key": key, "value": str(value)})
        self.entity_type = entity_type
        self.key = key
        self.value = value


class ServiceValidationError(AllocateAIServiceError):
    """Raised when business logic or cross-entity validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Any] = None) -> None:
        det = details or {}
        if field:
            det["field"] = field
        super().__init__(message, details=det)
        self.field = field


class ConflictError(AllocateAIServiceError):
    """Raised when an operation conflicts with the current resource state or relational link."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message, details=details)


class InvalidStateTransitionError(AllocateAIServiceError):
    """Raised when an entity lifecycle transition is invalid or forbidden by contract."""

    def __init__(
        self,
        entity_type: str,
        current_state: str,
        target_state: str,
        message: Optional[str] = None,
    ) -> None:
        msg = (
            message
            or f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'"
        )
        super().__init__(
            msg,
            details={
                "entity_type": entity_type,
                "current_state": current_state,
                "target_state": target_state,
            },
        )
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state


class ProcessingError(AllocateAIServiceError):
    """Raised when an orchestration workflow or engine execution encounters a processing failure."""

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        det = {"cause": str(cause)} if cause else {}
        super().__init__(message, details=det)
        self.__cause__ = cause

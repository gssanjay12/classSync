import enum

class UserRole(str, enum.Enum):
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"
    TEACHER = "FACULTY" # Alias

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str) and value.upper() in ("TEACHER", "FACULTY"):
            return cls.FACULTY
        return super()._missing_(value)

class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"

class PollStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"

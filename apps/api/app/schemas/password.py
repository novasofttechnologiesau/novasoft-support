from typing import Annotated
from pydantic import AfterValidator


def validate_password(value: str) -> str:
    if not 12 <= len(value.encode("utf-8")) <= 72:
        raise ValueError("Password must be between 12 and 72 UTF-8 bytes")
    return value


NewPassword = Annotated[str, AfterValidator(validate_password)]

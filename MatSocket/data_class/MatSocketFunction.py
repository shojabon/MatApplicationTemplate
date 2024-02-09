from __future__ import annotations

import socket
from typing import TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from MatSocket import MatSocket


class MatSocketFunction:

    def information(self):
        pass

    def __init__(self):
        self.path: str = ""
        self.function_schema: BaseModel | None = None
        self.main: MatSocket | None = None
        self.information()
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if self.path.endswith("/"):
            self.path = self.path[:-1]

    def handle_message_internal(self, origin: str, data: dict):
        if self.function_schema is not None:
            try:
                data = self.function_schema.parse_obj(data)
            except Exception as e:
                return "error_schema_invalid", {"message": str(e)}

        return self.handle_message(origin, data)

    def handle_message(self, origin: str, data: dict):
        pass

    def get_json(self) -> dict:
        return {
            "path": self.path,
            "function_schema": self.function_schema.schema_json() if self.function_schema is not None else None
        }

    def from_json(self, data: dict):
        self.path = data["path"]
        self.function_schema = data["function_schema"]
        return self

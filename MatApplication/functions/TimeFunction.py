import time

from expiringdict import ExpiringDict
from pydantic import BaseModel

from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class TimeFunctionInput(BaseModel):
    target: str


class TimeFunction(MatSocketFunction):

    def information(self):
        self.path = "/time"
        self.function_schema = TimeFunctionInput

    def handle_message(self, origin: str, data: dict):
        return "success", {"time": time.time()}
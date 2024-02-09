import time

from expiringdict import ExpiringDict

from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class PingFunction(MatSocketFunction):

    def information(self):
        self.path = "/system/ping"
        self.function_schema = None

    def handle_message(self, origin: str, data: dict):
        return "success", {"time": time.time()}
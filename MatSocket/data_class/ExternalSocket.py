from __future__ import annotations

import time
from threading import Thread
from typing import TYPE_CHECKING

from MatSocket.data_class.MatSocketFunction import MatSocketFunction

if TYPE_CHECKING:
    from MatSocket import MatSocket


class ExternalSocket:

    def __init__(self, main: MatSocket):
        self.name = None
        self.main: MatSocket = main

        self.known_functions: dict[str, MatSocketFunction] = {}

        self.latency = 10000000

    def is_online(self) -> bool:
        send_time = time.time()
        result = self.main.send_message(self.name, "/system/ping", {}, reply=True, reply_timeout=1)
        if result is None:
            return False
        accept_time = time.time()
        self.latency = accept_time - send_time
        return True

    def update_functions(self):
        result = self.main.send_message(self.name, "/system/socket/info", {}, reply=True, reply_timeout=1)
        if result is None:
            return False
        if result["status"] != "success":
            return False
        for key, value in result["data"]["functions"].items():
            socket_function = MatSocketFunction()
            socket_function.from_json(value)
            self.known_functions[socket_function.path] = socket_function

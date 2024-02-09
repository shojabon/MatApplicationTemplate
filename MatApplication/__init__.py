import json
import time

from MatSocket import MatSocket


class MatApplication:

    def __init__(self):
        config_file = open("config/config.json", "r")
        self.config = json.load(config_file)
        config_file.close()
        socket_config = self.config["socket"]
        self.mat_socket = MatSocket(socket_config["name"], socket_config["host"], socket_config["port"], socket_config["username"], socket_config["password"])

        self.mat_socket.start()
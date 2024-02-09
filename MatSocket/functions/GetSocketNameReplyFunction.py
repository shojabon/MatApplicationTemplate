import time

from MatSocket.data_class.ExternalSocket import ExternalSocket
from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class GetSocketNameReplyFunction(MatSocketFunction):

    def information(self):
        self.path = "/system/socket/name/reply"
        self.function_schema = None

    def handle_message(self, origin: str, data: dict):
        print("found socket", origin)
        external_socket = ExternalSocket(self.main)
        external_socket.name = origin
        self.main.external_sockets[origin] = external_socket
        self.main.external_sockets[origin].update_functions()
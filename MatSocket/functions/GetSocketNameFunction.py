from expiringdict import ExpiringDict

from MatSocket.data_class.ExternalSocket import ExternalSocket
from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class GetSocketNameFunction(MatSocketFunction):

    def information(self):
        self.path = "/system/socket/name"
        self.function_schema = None

    def handle_message(self, origin: str, data: dict):
        external_socket = ExternalSocket(self.main)
        external_socket.name = origin
        self.main.external_sockets[origin] = external_socket
        print("new socket", origin)

        self.main.send_message(origin, "/system/socket/name/reply", {"name": self.main.self_name})
        self.main.external_sockets[origin].update_functions()
